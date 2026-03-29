from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Date
from app.models.base import Base, AuditMixin

class Resident(Base, AuditMixin):
    __tablename__ = "residents"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    dob = Column(Date, nullable=True)
    nhs_number = Column(String, nullable=True)
    room_number = Column(String, nullable=True)
    allergies = Column(JSON, default=list)
    key_risks = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)

class BodyRegion(Base):
    __tablename__ = "body_regions"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
