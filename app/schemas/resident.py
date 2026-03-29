from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ResidentCreate(BaseModel):
    unit_id: str
    room_id: str | None = None
    nhs_number: str | None = None
    first_name: str
    last_name: str
    date_of_birth: date
    allergies: list[str] = []
    gp_name: str | None = None
    gp_practice_email: str | None = None


class ResidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    unit_id: str
    room_id: str | None = None
    nhs_number: str | None = None
    first_name: str
    last_name: str
    date_of_birth: date
    allergies: list[str]
    gp_name: str | None = None
    gp_practice_email: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ResidentUpdate(BaseModel):
    room_id: str | None = None
    nhs_number: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    allergies: list[str] | None = None
    gp_name: str | None = None
    gp_practice_email: str | None = None
    is_active: bool | None = None
