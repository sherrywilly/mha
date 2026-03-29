import enum
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Date, Float, Integer, Enum
from app.models.base import Base, AuditMixin

class FrequencyType(str, enum.Enum):
    daily_times = "daily_times"
    interval = "interval"
    weekly = "weekly"
    prn = "prn"
    taper = "taper"

class Drug(Base, AuditMixin):
    __tablename__ = "drugs"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    generic_name = Column(String, nullable=True)
    category = Column(String, nullable=True)
    controlled_drug_schedule = Column(Integer, nullable=True)
    unit_of_measure = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class MedicationOrder(Base, AuditMixin):
    __tablename__ = "medication_orders"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    resident_id = Column(String, ForeignKey("residents.id"), nullable=False)
    drug_id = Column(String, ForeignKey("drugs.id"), nullable=False)
    prescribed_by = Column(String, nullable=True)
    dose_amount = Column(Float, nullable=True)
    dose_unit = Column(String, nullable=True)
    route = Column(String, nullable=True)
    mode_of_administration = Column(JSON, default=dict)
    frequency_type = Column(Enum(FrequencyType, native_enum=False), nullable=False)
    daily_times = Column(JSON, default=list)
    interval_hours = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(String, nullable=True)
