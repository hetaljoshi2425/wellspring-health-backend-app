from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import StaffPreferenceCreate, StaffPreferenceRead

router = APIRouter()

@router.post("/preferences", response_model=StaffPreferenceRead)
async def set_staff_preference(pref_in: StaffPreferenceCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.StaffPreference).where(
            models.StaffPreference.user_id == pref_in.user_id,
            models.StaffPreference.key == pref_in.key,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.value = pref_in.value
        await db.commit()
        await db.refresh(existing)
        return existing

    pref = models.StaffPreference(**pref_in.model_dump())
    db.add(pref)
    await db.commit()
    await db.refresh(pref)
    return pref

@router.get("/preferences/{user_id}", response_model=List[StaffPreferenceRead])
async def list_staff_preferences(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.StaffPreference).where(models.StaffPreference.user_id == user_id)
    )
    return result.scalars().all()
