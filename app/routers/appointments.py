from datetime import datetime, date
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..database import get_db
from .. import models
from ..schemas import AppointmentCreate, AppointmentRead

router = APIRouter()

@router.post("/", response_model=AppointmentRead)
async def create_appointment(appointment_in: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    # Basic validation: start < end
    if appointment_in.start_time >= appointment_in.end_time:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")
    appt = models.Appointment(**appointment_in.model_dump())
    db.add(appt)
    await db.commit()
    await db.refresh(appt)
    return appt

@router.get("/", response_model=List[AppointmentRead])
async def list_appointments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Appointment))
    return result.scalars().all()

@router.get("/calendar")
async def calendar_view(
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD, inclusive)"),
    provider_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, list]:
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    stmt = select(models.Appointment).where(
        and_(models.Appointment.start_time >= start_dt, models.Appointment.start_time <= end_dt)
    )
    if provider_id:
        stmt = stmt.where(models.Appointment.provider_id == provider_id)
    result = await db.execute(stmt)
    appts = result.scalars().all()
    grouped = {}
    for a in appts:
        day = a.start_time.date().isoformat()
        grouped.setdefault(day, []).append(AppointmentRead.model_validate(a))
    return grouped
