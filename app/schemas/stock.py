from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class StockLocationCreate(BaseModel):
    unit_id: str
    name: str
    location_type: str
    is_active: bool = True

class StockLocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    unit_id: str
    name: str
    location_type: str
    is_active: bool

class StockTransactionCreate(BaseModel):
    item_id: str
    transaction_type: str
    quantity_change: float
    quantity_after: Optional[float] = None
    notes: Optional[str] = None
    performed_by_id: str
    client_event_id: str

class StockTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    item_id: str
    transaction_type: str
    quantity_change: float
    quantity_after: Optional[float] = None
    performed_by_id: str
    client_event_id: str

class StockItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    location_id: str
    drug_id: str
    on_hand_qty: float
    reorder_threshold: Optional[float] = None
    unit_of_measure: Optional[str] = None

class StockAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    item_id: str
    alert_type: str
    triggered_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class StockCountItem(BaseModel):
    item_id: str
    counted_qty: float
    performed_by_id: str
    client_event_id: str
