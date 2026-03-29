import enum
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, Enum
from app.models.base import Base, AuditMixin

class PrescriptionStatus(str, enum.Enum):
    draft = "draft"
    ai_drafted = "ai_drafted"
    approved = "approved"
    sent = "sent"

class GPContact(Base):
    __tablename__ = "gp_contacts"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    name = Column(String, nullable=False)
    practice_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class PrescriptionRequest(Base, AuditMixin):
    __tablename__ = "prescription_requests"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    resident_id = Column(String, ForeignKey("residents.id"), nullable=False)
    gp_contact_id = Column(String, ForeignKey("gp_contacts.id"), nullable=True)
    requested_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(PrescriptionStatus, native_enum=False), default=PrescriptionStatus.draft)
    ai_draft_content = Column(Text, nullable=True)
    notes = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
