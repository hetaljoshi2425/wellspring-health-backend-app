from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Date,
    ForeignKey,
    Text,
    Float,
)
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="provider")  # provider, admin, billing, peer, waads, dahs
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String, nullable=False)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)


    appointments = relationship("Appointment", back_populates="provider")
    staff_preferences = relationship("StaffPreference", back_populates="user")

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="client")
    notes = relationship("ProgressNote", back_populates="client")
    treatment_plans = relationship("TreatmentPlan", back_populates="client")
    invoices = relationship("Invoice", back_populates="client")
    insurance_info = relationship("InsuranceInfo", back_populates="client", uselist=False)
    family_contacts = relationship("FamilyContact", back_populates="client")
    staff_assignments = relationship("StaffAssignment", back_populates="client")
    documents = relationship("Document", back_populates="client")
    reminders = relationship("ReminderLog", back_populates="client")
    assessments = relationship("InitialAssessment", back_populates="client")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    type = Column(String, default="individual")  # individual, group, telehealth, waads, dahs, peer
    status = Column(String, default="scheduled")  # scheduled, completed, canceled, no_show
    location = Column(String, nullable=True)

    client = relationship("Client", back_populates="appointments")
    provider = relationship("User", back_populates="appointments")

class ProgressNote(Base):
    __tablename__ = "progress_notes"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    note_text = Column(Text, nullable=False)
    dsm5_code = Column(String, nullable=True)
    modifiers = Column(String, nullable=True)
    service_line = Column(String, nullable=True)  # outpatient, peer, waads, dahs, etc.

    client = relationship("Client", back_populates="notes")

class TreatmentPlan(Base):
    __tablename__ = "treatment_plans"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    goals = Column(Text, nullable=False)
    interventions = Column(Text, nullable=True)
    target_date = Column(Date, nullable=True)
    status = Column(String, default="active")  # active, completed, archived

    client = relationship("Client", back_populates="treatment_plans")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, paid, void
    description = Column(Text, nullable=True)
    bill_to_name = Column(String, nullable=True)
    bill_to_relationship = Column(String, nullable=True)  # self, parent, guardian, etc.

    client = relationship("Client", back_populates="invoices")

class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    payer_name = Column(String, nullable=False)
    status = Column(String, default="draft")  # draft, submitted, paid, denied
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    claim_number = Column(String, nullable=True)

class TelehealthSession(Base):
    __tablename__ = "telehealth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    join_url = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="scheduled")  # scheduled, live, completed

class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    strength = Column(String, nullable=True)
    form = Column(String, nullable=True)  # tablet, capsule, etc.

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    dosage_instructions = Column(Text, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)

class ICD10Code(Base):
    __tablename__ = "icd10_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class InsuranceInfo(Base):
    __tablename__ = "insurance_info"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    primary_payer_name = Column(String, nullable=True)
    primary_member_id = Column(String, nullable=True)
    primary_group_id = Column(String, nullable=True)
    primary_plan_name = Column(String, nullable=True)
    primary_relationship = Column(String, nullable=True)
    secondary_payer_name = Column(String, nullable=True)
    secondary_member_id = Column(String, nullable=True)
    secondary_group_id = Column(String, nullable=True)
    secondary_plan_name = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    client = relationship("Client", back_populates="insurance_info")

class FamilyContact(Base):
    __tablename__ = "family_contacts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String, nullable=False)
    relationships = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    client = relationship("Client", back_populates="family_contacts")

class StaffAssignment(Base):
    __tablename__ = "staff_assignments"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    staff_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=True)
    is_primary = Column(Boolean, default=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    client = relationship("Client", back_populates="staff_assignments")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    document_type = Column(String, nullable=False)  # general, clinical
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    client = relationship("Client", back_populates="documents")

class ReminderLog(Base):
    __tablename__ = "reminder_logs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    reminder_type = Column(String, nullable=True)
    reminder_text = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    client = relationship("Client", back_populates="reminders")

class InitialAssessment(Base):
    __tablename__ = "initial_assessments"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    assessment_date = Column(Date, default=date.today)
    presenting_problem = Column(Text, nullable=True)
    history = Column(Text, nullable=True)
    mental_status = Column(Text, nullable=True)
    diagnosis_code = Column(String, nullable=True)
    risk_level = Column(String, nullable=True)
    recommendations = Column(Text, nullable=True)

    client = relationship("Client", back_populates="assessments")

class StaffPreference(Base):
    __tablename__ = "staff_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=True)

    user = relationship("User", back_populates="staff_preferences")
