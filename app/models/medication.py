from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DrugForm:
    TABLET = "TABLET"
    CAPSULE = "CAPSULE"
    LIQUID = "LIQUID"
    INJECTION = "INJECTION"
    TOPICAL = "TOPICAL"
    PATCH = "PATCH"
    INHALER = "INHALER"
    DROPS = "DROPS"
    SUPPOSITORY = "SUPPOSITORY"
    OTHER = "OTHER"
    ALL = [TABLET, CAPSULE, LIQUID, INJECTION, TOPICAL, PATCH, INHALER, DROPS, SUPPOSITORY, OTHER]


class RouteEnum:
    ORAL = "ORAL"
    SUBLINGUAL = "SUBLINGUAL"
    TOPICAL = "TOPICAL"
    TRANSDERMAL = "TRANSDERMAL"
    INHALED = "INHALED"
    RECTAL = "RECTAL"
    SUBCUTANEOUS = "SUBCUTANEOUS"
    INTRAMUSCULAR = "INTRAMUSCULAR"
    INTRAVENOUS = "INTRAVENOUS"
    NASAL = "NASAL"
    OTHER = "OTHER"
    ALL = [ORAL, SUBLINGUAL, TOPICAL, TRANSDERMAL, INHALED, RECTAL, SUBCUTANEOUS, INTRAMUSCULAR, INTRAVENOUS, NASAL, OTHER]


class FrequencyType:
    DAILY_TIMES = "DAILY_TIMES"
    INTERVAL = "INTERVAL"
    WEEKLY = "WEEKLY"
    PRN = "PRN"
    TAPER = "TAPER"
    ONCE = "ONCE"
    ALL = [DAILY_TIMES, INTERVAL, WEEKLY, PRN, TAPER, ONCE]


class OrderStatus:
    ACTIVE = "ACTIVE"
    DISCONTINUED = "DISCONTINUED"
    COMPLETED = "COMPLETED"
    ALL = [ACTIVE, DISCONTINUED, COMPLETED]


class DoseStatus:
    PENDING = "PENDING"
    GIVEN = "GIVEN"
    REFUSED = "REFUSED"
    WITHHELD = "WITHHELD"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    OMITTED = "OMITTED"
    LATE = "LATE"
    ALL = [PENDING, GIVEN, REFUSED, WITHHELD, NOT_AVAILABLE, OMITTED, LATE]


class Drug(Base):
    __tablename__ = "drugs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    generic_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    form: Mapped[str] = mapped_column(String(20), nullable=False, default=DrugForm.TABLET)
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_controlled: Mapped[bool] = mapped_column(Boolean, default=False)
    controlled_schedule: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class MedicationOrder(Base):
    __tablename__ = "medication_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resident_id: Mapped[str] = mapped_column(String(36), ForeignKey("residents.id"), nullable=False)
    drug_id: Mapped[str] = mapped_column(String(36), ForeignKey("drugs.id"), nullable=False)
    prescribed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    dose: Mapped[str] = mapped_column(String(100), nullable=False)
    dose_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    route: Mapped[str] = mapped_column(String(20), nullable=False, default=RouteEnum.ORAL)
    frequency_type: Mapped[str] = mapped_column(String(20), nullable=False)
    frequency_times: Mapped[list | None] = mapped_column(JSON, nullable=True)
    frequency_interval_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    frequency_days: Mapped[list | None] = mapped_column(JSON, nullable=True)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date | None] = mapped_column(nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_prn: Mapped[bool] = mapped_column(Boolean, default=False)
    prn_max_doses_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prn_min_interval_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=OrderStatus.ACTIVE)
    client_event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_topical: Mapped[bool] = mapped_column(Boolean, default=False)

    doses_due: Mapped[list[DoseDue]] = relationship("DoseDue", back_populates="order", lazy="noload")
    administration_records: Mapped[list[AdministrationRecord]] = relationship("AdministrationRecord", back_populates="order", lazy="noload", foreign_keys="AdministrationRecord.order_id")


class DoseDue(Base):
    __tablename__ = "doses_due"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("medication_orders.id"), nullable=False)
    resident_id: Mapped[str] = mapped_column(String(36), ForeignKey("residents.id"), nullable=False)
    scheduled_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    dose_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=DoseStatus.PENDING)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    order: Mapped[MedicationOrder] = relationship("MedicationOrder", back_populates="doses_due", lazy="noload")
    administration_records: Mapped[list[AdministrationRecord]] = relationship("AdministrationRecord", back_populates="dose_due", lazy="noload")


class AdministrationRecord(Base):
    __tablename__ = "administration_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dose_due_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("doses_due.id"), nullable=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("medication_orders.id"), nullable=False)
    resident_id: Mapped[str] = mapped_column(String(36), ForeignKey("residents.id"), nullable=False)
    administered_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    witnessed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    administered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    dose_given: Mapped[str] = mapped_column(String(100), nullable=False)
    dose_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    route_used: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_not_given: Mapped[str | None] = mapped_column(String(255), nullable=True)
    outcome_prn: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_amendment: Mapped[bool] = mapped_column(Boolean, default=False)
    amended_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_record_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("administration_records.id"), nullable=True)

    dose_due: Mapped[DoseDue | None] = relationship("DoseDue", back_populates="administration_records", lazy="noload")
    order: Mapped[MedicationOrder] = relationship("MedicationOrder", back_populates="administration_records", lazy="noload", foreign_keys=[order_id])
