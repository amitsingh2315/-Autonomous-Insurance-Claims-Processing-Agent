"""
LangGraph workflow definition for the Insurance Claims Processing Agent.

Defines a StateGraph with 5 nodes that process FNOL documents through:
  extract_text → extract_fields → validate_fields → route_claim → generate_reasoning

The graph uses a shared ClaimState that flows between nodes.
"""

import logging
import os
from datetime import datetime, timezone
from langgraph.graph import StateGraph, START, END

from .state import ClaimState
from .extractor import extract_text, extract_fields
from .validator import validate_fields
from .router import route_claim
from .assignment import assign_claim
from .reasoning import generate_reasoning

logger = logging.getLogger(__name__)

# Cached compiled graph — built once, reused across calls
_COMPILED_GRAPH = None


def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph claims processing workflow.
    
    Graph structure (linear pipeline):
        START → extract_text → extract_fields → validate_fields 
              → route_claim → generate_reasoning → END
    
    Returns:
        Compiled LangGraph StateGraph ready for invocation.
    """
    logger.info("Building LangGraph workflow...")

    # Create the state graph with ClaimState schema
    graph = StateGraph(ClaimState)

    # --- Add nodes ---
    # Node 1: PDF text extraction (automation)
    graph.add_node("extract_text", extract_text)

    # Node 2: LLM field extraction (agent)
    graph.add_node("extract_fields", extract_fields)

    # Node 3: Field validation (automation)
    graph.add_node("validate_fields", validate_fields)

    # Node 4: Claim routing (rule-based)
    graph.add_node("route_claim", route_claim)

    # Node 5: Claim assignment (rule-based)
    graph.add_node("assign_claim", assign_claim)

    # Node 6: Reasoning generation (agent)
    graph.add_node("generate_reasoning", generate_reasoning)

    # --- Define edges (linear pipeline) ---
    graph.add_edge(START, "extract_text")
    graph.add_edge("extract_text", "extract_fields")
    graph.add_edge("extract_fields", "validate_fields")
    graph.add_edge("validate_fields", "route_claim")
    graph.add_edge("route_claim", "assign_claim")
    graph.add_edge("assign_claim", "generate_reasoning")
    graph.add_edge("generate_reasoning", END)

    # Compile the graph
    compiled = graph.compile()
    logger.info("LangGraph workflow compiled successfully")

    return compiled


def run_pipeline(pdf_path: str) -> dict:
    """
    Execute the full claims processing pipeline on a PDF.

    Reuses a module-level compiled graph to avoid rebuilding on every call.

    Args:
        pdf_path: Path to the FNOL PDF document.

    Returns:
        Final ClaimState dict with all processing results.
    """
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_graph()

    logger.info(f"Starting claims processing pipeline for: {pdf_path}")

    initial_state: ClaimState = {
        "pdf_path": pdf_path,
        "raw_text": "",
        "extracted_fields": {},
        "missing_fields": [],
        "recommended_route": "",
        "confidence_score": 0.0,
        "reasoning": "",
        "error": None,
    }

    result = _COMPILED_GRAPH.invoke(initial_state)
    logger.info(f"Pipeline complete -> Route: {result.get('recommended_route', 'Unknown')}")
    return result


def format_output(result: dict) -> dict:
    """
    Format the pipeline result into the required output JSON structure.

    missingFields uses snake_case field keys (e.g. "policy_number"),
    consistent with the keys inside extractedFields.

    Args:
        result: Raw pipeline result from LangGraph.

    Returns:
        Clean output dict matching the assignment specification.
    """
    return {
        "extractedFields": result.get("extracted_fields", {}),
        "missingFields":   result.get("missing_fields", []),    # snake_case keys
        "recommendedRoute": result.get("recommended_route", ""),
        "assignedTo":       result.get("assigned_to", ""),
        "reasoning":        result.get("reasoning", ""),
        "decisionBreakdown": result.get("decision_breakdown", ""),
        "confidenceScore":  result.get("confidence_score", 0.0),
        "fraudScore":       result.get("fraud_score", 0.0),
        "processingMetadata": {
            "model":     os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "pipeline":  "LangGraph v1",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "error":     result.get("error"),
        },
    }
