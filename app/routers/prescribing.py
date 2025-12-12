from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import MedicationCreate, MedicationRead, PrescriptionCreate, PrescriptionRead

router = APIRouter()

@router.post("/medications", response_model=MedicationRead)
async def create_medication(med_in: MedicationCreate, db: AsyncSession = Depends(get_db)):
    med = models.Medication(**med_in.model_dump())
    db.add(med)
    await db.commit()
    await db.refresh(med)
    return med

@router.get("/medications", response_model=List[MedicationRead])
async def list_medications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Medication))
    return result.scalars().all()

@router.post("/prescriptions", response_model=PrescriptionRead)
async def create_prescription(rx_in: PrescriptionCreate, db: AsyncSession = Depends(get_db)):
    rx = models.Prescription(**rx_in.model_dump())
    db.add(rx)
    await db.commit()
    await db.refresh(rx)
    return rx

@router.get("/prescriptions", response_model=List[PrescriptionRead])
async def list_prescriptions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Prescription))
    return result.scalars().all()
