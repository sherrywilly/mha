from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CDTransactionCreate(BaseModel):
    transaction_type: str
    drug_id: str
    resident_id: Optional[str] = None
    order_id: Optional[str] = None
    quantity: float
    unit: Optional[str] = None
    performed_by_id: str
    performed_at: Optional[datetime] = None
    reason: Optional[str] = None
    client_event_id: str

class CDTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    transaction_type: str
    drug_id: str
    quantity: float
    performed_by_id: str
    status: str
    client_event_id: str
