from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, log_audit_event
from app.database import get_db
from app.models.controlled import CDStockBalance, CDTransaction, WitnessStatus
from app.models.org import UnitAssignment, User
from app.schemas.controlled import (
    CDStockBalanceRead, CDTransactionCreate, CDTransactionRead, WitnessRequest,
)

router = APIRouter(prefix="/cd", tags=["controlled_drugs"])


async def _update_balance(db: AsyncSession, tx: CDTransaction) -> float:
    result = await db.execute(
        select(CDStockBalance).where(
            CDStockBalance.drug_id == tx.drug_id,
            CDStockBalance.site_id == tx.site_id,
        )
    )
    balance = result.scalar_one_or_none()
    if not balance:
        balance = CDStockBalance(drug_id=tx.drug_id, site_id=tx.site_id, current_balance=0.0, unit=tx.unit)
        db.add(balance)

    if tx.tx_type in ("ADMINISTER", "WASTE", "RETURN", "TRANSFER"):
        balance.current_balance -= tx.quantity
    elif tx.tx_type in ("RECEIVED", "STOCK_ADJUST"):
        balance.current_balance += tx.quantity

    balance.last_count_at = datetime.now(timezone.utc)
    balance.last_count_by = tx.performed_by
    return balance.current_balance


async def _check_cd_permission(db: AsyncSession, user: User) -> None:
    result = await db.execute(
        select(UnitAssignment).where(
            UnitAssignment.user_id == user.id,
            UnitAssignment.can_administer_cd == True,
        )
    )
    if not result.scalar_one_or_none() and user.role not in ("ADMIN", "MANAGER"):
        raise HTTPException(403, "Not authorised to handle controlled drugs")


@router.post("/transactions", response_model=CDTransactionRead, status_code=201)
async def create_cd_transaction(
    payload: CDTransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Idempotency
    existing = await db.execute(
        select(CDTransaction).where(CDTransaction.client_event_id == payload.client_event_id)
    )
    if tx := existing.scalar_one_or_none():
        return tx

    await _check_cd_permission(db, current_user)

    tx = CDTransaction(**payload.model_dump(), performed_by=current_user.id)
    db.add(tx)
    await db.flush()
    balance = await _update_balance(db, tx)
    tx.stock_balance_after = balance
    await log_audit_event(db, "CD_TRANSACTION", "cd_transaction", user_id=current_user.id, resource_id=tx.id,
                          detail={"tx_type": tx.tx_type, "quantity": tx.quantity})
    return tx


@router.post("/transactions/{tx_id}/witness", response_model=CDTransactionRead)
async def witness_cd_transaction(
    tx_id: str,
    payload: WitnessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tx = await db.get(CDTransaction, tx_id)
    if not tx:
        raise HTTPException(404, "Transaction not found")
    if tx.witness_status == WitnessStatus.COMPLETE:
        raise HTTPException(400, "Already witnessed")
    if tx.performed_by == payload.witnessed_by:
        raise HTTPException(400, "Witness must be different from performer")

    await _check_cd_permission(db, current_user)

    tx.witnessed_by = payload.witnessed_by
    tx.witnessed_at = payload.witnessed_at
    tx.witness_status = WitnessStatus.COMPLETE
    await log_audit_event(db, "CD_WITNESS", "cd_transaction", user_id=current_user.id, resource_id=tx_id)
    return tx


@router.get("/transactions", response_model=list[CDTransactionRead])
async def list_cd_transactions(
    site_id: str | None = None,
    drug_id: str | None = None,
    from_dt: str | None = None,
    to_dt: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(CDTransaction)
    if site_id:
        q = q.where(CDTransaction.site_id == site_id)
    if drug_id:
        q = q.where(CDTransaction.drug_id == drug_id)
    if from_dt:
        q = q.where(CDTransaction.performed_at >= datetime.fromisoformat(from_dt))
    if to_dt:
        q = q.where(CDTransaction.performed_at <= datetime.fromisoformat(to_dt))
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/balance", response_model=list[CDStockBalanceRead])
async def get_cd_balance(
    site_id: str | None = None,
    drug_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(CDStockBalance)
    if site_id:
        q = q.where(CDStockBalance.site_id == site_id)
    if drug_id:
        q = q.where(CDStockBalance.drug_id == drug_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/pending-witness", response_model=list[CDTransactionRead])
async def list_pending_witness(
    site_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(CDTransaction).where(CDTransaction.witness_status == WitnessStatus.PENDING)
    if site_id:
        q = q.where(CDTransaction.site_id == site_id)
    result = await db.execute(q)
    return result.scalars().all()
