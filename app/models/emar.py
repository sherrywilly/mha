import enum
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Enum, UniqueConstraint
from app.models.base import Base, AuditMixin

class DoseStatus(str, enum.Enum):
    due = "due"
    given = "given"
    refused = "refused"
    withheld = "withheld"
    not_available = "not_available"
    omitted = "omitted"
    late = "late"

class DoseDue(Base, AuditMixin):
    __tablename__ = "doses_due"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    order_id = Column(String, ForeignKey("medication_orders.id"), nullable=False)
    resident_id = Column(String, ForeignKey("residents.id"), nullable=False)
    scheduled_datetime = Column(DateTime(timezone=True), nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=True)
    window_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(DoseStatus, native_enum=False), default=DoseStatus.due)
    dose_key = Column(String, unique=True, nullable=False)

class AdministrationRecord(Base, AuditMixin):
    __tablename__ = "administration_records"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    dose_due_id = Column(String, ForeignKey("doses_due.id"), nullable=True)
    order_id = Column(String, ForeignKey("medication_orders.id"), nullable=False)
    resident_id = Column(String, ForeignKey("residents.id"), nullable=False)
    administered_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    administered_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    route_display = Column(String, nullable=True)
    mode_display = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    reason_code = Column(String, nullable=True)
    client_event_id = Column(String, unique=True, nullable=False)

class AdministrationBodyRegion(Base):
    __tablename__ = "administration_body_regions"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    administration_id = Column(String, ForeignKey("administration_records.id"), nullable=False)
    body_region_id = Column(String, ForeignKey("body_regions.id"), nullable=False)
