"""
Router module for the Insurance Claims Processing Agent.

Pure rule-based claim routing — NO LLM dependency.
Routes claims to appropriate processing queues based on deterministic business rules.

Routing Priority (highest to lowest):
1. Investigation — fraud indicators detected
2. Manual Review — mandatory fields missing
3. Specialist Queue — injury claims
4. Fast-track — low-value claims (< $25,000)
5. Standard Processing — default route

Enhancements (additive only, routing logic unchanged):
- fraud_score: Keyword-based risk score (0.0 – 1.0)
- decision_breakdown: Structured XAI bullet list explaining the decision
- confidence_score: Upgraded 3-component formula
"""

import logging
from typing import Any

from .state import ClaimState

logger = logging.getLogger(__name__)

# =============================================================================
# Routing Constants (unchanged)
# =============================================================================
ROUTE_FAST_TRACK    = "Fast-track"
ROUTE_MANUAL_REVIEW = "Manual Review"
ROUTE_INVESTIGATION = "Investigation"
ROUTE_SPECIALIST    = "Specialist Queue"
ROUTE_STANDARD      = "Standard Processing"

# Fraud indicator keywords (case-insensitive matching)
FRAUD_KEYWORDS = ["fraud", "staged", "inconsistent"]

# Damage threshold for fast-track processing
FAST_TRACK_THRESHOLD = 25_000

# Claim types that require specialist handling
SPECIALIST_CLAIM_TYPES = ["injury", "bodily_injury", "personal_injury"]

# All key fields used for data-completeness calculation
_ALL_KEY_FIELDS = [
    ("policy_info",      "policy_number"),
    ("policy_info",      "policyholder_name"),
    ("policy_info",      "effective_date_start"),
    ("policy_info",      "effective_date_end"),
    ("incident_info",    "incident_date"),
    ("incident_info",    "incident_time"),
    ("incident_info",    "incident_location"),
    ("incident_info",    "incident_description"),
    ("involved_parties", "claimant_name"),
    ("involved_parties", "claimant_contact"),
    ("asset_details",    "asset_type"),
    ("asset_details",    "asset_id"),
    ("asset_details",    "estimated_damage"),
    ("other",            "claim_type"),
]


# =============================================================================
# NODE 4: Claim Routing (Deterministic / Rule-based)
# =============================================================================

