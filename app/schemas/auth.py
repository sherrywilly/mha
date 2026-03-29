from typing import Optional
from pydantic import BaseModel, ConfigDict

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    role_id: Optional[str] = None
    organisation_id: Optional[str] = None

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    role_id: Optional[str] = None
    organisation_id: Optional[str] = None
