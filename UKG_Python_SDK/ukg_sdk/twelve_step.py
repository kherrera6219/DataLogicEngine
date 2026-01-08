"""
Definitions for the 12‑step refinement workflow.

The 12‑step refinement process is used in the UKG system to progressively
improve the quality of answers and enforce domain‑specific checks.  While
this simplified SDK does not implement per‑step logic, exposing the step
names allows downstream tools to reference them for logging or analysis.

The typical steps include:

  1. Algorithm of Thought (AoT)
  2. Tree of Thought (ToT)
  3. Gap & Data Analysis
  4. Deep Reasoning & Planning
  5. Self‑Reflection & Critique
  6. Ethics/Safety/Compliance Checks
  7. Recursive Learning & Adjustment
  8. Advanced Parsing & Language Analysis
  9. External Validation & Research
  10. Answer Synthesis & Scoring
  11. Output Generation or Escalation
  12. Memory Patching & Offload

These names are indicative; full implementations may vary.
"""

from __future__ import annotations

from typing import List, Tuple


TWELVE_STEP_WORKFLOW: List[Tuple[int, str]] = [
    (1, "Algorithm of Thought"),
    (2, "Tree of Thought"),
    (3, "Gap & Data Analysis"),
    (4, "Deep Reasoning & Planning"),
    (5, "Self‑Reflection & Critique"),
    (6, "Ethics/Safety/Compliance Checks"),
    (7, "Recursive Learning & Adjustment"),
    (8, "Advanced Parsing & Language Analysis"),
    (9, "External Validation & Research"),
    (10, "Answer Synthesis & Scoring"),
    (11, "Output Generation or Escalation"),
    (12, "Memory Patching & Offload"),
]

def get_step_name(step_number: int) -> str:
    """Return the descriptive name for a given refinement step."""
    for num, name in TWELVE_STEP_WORKFLOW:
        if num == step_number:
            return name
    return "Unknown Step"
