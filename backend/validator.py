"""
Validator module for the Insurance Claims Processing Agent.

Pure rule-based validation — NO LLM dependency.
Checks for missing or empty mandatory fields required for claim processing.
"""

import logging
from typing import Any

from .state import ClaimState

logger = logging.getLogger(__name__)

# =============================================================================
# Mandatory fields that must be present for a claim to be processed
# Format: (section_key, field_key)
# The field_key is the canonical snake_case name used in missingFields output.
# =============================================================================
MANDATORY_FIELDS = [
    ("policy_info",      "policy_number"),
    ("policy_info",      "policyholder_name"),
    ("incident_info",    "incident_date"),
    ("incident_info",    "incident_location"),
    ("incident_info",    "incident_description"),
    ("involved_parties", "claimant_name"),
    ("other",            "claim_type"),
]


# =============================================================================
# NODE 3: Field Validation (Deterministic / Automation)
# =============================================================================

def validate_fields(state: ClaimState) -> dict[str, Any]:
    """
    Validate extracted fields by checking for missing mandatory data.
    
    This is a deterministic automation step — no LLM involved.
    Rules are explicit and transparent.
    
    Args:
        state: Current claim state containing extracted_fields.
        
    Returns:
        Dict with missing_fields list to merge into state.
    """
    extracted = state.get("extracted_fields", {})
    logger.info("Validating extracted fields...")

    missing: list[str] = []

    for section_key, field_key in MANDATORY_FIELDS:
        section = extracted.get(section_key, {}) or {}
        value = section.get(field_key)

        # A field is considered missing if it is None, empty string, or empty list
        if value is None or value == "" or value == []:
            missing.append(field_key)          # snake_case key, NOT display name
            logger.debug(f"   MISSING: {section_key}.{field_key}")
        else:
            logger.debug(f"   OK: {section_key}.{field_key} = {str(value)[:60]}")

    if missing:
        logger.warning(f"{len(missing)} mandatory field(s) missing: {', '.join(missing)}")
    else:
        logger.info("All mandatory fields present")

    return {"missing_fields": missing}
