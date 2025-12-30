from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.utils.auth_utils import get_current_user 
from ..database import get_db
from .. import models
from ..schemas import StaffAssignmentCreate, StaffAssignmentRead

router = APIRouter()

@router.post("/", response_model=StaffAssignmentRead)
async def assign_staff(assignment_in: StaffAssignmentCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    client_result = await db.execute(select(models.Client).where(models.Client.id == assignment_in.client_id))
    client = client_result.scalar_one_or_none()

    if not client:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={ "success": False, "message": "Client not found"})
        
    staff_result = await db.execute(select(models.User).where(models.User.id == assignment_in.staff_user_id))
    staff = staff_result.scalar_one_or_none()

    if not staff:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Staff user not found"})
    
    if staff.role !=  assignment_in.role:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Invalid Staff user role."})
   

    existing = await db.execute(
        select(models.StaffAssignment).where(
            and_(
                models.StaffAssignment.client_id == assignment_in.client_id,
                models.StaffAssignment.staff_user_id == assignment_in.staff_user_id,

                models.StaffAssignment.start_date <= assignment_in.end_date,
                models.StaffAssignment.end_date >= assignment_in.start_date,
            )
        )
    )
    
    if existing.scalar_one_or_none():
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"success": False, "message": "Staff already assigned to this client during the selected date range"})
        
    assignment = models.StaffAssignment(**assignment_in.model_dump())
    db.add(assignment)
    await db.commit()
    
    result = await db.execute(
        select(models.StaffAssignment)
        .options(
            selectinload(models.StaffAssignment.client),
            selectinload(models.StaffAssignment.staff_user)
        )
        .where(models.StaffAssignment.id == assignment.id)
    )
    result_data = result.scalar_one()

    return result_data

@router.get("/client/{client_id}", response_model=List[StaffAssignmentRead])
async def list_staff_assignments(client_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(
        select(models.StaffAssignment)
        .options(
            selectinload(models.StaffAssignment.client),
            selectinload(models.StaffAssignment.staff_user),
        )
        .where(models.StaffAssignment.client_id == client_id)
    )

    return result.scalars().all()


@router.put("/{assignment_id}", response_model=StaffAssignmentRead)
async def update_staff_assignment(
    assignment_id: int,
    assignment_in: StaffAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(select(models.StaffAssignment).where(models.StaffAssignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        return JSONResponse( status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Assignment record not found"})

    client = await db.scalar(select(models.Client).where(models.Client.id == assignment_in.client_id))
    if not client:
        return JSONResponse( status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Client not found"})

    staff = await db.scalar(select(models.User).where(models.User.id == assignment_in.staff_user_id))
    if not staff:
        return JSONResponse( status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Staff user not found"})

    overlap = await db.execute(
        select(models.StaffAssignment).where(
            and_( models.StaffAssignment.id != assignment_id,
                models.StaffAssignment.client_id == assignment_in.client_id,
                models.StaffAssignment.staff_user_id == assignment_in.staff_user_id,
                models.StaffAssignment.start_date <= assignment_in.end_date,
                models.StaffAssignment.end_date >= assignment_in.start_date,
            )
        )
    )

    if overlap.scalar_one_or_none():
        return JSONResponse( status_code=status.HTTP_409_CONFLICT, content={ "success": False, "message": "Staff already assigned to this client during the selected date range"})

    for field, value in assignment_in.model_dump().items():
        setattr(assignment, field, value)

    await db.commit()

    result = await db.execute(select(models.StaffAssignment).options(selectinload(models.StaffAssignment.client), selectinload(models.StaffAssignment.staff_user)).where(models.StaffAssignment.id == assignment_id))

    return result.scalar_one()


@router.delete("/{assignment_id}")
async def delete_staff_assignment(assignment_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(models.StaffAssignment).where(models.StaffAssignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "Assignment record not found"})

    await db.delete(assignment)
    await db.commit()

    return { "success": True, "message": "Staff assignment deleted successfully"}
