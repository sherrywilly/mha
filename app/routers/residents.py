"""Resident management endpoints."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Resident, UserRole
from app.routers.deps import get_current_user, require_roles, tenant_guard
from app.schemas.schemas import ResidentCreate, ResidentOut

router = APIRouter(prefix="/residents", tags=["residents"])

_staff_roles = (UserRole.admin, UserRole.nurse, UserRole.gp)


@router.post("/", response_model=ResidentOut, status_code=status.HTTP_201_CREATED)
def create_resident(
    payload: ResidentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.admin, UserRole.nurse)),
):
    resident = Resident(**payload.model_dump(), care_home_id=current_user.care_home_id)
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident


@router.get("/", response_model=List[ResidentOut])
def list_residents(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return (
        db.query(Resident)
        .filter(
            Resident.care_home_id == current_user.care_home_id,
            Resident.is_active.is_(True),
        )
        .all()
    )


@router.get("/{resident_id}", response_model=ResidentOut)
def get_resident(
    resident_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    tenant_guard(resident.care_home_id, current_user)
    return resident


@router.patch("/{resident_id}", response_model=ResidentOut)
def update_resident(
    resident_id: str,
    payload: ResidentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.admin, UserRole.nurse)),
):
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    tenant_guard(resident.care_home_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(resident, field, value)
    db.commit()
    db.refresh(resident)
    return resident


@router.delete("/{resident_id}", status_code=status.HTTP_204_NO_CONTENT)
def discharge_resident(
    resident_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.admin)),
):
    """Soft-delete: set is_active=False. Records are never hard-deleted."""
    from datetime import datetime, timezone

    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    tenant_guard(resident.care_home_id, current_user)
    resident.is_active = False
    resident.discharged_at = datetime.now(timezone.utc)
    db.commit()
