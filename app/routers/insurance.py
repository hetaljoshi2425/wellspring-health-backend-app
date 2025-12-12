from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import InsuranceInfoCreate, InsuranceInfoRead

router = APIRouter()

@router.post("/", response_model=InsuranceInfoRead)
async def upsert_insurance(info_in: InsuranceInfoCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.InsuranceInfo).where(models.InsuranceInfo.client_id == info_in.client_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        for field, value in info_in.model_dump().items():
            setattr(existing, field, value)
        await db.commit()
        await db.refresh(existing)
        return existing
    info = models.InsuranceInfo(**info_in.model_dump())
    db.add(info)
    await db.commit()
    await db.refresh(info)
    return info

@router.get("/client/{client_id}", response_model=InsuranceInfoRead | None)
async def get_insurance_for_client(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.InsuranceInfo).where(models.InsuranceInfo.client_id == client_id)
    )
    return result.scalar_one_or_none()
