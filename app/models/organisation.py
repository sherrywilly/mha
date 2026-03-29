from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, JSON
from app.models.base import Base, AuditMixin

class Organisation(Base, AuditMixin):
    __tablename__ = "organisations"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class Site(Base, AuditMixin):
    __tablename__ = "sites"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    organisation_id = Column(String, ForeignKey("organisations.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    allowed_ip_ranges = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)

class Unit(Base, AuditMixin):
    __tablename__ = "units"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
