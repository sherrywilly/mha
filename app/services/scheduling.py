from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medication import DoseDue, FrequencyType, MedicationOrder


def _dose_key(order_id: str, scheduled_dt: datetime) -> str:
    raw = f"{order_id}:{scheduled_dt.isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def generate_dose_due(
    order: MedicationOrder,
    date_from: date,
    date_to: date,
    db: AsyncSession,
) -> list[DoseDue]:
    if order.frequency_type == FrequencyType.PRN:
        return []

    # Collect existing dose_keys to avoid duplicates
    existing_result = await db.execute(
        select(DoseDue.dose_key).where(DoseDue.order_id == order.id)
    )
    existing_keys = {row[0] for row in existing_result.all()}

    created: list[DoseDue] = []
    current = date_from

    while current <= date_to:
        scheduled_dts: list[datetime] = []

        if order.frequency_type == FrequencyType.DAILY_TIMES:
            times = order.frequency_times or ["08:00"]
            for t in times:
                h, m = map(int, t.split(":"))
                scheduled_dts.append(datetime(current.year, current.month, current.day, h, m))

        elif order.frequency_type == FrequencyType.INTERVAL:
            if order.frequency_interval_hours:
                # Build a single pass over the whole date range on first day only
                start_dt = datetime.combine(date_from, datetime.min.time()).replace(hour=8)
                end_dt = datetime.combine(date_to, datetime.max.time())
                current_dt = start_dt
                while current_dt <= end_dt:
                    if current_dt.date() == current:
                        scheduled_dts.append(current_dt)
                    current_dt += timedelta(hours=order.frequency_interval_hours)

        elif order.frequency_type == FrequencyType.WEEKLY:
            days = order.frequency_days or [0]
            if current.weekday() in days:
                times = order.frequency_times or ["08:00"]
                for t in times:
                    h, m = map(int, t.split(":"))
                    scheduled_dts.append(datetime(current.year, current.month, current.day, h, m))

        elif order.frequency_type == FrequencyType.ONCE:
            if current == order.start_date:
                times = order.frequency_times or ["08:00"]
                for t in times:
                    h, m = map(int, t.split(":"))
                    scheduled_dts.append(datetime(current.year, current.month, current.day, h, m))

        elif order.frequency_type == FrequencyType.TAPER:
            times = order.frequency_times or ["08:00"]
            for t in times:
                h, m = map(int, t.split(":"))
                scheduled_dts.append(datetime(current.year, current.month, current.day, h, m))

        for sdt in scheduled_dts:
            key = _dose_key(order.id, sdt)
            if key not in existing_keys:
                dose = DoseDue(
                    order_id=order.id,
                    resident_id=order.resident_id,
                    scheduled_datetime=sdt,
                    window_start=sdt - timedelta(minutes=30),
                    window_end=sdt + timedelta(hours=1),
                    dose_key=key,
                )
                db.add(dose)
                created.append(dose)
                existing_keys.add(key)

        if order.frequency_type == FrequencyType.INTERVAL:
            current += timedelta(days=1)
            continue

        current += timedelta(days=1)

    await db.flush()
    return created
