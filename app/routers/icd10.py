from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import ICD10CodeCreate, ICD10CodeRead

router = APIRouter()

@router.post("/", response_model=ICD10CodeRead)
async def create_icd10(code_in: ICD10CodeCreate, db: AsyncSession = Depends(get_db)):
    code = models.ICD10Code(**code_in.model_dump())
    db.add(code)
    await db.commit()
    await db.refresh(code)
    return code

@router.get("/", response_model=List[ICD10CodeRead])
async def list_icd10(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.ICD10Code))
    return result.scalars().all()

@router.get("/search", response_model=List[ICD10CodeRead])
async def search_icd10(q: str, db: AsyncSession = Depends(get_db)):
    term = f"%{q}%"
    result = await db.execute(
        select(models.ICD10Code).where(
            (models.ICD10Code.description.ilike(term)) | (models.ICD10Code.code.ilike(term))
        ).limit(20)
    )
    return result.scalars().all()
