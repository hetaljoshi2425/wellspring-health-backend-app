from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from .. import models
from ..schemas import InitialAssessmentCreate, InitialAssessmentRead

router = APIRouter()

@router.post("/", response_model=InitialAssessmentRead)
async def create_assessment(assess_in: InitialAssessmentCreate, db: AsyncSession = Depends(get_db)):
    assessment = models.InitialAssessment(**assess_in.model_dump())
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return assessment

@router.get("/client/{client_id}", response_model=List[InitialAssessmentRead])
async def list_assessments(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.InitialAssessment).where(models.InitialAssessment.client_id == client_id)
    )
    return result.scalars().all()
