from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import UserRole


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sites: Mapped[list[Site]] = relationship("Site", back_populates="organisation", lazy="noload")
    users: Mapped[list[User]] = relationship("User", back_populates="organisation", lazy="noload")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    allowed_ip_ranges: Mapped[list | None] = mapped_column(JSON, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/London")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    organisation: Mapped[Organisation] = relationship("Organisation", back_populates="sites", lazy="noload")
    units: Mapped[list[Unit]] = relationship("Unit", back_populates="site", lazy="noload")
    approved_devices: Mapped[list[ApprovedDevice]] = relationship("ApprovedDevice", back_populates="site", lazy="noload")
    access_policy: Mapped[AccessPolicy | None] = relationship("AccessPolicy", back_populates="site", uselist=False, lazy="noload")


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    site: Mapped[Site] = relationship("Site", back_populates="units", lazy="noload")
    rooms: Mapped[list[Room]] = relationship("Room", back_populates="unit", lazy="noload")
    assignments: Mapped[list[UnitAssignment]] = relationship("UnitAssignment", back_populates="unit", lazy="noload")


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    unit_id: Mapped[str] = mapped_column(String(36), ForeignKey("units.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    unit: Mapped[Unit] = relationship("Unit", back_populates="rooms", lazy="noload")


class ApprovedDevice(Base):
    __tablename__ = "approved_devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    device_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    registered_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    site: Mapped[Site] = relationship("Site", back_populates="approved_devices", lazy="noload")


class AccessPolicy(Base):
    __tablename__ = "access_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False, unique=True)
    require_ip_allowlist: Mapped[bool] = mapped_column(Boolean, default=False)
    require_approved_device: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_offsite_with_mfa: Mapped[bool] = mapped_column(Boolean, default=True)
    break_glass_requires_manager_approval: Mapped[bool] = mapped_column(Boolean, default=True)

    site: Mapped[Site] = relationship("Site", back_populates="access_policy", lazy="noload")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.NURSE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    organisation: Mapped[Organisation] = relationship("Organisation", back_populates="users", lazy="noload")
    unit_assignments: Mapped[list[UnitAssignment]] = relationship("UnitAssignment", back_populates="user", lazy="noload")
    audit_logs: Mapped[list[AuditLog]] = relationship("AuditLog", back_populates="user", lazy="noload", foreign_keys="AuditLog.user_id")


class UnitAssignment(Base):
    __tablename__ = "unit_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    unit_id: Mapped[str] = mapped_column(String(36), ForeignKey("units.id"), nullable=False)
    can_administer_cd: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship("User", back_populates="unit_assignments", lazy="noload")
    unit: Mapped[Unit] = relationship("Unit", back_populates="assignments", lazy="noload")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_break_glass: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User | None] = relationship("User", back_populates="audit_logs", lazy="noload", foreign_keys=[user_id])


class BreakGlassSession(Base):
    __tablename__ = "break_glass_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
