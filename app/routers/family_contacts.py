from typing import List
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import FamilyContactCreate, FamilyContactRead, FamilyContactUpdate
from app.utils.auth_utils import get_current_user

router = APIRouter()

@router.post("/", response_model=FamilyContactRead)
async def create_family_contact(contact_in: FamilyContactCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
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


@router.put("/clients/{client_id}/{contact_id}", response_model=FamilyContactRead)
async def update_family_contact(
    client_id: int,
    contact_id: int,
    contact_in: FamilyContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(models.FamilyContact).where(
            models.FamilyContact.id == contact_id,
            models.FamilyContact.client_id == client_id,
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=404,
            detail="Family contact not found for this client",
        )

    update_data = contact_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(contact, field, value)

    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/clients/{client_id}/{contact_id}", status_code=200)
async def delete_family_contact(
    client_id: int,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(models.FamilyContact).where(
            models.FamilyContact.id == contact_id,
            models.FamilyContact.client_id == client_id,
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=404,
            detail="Family contact not found for this client",
        )

    await db.delete(contact)
    await db.commit()

    return {
        "success": True,
        "message": "Family contact deleted successfully",
        "client_id": client_id,
        "contact_id": contact_id,
    }