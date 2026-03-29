from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DoseDueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_id: str
    resident_id: str
    scheduled_datetime: datetime
    status: str
    dose_key: str

class AdministrationRecordCreate(BaseModel):
    dose_due_id: Optional[str] = None
    order_id: str
    resident_id: str
    administered_by_id: str
    administered_at: datetime
    status: str
    route_display: Optional[str] = None
    mode_display: Optional[str] = None
    notes: Optional[str] = None
    reason_code: Optional[str] = None
    client_event_id: str

class AdministrationRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_id: str
    resident_id: str
    administered_by_id: str
    administered_at: datetime
    status: str
    client_event_id: str
    notes: Optional[str] = None
