from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import ICD10CodeCreate, ICD10CodeRead, ICD10CodeUpdate

from app.utils.auth_utils import get_current_user
from app.models import ICD10Code
router = APIRouter()

@router.post("/", response_model=ICD10CodeRead)
async def create_icd10(payload: ICD10CodeCreate, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    code_value = payload.code.strip().upper()
    
    result = await db.execute(select(ICD10Code).where(ICD10Code.code == code_value))
    if result.scalar_one_or_none():
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success":False, "message": "ICD10 code already exists"})
    
    code = ICD10Code(
        code=code_value,
        description=payload.description.strip(),
        category=payload.category.strip() if payload.category else None,
        is_active=payload.is_active,
    )
    db.add(code)
    await db.commit()
    await db.refresh(code)
    return code

@router.get("/", response_model=List[ICD10CodeRead])
async def list_icd10(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user), ):
    result = await db.execute(select(models.ICD10Code))
    return result.scalars().all()

@router.get("/search", response_model=List[ICD10CodeRead])
async def search_icd10(q: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user), ):
    if not q.strip():
        return []
    
    term = f"%{q.strip()}%"
    result = await db.execute(
        select(models.ICD10Code).where(
            (models.ICD10Code.description.ilike(term)) | (models.ICD10Code.code.ilike(term))
        ).limit(20)
    )
    return result.scalars().all()


@router.put("/{icd10_id}", response_model=ICD10CodeRead)
async def update_icd10(
    icd10_id: int,
    payload: ICD10CodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(select(ICD10Code).where(ICD10Code.id == icd10_id))
    icd10 = result.scalar_one_or_none()

    if not icd10:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success":False, "message": "ICD10 code not found"})

    update_data = payload.model_dump(exclude_unset=True)

    # Validate code uniqueness
    if "code" in update_data:
        new_code = update_data["code"].strip().upper()

        dup_check = await db.execute(select(ICD10Code).where(ICD10Code.code == new_code, ICD10Code.id != icd10_id))
        if dup_check.scalar_one_or_none():
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success":False, "message":"ICD10 code already exists"})

        icd10.code = new_code

    if "description" in update_data:
        icd10.description = update_data["description"].strip()

    if "category" in update_data:
        icd10.category = (
            update_data["category"].strip()
            if update_data["category"] else None
        )

    if "is_active" in update_data:
        icd10.is_active = update_data["is_active"]

    await db.commit()
    await db.refresh(icd10)
    return icd10


@router.delete("/{icd10_id}")
async def delete_icd10(
    icd10_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ICD10Code).where(ICD10Code.id == icd10_id)
    )
    icd10 = result.scalar_one_or_none()

    if not icd10:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success":False, "message":"ICD10 code not found"})

    await db.delete(icd10)
    await db.commit()

    return {
        "success": True,
        "message": "ICD10 code deleted successfully"
    }
