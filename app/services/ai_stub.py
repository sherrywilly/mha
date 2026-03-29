from __future__ import annotations


def draft_gp_message(context: dict) -> str:
    """Return an SBAR-format GP message stub with context data filled in."""
    resident_name = context.get("resident_name", "the resident")
    drug_name = context.get("drug_name", "the medication")
    qty = context.get("requested_qty", "")
    qty_unit = context.get("requested_qty_unit", "")
    qty_str = f"{qty} {qty_unit}".strip() if qty else "as required"

    return (
        f"Dear GP,\n\n"
        f"SITUATION: We are writing to request a prescription for {resident_name}.\n\n"
        f"BACKGROUND: {resident_name} is currently prescribed {drug_name} and requires a further supply.\n\n"
        f"ASSESSMENT: The current stock is running low. We require {qty_str} of {drug_name}.\n\n"
        f"RECOMMENDATION: Please issue a prescription at your earliest convenience.\n\n"
        f"Please do not hesitate to contact us if you require any further information.\n\n"
        f"Kind regards,\nNursing Team\n\n"
        f"[AI-generated draft - please review before sending]"
    )


def summarize_audit_gap(records: list) -> str:
    """Return a stub summary of audit gaps."""
    if not records:
        return "No audit records found for the specified period."
    count = len(records)
    return (
        f"Audit summary: {count} record(s) reviewed. "
        f"No significant gaps detected (stub - real analysis not implemented)."
    )


def detect_duplicate_order(new_order: dict, existing_orders: list[dict]) -> dict:
    """Stub: detect potential duplicate medication orders."""
    duplicates = [
        o for o in existing_orders
        if o.get("drug_id") == new_order.get("drug_id")
        and o.get("resident_id") == new_order.get("resident_id")
        and o.get("status") == "ACTIVE"
    ]
    return {
        "is_duplicate": len(duplicates) > 0,
        "potential_duplicates": duplicates,
        "message": (
            f"Found {len(duplicates)} potentially duplicate active order(s) for this drug and resident."
            if duplicates else "No duplicates detected."
        ),
    }
