from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MedicationErrorCreate(BaseModel):
    administration_id: Optional[str] = None
    resident_id: str
    reported_by_id: str
    error_type: str
    severity: str
    description: Optional[str] = None
    contributing_factors: Optional[List] = []
    actions_taken: Optional[str] = None

class MedicationErrorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    resident_id: str
    reported_by_id: str
    error_type: str
    severity: str
    description: Optional[str] = None
    closed_at: Optional[datetime] = None
