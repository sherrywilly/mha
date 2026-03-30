"""
Smart Lead Scoring service.

Assigns an urgency score (0–100) to a new lead based on signals that
indicate how quickly the prospect needs a placement.

Scoring factors
---------------
- source == "hospital_discharge"  → +50 points  (needs placement imminently)
- source == "social_worker"       → +30 points
- source == "gp_referral"         → +25 points
- source == "website"             → +10 points  (browsing, low urgency)
- care_needs mentions keywords    → +5 per keyword (up to +20)
- prospective_resident_dob set    → +5 (more concrete enquiry)
- enquirer_email provided         → +5 (contactable)
- enquirer_phone provided         → +5 (contactable)

Maximum score is capped at 100.
"""

HIGH_URGENCY_SOURCES = {
    "hospital_discharge": 50,
    "social_worker": 30,
    "gp_referral": 25,
    "nhs_111": 25,
    "cqc_transfer": 20,
    "website": 10,
    "word_of_mouth": 8,
}

CARE_NEED_KEYWORDS = [
    "dementia",
    "alzheimer",
    "stroke",
    "parkinson",
    "diabetes",
    "wheelchair",
    "oxygen",
    "dialysis",
    "terminal",
    "palliative",
    "falls",
    "incontinence",
    "catheter",
    "peg",
]


def score_lead(
    source: str | None,
    care_needs: str | None,
    prospective_resident_dob: object | None,
    enquirer_email: str | None,
    enquirer_phone: str | None,
) -> int:
    """Return urgency score 0–100."""
    score = 0

    # Source signal
    if source:
        score += HIGH_URGENCY_SOURCES.get(source.lower(), 5)

    # Care needs keywords
    if care_needs:
        text = care_needs.lower()
        keyword_hits = sum(1 for kw in CARE_NEED_KEYWORDS if kw in text)
        score += min(keyword_hits * 5, 20)

    # Concreteness signals
    if prospective_resident_dob:
        score += 5
    if enquirer_email:
        score += 5
    if enquirer_phone:
        score += 5

    return min(score, 100)
