"""
Extractor module for the Insurance Claims Processing Agent.

Contains two pipeline functions:
1. extract_text() — Deterministic PDF text extraction using pdfplumber
2. extract_fields() — LLM-powered structured field extraction using Groq
"""

import json
import logging
import os
from typing import Any

import pdfplumber
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from .prompts import FIELD_EXTRACTION_PROMPT
from .state import ClaimState

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


# =============================================================================
# NODE 1: Text Extraction (Deterministic / Automation)
# =============================================================================

def extract_text(state: ClaimState) -> dict[str, Any]:
    """
    Extract raw text from a PDF document using pdfplumber.
    
    This is a deterministic automation step — no LLM involved.
    
    Args:
        state: Current claim state containing pdf_path.
        
    Returns:
        Dict with raw_text or error to merge into state.
    """
    pdf_path = state.get("pdf_path", "")
    logger.info(f"📄 Extracting text from: {pdf_path}")

    # Validate the PDF path exists
    if not pdf_path or not os.path.exists(pdf_path):
        error_msg = f"PDF file not found: {pdf_path}"
        logger.error(error_msg)
        return {"raw_text": "", "error": error_msg}

    try:
        full_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            logger.info(f"   Found {len(pdf.pages)} page(s)")
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                full_text += page_text + "\n"
                logger.debug(f"   Page {i+1}: {len(page_text)} chars extracted")

        if not full_text.strip():
            logger.warning("⚠️  No text extracted from PDF (may be image-based)")
            return {"raw_text": "", "error": "No text could be extracted from PDF. It may be image-based."}

        logger.info(f"Extracted {len(full_text)} characters of text")
        return {"raw_text": full_text.strip(), "error": None}

    except Exception as e:
        error_msg = f"PDF extraction failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {"raw_text": "", "error": error_msg}


# =============================================================================
# NODE 2: Field Extraction (Agentic / LLM)
# =============================================================================

def extract_fields(state: ClaimState) -> dict[str, Any]:
    """
    Use Groq LLM to extract structured fields from raw text.
    
    This is an agentic step — uses LLM for cognitive understanding.
    
    Args:
        state: Current claim state containing raw_text.
        
    Returns:
        Dict with extracted_fields and confidence_score to merge into state.
    """
    raw_text = state.get("raw_text", "")

    # If there's already an error or no text, skip extraction
    if state.get("error") or not raw_text:
        logger.warning("⚠️  Skipping field extraction — no text available")
        return {
            "extracted_fields": _get_empty_fields(),
            "confidence_score": 0.0,
        }

    logger.info("Extracting fields using Groq LLM...")

    try:
        # Initialize Groq LLM
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        llm = ChatGroq(
            model=model_name,
            temperature=0,  # Deterministic output for extraction
            api_key=os.getenv("GROQ_API_KEY"),
        )

        # Build the prompt with the raw text
        prompt = FIELD_EXTRACTION_PROMPT.format(raw_text=raw_text)
        
        # Call the LLM
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content.strip()

        # Parse JSON from response (handle potential markdown wrapping)
        extracted = _parse_llm_json(response_text)
        
        if extracted is None:
            logger.error("❌ Failed to parse LLM response as JSON")
            return {
                "extracted_fields": _get_empty_fields(),
                "confidence_score": 0.0,
                "error": "LLM returned invalid JSON for field extraction",
            }

        # Sanitize: replace empty strings with None for consistency
        extracted = _sanitize_fields(extracted)

        # Calculate confidence based on field completeness
        confidence = _calculate_confidence(extracted)
        logger.info(f"Fields extracted successfully (confidence: {confidence:.2f})")
        
        return {
            "extracted_fields": extracted,
            "confidence_score": confidence,
        }

    except Exception as e:
        error_msg = f"LLM field extraction failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {
            "extracted_fields": _get_empty_fields(),
            "confidence_score": 0.0,
            "error": error_msg,
        }


# =============================================================================
# Helper Functions
# =============================================================================

def _parse_llm_json(text: str) -> dict | None:
    """
    Parse JSON from LLM response, handling markdown code blocks.
    
    Args:
        text: Raw LLM response text.
        
    Returns:
        Parsed dict or None if parsing fails.
    """
    # Strip markdown code block wrappers if present
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.debug(f"JSON parse failed for: {cleaned[:200]}...")
        # Try to find JSON object in the response
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                return None
        return None


def _sanitize_fields(fields: dict) -> dict:
    """
    Walk the extracted fields dict and convert any empty string values to None.

    Enforces the contract: missing values MUST be null, never empty string "".
    Lists are preserved as-is; empty-string items inside lists are also nulled.

    Args:
        fields: Nested dict of extracted fields from LLM.

    Returns:
        Same structure with "" replaced by None at every level.
    """
    if not isinstance(fields, dict):
        return fields
    sanitized = {}
    for k, v in fields.items():
        if isinstance(v, dict):
            sanitized[k] = _sanitize_fields(v)
        elif isinstance(v, str) and v.strip() == "":
            sanitized[k] = None          # empty string → null
        elif isinstance(v, list):
            # Sanitize empty-string items inside lists too
            sanitized[k] = [
                None if (isinstance(i, str) and i.strip() == "") else i
                for i in v
            ]
        else:
            sanitized[k] = v
    return sanitized


def _calculate_confidence(fields: dict) -> float:
    """
    Calculate confidence score based on how many key fields were extracted.
    
    Args:
        fields: Extracted fields dictionary.
        
    Returns:
        Confidence score between 0.0 and 1.0.
    """
    key_fields = [
        ("policy_info", "policy_number"),
        ("policy_info", "policyholder_name"),
        ("incident_info", "incident_date"),
        ("incident_info", "incident_location"),
        ("incident_info", "incident_description"),
        ("involved_parties", "claimant_name"),
        ("asset_details", "asset_type"),
        ("asset_details", "estimated_damage"),
        ("other", "claim_type"),
    ]

    filled = 0
    for section, field in key_fields:
        value = fields.get(section, {}).get(field)
        if value is not None and value != "" and value != []:
            filled += 1

    return round(filled / len(key_fields), 2)


def _get_empty_fields() -> dict:
    """Return the empty fields template when extraction fails."""
    return {
        "policy_info": {
            "policy_number": None,
            "policyholder_name": None,
            "effective_date_start": None,
            "effective_date_end": None,
        },
        "incident_info": {
            "incident_date": None,
            "incident_time": None,
            "incident_location": None,
            "incident_description": None,
        },
        "involved_parties": {
            "claimant_name": None,
            "claimant_contact": None,
            "third_parties": [],
            "third_party_contacts": [],
        },
        "asset_details": {
            "asset_type": None,
            "asset_id": None,
            "estimated_damage": None,
        },
        "other": {
            "claim_type": None,
            "attachments": [],
            "initial_estimate": None,
        },
    }
