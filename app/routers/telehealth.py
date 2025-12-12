from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import TelehealthSessionCreate, TelehealthSessionRead

router = APIRouter()

@router.post("/sessions", response_model=TelehealthSessionRead)
async def create_telehealth_session(session_in: TelehealthSessionCreate, db: AsyncSession = Depends(get_db)):
    join_url = f"https://video.wellspring-ehr.local/session/{session_in.appointment_id}"
    session = models.TelehealthSession(
        appointment_id=session_in.appointment_id,
        provider_id=session_in.provider_id,
        client_id=session_in.client_id,
        start_time=session_in.start_time,
        status=session_in.status,
        join_url=join_url,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.get("/sessions", response_model=List[TelehealthSessionRead])
async def list_telehealth_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.TelehealthSession))
    return result.scalars().all()
