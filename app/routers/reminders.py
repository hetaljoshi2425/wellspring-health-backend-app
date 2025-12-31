from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import datetime

from ..database import get_db
from .. import models
from ..schemas import ReminderLogCreate, ReminderLogRead, ReminderLogUpdate
from app.utils.auth_utils import get_current_user


router = APIRouter()

@router.post("/", response_model=ReminderLogRead)
async def create_reminder(rem_in: ReminderLogCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user),):
    client_result = await db.execute(select(models.Client).where(models.Client.id == rem_in.client_id))
    client = client_result.scalar_one_or_none()

    if not client:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={ "success": False, "message": "Client not found"})
    try:
        data = rem_in.model_dump()
        due_date = data.get("due_date")
        
        if due_date:
            if due_date.tzinfo is not None:
                due_date = due_date.replace(tzinfo=None)

            if due_date < datetime.datetime.now():
                return JSONResponse( status_code=status.HTTP_400_BAD_REQUEST, content={ "success": False, "message": "due_date cannot be in the past"})

            data["due_date"] = due_date
            
        rem = models.ReminderLog(**data)
        db.add(rem)
        await db.commit()
        await db.refresh(rem)
        
        result = await db.execute(select(models.ReminderLog).options(selectinload(models.ReminderLog.client)).where(models.ReminderLog.id == rem.id))
        return result.scalar_one()
    
    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)},
        )

@router.get("/client/{client_id}", response_model=List[ReminderLogRead])
async def list_reminders(client_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user),):
    try:
        result = await db.execute(select(models.ReminderLog).options(selectinload(models.ReminderLog.client)).where(models.ReminderLog.client_id == client_id))
        return result.scalars().all()
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)},
        )   

@router.patch("/{reminder_id}", response_model=ReminderLogRead)
async def update_reminder(
    reminder_id: int,
    rem_in: ReminderLogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(models.ReminderLog).options(selectinload(models.ReminderLog.client)).where(models.ReminderLog.id == reminder_id))
    rem = result.scalar_one_or_none()

    if not rem:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Reminder not found"})

    try:
        data = rem_in.model_dump(exclude_unset=True)
        if "due_date" in data and data["due_date"] is not None:
            due_date = data["due_date"]

            if due_date.tzinfo is not None:
                due_date = due_date.replace(tzinfo=None)

            if due_date < datetime.datetime.now():
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": "due_date cannot be in the past"})

            data["due_date"] = due_date
            
        if "completed" in data:
            rem.completed_at = datetime.datetime.now() if data["completed"] else None

        for k, v in data.items():
            setattr(rem, k, v)

        await db.commit()
        await db.refresh(rem)
        return rem
    except Exception as e:
        await db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"success": False, "message": str(e)})


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
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message":"Reminder not found"})
    
    try:
        await db.delete(rem)
        await db.commit()
        
        return JSONResponse(status_code=status.HTTP_200_OK, content={ "success": True, "message": "Reminder deleted successfully"})
        
    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)},
        )