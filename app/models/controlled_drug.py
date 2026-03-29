import enum
from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Enum
from app.models.base import Base, AuditMixin

class CDTransactionType(str, enum.Enum):
    administer = "administer"
    waste = "waste"
    returned = "returned"
    stock_adjust = "stock_adjust"
    received = "received"

class CDStatus(str, enum.Enum):
    pending_witness = "pending_witness"
    complete = "complete"
    cancelled = "cancelled"

class CDTransaction(Base, AuditMixin):
    __tablename__ = "cd_transactions"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    transaction_type = Column("transaction_type", Enum(CDTransactionType, native_enum=False), nullable=False)
    drug_id = Column(String, ForeignKey("drugs.id"), nullable=False)
    resident_id = Column(String, ForeignKey("residents.id"), nullable=True)
    order_id = Column(String, ForeignKey("medication_orders.id"), nullable=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    performed_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    performed_at = Column(DateTime(timezone=True), nullable=True)
    witnessed_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    witnessed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(CDStatus, native_enum=False), default=CDStatus.pending_witness)
    reason = Column(String, nullable=True)
    client_event_id = Column(String, unique=True, nullable=False)
