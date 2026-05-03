"""
Unit tests for the Insurance Claims Processing Agent.

Tests the deterministic components (validator, router) independently.
LLM-dependent tests require GROQ_API_KEY to be set.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.validator import validate_fields
from backend.router import route_claim


# =============================================================================
# Test Data Fixtures
# =============================================================================

def _make_state(overrides: dict = None) -> dict:
    """Create a complete claim state for testing."""
    state = {
        "pdf_path": "test.pdf",
        "raw_text": "Sample text",
        "extracted_fields": {
            "policy_info": {
                "policy_number": "AUTO-2024-78432",
                "policyholder_name": "Robert Mitchell",
                "effective_date_start": "2024-01-15",
                "effective_date_end": "2025-01-15",
            },
            "incident_info": {
                "incident_date": "2024-03-15",
                "incident_time": "14:35",
                "incident_location": "Main St and Oak Ave, Springfield, IL",
                "incident_description": "Vehicle collision at intersection",
            },
            "involved_parties": {
                "claimant_name": "Robert Mitchell",
                "claimant_contact": "(555) 987-6543",
                "third_parties": ["Jennifer Thompson"],
                "third_party_contacts": ["(555) 321-0987"],
            },
            "asset_details": {
                "asset_type": "vehicle",
                "asset_id": "4T1G11AK5NU000123",
                "estimated_damage": 18500,
            },
            "other": {
                "claim_type": "collision",
                "attachments": ["Police Report"],
                "initial_estimate": 18500,
            },
        },
        "missing_fields": [],
        "recommended_route": "",
        "confidence_score": 0.0,
        "reasoning": "",
        "error": None,
    }
    if overrides:
        # Deep merge for extracted_fields
        for key, value in overrides.items():
            if key == "extracted_fields" and isinstance(value, dict):
                for section, fields in value.items():
                    if section in state["extracted_fields"] and isinstance(fields, dict):
                        state["extracted_fields"][section].update(fields)
                    else:
                        state["extracted_fields"][section] = fields
            else:
                state[key] = value
    return state


# =============================================================================
# Validator Tests
# =============================================================================

class TestValidator:
    """Tests for the rule-based field validator."""

    def test_all_fields_present(self):
        """All mandatory fields present → no missing fields."""
        state = _make_state()
        result = validate_fields(state)
        assert result["missing_fields"] == []

    def test_missing_policy_number(self):
        """Missing policy number → reported as missing."""
        state = _make_state()
        state["extracted_fields"]["policy_info"]["policy_number"] = None
        result = validate_fields(state)
        assert "Policy Number" in result["missing_fields"]

    def test_missing_multiple_fields(self):
        """Multiple missing fields → all reported."""
        state = _make_state()
        state["extracted_fields"]["policy_info"]["policy_number"] = None
        state["extracted_fields"]["incident_info"]["incident_date"] = None
        state["extracted_fields"]["involved_parties"]["claimant_name"] = ""
        result = validate_fields(state)
        assert len(result["missing_fields"]) == 3
        assert "Policy Number" in result["missing_fields"]
        assert "Incident Date" in result["missing_fields"]
        assert "Claimant Name" in result["missing_fields"]

    def test_empty_string_counts_as_missing(self):
        """Empty strings should be treated as missing."""
        state = _make_state()
        state["extracted_fields"]["other"]["claim_type"] = ""
        result = validate_fields(state)
        assert "Claim Type" in result["missing_fields"]

    def test_empty_extracted_fields(self):
        """Empty extracted_fields → all mandatory fields missing."""
        state = _make_state()
        state["extracted_fields"] = {}
        result = validate_fields(state)
        assert len(result["missing_fields"]) == 7  # All 7 mandatory fields


# =============================================================================
# Router Tests
# =============================================================================

class TestRouter:
    """Tests for the rule-based claim router."""

    def test_fast_track_low_damage(self):
        """Low damage (< $25,000) with all fields → Fast-track."""
        state = _make_state()
        state["missing_fields"] = []
        result = route_claim(state)
        assert result["recommended_route"] == "Fast-track"

    def test_manual_review_missing_fields(self):
        """Missing mandatory fields → Manual Review."""
        state = _make_state()
        state["missing_fields"] = ["Policy Number", "Incident Date"]
        result = route_claim(state)
        assert result["recommended_route"] == "Manual Review"

    def test_investigation_fraud_keyword(self):
        """Fraud keywords in description → Investigation (highest priority)."""
        state = _make_state()
        state["extracted_fields"]["incident_info"]["incident_description"] = (
            "The accident appears to be staged and inconsistent with evidence"
        )
        state["missing_fields"] = ["Policy Number"]  # Even with missing fields
        result = route_claim(state)
        # Investigation has highest priority
        assert result["recommended_route"] == "Investigation"

    def test_specialist_queue_injury(self):
        """Injury claim type → Specialist Queue."""
        state = _make_state()
        state["extracted_fields"]["other"]["claim_type"] = "injury"
        state["extracted_fields"]["asset_details"]["estimated_damage"] = 50000
        state["missing_fields"] = []
        result = route_claim(state)
        assert result["recommended_route"] == "Specialist Queue"

    def test_standard_processing_high_damage(self):
        """High damage (>= $25,000) with all fields, no flags → Standard Processing."""
        state = _make_state()
        state["extracted_fields"]["asset_details"]["estimated_damage"] = 50000
        state["missing_fields"] = []
        result = route_claim(state)
        assert result["recommended_route"] == "Standard Processing"

    def test_fraud_priority_over_missing_fields(self):
        """Investigation should take priority over Manual Review."""
        state = _make_state()
        state["extracted_fields"]["incident_info"]["incident_description"] = "suspicious fraud case"
        state["missing_fields"] = ["Policy Number"]
        result = route_claim(state)
        assert result["recommended_route"] == "Investigation"

    def test_confidence_scores(self):
        """Each route should have a confidence score > 0."""
        state = _make_state()
        state["missing_fields"] = []
        result = route_claim(state)
        assert result["confidence_score"] > 0.0


# =============================================================================
# Integration Test (requires GROQ_API_KEY)
# =============================================================================

@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set — skipping LLM integration tests",
)
class TestIntegration:
    """Integration tests that require a live Groq API key."""

    def test_full_pipeline(self):
        """Test the full pipeline with a sample PDF (if available)."""
        from backend.graph import run_pipeline, format_output

        sample_pdf = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "sample_fnol.pdf"
        )
        if not os.path.exists(sample_pdf):
            pytest.skip("Sample PDF not found — run data/generate_sample_pdf.py first")

        result = run_pipeline(sample_pdf)
        output = format_output(result)

        # Verify output structure
        assert "extractedFields" in output
        assert "missingFields" in output
        assert "recommendedRoute" in output
        assert "reasoning" in output
        assert "confidenceScore" in output

        # Route should be determined
        assert output["recommendedRoute"] != ""
        assert output["reasoning"] != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