def route_claim(state: ClaimState) -> dict[str, Any]:
    """
    Route claim to the appropriate processing queue based on business rules.

    This is a deterministic rule-based step — no LLM involved.
    Priority order: Investigation > Manual Review > Specialist > Fast-track > Standard

    Enhancements (additive):
    - Computes fraud_score (keyword ratio)
    - Computes structured decision_breakdown (XAI)
    - Uses upgraded composite confidence formula

    Args:
        state: Current claim state with extracted_fields and missing_fields.

    Returns:
        Dict with recommended_route, confidence_score, fraud_score,
        decision_breakdown merged into state.
    """
    extracted = state.get("extracted_fields", {})
    missing   = state.get("missing_fields", [])

    logger.info("🔀 Routing claim based on business rules...")

    # ── Compute fraud score ──────────────────────────────────────────────────
    description = (extracted.get("incident_info", {}).get("incident_description") or "").lower()
    fraud_score = _compute_fraud_score(description)

    # ── Pre-compute data completeness ────────────────────────────────────────
    data_completeness = _compute_data_completeness(extracted)

    # ── Extraction confidence carried from extractor node ────────────────────
    extraction_confidence = state.get("confidence_score", 0.8)

    breakdown_lines: list[str] = []

    # --- Rule 1: Check for fraud indicators (HIGHEST PRIORITY) ---
    triggered_keyword = next((kw for kw in FRAUD_KEYWORDS if kw in description), None)

    if triggered_keyword:
        logger.warning(f"🚨 Fraud indicator detected: '{triggered_keyword}' found in description")
        breakdown_lines.append("Decision Breakdown:")
        breakdown_lines.append(f"✘ Possible signs of fraud found → Needs investigation")
        breakdown_lines.append(f"⚠ Fraud risk: {fraud_score:.0%}")
        breakdown_lines.append("✔ This claim is sent to the fraud team")
        rule_confidence = 1.0
        breakdown_lines.append("\nFinal Decision: Sent to Fraud Team")

        return {
            "recommended_route":  ROUTE_INVESTIGATION,
            "confidence_score":   _composite_confidence(extraction_confidence, rule_confidence, data_completeness),
            "fraud_score":        fraud_score,
            "decision_breakdown": "\n".join(breakdown_lines),
            "rule_confidence":    rule_confidence,
            "data_completeness":  data_completeness,
        }

    # --- Rule 2: Check for missing mandatory fields ---
    if missing:
        logger.info(f"📋 {len(missing)} mandatory field(s) missing → Manual Review")
        breakdown_lines.append("Decision Breakdown:")
        breakdown_lines.append(f"✘ Missing details: {', '.join(missing)}")
        breakdown_lines.append("✔ No signs of fraud found")
        breakdown_lines.append("✔ This claim needs a person to review it")
        rule_confidence = 1.0
        breakdown_lines.append("\nFinal Decision: Sent for Human Review")

        return {
            "recommended_route":  ROUTE_MANUAL_REVIEW,
            "confidence_score":   _composite_confidence(extraction_confidence, rule_confidence, data_completeness),
            "fraud_score":        fraud_score,
            "decision_breakdown": "\n".join(breakdown_lines),
            "rule_confidence":    rule_confidence,
            "data_completeness":  data_completeness,
        }

    # --- Rule 3: Check if claim type requires specialist ---
    claim_type = (extracted.get("other", {}).get("claim_type") or "").lower().strip()
    if claim_type in SPECIALIST_CLAIM_TYPES:
        logger.info(f"🏥 Injury claim detected (type: {claim_type}) → Specialist Queue")
        breakdown_lines.append("Decision Breakdown:")
        breakdown_lines.append("✔ No signs of fraud found")
        breakdown_lines.append("✔ All required details are filled")
        breakdown_lines.append(f"✘ This claim involves {claim_type}, so a specialist will handle it")
        breakdown_lines.append("✔ This claim is sent to a specialist team")
        rule_confidence = 0.8
        breakdown_lines.append("\nFinal Decision: Sent to Specialist Team")

        return {
            "recommended_route":  ROUTE_SPECIALIST,
            "confidence_score":   _composite_confidence(extraction_confidence, rule_confidence, data_completeness),
            "fraud_score":        fraud_score,
            "decision_breakdown": "\n".join(breakdown_lines),
            "rule_confidence":    rule_confidence,
            "data_completeness":  data_completeness,
        }

    # --- Rule 4: Check damage amount for fast-track ---
    estimated_damage = extracted.get("asset_details", {}).get("estimated_damage")
    if estimated_damage is not None:
        try:
            damage_value = float(estimated_damage)
            if damage_value < FAST_TRACK_THRESHOLD:
                logger.info(f"⚡ Low damage (${damage_value:,.2f} < ${FAST_TRACK_THRESHOLD:,}) → Fast-track")
                breakdown_lines.append("Decision Breakdown:")
                breakdown_lines.append("✔ Damage is under $25,000 → Fast processing allowed")
                breakdown_lines.append("✔ All required details are filled")
                breakdown_lines.append("✔ No signs of fraud found")
                rule_confidence = 0.8
                breakdown_lines.append("\nFinal Decision: Fast Processing Approved")

                return {
                    "recommended_route":  ROUTE_FAST_TRACK,
                    "confidence_score":   _composite_confidence(extraction_confidence, rule_confidence, data_completeness),
                    "fraud_score":        fraud_score,
                    "decision_breakdown": "\n".join(breakdown_lines),
                    "rule_confidence":    rule_confidence,
                    "data_completeness":  data_completeness,
                }
        except (ValueError, TypeError):
            logger.warning(f"⚠️  Could not parse estimated_damage: {estimated_damage}")

    # --- Rule 5: Default route ---
    logger.info("📦 No special routing rules triggered → Standard Processing")
    breakdown_lines.append("Decision Breakdown:")
    breakdown_lines.append("✔ No signs of fraud found")
    breakdown_lines.append("✔ All required details are filled")
    breakdown_lines.append("✔ Damage amount is over $25,000")
    breakdown_lines.append("✔ This claim will go through normal processing")
    rule_confidence = 0.8
    breakdown_lines.append("\nFinal Decision: Normal Processing")

    return {
        "recommended_route":  ROUTE_STANDARD,
        "confidence_score":   _composite_confidence(extraction_confidence, rule_confidence, data_completeness),
        "fraud_score":        fraud_score,
        "decision_breakdown": "\n".join(breakdown_lines),
        "rule_confidence":    rule_confidence,
        "data_completeness":  data_completeness,
    }


# =============================================================================
# Helper: Fraud Score
# =============================================================================

def _compute_fraud_score(description: str) -> float:
    """
    Compute a simple keyword-based fraud risk score.

    fraud_score = matched_keywords / total_keywords

    Args:
        description: Lowercased incident description.

    Returns:
        Float 0.0 (no risk) – 1.0 (all keywords present).
    """
    matched = sum(1 for kw in FRAUD_KEYWORDS if kw in description)
    return round(matched / len(FRAUD_KEYWORDS), 2)


# =============================================================================
# Helper: Data Completeness
# =============================================================================

def _compute_data_completeness(extracted: dict) -> float:
    """
    Fraction of all known fields that are filled.

    Args:
        extracted: Extracted fields dict.

    Returns:
        Completeness ratio (0.0 – 1.0).
    """
    filled = sum(
        1 for section, field in _ALL_KEY_FIELDS
        if (v := extracted.get(section, {}).get(field)) is not None
        and v != "" and v != []
    )
    return round(filled / len(_ALL_KEY_FIELDS), 2)


# =============================================================================
# Helper: Composite Confidence Formula
# =============================================================================

def _composite_confidence(
    extraction_confidence: float,
    rule_confidence: float,
    data_completeness: float,
) -> float:
    """
    Upgraded composite confidence:

        confidence = extraction_confidence * 0.5
                   + rule_confidence       * 0.3
                   + data_completeness    * 0.2

    Args:
        extraction_confidence: % key fields extracted (from extractor node).
        rule_confidence: Rule clarity score (1.0 definitive, 0.8 soft).
        data_completeness: Filled fields / total fields.

    Returns:
        Composite confidence (0.0 – 1.0).
    """
    score = (
        extraction_confidence * 0.5
        + rule_confidence       * 0.3
        + data_completeness     * 0.2
    )
    return round(min(score, 1.0), 2)
