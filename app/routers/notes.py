from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import ProgressNoteCreate, ProgressNoteRead

router = APIRouter()

@router.post("/", response_model=ProgressNoteRead)
async def create_note(note_in: ProgressNoteCreate, db: AsyncSession = Depends(get_db)):
    note = models.ProgressNote(**note_in.model_dump())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note

@router.get("/client/{client_id}", response_model=List[ProgressNoteRead])
async def list_notes_for_client(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.ProgressNote).where(models.ProgressNote.client_id == client_id).order_by(models.ProgressNote.created_at.desc())
    )
    return result.scalars().all()
