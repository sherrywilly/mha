from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LocationType:
    SHELF = "SHELF"
    TROLLEY = "TROLLEY"
    FRIDGE = "FRIDGE"
    CD_CABINET = "CD_CABINET"
    OTHER = "OTHER"
    ALL = [SHELF, TROLLEY, FRIDGE, CD_CABINET, OTHER]


class StockTxType:
    RECEIVE = "RECEIVE"
    MOVE = "MOVE"
    CONSUME = "CONSUME"
    COUNT = "COUNT"
    ADJUST = "ADJUST"
    WASTE = "WASTE"
    RETURN = "RETURN"
    ALL = [RECEIVE, MOVE, CONSUME, COUNT, ADJUST, WASTE, RETURN]


class AlertType:
    LOW_STOCK = "LOW_STOCK"
    RUNOUT_RISK = "RUNOUT_RISK"
    NOT_AVAILABLE_TRIGGER = "NOT_AVAILABLE_TRIGGER"
    VARIANCE = "VARIANCE"
    EXPIRY_NEAR = "EXPIRY_NEAR"
    ALL = [LOW_STOCK, RUNOUT_RISK, NOT_AVAILABLE_TRIGGER, VARIANCE, EXPIRY_NEAR]


class ShiftEnum:
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    NIGHT = "NIGHT"
    ALL = [MORNING, AFTERNOON, NIGHT]


class StockLocation(Base):
    __tablename__ = "stock_locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    unit_id: Mapped[str] = mapped_column(String(36), ForeignKey("units.id"), nullable=False)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_type: Mapped[str] = mapped_column(String(20), nullable=False, default=LocationType.SHELF)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    items: Mapped[list[StockItem]] = relationship("StockItem", back_populates="location", lazy="noload")


class StockItem(Base):
    __tablename__ = "stock_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    drug_id: Mapped[str] = mapped_column(String(36), ForeignKey("drugs.id"), nullable=False)
    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_locations.id"), nullable=False)
    batch_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    on_hand_qty: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    low_stock_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    location: Mapped[StockLocation] = relationship("StockLocation", back_populates="items", lazy="noload")


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    drug_id: Mapped[str] = mapped_column(String(36), ForeignKey("drugs.id"), nullable=False)
    from_location_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stock_locations.id"), nullable=True)
    to_location_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stock_locations.id"), nullable=True)
    tx_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    performed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    client_event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class StockAlert(Base):
    __tablename__ = "stock_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    drug_id: Mapped[str] = mapped_column(String(36), ForeignKey("drugs.id"), nullable=False)
    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_locations.id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    location_ref: Mapped[StockLocation] = relationship("StockLocation", lazy="noload", foreign_keys=[location_id])


class ShiftStockCheck(Base):
    __tablename__ = "shift_stock_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    unit_id: Mapped[str] = mapped_column(String(36), ForeignKey("units.id"), nullable=False)
    performed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    shift: Mapped[str] = mapped_column(String(20), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    check_items: Mapped[list[ShiftStockCheckItem]] = relationship("ShiftStockCheckItem", back_populates="check", lazy="noload")


class ShiftStockCheckItem(Base):
    __tablename__ = "shift_stock_check_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_id: Mapped[str] = mapped_column(String(36), ForeignKey("shift_stock_checks.id"), nullable=False)
    stock_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_items.id"), nullable=False)
    counted_qty: Mapped[float] = mapped_column(Float, nullable=False)
    expected_qty: Mapped[float] = mapped_column(Float, nullable=False)
    variance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    variance_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    check: Mapped[ShiftStockCheck] = relationship("ShiftStockCheck", back_populates="check_items", lazy="noload")
