from typing import Optional, List
from datetime import date
from pydantic import BaseModel, ConfigDict

class DrugCreate(BaseModel):
    name: str
    generic_name: Optional[str] = None
    category: Optional[str] = None
    controlled_drug_schedule: Optional[int] = None
    unit_of_measure: Optional[str] = None
    is_active: bool = True

class DrugOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    generic_name: Optional[str] = None
    category: Optional[str] = None
    controlled_drug_schedule: Optional[int] = None
    unit_of_measure: Optional[str] = None
    is_active: bool

class MedicationOrderCreate(BaseModel):
    resident_id: str
    drug_id: str
    prescribed_by: Optional[str] = None
    dose_amount: Optional[float] = None
    dose_unit: Optional[str] = None
    route: Optional[str] = None
    mode_of_administration: Optional[dict] = {}
    frequency_type: str
    daily_times: Optional[List[str]] = []
    interval_hours: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True
    notes: Optional[str] = None

class MedicationOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    resident_id: str
    drug_id: str
    prescribed_by: Optional[str] = None
    dose_amount: Optional[float] = None
    dose_unit: Optional[str] = None
    route: Optional[str] = None
    frequency_type: str
    daily_times: Optional[List[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool
