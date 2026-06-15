"""A14-9: Tests for CoordinateResolver17 — query-routing, meta-routing, defaults."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ukg_sdk.coordinates17 import Coordinate17, CoordinateResolver17


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def pillar_catalog_file(tmp_path: Path) -> Path:
    catalog = [
        {
            "id": "P-HEALTH",
            "sector": "healthcare",
            "keywords": ["medical", "diagnosis", "patient", "clinical"],
        },
        {
            "id": "P-LEGAL",
            "sector": "legal",
            "keywords": ["contract", "law", "regulation", "compliance"],
        },
        {
            "id": "P-TECH",
            "sector": "technology",
            "keywords": ["software", "api", "cloud", "database"],
        },
    ]
    p = tmp_path / "pillar_catalog.json"
    p.write_text(json.dumps(catalog), encoding="utf-8")
    return p


@pytest.fixture()
def axis2_catalog_file(tmp_path: Path) -> Path:
    catalog = {
        "healthcare": {"label": "Healthcare & Life Sciences"},
        "legal": {"label": "Legal & Regulatory"},
        "technology": {"label": "Technology & Engineering"},
    }
    p = tmp_path / "axis2_catalog.json"
    p.write_text(json.dumps(catalog), encoding="utf-8")
    return p


@pytest.fixture()
def resolver(pillar_catalog_file: Path, axis2_catalog_file: Path) -> CoordinateResolver17:
    return CoordinateResolver17(
        axis2_json=str(axis2_catalog_file),
        pillar_json=str(pillar_catalog_file),
    )


# ---------------------------------------------------------------------------
# Default / no-catalog resolver
# ---------------------------------------------------------------------------

def test_default_coord_values_no_catalog():
    """Resolver with no catalog files returns safe defaults."""
    r = CoordinateResolver17()
    c = r.resolve({"query": "hello world"})
    assert isinstance(c, Coordinate17)
    assert c.axis_17 == "standard"  # A14-4: must NOT be 'moderate'
    assert c.axis_7 == 1.0
    assert c.axis_11 == "en"


def test_empty_context_no_crash():
    r = CoordinateResolver17()
    c = r.resolve({})
    assert c.as_compact_string() != ""


# ---------------------------------------------------------------------------
# A14-2: Query text drives pillar matching
# ---------------------------------------------------------------------------

def test_query_drives_pillar_matching(resolver: CoordinateResolver17):
    """Keyword in query text (not meta) triggers pillar resolution."""
    # Simulate the CORRECT call pattern from overlay.run(): {**meta, 'query': query}
    c = resolver.resolve({"query": "What is the best diagnosis for chest pain?"})
    assert c.pillar == "P-HEALTH"
    assert c.sector == "healthcare"


def test_legal_keyword_in_query(resolver: CoordinateResolver17):
    c = resolver.resolve({"query": "Explain the regulation around data contracts"})
    assert c.pillar == "P-LEGAL"


def test_tech_keyword_in_query(resolver: CoordinateResolver17):
    c = resolver.resolve({"query": "How do I connect to a cloud database via the api?"})
    assert c.pillar == "P-TECH"


def test_meta_only_no_query_no_pillar(resolver: CoordinateResolver17):
    """Without 'query' key, no keyword matching fires — pillar stays empty.

    This is the OLD (broken) pattern: resolver.resolve(meta) without query.
    Confirms that omitting 'query' from the context dict means no pillar signal.
    """
    c = resolver.resolve({"sector": "healthcare"})
    # Sector from axis2 catalog may match, but pillar from keywords won't
    assert c.pillar == ""  # no keyword match without query text


# ---------------------------------------------------------------------------
# Meta/context overrides
# ---------------------------------------------------------------------------

def test_explicit_axis_override(resolver: CoordinateResolver17):
    c = resolver.resolve({"query": "test", "axis_13": "confidential", "axis_11": "fr"})
    assert c.axis_13 == "confidential"
    assert c.axis_11 == "fr"


def test_axis_7_float_coercion(resolver: CoordinateResolver17):
    c = resolver.resolve({"query": "test", "axis_7": "0.85"})
    assert c.axis_7 == pytest.approx(0.85)


def test_axis_7_bad_value_uses_default(resolver: CoordinateResolver17):
    c = resolver.resolve({"query": "test", "axis_7": "not-a-float"})
    assert c.axis_7 == 1.0


def test_truth_mode_sets_axis_17(resolver: CoordinateResolver17):
    c = resolver.resolve({"query": "test", "truth_mode": "high_stakes"})
    assert c.axis_17 == "high_stakes"


def test_axis_17_default_is_standard(resolver: CoordinateResolver17):
    """A14-4: axis_17 must default to 'standard', never 'moderate'."""
    c = resolver.resolve({"query": "a simple query"})
    assert c.axis_17 == "standard"
    assert c.axis_17 != "moderate"


# ---------------------------------------------------------------------------
# as_compact_string and as_dict
# ---------------------------------------------------------------------------

def test_compact_string_format(resolver: CoordinateResolver17):
    c = resolver.resolve({"query": "medical diagnosis"})
    s = c.as_compact_string()
    parts = s.split(".")
    assert len(parts) == 5
    assert parts[0] == "P-HEALTH"


def test_as_dict_has_all_axes(resolver: CoordinateResolver17):
    c = resolver.resolve({"query": "test"})
    d = c.as_dict()
    for i in range(1, 18):
        assert f"axis_{i}" in d
    assert "pillar" in d
    assert "sector" in d
