"""
Assignment module for the Insurance Claims Processing Agent.

Handles intelligent claim-to-employee assignment using:
- An in-memory employee database with roles and current load
- A route → role mapping to match claim type to skill
- Least-load selection so no single employee is overloaded

This is a pure rule-based step — NO LLM involved.
"""

import logging
from typing import Any

from .state import ClaimState

logger = logging.getLogger(__name__)

# =============================================================================
# Employee Database (in-memory)
# =============================================================================

# Each employee has a name, a role (matches route_to_role values), and a load
# counter tracking how many open claims are currently assigned to them.
EMPLOYEES: list[dict] = [
    {"name": "Ravi", "role": "fast_track", "load": 2},
    {"name": "Priya", "role": "investigation", "load": 1},
    {"name": "Amit", "role": "manual_review", "load": 3},
    {"name": "Neha", "role": "specialist", "load": 1}
]

# =============================================================================
# Route → Role Mapping
# =============================================================================

ROUTE_TO_ROLE: dict[str, str] = {
    "Fast-track": "fast_track",
    "Investigation": "investigation",
    "Manual Review": "manual_review",
    "Specialist Queue": "specialist"
}


# =============================================================================
# NODE 6: Claim Assignment (Deterministic / Rule-based)
# =============================================================================

def assign_claim(state: ClaimState) -> dict[str, Any]:
    """
    Assign the claim to the most suitable available employee.

    Selection logic:
    1. Filter employees whose role matches the required role for the route.
    2. Among matching employees, pick the one with the lowest current load.
    3. Increment that employee's load to reflect the new assignment.

    Falls back to "Unassigned" if no matching employee is found.

    Args:
        state: Current claim state with recommended_route.

    Returns:
        Dict with assigned_to field to merge into state.
    """
    route = state.get("recommended_route", "")
    required_role = ROUTE_TO_ROLE.get(route, "fast_track") # Fallback if not standard

    logger.info(f"🧑‍💼 Assigning claim (route={route}, role={required_role})...")

    # Filter employees by role
    candidates = [e for e in EMPLOYEES if e["role"] == required_role]

    if not candidates:
        logger.warning(f"⚠️  No employee found for role '{required_role}' — claim Unassigned")
        return {"assigned_to": "Unassigned"}

    # Pick employee with lowest load (ties go to first in list)
    best = min(candidates, key=lambda e: e["load"])
    best["load"] += 1  # increment load after assignment

    logger.info(f"✅ Claim assigned to {best['name']} (load now {best['load']})")
    return {"assigned_to": best["name"]}
