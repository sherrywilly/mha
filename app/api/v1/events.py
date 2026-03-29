from typing import List, Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.ingested_event import IngestedEvent

router = APIRouter()


class EventItem(BaseModel):
    client_event_id: str
    event_type: str
    payload: Dict[str, Any] = {}


class IngestResponse(BaseModel):
    client_event_id: str
    result: str  # "created" or "duplicate"


@router.post("/events/ingest", response_model=List[IngestResponse])
def ingest_events(
    events: List[EventItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organisation_id or "global"
    results = []
    for event in events:
        record = IngestedEvent(
            organisation_id=org_id,
            client_event_id=event.client_event_id,
            event_type=event.event_type,
        )
        try:
            db.add(record)
            db.commit()
            results.append(IngestResponse(client_event_id=event.client_event_id, result="created"))
        except IntegrityError:
            db.rollback()
            results.append(IngestResponse(client_event_id=event.client_event_id, result="duplicate"))
    return results
