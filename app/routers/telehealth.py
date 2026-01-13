from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import TelehealthSessionCreate, TelehealthSessionRead

from app.utils.auth_utils import get_current_user 

router = APIRouter()

@router.post("/sessions", response_model=TelehealthSessionRead)
async def create_telehealth_session(session_in: TelehealthSessionCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    join_url = f"https://video.wellspring-ehr.local/session/{session_in.appointment_id}"
    
    try:
        if session_in.start_time:
            start_time = session_in.start_time
            if start_time.tzinfo is not None:
                start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            start_time = datetime.now()
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={ "success": False, "message": "Invalid start_time format"})
    
    appointment = await db.execute(select(models.Appointment.id).where(models.Appointment.id == session_in.appointment_id))
    if not appointment.scalar_one_or_none():
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": "Invalid appointment_id"})
    

    provider = await db.execute(select(models.User.id).where(models.User.id == session_in.provider_id))
    if not provider.scalar_one_or_none():
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": "Invalid provider_id"})

    client = await db.execute(select(models.Client.id).where(models.Client.id == session_in.client_id))
    if not client.scalar_one_or_none():
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": "Invalid client_id"})
    
    session = models.TelehealthSession(
        appointment_id=session_in.appointment_id,
        provider_id=session_in.provider_id,
        client_id=session_in.client_id,
        start_time=session_in.start_time,
        status=session_in.status,
        join_url=join_url,
    )
    try:
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    except Exception as e:
        await db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={ "success": False, "message": f"Unexpected server error {str(e)}"})

@router.get("/sessions", response_model=List[TelehealthSessionRead])
async def list_telehealth_sessions(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    # result = await db.execute(select(models.TelehealthSession))
    result = await db.execute(select(models.TelehealthSession))
    sessions = result.scalars().all()
    return [
        TelehealthSessionRead(
            id=s.id,
            appointment_id=s.appointment_id,
            provider_id=s.provider_id,
            client_id=s.client_id,
            start_time=s.start_time,
            end_time=s.end_time,
            join_url=s.join_url,
            status=str(s.status),
        )
        for s in sessions
    ]
