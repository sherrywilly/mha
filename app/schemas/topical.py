from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TopicalSiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    label: str
    body_region: str


class TopicalAdminCreate(BaseModel):
    administration_record_id: str
    body_site_id: str
    body_site_code: str
    area_description: str | None = None
    mode_of_administration: str = "APPLY"
    condition_before: str | None = None
    condition_after: str | None = None
    image_reference: str | None = None
    administered_at: datetime


class TopicalAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    administration_record_id: str
    body_site_id: str
    body_site_code: str
    area_description: str | None = None
    mode_of_administration: str
    condition_before: str | None = None
    condition_after: str | None = None
    image_reference: str | None = None
    administered_by: str
    administered_at: datetime
