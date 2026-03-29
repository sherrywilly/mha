from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MedicationErrorCreate(BaseModel):
    resident_id: str
    order_id: str | None = None
    drug_id: str | None = None
    error_type: str
    severity: str
    description: str
    immediate_action_taken: str
    outcome: str | None = None
    gp_notified: bool = False
    family_notified: bool = False
    occurred_at: datetime
    client_event_id: str


class MedicationErrorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    resident_id: str
    order_id: str | None = None
    drug_id: str | None = None
    reported_by: str
    error_type: str
    severity: str
    description: str
    immediate_action_taken: str
    outcome: str | None = None
    gp_notified: bool
    family_notified: bool
    occurred_at: datetime
    reported_at: datetime
    client_event_id: str
    is_closed: bool
    closed_at: datetime | None = None
    closed_by: str | None = None
    investigation_notes: str | None = None


class CloseErrorRequest(BaseModel):
    investigation_notes: str | None = None
