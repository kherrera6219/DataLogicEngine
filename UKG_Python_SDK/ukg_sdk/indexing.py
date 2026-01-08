"""
Unified indexing utilities.

The UKG system uses a unified indexing scheme to map data across multiple
taxonomies and code systems.  For example, industry sectors may be
represented by NAICS, SIC, PSC or NIC codes, and there is a one‑to‑one
mapping between these codes and UKG pillar identifiers.  Similarly, the
Nürnberg numbering scheme and SAM.gov naming conventions are used to
generate stable, disambiguated identifiers for entities.  This module
provides helper functions to normalise and convert between these schemes.

In this simplified SDK, the functions are primarily placeholders.  They
return the input values unchanged, but serve as extension points for
enterprises to implement proper mappings and metadata tagging.
"""

from __future__ import annotations

from typing import Dict


def normalise_code(code: str) -> str:
    """Normalise a sector or pillar code by stripping whitespace and
    uppercasing.  Real implementations should remove punctuation and
    standardise formats (e.g. NAICS vs SIC)."""
    return code.strip().upper() if code else ""


def nurnberg_to_samgov(nurnberg_code: str) -> str:
    """Convert a Nürnberg number to a SAM.gov naming convention.

    In this stub implementation, we simply return the Nürnberg code
    unchanged.  Enterprises can implement logic to map bespoke numbering
    systems into SAM.gov names (or other canonical identifiers)."""
    return nurnberg_code


def attach_meta_tags(entity: Dict[str, str]) -> Dict[str, str]:
    """Attach meta tagging to an entity record.

    This function can be used to add additional annotations (e.g. source,
    confidence, risk tags) to an entity dictionary.  In this stub, we
    leave the entity unchanged but provide an extension hook.

    Parameters
    ----------
    entity:
        A dictionary representing an entity (for example, a knowledge
        node or classification output).

    Returns
    -------
    Dict[str, str]
        The annotated entity.  Currently identical to input.
    """
    return entity
