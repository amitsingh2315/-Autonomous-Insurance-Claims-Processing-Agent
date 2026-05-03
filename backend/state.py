"""
State definition for the Insurance Claims Processing Agent.

This module defines the shared state schema used by all LangGraph nodes.
Each node reads from and writes to this state as data flows through the pipeline.
"""

from typing import TypedDict, Optional


class ClaimState(TypedDict, total=False):
    """
    Shared state passed between LangGraph nodes.

    Attributes:
        pdf_path: Path to the input FNOL PDF document.
        raw_text: Extracted raw text from the PDF.
        extracted_fields: Structured dict of extracted claim fields.
        missing_fields: List of mandatory fields that are missing or empty.
        recommended_route: The routing decision (e.g., "Fast-track", "Manual Review").
        confidence_score: Composite confidence score (0.0 - 1.0).
        reasoning: Human-readable LLM explanation of the routing decision.
        error: Error message if any step fails.

        # ── New fields (enhancements) ────────────────────────────────────────
        assigned_to: Name of the employee assigned to handle this claim.
        decision_breakdown: Structured bullet-point XAI explanation of decision.
        fraud_score: Simple keyword-based fraud risk score (0.0 - 1.0).
        extraction_confidence: % of key fields successfully extracted (0.0-1.0).
        data_completeness: Filled mandatory fields / total mandatory fields.
        rule_confidence: Confidence of the routing rule that fired (0.0-1.0).
    """
    pdf_path: str
    raw_text: str
    extracted_fields: dict
    missing_fields: list
    recommended_route: str
    confidence_score: float
    reasoning: str
    error: Optional[str]
    # Enhancement fields
    assigned_to: str
    decision_breakdown: str
    fraud_score: float
    extraction_confidence: float
    data_completeness: float
    rule_confidence: float
