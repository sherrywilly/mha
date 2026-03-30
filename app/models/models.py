"""
SQLAlchemy ORM models for SafeCare eMAR & Lead Engine.

Multi-tenant design: every table that holds tenant-specific data carries a
`care_home_id` foreign key.  The application layer always filters by the
calling user's `care_home_id`, so Care Home A can never see Care Home B data.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class UserRole(str, enum.Enum):
    admin = "admin"
    nurse = "nurse"
    gp = "gp"
    family = "family"


class LeadStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    touring = "touring"
    offer_made = "offer_made"
    admitted = "admitted"
    lost = "lost"


class MedEventType(str, enum.Enum):
    administered = "administered"
    refused = "refused"
    omitted = "omitted"
    held = "held"
    correction = "correction"


class VitalType(str, enum.Enum):
    blood_pressure_systolic = "blood_pressure_systolic"
    blood_pressure_diastolic = "blood_pressure_diastolic"
    blood_sugar = "blood_sugar"
    pulse = "pulse"
    temperature = "temperature"
    oxygen_saturation = "oxygen_saturation"


# ---------------------------------------------------------------------------
# CareHome (tenant root)
# ---------------------------------------------------------------------------


class CareHome(Base):
    __tablename__ = "care_homes"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    cqc_registration_number = Column(String(50), unique=True)
    bed_count = Column(Integer, nullable=False, default=0)
    tier = Column(Integer, nullable=False, default=1)  # 1 = eMAR only, 2 = eMAR + CRM
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    users = relationship("User", back_populates="care_home")
    residents = relationship("Resident", back_populates="care_home")
    leads = relationship("Lead", back_populates="care_home")


# ---------------------------------------------------------------------------
# User (staff, GP, family member)
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    care_home_id = Column(UUID(as_uuid=False), ForeignKey("care_homes.id"), nullable=False)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (UniqueConstraint("care_home_id", "email", name="uq_user_email_per_home"),)

    care_home = relationship("CareHome", back_populates="users")
    med_events = relationship("MedEvent", back_populates="administered_by")


# ---------------------------------------------------------------------------
# dm+d Drug (NHS Dictionary of Medicines and Devices)
# ---------------------------------------------------------------------------


class Drug(Base):
    """Canonical NHS dm+d drug entry. Synced from the NHSBSA dm+d API."""

    __tablename__ = "drugs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    dmd_id = Column(String(50), unique=True, nullable=False)  # Virtual Medicinal Product ID
    name = Column(String(500), nullable=False)
    form = Column(String(100))
    strength = Column(String(100))
    unit_of_measure = Column(String(50))
    is_controlled = Column(Boolean, default=False)
    last_synced_at = Column(DateTime(timezone=True), default=_now)

    prescriptions = relationship("Prescription", back_populates="drug")


# ---------------------------------------------------------------------------
# Resident
# ---------------------------------------------------------------------------


class Resident(Base):
    __tablename__ = "residents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    care_home_id = Column(UUID(as_uuid=False), ForeignKey("care_homes.id"), nullable=False)
    nhs_number = Column(String(10))
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime(timezone=True))
    room_number = Column(String(20))
    gp_name = Column(String(255))
    gp_email = Column(String(255))
    gp_phone = Column(String(50))
    allergies = Column(Text)
    is_active = Column(Boolean, default=True)
    admitted_at = Column(DateTime(timezone=True), default=_now)
    discharged_at = Column(DateTime(timezone=True), nullable=True)

    care_home = relationship("CareHome", back_populates="residents")
    prescriptions = relationship("Prescription", back_populates="resident")
    vitals = relationship("Vital", back_populates="resident")
    family_links = relationship("FamilyResidentLink", back_populates="resident")


# ---------------------------------------------------------------------------
# Prescription
# ---------------------------------------------------------------------------


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    resident_id = Column(UUID(as_uuid=False), ForeignKey("residents.id"), nullable=False)
    drug_id = Column(UUID(as_uuid=False), ForeignKey("drugs.id"), nullable=False)
    dose = Column(String(100), nullable=False)
    route = Column(String(50))        # e.g. oral, topical
    frequency = Column(String(100))   # e.g. "twice daily"
    times_of_day = Column(String(255))  # e.g. "08:00,20:00"
    start_date = Column(DateTime(timezone=True), default=_now)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    prescriber_name = Column(String(255))
    notes = Column(Text)

    resident = relationship("Resident", back_populates="prescriptions")
    drug = relationship("Drug", back_populates="prescriptions")
    med_events = relationship("MedEvent", back_populates="prescription")


# ---------------------------------------------------------------------------
# Vital Signs
# ---------------------------------------------------------------------------


class Vital(Base):
    __tablename__ = "vitals"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    resident_id = Column(UUID(as_uuid=False), ForeignKey("residents.id"), nullable=False)
    recorded_by_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    vital_type = Column(Enum(VitalType), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    recorded_at = Column(DateTime(timezone=True), default=_now)
    notes = Column(Text)

    resident = relationship("Resident", back_populates="vitals")


# ---------------------------------------------------------------------------
# MedEvent — WORM audit trail
#
# Records are NEVER deleted or updated.  Corrections are inserted as new rows
# with event_type=correction, referencing the original via corrects_event_id.
# ---------------------------------------------------------------------------


class MedEvent(Base):
    __tablename__ = "med_events"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    prescription_id = Column(UUID(as_uuid=False), ForeignKey("prescriptions.id"), nullable=False)
    administered_by_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    event_type = Column(Enum(MedEventType), nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    actual_time = Column(DateTime(timezone=True), default=_now)
    notes = Column(Text)
    # For corrections only
    corrects_event_id = Column(UUID(as_uuid=False), ForeignKey("med_events.id"), nullable=True)
    correction_reason = Column(Text)
    # Vitals snapshot at administration time (Vitals Bridge)
    bp_systolic = Column(Float, nullable=True)
    bp_diastolic = Column(Float, nullable=True)
    blood_sugar = Column(Float, nullable=True)
    # Was the medication blocked by the Vitals Bridge?
    vitals_blocked = Column(Boolean, default=False)
    gp_alerted = Column(Boolean, default=False)

    prescription = relationship("Prescription", back_populates="med_events")
    administered_by = relationship("User", back_populates="med_events")
    correction_of = relationship("MedEvent", remote_side="MedEvent.id", foreign_keys=[corrects_event_id])


# ---------------------------------------------------------------------------
# FamilyResidentLink — read-only family portal access
# ---------------------------------------------------------------------------


class FamilyResidentLink(Base):
    __tablename__ = "family_resident_links"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    family_user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    resident_id = Column(UUID(as_uuid=False), ForeignKey("residents.id"), nullable=False)
    relationship_label = Column(String(100))  # e.g. "Daughter", "Son"
    created_at = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        UniqueConstraint("family_user_id", "resident_id", name="uq_family_resident"),
    )

    resident = relationship("Resident", back_populates="family_links")


# ---------------------------------------------------------------------------
# Lead CRM
# ---------------------------------------------------------------------------


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    care_home_id = Column(UUID(as_uuid=False), ForeignKey("care_homes.id"), nullable=False)
    enquirer_name = Column(String(255), nullable=False)
    enquirer_email = Column(String(255))
    enquirer_phone = Column(String(50))
    relationship_to_resident = Column(String(100))  # e.g. "Daughter"
    prospective_resident_name = Column(String(255))
    prospective_resident_dob = Column(DateTime(timezone=True), nullable=True)
    care_needs = Column(Text)
    source = Column(String(100))  # e.g. "website", "hospital_discharge", "word_of_mouth"
    urgency_score = Column(Integer, default=0)  # 0-100; computed by score_lead()
    status = Column(Enum(LeadStatus), default=LeadStatus.new)
    assigned_to_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    care_home = relationship("CareHome", back_populates="leads")
    history = relationship("LeadStatusHistory", back_populates="lead")


class LeadStatusHistory(Base):
    __tablename__ = "lead_status_history"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    lead_id = Column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=False)
    changed_by_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    old_status = Column(Enum(LeadStatus))
    new_status = Column(Enum(LeadStatus), nullable=False)
    notes = Column(Text)
    changed_at = Column(DateTime(timezone=True), default=_now)

    lead = relationship("Lead", back_populates="history")
