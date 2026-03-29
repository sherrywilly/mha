import enum
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Float, Enum, UniqueConstraint
from app.models.base import Base, AuditMixin

class LocationType(str, enum.Enum):
    shelf = "shelf"
    trolley = "trolley"
    fridge = "fridge"

class StockTransactionType(str, enum.Enum):
    count = "count"
    dispense = "dispense"
    receive = "receive"
    adjust = "adjust"
    waste = "waste"

class AlertType(str, enum.Enum):
    low_stock = "low_stock"
    not_available = "not_available"

class StockLocation(Base):
    __tablename__ = "stock_locations"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    name = Column(String, nullable=False)
    location_type = Column(Enum(LocationType, native_enum=False), nullable=False)
    is_active = Column(Boolean, default=True)

class StockItem(Base):
    __tablename__ = "stock_items"
    __table_args__ = (UniqueConstraint("location_id", "drug_id"),)
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    location_id = Column(String, ForeignKey("stock_locations.id"), nullable=False)
    drug_id = Column(String, ForeignKey("drugs.id"), nullable=False)
    on_hand_qty = Column(Float, default=0.0)
    reorder_threshold = Column(Float, nullable=True)
    unit_of_measure = Column(String, nullable=True)

class StockTransaction(Base, AuditMixin):
    __tablename__ = "stock_transactions"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    item_id = Column(String, ForeignKey("stock_items.id"), nullable=False)
    transaction_type = Column(Enum(StockTransactionType, native_enum=False), nullable=False)
    quantity_change = Column(Float, nullable=False)
    quantity_after = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    performed_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_event_id = Column(String, unique=True, nullable=False)

class StockAlert(Base):
    __tablename__ = "stock_alerts"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    item_id = Column(String, ForeignKey("stock_items.id"), nullable=False)
    alert_type = Column(Enum(AlertType, native_enum=False), nullable=False)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    notes = Column(String, nullable=True)
