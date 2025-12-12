from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator, Field
import re
from fastapi import HTTPException

ALLOWED_ROLES = {"provider", "admin", "billing", "peer", "waads", "dahs"}

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "provider"
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str

    @validator("password")
    def validate_password(cls, value):
        """
        Password must contain:
        - Minimum 8 characters
        - At least one uppercase
        - At least one lowercase
        - At least one digit
        - At least one special character
        """

        if len(value) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

        if not re.search(r"[A-Z]", value):
            raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter.")

        if not re.search(r"[a-z]", value):
            raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter.")

        if not re.search(r"[0-9]", value):
            raise HTTPException(status_code=400, detail="Password must contain at least one digit.")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise HTTPException(status_code=400, detail="Password must contain at least one special character.")

        return value

    @validator("role")
    def validate_role(cls, value):
        if value not in ALLOWED_ROLES:
            raise HTTPException(status_code=400, detail= f"Invalid role. Allowed roles: {', '.join(ALLOWED_ROLES)}")
        return value
    
class RequestPasswordReset(BaseModel):
    email: EmailStr
    
class VerifyResetToken(BaseModel):
    token: str
    
class ResetPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)

    @validator("new_password")
    def validate_new_password(cls, value):
        """
        Password must contain:
        - Minimum 8 characters
        - At least one uppercase
        - At least one lowercase
        - At least one digit
        - At least one special character
        """

        if len(value) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

        if not re.search(r"[A-Z]", value):
            raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter.")

        if not re.search(r"[a-z]", value):
            raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter.")

        if not re.search(r"[0-9]", value):
            raise HTTPException(status_code=400, detail="Password must contain at least one digit.")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise HTTPException(status_code=400, detail="Password must contain at least one special character.")

        return value

    @validator("confirm_password")
    def passwords_match(cls, confirm_password, values):
        """
        Confirm password must match new_password
        """
        new_password = values.get("new_password")

        if new_password and confirm_password != new_password:
            raise HTTPException(status_code=400, detail="New password and confirm password do not match.")

        return confirm_password
 
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserRead(UserBase):
    id: int
    class Config:
        from_attributes = True

class ClientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class AppointmentBase(BaseModel):
    client_id: int
    provider_id: int
    start_time: datetime
    end_time: datetime
    type: str = "individual"
    status: str = "scheduled"
    location: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentRead(AppointmentBase):
    id: int
    class Config:
        from_attributes = True

class ProgressNoteBase(BaseModel):
    client_id: int
    provider_id: int
    appointment_id: Optional[int] = None
    note_text: str
    dsm5_code: Optional[str] = None
    modifiers: Optional[str] = None
    service_line: Optional[str] = None

class ProgressNoteCreate(ProgressNoteBase):
    pass

class ProgressNoteRead(ProgressNoteBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    client_id: int
    total_amount: float
    status: str = "pending"
    description: Optional[str] = None
    bill_to_name: Optional[str] = None
    bill_to_relationship: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceRead(InvoiceBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class ClaimBase(BaseModel):
    client_id: int
    appointment_id: Optional[int] = None
    payer_name: str
    status: str = "draft"
    amount: float

class ClaimCreate(ClaimBase):
    pass

class ClaimRead(ClaimBase):
    id: int
    created_at: datetime
    claim_number: Optional[str] = None
    class Config:
        from_attributes = True

class TelehealthSessionBase(BaseModel):
    appointment_id: int
    provider_id: int
    client_id: int
    start_time: datetime
    status: str = "scheduled"

class TelehealthSessionCreate(TelehealthSessionBase):
    pass

class TelehealthSessionRead(TelehealthSessionBase):
    id: int
    join_url: str
    end_time: Optional[datetime] = None
    class Config:
        from_attributes = True

class MedicationBase(BaseModel):
    name: str
    strength: Optional[str] = None
    form: Optional[str] = None

class MedicationCreate(MedicationBase):
    pass

class MedicationRead(MedicationBase):
    id: int
    class Config:
        from_attributes = True

class PrescriptionBase(BaseModel):
    client_id: int
    provider_id: int
    medication_id: int
    dosage_instructions: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "active"

class PrescriptionCreate(PrescriptionBase):
    pass

class PrescriptionRead(PrescriptionBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class ICD10CodeBase(BaseModel):
    code: str
    description: str
    category: Optional[str] = None
    is_active: bool = True

class ICD10CodeCreate(ICD10CodeBase):
    pass

class ICD10CodeRead(ICD10CodeBase):
    id: int
    class Config:
        from_attributes = True

class InsuranceInfoBase(BaseModel):
    client_id: int
    primary_payer_name: Optional[str] = None
    primary_member_id: Optional[str] = None
    primary_group_id: Optional[str] = None
    primary_plan_name: Optional[str] = None
    primary_relationship: Optional[str] = None
    secondary_payer_name: Optional[str] = None
    secondary_member_id: Optional[str] = None
    secondary_group_id: Optional[str] = None
    secondary_plan_name: Optional[str] = None
    notes: Optional[str] = None

class InsuranceInfoCreate(InsuranceInfoBase):
    pass

class InsuranceInfoRead(InsuranceInfoBase):
    id: int
    class Config:
        from_attributes = True

class FamilyContactBase(BaseModel):
    client_id: int
    name: str
    relationship: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    notes: Optional[str] = None

class FamilyContactCreate(FamilyContactBase):
    pass

class FamilyContactRead(FamilyContactBase):
    id: int
    class Config:
        from_attributes = True

class StaffAssignmentBase(BaseModel):
    client_id: int
    staff_user_id: int
    role: Optional[str] = None
    is_primary: bool = False
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None

class StaffAssignmentCreate(StaffAssignmentBase):
    pass

class StaffAssignmentRead(StaffAssignmentBase):
    id: int
    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    client_id: int
    document_type: str
    title: str
    file_path: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentRead(DocumentBase):
    id: int
    uploaded_at: datetime
    uploaded_by_user_id: Optional[int] = None
    class Config:
        from_attributes = True

class ReminderLogBase(BaseModel):
    client_id: int
    reminder_type: Optional[str] = None
    reminder_text: str
    due_date: Optional[datetime] = None
    completed: bool = False

class ReminderLogCreate(ReminderLogBase):
    pass

class ReminderLogRead(ReminderLogBase):
    id: int
    completed_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class InitialAssessmentBase(BaseModel):
    client_id: int
    assessment_date: Optional[date] = None
    presenting_problem: Optional[str] = None
    history: Optional[str] = None
    mental_status: Optional[str] = None
    diagnosis_code: Optional[str] = None
    risk_level: Optional[str] = None
    recommendations: Optional[str] = None

class InitialAssessmentCreate(InitialAssessmentBase):
    pass

class InitialAssessmentRead(InitialAssessmentBase):
    id: int
    class Config:
        from_attributes = True

class StaffPreferenceBase(BaseModel):
    user_id: int
    key: str
    value: Optional[str] = None

class StaffPreferenceCreate(StaffPreferenceBase):
    pass

class StaffPreferenceRead(StaffPreferenceBase):
    id: int
    class Config:
        from_attributes = True
