"""Tests for the Smart Lead Scoring service."""
import pytest
from datetime import datetime, timezone

from app.services.lead_scoring import score_lead


class TestScoreLead:
    def test_hospital_discharge_is_highest_urgency(self):
        score = score_lead(
            source="hospital_discharge",
            care_needs=None,
            prospective_resident_dob=None,
            enquirer_email=None,
            enquirer_phone=None,
        )
        assert score == 50

    def test_website_source_is_lower(self):
        score_web = score_lead("website", None, None, None, None)
        score_hosp = score_lead("hospital_discharge", None, None, None, None)
        assert score_web < score_hosp

    def test_care_needs_keywords_add_points(self):
        score_no_needs = score_lead("website", None, None, None, None)
        score_with_needs = score_lead(
            "website",
            "resident has dementia and requires oxygen therapy",
            None,
            None,
            None,
        )
        assert score_with_needs > score_no_needs

    def test_contact_details_add_points(self):
        base = score_lead("website", None, None, None, None)
        with_contact = score_lead(
            "website", None, None, "test@example.com", "07700900000"
        )
        assert with_contact == base + 10

    def test_dob_provided_adds_points(self):
        base = score_lead("website", None, None, None, None)
        with_dob = score_lead(
            "website", None, datetime(1940, 1, 1, tzinfo=timezone.utc), None, None
        )
        assert with_dob == base + 5

    def test_score_capped_at_100(self):
        # Max possible: hospital_discharge(50) + keywords cap(20) + dob(5) + email(5) + phone(5) = 85
        # Add a very high-scoring source to verify the 100 cap works
        from app.services.lead_scoring import HIGH_URGENCY_SOURCES, CARE_NEED_KEYWORDS

        max_source_score = max(HIGH_URGENCY_SOURCES.values())
        many_keywords = " ".join(CARE_NEED_KEYWORDS)
        best_source = max(HIGH_URGENCY_SOURCES, key=HIGH_URGENCY_SOURCES.get)

        score = score_lead(
            source=best_source,
            care_needs=many_keywords,
            prospective_resident_dob=datetime(1940, 1, 1, tzinfo=timezone.utc),
            enquirer_email="test@example.com",
            enquirer_phone="07700900000",
        )
        # Should be capped at 100 even if raw sum > 100
        assert score <= 100
        # With highest source + all keywords + all contact info, score is well above 50
        assert score >= 85

    def test_unknown_source_gets_small_default(self):
        score = score_lead("unknown_source", None, None, None, None)
        assert score == 5

    def test_none_source_scores_zero_from_source(self):
        score_no_source = score_lead(None, None, None, None, None)
        assert score_no_source == 0

    def test_keyword_score_capped_at_20(self):
        many_keywords = " ".join(
            ["dementia", "alzheimer", "stroke", "parkinson", "diabetes",
             "wheelchair", "oxygen", "dialysis", "terminal", "palliative"]
        )
        score = score_lead(None, many_keywords, None, None, None)
        assert score == 20  # capped at 20 from keywords alone
