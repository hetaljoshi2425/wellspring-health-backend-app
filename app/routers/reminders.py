from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import ReminderLogCreate, ReminderLogRead

router = APIRouter()

@router.post("/", response_model=ReminderLogRead)
async def create_reminder(rem_in: ReminderLogCreate, db: AsyncSession = Depends(get_db)):
    rem = models.ReminderLog(**rem_in.model_dump())
    db.add(rem)
    await db.commit()
    await db.refresh(rem)
    return rem

@router.get("/client/{client_id}", response_model=List[ReminderLogRead])
async def list_reminders(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.ReminderLog).where(models.ReminderLog.client_id == client_id)
    )
    return result.scalars().all()
