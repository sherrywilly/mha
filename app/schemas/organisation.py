from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class OrganisationCreate(BaseModel):
    name: str
    is_active: bool = True

class OrganisationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    is_active: bool

class SiteCreate(BaseModel):
    organisation_id: str
    name: str
    address: Optional[str] = None
    allowed_ip_ranges: Optional[List[str]] = []
    is_active: bool = True

class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organisation_id: str
    name: str
    address: Optional[str] = None
    is_active: bool

class UnitCreate(BaseModel):
    site_id: str
    name: str
    description: Optional[str] = None
    is_active: bool = True

class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    site_id: str
    name: str
    description: Optional[str] = None
    is_active: bool
