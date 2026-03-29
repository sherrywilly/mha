from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GPContactCreate(BaseModel):
    site_id: str
    practice_name: str
    email: str
    phone: str | None = None
    notes: str | None = None


class GPContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    site_id: str
    practice_name: str
    email: str
    phone: str | None = None
    notes: str | None = None
    is_active: bool


class PrescriptionRequestCreate(BaseModel):
    resident_id: str
    drug_id: str
    requested_qty: int | None = None
    requested_qty_unit: str | None = None
    message_subject: str | None = None
    message_body: str | None = None
    gp_contact_id: str | None = None
    client_event_id: str
    context_snapshot: dict = {}


class PrescriptionRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    resident_id: str
    drug_id: str
    requested_qty: int | None = None
    requested_qty_unit: str | None = None
    status: str
    created_by: str
    approved_by: str | None = None
    message_subject: str | None = None
    message_body: str | None = None
    ai_draft: str | None = None
    context_snapshot: dict
    sent_at: datetime | None = None
    send_channel: str | None = None
    gp_contact_id: str | None = None
    reply_summary: str | None = None
    reply_at: datetime | None = None
    client_event_id: str
    created_at: datetime
    updated_at: datetime


class ReplySummaryUpdate(BaseModel):
    reply_summary: str
