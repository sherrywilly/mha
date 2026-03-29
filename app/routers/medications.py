from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, log_audit_event
from app.database import get_db
from app.models.medication import AdministrationRecord, DoseDue, Drug, MedicationOrder
from app.models.org import User
from app.schemas.medication import (
    AdministrationCreate, AdministrationRead,
    DoseDueRead, DrugCreate, DrugRead,
    GenerateDoseDueRequest,
    MedicationOrderCreate, MedicationOrderRead, MedicationOrderUpdate,
)
from app.services.scheduling import generate_dose_due

router = APIRouter(tags=["medications"])


@router.post("/drugs", response_model=DrugRead, status_code=201)
async def create_drug(payload: DrugCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    drug = Drug(**payload.model_dump())
    db.add(drug)
    await db.flush()
    await log_audit_event(db, "CREATE_DRUG", "drug", user_id=current_user.id, resource_id=drug.id)
    return drug


@router.get("/drugs", response_model=list[DrugRead])
async def list_drugs(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Drug).where(Drug.is_active == True))
    return result.scalars().all()


@router.post("/medication-orders", response_model=MedicationOrderRead, status_code=201)
async def create_medication_order(
    payload: MedicationOrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Idempotency check
    existing = await db.execute(
        select(MedicationOrder).where(MedicationOrder.client_event_id == payload.client_event_id)
    )
    existing_order = existing.scalar_one_or_none()
    if existing_order:
        return existing_order

    order = MedicationOrder(**payload.model_dump(), created_by=current_user.id)
    db.add(order)
    await db.flush()
    await log_audit_event(db, "CREATE_MEDICATION_ORDER", "medication_order", user_id=current_user.id, resource_id=order.id)
    return order


@router.get("/medication-orders", response_model=list[MedicationOrderRead])
async def list_medication_orders(
    resident_id: str | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(MedicationOrder)
    if resident_id:
        q = q.where(MedicationOrder.resident_id == resident_id)
    if status:
        q = q.where(MedicationOrder.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/medication-orders/{order_id}", response_model=MedicationOrderRead)
async def get_medication_order(order_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    order = await db.get(MedicationOrder, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order


@router.put("/medication-orders/{order_id}", response_model=MedicationOrderRead)
async def update_medication_order(
    order_id: str,
    payload: MedicationOrderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await db.get(MedicationOrder, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(order, k, v)
    order.version += 1
    await log_audit_event(db, "UPDATE_MEDICATION_ORDER", "medication_order", user_id=current_user.id, resource_id=order_id)
    return order


@router.get("/dose-due", response_model=list[DoseDueRead])
async def list_doses_due(
    resident_id: str | None = None,
    unit_id: str | None = None,
    date: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.resident import Resident
    q = select(DoseDue)
    if resident_id:
        q = q.where(DoseDue.resident_id == resident_id)
    if unit_id:
        q = q.join(Resident, DoseDue.resident_id == Resident.id).where(Resident.unit_id == unit_id)
    if date:
        from datetime import datetime as dt
        day = dt.strptime(date, "%Y-%m-%d").date()
        day_start = dt.combine(day, dt.min.time())
        day_end = dt.combine(day, dt.max.time())
        q = q.where(DoseDue.scheduled_datetime.between(day_start, day_end))
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/dose-due/generate", response_model=list[DoseDueRead])
async def generate_doses(
    payload: GenerateDoseDueRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await db.get(MedicationOrder, payload.order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    doses = await generate_dose_due(order, payload.date_from, payload.date_to, db)
    return doses
