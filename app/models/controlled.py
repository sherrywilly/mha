from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CDTxType:
    ADMINISTER = "ADMINISTER"
    WASTE = "WASTE"
    RETURN = "RETURN"
    STOCK_ADJUST = "STOCK_ADJUST"
    RECEIVED = "RECEIVED"
    TRANSFER = "TRANSFER"
    ALL = [ADMINISTER, WASTE, RETURN, STOCK_ADJUST, RECEIVED, TRANSFER]


class WitnessStatus:
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"
    ESCALATED = "ESCALATED"
    ALL = [PENDING, COMPLETE, ESCALATED]


class CDTransaction(Base):
    __tablename__ = "cd_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    drug_id: Mapped[str] = mapped_column(String(36), ForeignKey("drugs.id"), nullable=False)
    resident_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("residents.id"), nullable=True)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("medication_orders.id"), nullable=True)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    tx_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    stock_balance_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    performed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    witnessed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    witnessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    witness_status: Mapped[str] = mapped_column(String(20), nullable=False, default=WitnessStatus.PENDING)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_amendment: Mapped[bool] = mapped_column(Boolean, default=False)


class CDStockBalance(Base):
    __tablename__ = "cd_stock_balances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    drug_id: Mapped[str] = mapped_column(String(36), ForeignKey("drugs.id"), nullable=False)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    current_balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    last_count_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_count_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
