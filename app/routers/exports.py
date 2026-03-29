from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.org import User
from app.services.export_service import (
    generate_audit_pack_zip,
    generate_cd_register_pdf,
    generate_mar_csv,
    generate_mar_pdf,
)

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/mar")
async def export_mar(
    resident_id: str,
    date_from: str,
    date_to: str,
    format: str = "pdf",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    df = date.fromisoformat(date_from)
    dt = date.fromisoformat(date_to)
    if format == "csv":
        content = await generate_mar_csv(resident_id, df, dt, db)
        return Response(content=content.encode(), media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=mar.csv"})
    else:
        content = await generate_mar_pdf(resident_id, df, dt, db)
        return Response(content=content, media_type="application/pdf",
                        headers={"Content-Disposition": "attachment; filename=mar.pdf"})


@router.get("/unit-mar")
async def export_unit_mar(
    unit_id: str,
    date_from: str,
    date_to: str,
    format: str = "pdf",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    from sqlalchemy import select
    from app.models.resident import Resident

    df = date.fromisoformat(date_from)
    dt = date.fromisoformat(date_to)

    result = await db.execute(select(Resident).where(Resident.unit_id == unit_id, Resident.is_active == True))
    residents = result.scalars().all()

    if format == "csv":
        parts = []
        for r in residents:
            parts.append(await generate_mar_csv(r.id, df, dt, db))
        content = "\n".join(parts)
        return Response(content=content.encode(), media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=unit_mar.csv"})
    else:
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = [Paragraph(f"Unit MAR: {unit_id}", styles["Title"])]
        doc.build(elements)
        return Response(content=buf.getvalue(), media_type="application/pdf",
                        headers={"Content-Disposition": "attachment; filename=unit_mar.pdf"})


@router.get("/audit-pack")
async def export_audit_pack(
    site_id: str,
    date_from: str,
    date_to: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    df = date.fromisoformat(date_from)
    dt = date.fromisoformat(date_to)
    content = await generate_audit_pack_zip(site_id, df, dt, db)
    return Response(content=content, media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=audit_pack.zip"})


@router.get("/cd-register")
async def export_cd_register(
    site_id: str,
    date_from: str,
    date_to: str,
    format: str = "pdf",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    df = date.fromisoformat(date_from)
    dt = date.fromisoformat(date_to)
    if format == "csv":
        from app.models.controlled import CDTransaction
        from sqlalchemy import select
        result = await db.execute(
            select(CDTransaction).where(
                CDTransaction.site_id == site_id,
                CDTransaction.performed_at >= df,
                CDTransaction.performed_at <= dt,
            )
        )
        txs = result.scalars().all()
        import csv
        import io
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "drug_id", "tx_type", "quantity", "unit", "performed_at", "witness_status"])
        for tx in txs:
            writer.writerow([tx.id, tx.drug_id, tx.tx_type, tx.quantity, tx.unit, tx.performed_at, tx.witness_status])
        return Response(content=buf.getvalue().encode(), media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=cd_register.csv"})
    else:
        content = await generate_cd_register_pdf(site_id, df, dt, db)
        return Response(content=content, media_type="application/pdf",
                        headers={"Content-Disposition": "attachment; filename=cd_register.pdf"})
