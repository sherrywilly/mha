from uuid import uuid4
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.api.deps import get_db, get_current_user
from app.models.emar import DoseDue, AdministrationRecord
from app.schemas.emar import DoseDueOut, AdministrationRecordCreate, AdministrationRecordOut

router = APIRouter()

@router.get("/doses-due", response_model=List[DoseDueOut])
def list_doses_due(
    unit_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(DoseDue)
    if status:
        q = q.filter(DoseDue.status == status)
    return q.all()

@router.post("/administration-records", response_model=AdministrationRecordOut)
def create_admin_record(
    payload: AdministrationRecordCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    record = AdministrationRecord(id=str(uuid4()), **payload.model_dump())
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError:
        db.rollback()
        existing = db.query(AdministrationRecord).filter(
            AdministrationRecord.client_event_id == payload.client_event_id
        ).first()
        if existing:
            return existing
        raise HTTPException(status_code=409, detail="Conflict")

@router.get("/administration-records", response_model=List[AdministrationRecordOut])
def list_admin_records(
    resident_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(AdministrationRecord)
    if resident_id:
        q = q.filter(AdministrationRecord.resident_id == resident_id)
    return q.all()
