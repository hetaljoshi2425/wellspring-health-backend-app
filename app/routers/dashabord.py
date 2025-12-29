from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from .. import models
from app.utils.auth_utils import get_current_user

router = APIRouter()

@router.get("/dashboard")
async def dashboard_counts(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Count clinics
    clinics_count = await db.scalar(
        select(func.count(models.Client.id))
    )

    # Count appointments
    appointments_count = await db.scalar(
        select(func.count(models.Appointment.id))
    )

    return {
        "success": True,
        "data": {
            "clients_count": clinics_count or 0,
            "appointments_count": appointments_count or 0,
        },
    }
