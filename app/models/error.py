import enum
from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, DateTime, JSON, Text, Enum
from app.models.base import Base, AuditMixin

class ErrorType(str, enum.Enum):
    near_miss = "near_miss"
    error = "error"

class Severity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class MedicationError(Base, AuditMixin):
    __tablename__ = "medication_errors"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    administration_id = Column(String, ForeignKey("administration_records.id"), nullable=True)
    resident_id = Column(String, ForeignKey("residents.id"), nullable=False)
    reported_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    error_type = Column(Enum(ErrorType, native_enum=False), nullable=False)
    severity = Column(Enum(Severity, native_enum=False), nullable=False)
    description = Column(Text, nullable=True)
    contributing_factors = Column(JSON, default=list)
    actions_taken = Column(Text, nullable=True)
    closed_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
