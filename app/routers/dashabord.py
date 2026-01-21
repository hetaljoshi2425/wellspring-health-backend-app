from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from .. import models
from app.utils.auth_utils import get_current_user
from datetime import datetime, timezone, timedelta

router = APIRouter()

@router.get("/dashboard")
async def dashboard_counts(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    recent_since = now - timedelta(days=7)
    # Count clinics
    clinics_count = await db.scalar(
        select(func.count(models.Client.id))
    )

    # Count appointments
    appointments_count = await db.scalar(
        select(func.count(models.Appointment.id))
    )
    
    # Total telehealth session count
    telehealth_session_count = await db.scalar(
        select(func.count(models.TelehealthSession.id))
    )
    
    #Upcomming appointments
    upcoming_appointments_count = await db.scalar(
        select(func.count(models.Appointment.id)).where(
            models.Appointment.start_time >= now,
            models.Appointment.status == "scheduled",
        )
    )
    
    # Recent progress notes
    recent_notes_count = await db.scalar(
        select(func.count(models.ProgressNote.id)).where(
            models.ProgressNote.created_at >= recent_since
        )
    )

    # Recent documents
    recent_documents_count = await db.scalar(
        select(func.count(models.Document.id)).where(
            models.Document.uploaded_at >= recent_since
        )
    )
    return {
        "success": True,
        "data": {
            "clients_count": clinics_count or 0,
            "appointments_count": appointments_count or 0,
            "upcoming_appointments_count": upcoming_appointments_count or 0,
            "recent_notes_count": recent_notes_count or 0,
            "recent_documents_count": recent_documents_count or 0,
            "telehealth_session_count": telehealth_session_count or 0,
        },
    }
