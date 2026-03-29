from __future__ import annotations

import csv
import io
import zipfile
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def generate_mar_pdf(
    resident_id: str,
    date_from: date,
    date_to: date,
    db: AsyncSession,
) -> bytes:
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    from app.models.medication import AdministrationRecord, MedicationOrder
    from app.models.resident import Resident

    resident = await db.get(Resident, resident_id)
    name = f"{resident.first_name} {resident.last_name}" if resident else resident_id

    result = await db.execute(
        select(AdministrationRecord).where(
            AdministrationRecord.resident_id == resident_id,
            AdministrationRecord.administered_at >= datetime.combine(date_from, datetime.min.time()),
            AdministrationRecord.administered_at <= datetime.combine(date_to, datetime.max.time()),
        )
    )
    records = result.scalars().all()

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph(f"MAR Report: {name}", styles["Title"]))
    elements.append(Paragraph(f"Period: {date_from} to {date_to}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [["Date/Time", "Order ID", "Dose Given", "Route", "Administered By", "Notes"]]
    for r in records:
        data.append([
            r.administered_at.strftime("%Y-%m-%d %H:%M"),
            r.order_id[:8],
            f"{r.dose_given} {r.dose_unit}",
            r.route_used,
            r.administered_by[:8],
            (r.notes or "")[:50],
        ])

    if len(data) > 1:
        table = Table(data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)

    doc.build(elements)
    return buf.getvalue()


async def generate_mar_csv(
    resident_id: str,
    date_from: date,
    date_to: date,
    db: AsyncSession,
) -> str:
    from app.models.medication import AdministrationRecord
    result = await db.execute(
        select(AdministrationRecord).where(
            AdministrationRecord.resident_id == resident_id,
            AdministrationRecord.administered_at >= datetime.combine(date_from, datetime.min.time()),
            AdministrationRecord.administered_at <= datetime.combine(date_to, datetime.max.time()),
        )
    )
    records = result.scalars().all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["administered_at", "order_id", "dose_given", "dose_unit", "route_used",
                     "administered_by", "witnessed_by", "notes", "reason_not_given"])
    for r in records:
        writer.writerow([
            r.administered_at.isoformat(), r.order_id, r.dose_given, r.dose_unit,
            r.route_used, r.administered_by, r.witnessed_by or "",
            r.notes or "", r.reason_not_given or "",
        ])
    return buf.getvalue()


async def generate_audit_pack_zip(
    site_id: str,
    date_from: date,
    date_to: date,
    db: AsyncSession,
) -> bytes:
    from app.models.org import AuditLog
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.timestamp >= datetime.combine(date_from, datetime.min.time()),
            AuditLog.timestamp <= datetime.combine(date_to, datetime.max.time()),
        )
    )
    logs = result.scalars().all()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        csv_buf = io.StringIO()
        writer = csv.writer(csv_buf)
        writer.writerow(["id", "user_id", "action", "resource_type", "resource_id", "timestamp", "ip_address"])
        for log in logs:
            writer.writerow([log.id, log.user_id or "", log.action, log.resource_type,
                             log.resource_id or "", log.timestamp.isoformat(), log.ip_address or ""])
        zf.writestr(f"audit_log_{date_from}_{date_to}.csv", csv_buf.getvalue())
        zf.writestr("README.txt", f"Audit pack for site {site_id} from {date_from} to {date_to}")
    return buf.getvalue()


async def generate_cd_register_pdf(
    site_id: str,
    date_from: date,
    date_to: date,
    db: AsyncSession,
) -> bytes:
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    from app.models.controlled import CDTransaction
    result = await db.execute(
        select(CDTransaction).where(
            CDTransaction.site_id == site_id,
            CDTransaction.performed_at >= datetime.combine(date_from, datetime.min.time()),
            CDTransaction.performed_at <= datetime.combine(date_to, datetime.max.time()),
        )
    )
    txs = result.scalars().all()

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"CD Register: {site_id}", styles["Title"]),
        Paragraph(f"Period: {date_from} to {date_to}", styles["Normal"]),
        Spacer(1, 12),
    ]

    data = [["Date/Time", "Drug ID", "Type", "Qty", "Unit", "Balance After", "Performed By", "Witness Status"]]
    for tx in txs:
        data.append([
            tx.performed_at.strftime("%Y-%m-%d %H:%M"),
            tx.drug_id[:8],
            tx.tx_type,
            tx.quantity,
            tx.unit,
            tx.stock_balance_after if tx.stock_balance_after is not None else "-",
            tx.performed_by[:8],
            tx.witness_status,
        ])

    if len(data) > 1:
        table = Table(data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)

    doc.build(elements)
    return buf.getvalue()
