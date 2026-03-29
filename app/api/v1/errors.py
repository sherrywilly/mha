from uuid import uuid4
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_role
from app.models.error import MedicationError
from app.schemas.error import MedicationErrorCreate, MedicationErrorOut
from app.core.rbac import ROLE_ADMIN, ROLE_MANAGER

router = APIRouter()

@router.post("/medication-errors", response_model=MedicationErrorOut, status_code=201)
def create_error(payload: MedicationErrorCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    err = MedicationError(id=str(uuid4()), **payload.model_dump())
    db.add(err)
    db.commit()
    db.refresh(err)
    return err

@router.get("/medication-errors", response_model=List[MedicationErrorOut])
def list_errors(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(MedicationError).all()

@router.post("/medication-errors/{error_id}/close", response_model=MedicationErrorOut)
def close_error(error_id: str, db: Session = Depends(get_db), current_user=Depends(require_role(ROLE_ADMIN, ROLE_MANAGER))):
    err = db.query(MedicationError).filter(MedicationError.id == error_id).first()
    if not err:
        raise HTTPException(status_code=404, detail="Not found")
    err.closed_by_id = current_user.id
    err.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(err)
    return err
