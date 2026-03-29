from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PrescriptionStatus:
    DRAFT = "DRAFT"
    READY_TO_SEND = "READY_TO_SEND"
    SENT = "SENT"
    REPLIED = "REPLIED"
    CLOSED = "CLOSED"
    ALL = [DRAFT, READY_TO_SEND, SENT, REPLIED, CLOSED]


class GPContact(Base):
    __tablename__ = "gp_contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    practice_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PrescriptionRequest(Base):
    __tablename__ = "prescription_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resident_id: Mapped[str] = mapped_column(String(36), ForeignKey("residents.id"), nullable=False)
    drug_id: Mapped[str] = mapped_column(String(36), ForeignKey("drugs.id"), nullable=False)
    requested_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requested_qty_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=PrescriptionStatus.DRAFT)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    message_subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    message_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    send_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gp_contact_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gp_contacts.id"), nullable=True)
    reply_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    client_event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
