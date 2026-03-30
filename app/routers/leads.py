"""
Lead CRM router — Smart Lead Scoring & pipeline management.

Urgency score is computed automatically on create using the lead scoring service.
Status transitions are tracked in lead_status_history (append-only).
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Lead, LeadStatusHistory, UserRole
from app.routers.deps import get_current_user, require_roles, tenant_guard
from app.schemas.schemas import LeadCreate, LeadOut, LeadStatusUpdate
from app.services.lead_scoring import score_lead

router = APIRouter(prefix="/leads", tags=["leads"])

_crm_roles = (UserRole.admin, UserRole.nurse)


@router.post("/", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(*_crm_roles)),
):
    urgency = score_lead(
        source=payload.source,
        care_needs=payload.care_needs,
        prospective_resident_dob=payload.prospective_resident_dob,
        enquirer_email=payload.enquirer_email,
        enquirer_phone=payload.enquirer_phone,
    )
    lead = Lead(
        **payload.model_dump(),
        care_home_id=current_user.care_home_id,
        urgency_score=urgency,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/", response_model=List[LeadOut])
def list_leads(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(*_crm_roles)),
):
    return (
        db.query(Lead)
        .filter(Lead.care_home_id == current_user.care_home_id)
        .order_by(Lead.urgency_score.desc(), Lead.created_at.desc())
        .all()
    )


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(*_crm_roles)),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    tenant_guard(lead.care_home_id, current_user)
    return lead


@router.patch("/{lead_id}/status", response_model=LeadOut)
def update_lead_status(
    lead_id: str,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(*_crm_roles)),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    tenant_guard(lead.care_home_id, current_user)

    old_status = lead.status
    lead.status = payload.new_status

    history = LeadStatusHistory(
        lead_id=lead.id,
        changed_by_id=current_user.id,
        old_status=old_status,
        new_status=payload.new_status,
        notes=payload.notes,
    )
    db.add(history)
    db.commit()
    db.refresh(lead)
    return lead
