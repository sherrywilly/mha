"""
NHS dm+d (Dictionary of Medicines and Devices) synchronisation service.

In production this calls the NHSBSA TRUD / FHIR API to pull the latest
VMP (Virtual Medicinal Product) data and upserts it into the local `drugs`
table.

This module provides:
  - fetch_dmd_drug(dmd_id)  → look up one drug from the API
  - sync_dmd_batch()        → bulk sync (run nightly via a scheduled job)
"""
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

DMD_FHIR_BASE = "https://dmd.nhs.uk/fhir"  # Public NHS dm+d FHIR endpoint


def _build_vmp_url(dmd_id: str) -> str:
    return f"{DMD_FHIR_BASE}/Medication/{dmd_id}"


def fetch_dmd_drug(dmd_id: str) -> Optional[dict]:
    """
    Fetch one drug by its dm+d VMP ID from the NHS FHIR API.

    Returns a normalised dict with keys:
        dmd_id, name, form, strength, unit_of_measure, is_controlled
    or None if the drug is not found / API is unavailable.
    """
    url = _build_vmp_url(dmd_id)
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(url, headers={"Accept": "application/fhir+json"})
        if response.status_code == 404:
            logger.warning("dm+d drug not found: %s", dmd_id)
            return None
        response.raise_for_status()
        data = response.json()
        return _parse_fhir_medication(data)
    except httpx.HTTPError as exc:
        logger.error("dm+d API error for %s: %s", dmd_id, exc)
        return None


def _parse_fhir_medication(fhir: dict) -> dict:
    """Extract the fields we care about from a FHIR Medication resource."""
    code = fhir.get("code", {})
    codings = code.get("coding", [])
    name = code.get("text") or (codings[0].get("display") if codings else "Unknown")

    form_concept = fhir.get("form", {}).get("coding", [{}])
    form = form_concept[0].get("display") if form_concept else None

    ingredients = fhir.get("ingredient", [])
    strength = None
    unit_of_measure = None
    if ingredients:
        ratio = ingredients[0].get("strength", {})
        numerator = ratio.get("numerator", {})
        strength = f"{numerator.get('value', '')} {numerator.get('unit', '')}".strip()
        unit_of_measure = numerator.get("unit")

    dmd_id = fhir.get("id", "")
    extension = fhir.get("extension", [])
    is_controlled = any(
        ext.get("url", "").endswith("controlledDrug") for ext in extension
    )

    return {
        "dmd_id": dmd_id,
        "name": name,
        "form": form,
        "strength": strength or None,
        "unit_of_measure": unit_of_measure,
        "is_controlled": is_controlled,
    }


def sync_dmd_batch(dmd_ids: list[str]) -> list[dict]:
    """
    Fetch a batch of drugs by their dm+d IDs.

    Returns a list of normalised drug dicts (skips any that returned None).
    Intended to be called from a nightly Celery / APScheduler task.
    """
    results = []
    for dmd_id in dmd_ids:
        drug = fetch_dmd_drug(dmd_id)
        if drug:
            results.append(drug)
    logger.info("dm+d sync complete: %d/%d drugs fetched", len(results), len(dmd_ids))
    return results
