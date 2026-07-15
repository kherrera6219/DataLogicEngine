from __future__ import annotations

from pathlib import Path

from scripts.check_circular_deps import analyze_dependencies


def _write_module(root: Path, relative: str, source: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_dependency_gate_reports_real_cycle(tmp_path: Path):
    _write_module(tmp_path, "backend/__init__.py", "")
    _write_module(tmp_path, "backend/alpha.py", "from backend import beta\n")
    _write_module(tmp_path, "backend/beta.py", "from backend import alpha\n")

    result = analyze_dependencies(tmp_path, ["backend"])

    assert result["passed"] is False
    assert result["cycles"] == [["backend.alpha", "backend.beta"]]


def test_dependency_gate_passes_acyclic_graph(tmp_path: Path):
    _write_module(tmp_path, "backend/__init__.py", "")
    _write_module(tmp_path, "backend/alpha.py", "from backend import beta\n")
    _write_module(tmp_path, "backend/beta.py", "VALUE = 1\n")

    result = analyze_dependencies(tmp_path, ["backend"])

    assert result["passed"] is True
    assert result["cycles"] == []


def test_dependency_gate_fails_on_unparseable_source(tmp_path: Path):
    _write_module(tmp_path, "backend/__init__.py", "")
    _write_module(tmp_path, "backend/broken.py", "def broken(:\n")

    result = analyze_dependencies(tmp_path, ["backend"])

    assert result["passed"] is False
    assert len(result["parse_errors"]) == 1
