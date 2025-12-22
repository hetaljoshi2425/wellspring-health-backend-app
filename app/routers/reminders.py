from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import datetime

from ..database import get_db
from .. import models
from ..schemas import ReminderLogCreate, ReminderLogRead, ReminderLogUpdate
from app.utils.auth_utils import get_current_user


router = APIRouter()

@router.post("/", response_model=ReminderLogRead)
async def create_reminder(rem_in: ReminderLogCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user),):
    rem = models.ReminderLog(**rem_in.model_dump())
    db.add(rem)
    await db.commit()
    await db.refresh(rem)
    return rem

@router.get("/client/{client_id}", response_model=List[ReminderLogRead])
async def list_reminders(client_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user),):
    result = await db.execute(
        select(models.ReminderLog).where(models.ReminderLog.client_id == client_id)
    )
    return result.scalars().all()


@router.patch("/{reminder_id}", response_model=ReminderLogRead)
async def update_reminder(
    reminder_id: int,
    rem_in: ReminderLogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(models.ReminderLog).where(models.ReminderLog.id == reminder_id)
    )
    rem = result.scalar_one_or_none()

    if not rem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    data = rem_in.model_dump(exclude_unset=True)

    if "completed" in data:
        rem.completed_at = datetime.datetime.utcnow() if data["completed"] else None

    for k, v in data.items():
        setattr(rem, k, v)

    await db.commit()
    await db.refresh(rem)
    return rem


@router.delete("/{reminder_id}", status_code=204)
async def delete_reminder(
    reminder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(models.ReminderLog).where(models.ReminderLog.id == reminder_id)
    )
    rem = result.scalar_one_or_none()

    if not rem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    await db.delete(rem)
    await db.commit()
    
    return {
        "message": "Reminder deleted successfully",
        "reminder_id": reminder_id
    }