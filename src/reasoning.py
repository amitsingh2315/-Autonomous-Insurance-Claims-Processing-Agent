"""
Reasoning module for the Insurance Claims Processing Agent.

Uses Groq LLM to generate human-readable explanations for routing decisions.
Falls back to template-based reasoning if LLM is unavailable.
"""

import logging
import os
from typing import Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from .prompts import REASONING_PROMPT
from .state import ClaimState

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


# =============================================================================
# NODE 5: Reasoning Generation (Agentic / LLM)
# =============================================================================

def generate_reasoning(state: ClaimState) -> dict[str, Any]:
    """
    Generate a human-readable explanation for the routing decision using Groq LLM.
    
    This is an agentic step — uses LLM for natural language generation.
    Falls back to template-based reasoning if the LLM call fails.
    
    Args:
        state: Current claim state with all previous processing results.
        
    Returns:
        Dict with reasoning string to merge into state.
    """
    extracted = state.get("extracted_fields", {})
    missing = state.get("missing_fields", [])
    route = state.get("recommended_route", "Unknown")

    logger.info("💭 Generating reasoning for routing decision...")

    # Prepare context for the prompt
    claim_type = extracted.get("other", {}).get("claim_type") or "Unknown"
    estimated_damage = extracted.get("asset_details", {}).get("estimated_damage") or "Unknown"
    description = extracted.get("incident_info", {}).get("incident_description") or "No description available"
    missing_str = ", ".join(missing) if missing else "None"

    try:
        # Initialize Groq LLM
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        llm = ChatGroq(
            model=model_name,
            temperature=0.3,  # Slight creativity for natural language
            api_key=os.getenv("GROQ_API_KEY"),
        )

        # Build the reasoning prompt
        prompt = REASONING_PROMPT.format(
            claim_type=claim_type,
            estimated_damage=estimated_damage,
            incident_description=description,
            missing_fields=missing_str,
            recommended_route=route,
        )

        # Call the LLM
        response = llm.invoke([HumanMessage(content=prompt)])
        reasoning = response.content.strip()

        logger.info("✅ Reasoning generated successfully")
        return {"reasoning": reasoning}

    except Exception as e:
        logger.warning(f"⚠️  LLM reasoning failed ({str(e)}), using template fallback")
        # Fallback to template-based reasoning
        fallback = _generate_fallback_reasoning(
            route=route,
            claim_type=claim_type,
            estimated_damage=estimated_damage,
            missing_fields=missing,
            description=description,
        )
        return {"reasoning": fallback}


# =============================================================================
# Fallback Template Reasoning
# =============================================================================

def _generate_fallback_reasoning(
    route: str,
    claim_type: str,
    estimated_damage: Any,
    missing_fields: list,
    description: str,
) -> str:
    """
    Generate template-based reasoning when LLM is unavailable.
    
    Args:
        route: The routing decision.
        claim_type: Type of claim.
        estimated_damage: Estimated damage amount.
        missing_fields: List of missing mandatory fields.
        description: Incident description.
        
    Returns:
        Human-readable reasoning string.
    """
    if route == "Investigation":
        return (
            f"This claim is sent to the fraud team. We found possible signs of fraud "
            f"in the description. It needs human review before we can process it."
        )
    if route == "Manual Review":
        # Format snake_case keys as readable words for the explanation
        fields_str = ", ".join(f.replace("_", " ").title() for f in missing_fields)
        return (
            f"This claim needs human review. The following details are missing: {fields_str}. "
            f"We cannot process it without these details."
        )
    elif route == "Specialist Queue":
        return (
            f"This claim involves '{claim_type}'. It is sent to a specialist team who "
            f"handles these types of claims."
        )
    elif route == "Fast-track":
        return (
            f"This claim is approved for fast processing. The damage (${estimated_damage}) "
            f"is under $25,000. All details are filled, and no signs of fraud were found."
        )
    else:
        return (
            f"This claim will go through normal processing. All details are filled, "
            f"the damage is over $25,000, and no special handling is needed."
        )
