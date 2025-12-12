from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import FamilyContactCreate, FamilyContactRead

router = APIRouter()

@router.post("/", response_model=FamilyContactRead)
async def create_family_contact(contact_in: FamilyContactCreate, db: AsyncSession = Depends(get_db)):
    contact = models.FamilyContact(**contact_in.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact

@router.get("/client/{client_id}", response_model=List[FamilyContactRead])
async def list_family_contacts(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.FamilyContact).where(models.FamilyContact.client_id == client_id)
    )
    return result.scalars().all()
