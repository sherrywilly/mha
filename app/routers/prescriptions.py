from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, log_audit_event
from app.database import get_db
from app.models.org import User
from app.models.prescription import GPContact, PrescriptionRequest, PrescriptionStatus
from app.schemas.prescription import (
    GPContactCreate, GPContactRead,
    PrescriptionRequestCreate, PrescriptionRequestRead,
    ReplySummaryUpdate,
)
from app.services.ai_stub import draft_gp_message

router = APIRouter(tags=["prescriptions"])


@router.get("/gp-contacts", response_model=list[GPContactRead])
async def list_gp_contacts(
    site_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(GPContact).where(GPContact.is_active == True)
    if site_id:
        q = q.where(GPContact.site_id == site_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/gp-contacts", response_model=GPContactRead, status_code=201)
async def create_gp_contact(
    payload: GPContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact = GPContact(**payload.model_dump())
    db.add(contact)
    await db.flush()
    return contact


@router.post("/rx/requests", response_model=PrescriptionRequestRead, status_code=201)
async def create_rx_request(
    payload: PrescriptionRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(PrescriptionRequest).where(PrescriptionRequest.client_event_id == payload.client_event_id)
    )
    if req := existing.scalar_one_or_none():
        return req

    req = PrescriptionRequest(**payload.model_dump(), created_by=current_user.id)
    db.add(req)
    await db.flush()
    await log_audit_event(db, "CREATE_RX_REQUEST", "prescription_request", user_id=current_user.id, resource_id=req.id)
    return req


@router.post("/rx/requests/{req_id}/ai-draft", response_model=PrescriptionRequestRead)
async def generate_ai_draft(
    req_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    req = await db.get(PrescriptionRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    req.ai_draft = draft_gp_message(req.context_snapshot)
    return req


@router.post("/rx/requests/{req_id}/approve", response_model=PrescriptionRequestRead)
async def approve_rx_request(
    req_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    req = await db.get(PrescriptionRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    req.status = PrescriptionStatus.READY_TO_SEND
    req.approved_by = current_user.id
    await log_audit_event(db, "APPROVE_RX_REQUEST", "prescription_request", user_id=current_user.id, resource_id=req_id)
    return req


@router.post("/rx/requests/{req_id}/send", response_model=PrescriptionRequestRead)
async def send_rx_request(
    req_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    req = await db.get(PrescriptionRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    if req.status != PrescriptionStatus.READY_TO_SEND:
        raise HTTPException(400, "Request is not ready to send")
    # Stub: email sending would happen here
    req.status = PrescriptionStatus.SENT
    req.sent_at = datetime.now(timezone.utc)
    req.send_channel = "email"
    await log_audit_event(db, "SEND_RX_REQUEST", "prescription_request", user_id=current_user.id, resource_id=req_id)
    return req


@router.get("/rx/requests", response_model=list[PrescriptionRequestRead])
async def list_rx_requests(
    resident_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(PrescriptionRequest)
    if resident_id:
        q = q.where(PrescriptionRequest.resident_id == resident_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/rx/requests/{req_id}", response_model=PrescriptionRequestRead)
async def get_rx_request(
    req_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    req = await db.get(PrescriptionRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    return req


@router.post("/rx/requests/{req_id}/reply-summary", response_model=PrescriptionRequestRead)
async def set_reply_summary(
    req_id: str,
    payload: ReplySummaryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    req = await db.get(PrescriptionRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    req.reply_summary = payload.reply_summary
    req.reply_at = datetime.now(timezone.utc)
    req.status = PrescriptionStatus.REPLIED
    return req
