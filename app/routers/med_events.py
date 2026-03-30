"""
eMAR medication event endpoints (WORM audit trail).

Key rules enforced here:
  1. MedEvents are never deleted or modified.
  2. Corrections are new rows with event_type=correction referencing the original.
  3. Vitals Bridge: if BP or blood sugar is out of range the medication is
     automatically held and the GP is flagged for alert.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import MedEvent, MedEventType, Prescription, UserRole
from app.routers.deps import get_current_user, require_roles, tenant_guard
from app.schemas.schemas import MedEventCorrection, MedEventCreate, MedEventOut
from app.services.vitals_bridge import check_vitals

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/med-events", tags=["eMAR"])


def _gp_alert(resident, reasons: list[str]) -> None:
    """
    Placeholder: send an alert email to the resident's GP.

    In production this would dispatch via an email service (e.g. AWS SES / SendGrid).
    """
    if resident.gp_email:
        logger.warning(
            "GP ALERT for resident %s (%s): %s",
            resident.full_name,
            resident.gp_email,
            "; ".join(reasons),
        )


@router.post("/", response_model=MedEventOut, status_code=status.HTTP_201_CREATED)
def record_med_event(
    payload: MedEventCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.nurse, UserRole.admin)),
):
    prescription = db.query(Prescription).filter(
        Prescription.id == payload.prescription_id
    ).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    tenant_guard(prescription.resident.care_home_id, current_user)

    # Vitals Bridge check
    vitals_blocked, reasons = check_vitals(
        payload.bp_systolic, payload.bp_diastolic, payload.blood_sugar
    )
    event_type = payload.event_type
    gp_alerted = False

    if vitals_blocked:
        event_type = MedEventType.held
        gp_alerted = True
        _gp_alert(prescription.resident, reasons)

    event = MedEvent(
        prescription_id=payload.prescription_id,
        administered_by_id=current_user.id,
        event_type=event_type,
        scheduled_time=payload.scheduled_time,
        notes=payload.notes,
        bp_systolic=payload.bp_systolic,
        bp_diastolic=payload.bp_diastolic,
        blood_sugar=payload.blood_sugar,
        vitals_blocked=vitals_blocked,
        gp_alerted=gp_alerted,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/corrections", response_model=MedEventOut, status_code=status.HTTP_201_CREATED)
def correct_med_event(
    payload: MedEventCorrection,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.nurse, UserRole.admin)),
):
    """
    Create a correction record referencing an existing event.
    The original event is never modified (WORM).
    """
    original = db.query(MedEvent).filter(MedEvent.id == payload.corrects_event_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Original med event not found")
    tenant_guard(original.prescription.resident.care_home_id, current_user)

    correction = MedEvent(
        prescription_id=original.prescription_id,
        administered_by_id=current_user.id,
        event_type=MedEventType.correction,
        scheduled_time=original.scheduled_time,
        notes=payload.notes,
        corrects_event_id=original.id,
        correction_reason=payload.correction_reason,
    )
    db.add(correction)
    db.commit()
    db.refresh(correction)
    return correction


@router.get("/resident/{resident_id}", response_model=List[MedEventOut])
def list_events_for_resident(
    resident_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    events = (
        db.query(MedEvent)
        .join(MedEvent.prescription)
        .join(Prescription.resident)
        .filter(Prescription.resident_id == resident_id)
        .order_by(MedEvent.actual_time.desc())
        .all()
    )
    if events:
        tenant_guard(events[0].prescription.resident.care_home_id, current_user)
    return events
