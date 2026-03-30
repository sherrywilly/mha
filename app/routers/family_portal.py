"""
Family Portal router — read-only access for relatives.

Family members can only see residents they are explicitly linked to via
FamilyResidentLink.  They see medication events and vitals but cannot
create, modify, or delete anything.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import (
    FamilyResidentLink,
    MedEvent,
    Prescription,
    Resident,
    UserRole,
    Vital,
)
from app.routers.deps import require_roles
from app.schemas.schemas import ResidentSummary

router = APIRouter(prefix="/family-portal", tags=["family-portal"])


@router.get("/my-residents", response_model=List[ResidentSummary])
def my_residents(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.family)),
):
    """Return summaries of all residents the family member is linked to."""
    links = (
        db.query(FamilyResidentLink)
        .filter(FamilyResidentLink.family_user_id == current_user.id)
        .all()
    )
    summaries = []
    for link in links:
        resident = db.query(Resident).filter(Resident.id == link.resident_id).first()
        if not resident or not resident.is_active:
            continue

        recent_events = (
            db.query(MedEvent)
            .join(MedEvent.prescription)
            .filter(Prescription.resident_id == resident.id)
            .order_by(MedEvent.actual_time.desc())
            .limit(10)
            .all()
        )
        recent_vitals = (
            db.query(Vital)
            .filter(Vital.resident_id == resident.id)
            .order_by(Vital.recorded_at.desc())
            .limit(10)
            .all()
        )

        summaries.append(
            ResidentSummary(
                resident_id=resident.id,
                full_name=resident.full_name,
                room_number=resident.room_number,
                recent_med_events=recent_events,
                recent_vitals=recent_vitals,
            )
        )
    return summaries


@router.get("/residents/{resident_id}", response_model=ResidentSummary)
def get_resident_summary(
    resident_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.family)),
):
    """Return a single resident summary — only if the family member is linked."""
    link = (
        db.query(FamilyResidentLink)
        .filter(
            FamilyResidentLink.family_user_id == current_user.id,
            FamilyResidentLink.resident_id == resident_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=403, detail="Access to this resident is not permitted.")

    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident or not resident.is_active:
        raise HTTPException(status_code=404, detail="Resident not found")

    recent_events = (
        db.query(MedEvent)
        .join(MedEvent.prescription)
        .filter(Prescription.resident_id == resident.id)
        .order_by(MedEvent.actual_time.desc())
        .limit(20)
        .all()
    )
    recent_vitals = (
        db.query(Vital)
        .filter(Vital.resident_id == resident.id)
        .order_by(Vital.recorded_at.desc())
        .limit(20)
        .all()
    )

    return ResidentSummary(
        resident_id=resident.id,
        full_name=resident.full_name,
        room_number=resident.room_number,
        recent_med_events=recent_events,
        recent_vitals=recent_vitals,
    )
