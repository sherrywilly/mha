from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class OrganisationCreate(BaseModel):
    name: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None


class OrganisationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool
    created_at: datetime


class OrganisationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool | None = None


class SiteCreate(BaseModel):
    name: str
    address: str | None = None
    phone: str | None = None
    allowed_ip_ranges: list[str] | None = None
    timezone: str = "Europe/London"


class SiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    org_id: str
    name: str
    address: str | None = None
    phone: str | None = None
    allowed_ip_ranges: list[str] | None = None
    timezone: str
    is_active: bool
    created_at: datetime


class SiteUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    allowed_ip_ranges: list[str] | None = None
    timezone: str | None = None
    is_active: bool | None = None


class UnitCreate(BaseModel):
    name: str
    description: str | None = None


class UnitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    site_id: str
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime


class UnitUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ApprovedDeviceCreate(BaseModel):
    device_fingerprint: str
    device_name: str


class ApprovedDeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    site_id: str
    device_fingerprint: str
    device_name: str
    is_active: bool
    registered_at: datetime


class AccessPolicyCreate(BaseModel):
    require_ip_allowlist: bool = False
    require_approved_device: bool = False
    allow_offsite_with_mfa: bool = True
    break_glass_requires_manager_approval: bool = True


class AccessPolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    site_id: str
    require_ip_allowlist: bool
    require_approved_device: bool
    allow_offsite_with_mfa: bool
    break_glass_requires_manager_approval: bool
