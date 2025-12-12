from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import DocumentCreate, DocumentRead

router = APIRouter()

@router.post("/", response_model=DocumentRead)
async def create_document(doc_in: DocumentCreate, db: AsyncSession = Depends(get_db)):
    doc = models.Document(**doc_in.model_dump())
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc

@router.get("/client/{client_id}", response_model=List[DocumentRead])
async def list_documents(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Document).where(models.Document.client_id == client_id)
    )
    return result.scalars().all()
