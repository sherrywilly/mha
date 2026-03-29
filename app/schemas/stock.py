from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class StockLocationCreate(BaseModel):
    unit_id: str
    site_id: str
    name: str
    location_type: str = "SHELF"


class StockLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    unit_id: str
    site_id: str
    name: str
    location_type: str
    is_active: bool


class StockItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    drug_id: str
    location_id: str
    batch_no: str | None = None
    expiry_date: date | None = None
    on_hand_qty: float
    unit: str
    low_stock_threshold: float
    updated_at: datetime


class StockTransactionCreate(BaseModel):
    drug_id: str
    from_location_id: str | None = None
    to_location_id: str | None = None
    tx_type: str
    quantity: float
    unit: str
    reason: str | None = None
    performed_at: datetime
    client_event_id: str
    notes: str | None = None


class StockTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    drug_id: str
    from_location_id: str | None = None
    to_location_id: str | None = None
    tx_type: str
    quantity: float
    unit: str
    reason: str | None = None
    performed_by: str
    performed_at: datetime
    client_event_id: str
    notes: str | None = None


class StockAlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    drug_id: str
    location_id: str
    alert_type: str
    message: str
    is_resolved: bool
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None


class ShiftStockCheckCreate(BaseModel):
    unit_id: str
    shift: str
    performed_at: datetime
    notes: str | None = None


class ShiftStockCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    unit_id: str
    performed_by: str
    shift: str
    performed_at: datetime
    notes: str | None = None
    is_complete: bool


class ShiftCheckItemCreate(BaseModel):
    stock_item_id: str
    counted_qty: float
    expected_qty: float
    variance_reason: str | None = None
