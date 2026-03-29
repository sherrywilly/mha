from typing import Optional, List
from datetime import date
from pydantic import BaseModel, ConfigDict

class ResidentCreate(BaseModel):
    unit_id: str
    first_name: str
    last_name: str
    dob: Optional[date] = None
    nhs_number: Optional[str] = None
    room_number: Optional[str] = None
    allergies: Optional[List] = []
    key_risks: Optional[List] = []
    is_active: bool = True

class ResidentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    nhs_number: Optional[str] = None
    room_number: Optional[str] = None
    allergies: Optional[List] = None
    key_risks: Optional[List] = None
    is_active: Optional[bool] = None

class ResidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    unit_id: str
    first_name: str
    last_name: str
    dob: Optional[date] = None
    nhs_number: Optional[str] = None
    room_number: Optional[str] = None
    is_active: bool
