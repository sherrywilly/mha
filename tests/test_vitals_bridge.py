"""Tests for the Vitals Bridge service."""
import pytest

from app.services.vitals_bridge import check_vitals


class TestCheckVitals:
    def test_all_none_passes(self):
        blocked, reasons = check_vitals(None, None, None)
        assert not blocked
        assert reasons == []

    def test_normal_bp_passes(self):
        blocked, reasons = check_vitals(120.0, 80.0, None)
        assert not blocked
        assert reasons == []

    def test_normal_blood_sugar_passes(self):
        blocked, reasons = check_vitals(None, None, 6.0)
        assert not blocked
        assert reasons == []

    def test_high_systolic_blocks(self):
        blocked, reasons = check_vitals(190.0, 80.0, None)
        assert blocked
        assert len(reasons) == 1
        assert "BP Systolic" in reasons[0]

    def test_low_systolic_blocks(self):
        blocked, reasons = check_vitals(85.0, 80.0, None)
        assert blocked

    def test_high_diastolic_blocks(self):
        blocked, reasons = check_vitals(120.0, 115.0, None)
        assert blocked

    def test_low_blood_sugar_blocks(self):
        blocked, reasons = check_vitals(None, None, 3.0)
        assert blocked
        assert "Blood Sugar" in reasons[0]

    def test_high_blood_sugar_blocks(self):
        blocked, reasons = check_vitals(None, None, 15.0)
        assert blocked

    def test_multiple_out_of_range_returns_all_reasons(self):
        blocked, reasons = check_vitals(200.0, 120.0, 2.0)
        assert blocked
        assert len(reasons) == 3

    def test_boundary_values_pass(self):
        # Exactly at boundaries should be safe
        blocked, _ = check_vitals(90.0, 60.0, 3.5)
        assert not blocked
        blocked, _ = check_vitals(180.0, 110.0, 14.0)
        assert not blocked
