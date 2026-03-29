from uuid import uuid4
from sqlalchemy import Column, String, DateTime, func
from app.models.base import Base


class IngestedEvent(Base):
    """Persists ingested event IDs for idempotent batch ingestion."""
    __tablename__ = "ingested_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    organisation_id = Column(String, nullable=False, index=True)
    client_event_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # Unique per (organisation, client_event_id) pair
        __import__("sqlalchemy").UniqueConstraint("organisation_id", "client_event_id", name="uq_ingested_event_org_client"),
    )
