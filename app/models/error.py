from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ErrorType:
    WRONG_DOSE = "WRONG_DOSE"
    WRONG_DRUG = "WRONG_DRUG"
    WRONG_ROUTE = "WRONG_ROUTE"
    WRONG_TIME = "WRONG_TIME"
    WRONG_PATIENT = "WRONG_PATIENT"
    OMISSION = "OMISSION"
    EXTRA_DOSE = "EXTRA_DOSE"
    OTHER = "OTHER"
    ALL = [WRONG_DOSE, WRONG_DRUG, WRONG_ROUTE, WRONG_TIME, WRONG_PATIENT, OMISSION, EXTRA_DOSE, OTHER]


class ErrorSeverity:
    NEAR_MISS = "NEAR_MISS"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    SERIOUS = "SERIOUS"
    LIFE_THREATENING = "LIFE_THREATENING"
    ALL = [NEAR_MISS, MINOR, MODERATE, SERIOUS, LIFE_THREATENING]


class MedicationError(Base):
    __tablename__ = "medication_errors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resident_id: Mapped[str] = mapped_column(String(36), ForeignKey("residents.id"), nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("medication_orders.id"), nullable=True)
    drug_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("drugs.id"), nullable=True)
    reported_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    error_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    immediate_action_taken: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    gp_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    family_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    client_event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    investigation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
