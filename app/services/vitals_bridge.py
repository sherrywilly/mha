"""
Vitals Bridge service.

During a medication round the nurse can record a vital sign (BP or blood sugar).
If the reading is outside the safe range defined below the system:
  1. Blocks the medication administration.
  2. Records the event as MedEventType.held.
  3. Flags gp_alerted=True (the GP email notification is sent by the caller).
"""

# Safe ranges — these are conservative clinical defaults.
# A real deployment should allow GP/admin to configure per-resident thresholds.
SAFE_RANGES = {
    "bp_systolic": (90.0, 180.0),     # mmHg
    "bp_diastolic": (60.0, 110.0),    # mmHg
    "blood_sugar": (3.5, 14.0),       # mmol/L (fasting / post-meal combined)
}

VITAL_LABELS = {
    "bp_systolic": "BP Systolic",
    "bp_diastolic": "BP Diastolic",
    "blood_sugar": "Blood Sugar",
}


def check_vitals(
    bp_systolic: float | None,
    bp_diastolic: float | None,
    blood_sugar: float | None,
) -> tuple[bool, list[str]]:
    """
    Returns (is_blocked, list_of_reasons).

    If any vital is outside its safe range, is_blocked is True and
    list_of_reasons contains human-readable descriptions of each breach.
    """
    blocked = False
    reasons: list[str] = []

    checks = [
        ("bp_systolic", bp_systolic),
        ("bp_diastolic", bp_diastolic),
        ("blood_sugar", blood_sugar),
    ]

    for key, value in checks:
        if value is None:
            continue
        low, high = SAFE_RANGES[key]
        if not (low <= value <= high):
            blocked = True
            label = VITAL_LABELS[key]
            reasons.append(
                f"{label} reading of {value} is outside safe range [{low}–{high}]."
            )

    return blocked, reasons
