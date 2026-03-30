"""Pydantic request/response schemas for SafeCare eMAR & Lead Engine."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.models import LeadStatus, MedEventType, UserRole, VitalType


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    care_home_id: str


# ---------------------------------------------------------------------------
# CareHome
# ---------------------------------------------------------------------------


class CareHomeCreate(BaseModel):
    name: str
    address: Optional[str] = None
    cqc_registration_number: Optional[str] = None
    bed_count: int = Field(ge=1)
    tier: int = Field(default=1, ge=1, le=2)


class CareHomeOut(CareHomeCreate):
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole


class UserOut(BaseModel):
    id: str
    care_home_id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Drug (dm+d)
# ---------------------------------------------------------------------------


class DrugOut(BaseModel):
    id: str
    dmd_id: str
    name: str
    form: Optional[str] = None
    strength: Optional[str] = None
    unit_of_measure: Optional[str] = None
    is_controlled: bool
    last_synced_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Resident
# ---------------------------------------------------------------------------


class ResidentCreate(BaseModel):
    nhs_number: Optional[str] = None
    full_name: str
    date_of_birth: Optional[datetime] = None
    room_number: Optional[str] = None
    gp_name: Optional[str] = None
    gp_email: Optional[EmailStr] = None
    gp_phone: Optional[str] = None
    allergies: Optional[str] = None


class ResidentOut(ResidentCreate):
    id: str
    care_home_id: str
    is_active: bool
    admitted_at: datetime
    discharged_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Prescription
# ---------------------------------------------------------------------------


class PrescriptionCreate(BaseModel):
    drug_id: str
    dose: str
    route: Optional[str] = None
    frequency: Optional[str] = None
    times_of_day: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    prescriber_name: Optional[str] = None
    notes: Optional[str] = None


class PrescriptionOut(PrescriptionCreate):
    id: str
    resident_id: str
    is_active: bool
    drug: DrugOut

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Vital Signs
# ---------------------------------------------------------------------------


class VitalCreate(BaseModel):
    vital_type: VitalType
    value: float
    unit: Optional[str] = None
    notes: Optional[str] = None


class VitalOut(VitalCreate):
    id: str
    resident_id: str
    recorded_by_id: str
    recorded_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Med Event (eMAR — WORM)
# ---------------------------------------------------------------------------


class MedEventCreate(BaseModel):
    prescription_id: str
    event_type: MedEventType
    scheduled_time: datetime
    notes: Optional[str] = None
    # Vitals Bridge inputs
    bp_systolic: Optional[float] = None
    bp_diastolic: Optional[float] = None
    blood_sugar: Optional[float] = None


class MedEventCorrection(BaseModel):
    corrects_event_id: str
    correction_reason: str
    notes: Optional[str] = None


class MedEventOut(BaseModel):
    id: str
    prescription_id: str
    administered_by_id: str
    event_type: MedEventType
    scheduled_time: datetime
    actual_time: datetime
    notes: Optional[str] = None
    bp_systolic: Optional[float] = None
    bp_diastolic: Optional[float] = None
    blood_sugar: Optional[float] = None
    vitals_blocked: bool
    gp_alerted: bool
    corrects_event_id: Optional[str] = None
    correction_reason: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Family Portal
# ---------------------------------------------------------------------------


class FamilyResidentLinkCreate(BaseModel):
    family_user_id: str
    resident_id: str
    relationship_label: Optional[str] = None


class ResidentSummary(BaseModel):
    """Read-only summary shown to family members."""

    resident_id: str
    full_name: str
    room_number: Optional[str] = None
    recent_med_events: List[MedEventOut] = []
    recent_vitals: List[VitalOut] = []


# ---------------------------------------------------------------------------
# Lead CRM
# ---------------------------------------------------------------------------


class LeadCreate(BaseModel):
    enquirer_name: str
    enquirer_email: Optional[EmailStr] = None
    enquirer_phone: Optional[str] = None
    relationship_to_resident: Optional[str] = None
    prospective_resident_name: Optional[str] = None
    prospective_resident_dob: Optional[datetime] = None
    care_needs: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadStatusUpdate(BaseModel):
    new_status: LeadStatus
    notes: Optional[str] = None


class LeadOut(LeadCreate):
    id: str
    care_home_id: str
    urgency_score: int
    status: LeadStatus
    assigned_to_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
