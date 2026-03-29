from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base, AuditMixin

class Role(Base):
    __tablename__ = "roles"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, unique=True, nullable=False)
    permissions = Column(JSON, default=list)

class User(Base, AuditMixin):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role_id = Column(String, ForeignKey("roles.id"), nullable=True)
    organisation_id = Column(String, ForeignKey("organisations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = relationship("Role", lazy="joined")

class UserUnitAssignment(Base):
    __tablename__ = "user_unit_assignments"
    __table_args__ = (UniqueConstraint("user_id", "unit_id"),)
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True))
    assigned_by_id = Column(String, ForeignKey("users.id"), nullable=True)
