"""Formal DSQP persona component contract (owner lock G-DSQP).

Mainline already constructs a **seven-component** persona. This module freezes
the keys and maps them to IP/product labels (Traits / Related Roles language).

Do not change ``COMPONENT_KEYS`` without updating templates, validator, tests,
and any patent/disclosure crosswalk.
"""

from __future__ import annotations

from backend.dsqp.dsqp_chain import COMPONENT_KEYS

# Exact ordered 7-part contract (must match dsqp_chain.COMPONENT_KEYS).
DSQP_SEVEN_PART_KEYS: tuple[str, ...] = tuple(COMPONENT_KEYS)

# Product / IP disclosure labels for the same seven keys.
DSQP_PART_LABELS: dict[str, str] = {
    "job_role": "Job Role",
    "education": "Education",
    "certifications": "Certifications",
    "skills": "Traits / Skills",
    "training": "Training",
    "career_path": "Career Path",
    "related_jobs": "Related Roles",
}

assert len(DSQP_SEVEN_PART_KEYS) == 7, "DSQP contract must remain seven parts"
assert set(DSQP_SEVEN_PART_KEYS) == set(COMPONENT_KEYS)
assert set(DSQP_PART_LABELS) == set(DSQP_SEVEN_PART_KEYS)


def dsqp_contract_summary() -> dict[str, object]:
    return {
        "part_count": 7,
        "keys": list(DSQP_SEVEN_PART_KEYS),
        "labels": dict(DSQP_PART_LABELS),
        "policy": (
            "Seven-part DSQP is required (G-DSQP). "
            "skills maps to Traits/Skills; related_jobs maps to Related Roles."
        ),
    }
