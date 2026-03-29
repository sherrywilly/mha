from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CDTransactionCreate(BaseModel):
    drug_id: str
    resident_id: str | None = None
    order_id: str | None = None
    site_id: str
    tx_type: str
    quantity: float
    unit: str
    performed_at: datetime
    reason: str | None = None
    notes: str | None = None
    client_event_id: str
    is_amendment: bool = False


class CDTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    drug_id: str
    resident_id: str | None = None
    order_id: str | None = None
    site_id: str
    tx_type: str
    quantity: float
    unit: str
    stock_balance_after: float | None = None
    performed_by: str
    witnessed_by: str | None = None
    performed_at: datetime
    witnessed_at: datetime | None = None
    witness_status: str
    reason: str | None = None
    notes: str | None = None
    client_event_id: str
    is_amendment: bool


class CDStockBalanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    drug_id: str
    site_id: str
    current_balance: float
    unit: str
    last_count_at: datetime
    last_count_by: str | None = None


class WitnessRequest(BaseModel):
    witnessed_by: str
    witnessed_at: datetime
