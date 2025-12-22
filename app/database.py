from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

Base = declarative_base()

from app.models import User, Client, Appointment, ProgressNote, TreatmentPlan, Invoice, Claim, TelehealthSession, Medication, Prescription, AuditLog, ICD10Code, InsuranceInfo, FamilyContact, StaffAssignment, Document, ReminderLog, InitialAssessment, StaffPreference

engine = create_async_engine(settings.database_url, echo=False, future=True)

async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_db():
    async with async_session_maker() as session:
        yield session
