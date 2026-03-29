from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DrugCreate(BaseModel):
    name: str
    generic_name: str | None = None
    form: str = "TABLET"
    strength: str | None = None
    unit: str | None = None
    is_controlled: bool = False
    controlled_schedule: int | None = None


class DrugRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    generic_name: str | None = None
    form: str
    strength: str | None = None
    unit: str | None = None
    is_controlled: bool
    controlled_schedule: int | None = None
    is_active: bool


class MedicationOrderCreate(BaseModel):
    resident_id: str
    drug_id: str
    prescribed_by: str
    dose: str
    dose_unit: str
    route: str = "ORAL"
    frequency_type: str
    frequency_times: list[str] | None = None
    frequency_interval_hours: float | None = None
    frequency_days: list[int] | None = None
    start_date: date
    end_date: date | None = None
    instructions: str | None = None
    is_prn: bool = False
    prn_max_doses_per_day: int | None = None
    prn_min_interval_hours: float | None = None
    client_event_id: str
    is_topical: bool = False


class MedicationOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    resident_id: str
    drug_id: str
    prescribed_by: str
    dose: str
    dose_unit: str
    route: str
    frequency_type: str
    frequency_times: list[str] | None = None
    frequency_interval_hours: float | None = None
    frequency_days: list[int] | None = None
    start_date: date
    end_date: date | None = None
    instructions: str | None = None
    is_prn: bool
    prn_max_doses_per_day: int | None = None
    prn_min_interval_hours: float | None = None
    status: str
    client_event_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    version: int
    is_topical: bool


class MedicationOrderUpdate(BaseModel):
    status: str | None = None
    end_date: date | None = None
    instructions: str | None = None


class DoseDueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_id: str
    resident_id: str
    scheduled_datetime: datetime
    window_start: datetime
    window_end: datetime
    dose_key: str
    status: str
    updated_at: datetime


class AdministrationCreate(BaseModel):
    dose_due_id: str | None = None
    order_id: str
    resident_id: str
    administered_at: datetime
    dose_given: str
    dose_unit: str
    route_used: str
    notes: str | None = None
    reason_not_given: str | None = None
    outcome_prn: str | None = None
    client_event_id: str
    is_amendment: bool = False
    amended_reason: str | None = None
    original_record_id: str | None = None
    witnessed_by: str | None = None


class AdministrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    dose_due_id: str | None = None
    order_id: str
    resident_id: str
    administered_by: str
    witnessed_by: str | None = None
    administered_at: datetime
    dose_given: str
    dose_unit: str
    route_used: str
    notes: str | None = None
    reason_not_given: str | None = None
    outcome_prn: str | None = None
    client_event_id: str
    is_amendment: bool
    amended_reason: str | None = None
    original_record_id: str | None = None


class GenerateDoseDueRequest(BaseModel):
    order_id: str
    date_from: date
    date_to: date
