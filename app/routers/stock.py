from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, log_audit_event
from app.database import get_db
from app.models.org import User
from app.models.stock import (
    ShiftStockCheck, ShiftStockCheckItem,
    StockAlert, StockItem, StockLocation, StockTransaction,
)
from app.schemas.stock import (
    ShiftCheckItemCreate, ShiftStockCheckCreate, ShiftStockCheckRead,
    StockAlertRead, StockItemRead, StockLocationCreate, StockLocationRead,
    StockTransactionCreate, StockTransactionRead,
)

router = APIRouter(prefix="/stock", tags=["stock"])


async def _check_and_create_alerts(db: AsyncSession, drug_id: str, location_id: str) -> None:
    result = await db.execute(
        select(StockItem).where(
            StockItem.drug_id == drug_id, StockItem.location_id == location_id
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        return
    if item.on_hand_qty <= 0:
        alert = StockAlert(
            drug_id=drug_id, location_id=location_id,
            alert_type="RUNOUT_RISK",
            message=f"Drug {drug_id} has run out at location {location_id}",
        )
        db.add(alert)
    elif item.on_hand_qty < item.low_stock_threshold:
        alert = StockAlert(
            drug_id=drug_id, location_id=location_id,
            alert_type="LOW_STOCK",
            message=f"Drug {drug_id} is below threshold at location {location_id}",
        )
        db.add(alert)


@router.post("/locations", response_model=StockLocationRead, status_code=201)
async def create_location(
    payload: StockLocationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    loc = StockLocation(**payload.model_dump())
    db.add(loc)
    await db.flush()
    return loc


@router.get("/locations", response_model=list[StockLocationRead])
async def list_locations(
    unit_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(StockLocation).where(StockLocation.is_active == True)
    if unit_id:
        q = q.where(StockLocation.unit_id == unit_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/items", response_model=list[StockItemRead])
async def list_items(
    unit_id: str | None = None,
    location_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(StockItem)
    if location_id:
        q = q.where(StockItem.location_id == location_id)
    if unit_id:
        q = q.join(StockLocation, StockItem.location_id == StockLocation.id).where(StockLocation.unit_id == unit_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/transactions", response_model=StockTransactionRead, status_code=201)
async def create_stock_transaction(
    payload: StockTransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Idempotency
    existing = await db.execute(
        select(StockTransaction).where(StockTransaction.client_event_id == payload.client_event_id)
    )
    if tx := existing.scalar_one_or_none():
        return tx

    tx = StockTransaction(**payload.model_dump(), performed_by=current_user.id)
    db.add(tx)
    await db.flush()

    # Update stock items
    if payload.from_location_id:
        item_res = await db.execute(
            select(StockItem).where(
                StockItem.drug_id == payload.drug_id,
                StockItem.location_id == payload.from_location_id,
            )
        )
        item = item_res.scalar_one_or_none()
        if item:
            item.on_hand_qty -= payload.quantity
        await _check_and_create_alerts(db, payload.drug_id, payload.from_location_id)

    if payload.to_location_id:
        item_res = await db.execute(
            select(StockItem).where(
                StockItem.drug_id == payload.drug_id,
                StockItem.location_id == payload.to_location_id,
            )
        )
        item = item_res.scalar_one_or_none()
        if item:
            item.on_hand_qty += payload.quantity
        else:
            new_item = StockItem(
                drug_id=payload.drug_id,
                location_id=payload.to_location_id,
                on_hand_qty=payload.quantity,
                unit=payload.unit,
                low_stock_threshold=0.0,
            )
            db.add(new_item)

    await log_audit_event(db, "STOCK_TRANSACTION", "stock_transaction", user_id=current_user.id, resource_id=tx.id)
    return tx


@router.get("/alerts", response_model=list[StockAlertRead])
async def list_alerts(
    unit_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(StockAlert).where(StockAlert.is_resolved == False)
    if unit_id:
        q = q.join(StockLocation, StockAlert.location_id == StockLocation.id).where(StockLocation.unit_id == unit_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/alerts/{alert_id}/resolve", response_model=StockAlertRead)
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = await db.get(StockAlert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.is_resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    alert.resolved_by = current_user.id
    return alert


@router.post("/shift-checks", response_model=ShiftStockCheckRead, status_code=201)
async def create_shift_check(
    payload: ShiftStockCheckCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    check = ShiftStockCheck(**payload.model_dump(), performed_by=current_user.id)
    db.add(check)
    await db.flush()
    return check


@router.post("/shift-checks/{check_id}/items", response_model=ShiftStockCheckRead)
async def submit_shift_check_items(
    check_id: str,
    items: list[ShiftCheckItemCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    check = await db.get(ShiftStockCheck, check_id)
    if not check:
        raise HTTPException(404, "Shift check not found")
    for item_payload in items:
        variance = item_payload.counted_qty - item_payload.expected_qty
        check_item = ShiftStockCheckItem(
            check_id=check_id,
            stock_item_id=item_payload.stock_item_id,
            counted_qty=item_payload.counted_qty,
            expected_qty=item_payload.expected_qty,
            variance=variance,
            variance_reason=item_payload.variance_reason,
        )
        db.add(check_item)
        if variance != 0:
            stock_item = await db.get(StockItem, item_payload.stock_item_id)
            if stock_item:
                alert = StockAlert(
                    drug_id=stock_item.drug_id,
                    location_id=stock_item.location_id,
                    alert_type="VARIANCE",
                    message=f"Variance of {variance} found during shift check",
                )
                db.add(alert)
    check.is_complete = True
    return check
