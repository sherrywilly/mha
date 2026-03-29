from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, log_audit_event
from app.database import get_db
from app.models.error import MedicationError
from app.models.org import User
from app.schemas.error import CloseErrorRequest, MedicationErrorCreate, MedicationErrorRead

router = APIRouter(tags=["errors"])


@router.post("/medication-errors", response_model=MedicationErrorRead, status_code=201)
async def report_error(
    payload: MedicationErrorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(MedicationError).where(MedicationError.client_event_id == payload.client_event_id)
    )
    if err := existing.scalar_one_or_none():
        return err

    err = MedicationError(**payload.model_dump(), reported_by=current_user.id)
    db.add(err)
    await db.flush()
    await log_audit_event(db, "REPORT_MED_ERROR", "medication_error", user_id=current_user.id, resource_id=err.id,
                          detail={"severity": payload.severity, "type": payload.error_type})
    return err


@router.get("/medication-errors", response_model=list[MedicationErrorRead])
async def list_errors(
    resident_id: str | None = None,
    unit_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.resident import Resident
    q = select(MedicationError)
    if resident_id:
        q = q.where(MedicationError.resident_id == resident_id)
    if unit_id:
        q = q.join(Resident, MedicationError.resident_id == Resident.id).where(Resident.unit_id == unit_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/medication-errors/{error_id}", response_model=MedicationErrorRead)
async def get_error(
    error_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    err = await db.get(MedicationError, error_id)
    if not err:
        raise HTTPException(404, "Error not found")
    return err


@router.put("/medication-errors/{error_id}/close", response_model=MedicationErrorRead)
async def close_error(
    error_id: str,
    payload: CloseErrorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    err = await db.get(MedicationError, error_id)
    if not err:
        raise HTTPException(404, "Error not found")
    err.is_closed = True
    err.closed_at = datetime.now(timezone.utc)
    err.closed_by = current_user.id
    if payload.investigation_notes:
        err.investigation_notes = payload.investigation_notes
    await log_audit_event(db, "CLOSE_MED_ERROR", "medication_error", user_id=current_user.id, resource_id=error_id)
    return err
