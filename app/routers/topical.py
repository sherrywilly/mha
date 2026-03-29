from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, log_audit_event
from app.database import get_db
from app.models.org import User
from app.models.topical import TopicalAdministrationRecord, TopicalSite
from app.schemas.topical import TopicalAdminCreate, TopicalAdminRead, TopicalSiteRead

router = APIRouter(prefix="/topical", tags=["topical"])


@router.get("/body-sites", response_model=list[TopicalSiteRead])
async def list_body_sites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TopicalSite))
    return result.scalars().all()


@router.post("/administrations", response_model=TopicalAdminRead, status_code=201)
async def create_topical_admin(
    payload: TopicalAdminCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = TopicalAdministrationRecord(
        **payload.model_dump(),
        administered_by=current_user.id,
    )
    db.add(record)
    await db.flush()
    await log_audit_event(db, "TOPICAL_ADMINISTRATION", "topical_administration_record", user_id=current_user.id, resource_id=record.id)
    return record


@router.get("/administrations", response_model=list[TopicalAdminRead])
async def list_topical_admins(
    resident_id: str | None = None,
    order_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.medication import AdministrationRecord
    q = select(TopicalAdministrationRecord)
    if resident_id or order_id:
        q = q.join(
            AdministrationRecord,
            TopicalAdministrationRecord.administration_record_id == AdministrationRecord.id,
        )
        if resident_id:
            q = q.where(AdministrationRecord.resident_id == resident_id)
        if order_id:
            q = q.where(AdministrationRecord.order_id == order_id)
    result = await db.execute(q)
    return result.scalars().all()
