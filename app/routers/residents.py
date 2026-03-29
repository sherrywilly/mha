from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, log_audit_event
from app.database import get_db
from app.models.org import User
from app.models.resident import Resident
from app.schemas.resident import ResidentCreate, ResidentRead, ResidentUpdate

router = APIRouter(tags=["residents"])


@router.get("/residents", response_model=list[ResidentRead])
async def list_residents(
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resident).where(Resident.is_active == is_active))
    return result.scalars().all()


@router.post("/residents", response_model=ResidentRead, status_code=201)
async def create_resident(
    payload: ResidentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resident = Resident(**payload.model_dump())
    db.add(resident)
    await db.flush()
    await log_audit_event(db, "CREATE_RESIDENT", "resident", user_id=current_user.id, resource_id=resident.id)
    return resident


@router.get("/residents/{resident_id}", response_model=ResidentRead)
async def get_resident(
    resident_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resident = await db.get(Resident, resident_id)
    if not resident:
        raise HTTPException(404, "Resident not found")
    return resident


@router.put("/residents/{resident_id}", response_model=ResidentRead)
async def update_resident(
    resident_id: str,
    payload: ResidentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resident = await db.get(Resident, resident_id)
    if not resident:
        raise HTTPException(404, "Resident not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(resident, k, v)
    await log_audit_event(db, "UPDATE_RESIDENT", "resident", user_id=current_user.id, resource_id=resident_id)
    return resident


@router.delete("/residents/{resident_id}", status_code=204)
async def delete_resident(
    resident_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resident = await db.get(Resident, resident_id)
    if not resident:
        raise HTTPException(404, "Resident not found")
    resident.is_active = False
    await log_audit_event(db, "DEACTIVATE_RESIDENT", "resident", user_id=current_user.id, resource_id=resident_id)


@router.get("/units/{unit_id}/residents", response_model=list[ResidentRead])
async def list_unit_residents(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resident).where(Resident.unit_id == unit_id, Resident.is_active == True)
    )
    return result.scalars().all()
