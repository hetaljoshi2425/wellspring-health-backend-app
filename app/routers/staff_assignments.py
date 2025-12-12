from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import StaffAssignmentCreate, StaffAssignmentRead

router = APIRouter()

@router.post("/", response_model=StaffAssignmentRead)
async def assign_staff(assignment_in: StaffAssignmentCreate, db: AsyncSession = Depends(get_db)):
    assignment = models.StaffAssignment(**assignment_in.model_dump())
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment

@router.get("/client/{client_id}", response_model=List[StaffAssignmentRead])
async def list_staff_assignments(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.StaffAssignment).where(models.StaffAssignment.client_id == client_id)
    )
    return result.scalars().all()
