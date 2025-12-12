from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import ClientCreate, ClientRead

router = APIRouter()

@router.post("/", response_model=ClientRead)
async def create_client(client_in: ClientCreate, db: AsyncSession = Depends(get_db)):
    client = models.Client(**client_in.model_dump())
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client

@router.get("/", response_model=List[ClientRead])
async def list_clients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Client))
    return result.scalars().all()

@router.get("/{client_id}", response_model=ClientRead)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Client).where(models.Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
