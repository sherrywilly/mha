from uuid import uuid4
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_role
from app.models.prescription import PrescriptionRequest, PrescriptionStatus
from app.schemas.prescription import PrescriptionRequestCreate, PrescriptionRequestOut
from app.core.rbac import ROLE_ADMIN, ROLE_MANAGER

router = APIRouter()

@router.post("/prescription-requests", response_model=PrescriptionRequestOut, status_code=201)
def create_prescription_request(payload: PrescriptionRequestCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    pr = PrescriptionRequest(id=str(uuid4()), **payload.model_dump())
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr

@router.post("/prescription-requests/{pr_id}/ai-draft", response_model=PrescriptionRequestOut)
def ai_draft(pr_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    pr = db.query(PrescriptionRequest).filter(PrescriptionRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Not found")
    pr.status = PrescriptionStatus.ai_drafted
    pr.ai_draft_content = "AI-generated prescription draft placeholder."
    db.commit()
    db.refresh(pr)
    return pr

@router.post("/prescription-requests/{pr_id}/approve", response_model=PrescriptionRequestOut)
def approve_prescription(pr_id: str, db: Session = Depends(get_db), _=Depends(require_role(ROLE_ADMIN, ROLE_MANAGER))):
    pr = db.query(PrescriptionRequest).filter(PrescriptionRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Not found")
    pr.status = PrescriptionStatus.approved
    db.commit()
    db.refresh(pr)
    return pr

@router.post("/prescription-requests/{pr_id}/send", response_model=PrescriptionRequestOut)
def send_prescription(pr_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    pr = db.query(PrescriptionRequest).filter(PrescriptionRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Not found")
    pr.status = PrescriptionStatus.sent
    pr.sent_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pr)
    return pr
