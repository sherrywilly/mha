from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user
from app.models.user import User

router = APIRouter()

class EventItem(BaseModel):
    client_event_id: str
    event_type: str
    payload: Dict[str, Any] = {}

class IngestResponse(BaseModel):
    client_event_id: str
    result: str  # "created" or "duplicate"

_seen_events: Dict[str, set] = {}
# NOTE: In-memory deduplication only - use DB-backed solution for multi-instance production deployments

@router.post("/events/ingest", response_model=List[IngestResponse])
def ingest_events(
    events: List[EventItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organisation_id or "global"
    if org_id not in _seen_events:
        _seen_events[org_id] = set()

    results = []
    for event in events:
        if event.client_event_id in _seen_events[org_id]:
            results.append(IngestResponse(client_event_id=event.client_event_id, result="duplicate"))
        else:
            _seen_events[org_id].add(event.client_event_id)
            results.append(IngestResponse(client_event_id=event.client_event_id, result="created"))

    return results
