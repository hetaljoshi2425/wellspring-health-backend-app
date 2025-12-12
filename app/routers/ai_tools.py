from typing import Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from ..database import get_db
from .. import models

router = APIRouter()

@router.post("/note-suggestions")
async def generate_note_suggestions(payload: Dict, db: AsyncSession = Depends(get_db)):
    presenting_problem = payload.get("presenting_problem", "")
    diagnosis = payload.get("diagnosis", "")
    goal = payload.get("goal", "")

    suggested = (
        f"Client presented with {presenting_problem}. "
        f"Diagnosis is consistent with {diagnosis}. "
        f"Session focused on progress toward goal: {goal}. "
        "Client was engaged and responsive. Interventions included evidence-based "
        "cognitive and behavioral strategies, supportive reflection, and skills rehearsal."
    )

    return {"suggested_note": suggested}

@router.post("/wiley-style-note")
async def generate_wiley_style_note(payload: Dict, db: AsyncSession = Depends(get_db)):
    client_name = payload.get("client_name", "Client")
    presenting_problem = payload.get("presenting_problem", "")
    diagnosis = payload.get("diagnosis", "")
    goal = payload.get("goal", "")
    interventions = payload.get("interventions", "CBT techniques and supportive counseling")
    response = payload.get("response", "Client was engaged and receptive.")
    plan = payload.get("plan", "Continue weekly sessions and monitor symptoms.")

    note_text = f"""SUBJECTIVE:
    {client_name} reports {presenting_problem}. Client continues to experience symptoms consistent with {diagnosis} and is working toward the goal of {goal}.

    OBJECTIVE:
    Client arrived on time, was appropriately groomed, and oriented x4. Mood, affect, and behavior were within expected range for current diagnosis. No acute safety concerns were observed or reported.

    INTERVENTIONS:
    {interventions}. Psychoeducation was provided regarding symptoms and coping strategies. Collaborative problem-solving was used to identify barriers and supports.

    RESPONSE:
    {response} Client was able to articulate insights and identify at least one concrete strategy to apply between sessions.

    PLAN:
    {plan} Client was assigned homework to practice identified coping skills and to track mood or behavior patterns between sessions. Next appointment was scheduled and client agreed to contact the office or crisis resources if risk escalates.
    """

    return {"structured_note": note_text.strip()}

@router.post("/icd10-suggest")
async def suggest_icd10_codes(payload: Dict, db: AsyncSession = Depends(get_db)):
    presenting_problem = (payload.get("presenting_problem") or "").lower().strip()
    suggestions: List[dict] = []

    if presenting_problem:
        term = f"%{presenting_problem}%"
        stmt = select(models.ICD10Code).where(
            or_(
                models.ICD10Code.description.ilike(term),
                models.ICD10Code.code.ilike(term),
                models.ICD10Code.category.ilike(term),
            )
        ).limit(5)
        result = await db.execute(stmt)
        codes = result.scalars().all()
        for c in codes:
            suggestions.append(
                {"code": c.code, "description": c.description, "category": c.category}
            )

    if not suggestions:
        suggestions = [
            {
                "code": "F41.1",
                "description": "Generalized anxiety disorder",
                "category": "Anxiety disorders",
            },
            {
                "code": "F32.1",
                "description": "Major depressive disorder, single episode, moderate",
                "category": "Depressive disorders",
            },
            {
                "code": "F33.1",
                "description": "Major depressive disorder, recurrent, moderate",
                "category": "Depressive disorders",
            },
            {
                "code": "F43.10",
                "description": "Post-traumatic stress disorder, unspecified",
                "category": "Trauma- and stressor-related disorders",
            },
        ]

    return {"presenting_problem": presenting_problem, "suggested_codes": suggestions}
