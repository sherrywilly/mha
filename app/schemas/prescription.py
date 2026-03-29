from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class PrescriptionRequestCreate(BaseModel):
    resident_id: str
    gp_contact_id: Optional[str] = None
    requested_by_id: str
    notes: Optional[str] = None

class PrescriptionRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    resident_id: str
    requested_by_id: str
    status: str
    ai_draft_content: Optional[str] = None
    notes: Optional[str] = None
    sent_at: Optional[datetime] = None
