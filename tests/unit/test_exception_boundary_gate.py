from __future__ import annotations

from pathlib import Path

from scripts.check_exception_boundaries import audit_source_tree


def _write_source(root: Path, source: str) -> None:
    path = root / "backend" / "sample.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_gate_detects_broad_catch_and_module_root_logging(tmp_path: Path):
    _write_source(
        tmp_path,
        "import logging\n"
        "logging.basicConfig()\n"
        "try:\n"
        "    raise RuntimeError()\n"
        "except Exception:\n"
        "    pass\n",
    )

    report = audit_source_tree(
        tmp_path,
        ["backend"],
        max_broad_catch_sites=0,
        max_broad_catch_files=0,
    )

    assert report["passed"] is False
    assert report["broad_catch_site_count"] == 1
    assert report["basic_config_sites"] == ["backend/sample.py:2"]


def test_repository_gate_has_complete_taxonomy_and_no_basic_config():
    report = audit_source_tree(Path(__file__).resolve().parents[2])

    assert report["checks"]["typed_error_categories_complete"] is True
    assert report["basic_config_sites"] == []
    assert report["passed"] is True
