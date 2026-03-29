from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, log_audit_event
from app.database import get_db
from app.models.medication import AdministrationRecord, DoseDue
from app.models.org import User
from app.schemas.medication import AdministrationCreate, AdministrationRead

router = APIRouter(tags=["administration"])


@router.post("/administrations", response_model=AdministrationRead, status_code=201)
async def record_administration(
    payload: AdministrationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Idempotency
    existing = await db.execute(
        select(AdministrationRecord).where(AdministrationRecord.client_event_id == payload.client_event_id)
    )
    if rec := existing.scalar_one_or_none():
        return rec

    rec = AdministrationRecord(**payload.model_dump(), administered_by=current_user.id)
    db.add(rec)
    await db.flush()

    # Update DoseDue status if linked
    if payload.dose_due_id:
        dose = await db.get(DoseDue, payload.dose_due_id)
        if dose:
            dose.status = "GIVEN" if not payload.reason_not_given else payload.reason_not_given or "OMITTED"

    await log_audit_event(db, "ADMINISTER_DOSE", "administration_record", user_id=current_user.id, resource_id=rec.id)
    return rec


@router.get("/administrations", response_model=list[AdministrationRead])
async def list_administrations(
    resident_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(AdministrationRecord)
    if resident_id:
        q = q.where(AdministrationRecord.resident_id == resident_id)
    if date_from:
        from datetime import datetime
        q = q.where(AdministrationRecord.administered_at >= datetime.fromisoformat(date_from))
    if date_to:
        from datetime import datetime
        q = q.where(AdministrationRecord.administered_at <= datetime.fromisoformat(date_to))
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/administrations/{record_id}", response_model=AdministrationRead)
async def get_administration(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rec = await db.get(AdministrationRecord, record_id)
    if not rec:
        raise HTTPException(404, "Administration record not found")
    return rec
