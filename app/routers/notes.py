from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from .. import models
from ..schemas import ProgressNoteCreate, ProgressNoteRead, ProgressNoteUpdate
from app.utils.auth_utils import get_current_user 

router = APIRouter()

@router.post("/", response_model=ProgressNoteRead)
async def create_note(note_in: ProgressNoteCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):

    client = await db.get(models.Client, note_in.client_id)
    if not client:
        return JSONResponse(status_code=404, content={"success": False, "message": "Client not found"})

    provider = await db.get(models.User, note_in.provider_id)
    if not provider:
        return JSONResponse(status_code=404, content={"success": False, "message": "Provider not found"})

    appointment = None

    if note_in.appointment_id:
        appointment = await db.get(models.Appointment, note_in.appointment_id)

        if not appointment:
            return JSONResponse(status_code=404,content={ "success": False, "message": "Appointment not found"})

        if appointment.client_id != note_in.client_id:
            return JSONResponse(status_code=400, content={ "success": False, "message": "Appointment does not belong to this client"})

        if appointment.provider_id != note_in.provider_id:
            return JSONResponse(status_code=400, content={"success": False, "message": "Appointment does not belong to this provider"})
            
    note = models.ProgressNote(**note_in.model_dump())
    db.add(note)
    await db.commit()
    await db.refresh(note)

    result = await db.execute(
        select(models.ProgressNote)
        .where(models.ProgressNote.id == note.id)
        .options(selectinload(models.ProgressNote.appointment))
    )
    note = result.scalar_one()

    return note

@router.get("/client/{client_id}", response_model=List[ProgressNoteRead])
async def list_notes_for_client(client_id: int, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    client = await db.get(models.Client, client_id)
    if not client:
        return JSONResponse(status_code=404, content={ "success": False, "message": "Client not found",},)
    
    offset = (page - 1) * page_size

    notes_result = await db.execute(
        select(models.ProgressNote)
        .where(models.ProgressNote.client_id == client_id)
        .options(
            selectinload(models.ProgressNote.appointment),
        )
        .order_by(models.ProgressNote.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    notes = notes_result.scalars().all()
    return notes

@router.put("/{note_id}", response_model=ProgressNoteRead)
async def update_note(
    note_id: int,
    note_in: ProgressNoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    stmt = (
        select(models.ProgressNote)
        .where(models.ProgressNote.id == note_id)
        .options(
            selectinload(models.ProgressNote.client),
            selectinload(models.ProgressNote.provider),
            selectinload(models.ProgressNote.appointment),
        )
    )
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()

    if not note:
        return JSONResponse(status_code=404, content={"success": False, "message": "Progress note not found"})

    update_data = note_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(note, field, value)

    await db.commit()
    await db.refresh(note)
    return note

@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(models.ProgressNote).where(models.ProgressNote.id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        return JSONResponse(status_code=404, content={ "success": False, "message": "Progress note not found"})

    await db.delete(note)
    await db.commit()
    return JSONResponse(status_code=200, content={ "success": True, "message": "Progress note deleted successfully"})