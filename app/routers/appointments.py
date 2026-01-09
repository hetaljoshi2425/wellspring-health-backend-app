from datetime import datetime, date
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from ..database import get_db
from .. import models
from ..schemas import AppointmentCreate, AppointmentRead, AppointmentUpdate
from app.utils.auth_utils import get_current_user
from app.validators.appointment import *
from app.log_config import get_logger

router = APIRouter()

logger = get_logger("appointment")

def to_naive(dt: datetime) -> datetime:
    if dt.tzinfo:
        return dt.replace(tzinfo=None)
    return dt

@router.post("/", response_model=AppointmentRead)
async def create_appointment(appointment_in: AppointmentCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user),):
    # Basic validation: start < end
    try:
        start_time = appointment_in.start_time
        end_time = appointment_in.end_time
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
            
        if start_time >= end_time:
            logger.warning(f"appointment start_time must be before end_time")
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success":False, "message": "start_time must be before end_time"})
        
        data = await validate_client_provider(
            db,
            client_id=appointment_in.client_id,
            provider_id=appointment_in.provider_id,
        )
        
        appt = models.Appointment(
            **appointment_in.model_dump(exclude={"start_time", "end_time"}),
            start_time=start_time,
            end_time=end_time,
        )
        db.add(appt)
            
        await db.commit()
        await db.refresh(appt)
        logger.info(f"Appointment added to database")
        return appt
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error occurred {str(e)}.")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Unexpected error occurred {str(e)}.",
            },
        )


@router.get("/", response_model=List[AppointmentRead])
async def list_appointments(search: Optional[str] = Query(None, description="Search by client first name, last name, or email"  ), page: Optional[int] = Query(None, ge=1), page_size: Optional[int] = Query(None, ge=1, le=100), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user),):
    
    stmt = ( select(models.Appointment).join(models.Client).options(
        selectinload(models.Appointment.client), 
        selectinload(models.Appointment.provider),
        selectinload(models.Appointment.notes)
        ))

    if search:
        like = f"%{search}%"
        stmt = stmt.where( or_( models.Client.first_name.ilike(like), models.Client.last_name.ilike(like), models.Client.email.ilike(like),))

    stmt = stmt.order_by(models.Appointment.start_time.asc())

    if page is not None and page_size is not None:
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    items = result.scalars().all()

    return items

@router.get("/calendar")
async def calendar_view(
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD, inclusive)"),
    provider_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
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


@router.put("/{appointment_id}", response_model=AppointmentRead)
async def update_appointment(
    appointment_id: int,
    appointment_in: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stmt = (
        select(models.Appointment)
        .where(models.Appointment.id == appointment_id)
        .options(
            selectinload(models.Appointment.client),
            selectinload(models.Appointment.provider),
        )
    )

    result = await db.execute(stmt)
    appointment = result.scalar_one_or_none()

    if not appointment:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Appointment not found"})

    update_data = appointment_in.model_dump(exclude_unset=True)
    
    if not update_data:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": "No fields provided for update"})

    if appointment_in.start_time >= appointment_in.end_time:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": "start_time must be before end_time"})

    await validate_client_provider(
        db,
        client_id=update_data.get("client_id"),
        provider_id=update_data.get("provider_id"),
    )
    
    for field, value in update_data.items():
        setattr(appointment, field, value)

    await db.commit()
    await db.refresh(appointment)

    return appointment


@router.delete("/{appointment_id}", status_code=204)
async def delete_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stmt = select(models.Appointment).where(models.Appointment.id == appointment_id)
    result = await db.execute(stmt)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": "Appointment not found"})
    
    if appointment.status == "completed":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": "Completed appointments cannot be deleted",
        })
    await db.delete(appointment)
    await db.commit()
    return {
            "success": True,
            "message": "Appointment deleted successfully",
        }

@router.get("/filter", response_model=List[AppointmentRead])
async def filter_appointments(
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    appointment_id: Optional[int] = Query(None, description="Filter by appointment ID"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stmt = (
        select(models.Appointment)
        .options(
            selectinload(models.Appointment.client),
            selectinload(models.Appointment.provider),
        )
    )

    conditions = []

    if client_id is not None:
        conditions.append(models.Appointment.client_id == client_id)

    if appointment_id is not None:
        conditions.append(models.Appointment.id == appointment_id)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(models.Appointment.start_time.asc())

    result = await db.execute(stmt)
    appointments = result.scalars().all()

    return appointments
