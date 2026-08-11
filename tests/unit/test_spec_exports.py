from pathlib import Path

import yaml

from scripts.generate_spec_exports import generate_spec_exports


ROOT = Path(__file__).resolve().parents[2]


def test_spec_exports_cover_live_ka_and_axis_authorities(tmp_path: Path):
    outputs = generate_spec_exports(root=ROOT, output_dir=tmp_path)

    registry = yaml.safe_load(outputs["ka_registry"].read_text(encoding="utf-8"))
    assert registry["manifest_version"] == "2026.08.11-al10.1"
    assert registry["capability_count"] == 213
    assert registry["production_enabled_count"] == 211
    assert len(registry["algorithms"]) == 213
    assert {item["id"] for item in registry["algorithms"]} >= {
        "KA-Master",
        "L9-KA-001",
        "L10-KA-007",
        "KA-1114",
    }
    assert all("contract" in item for item in registry["algorithms"])

    axes = yaml.safe_load(outputs["axes_14_17"].read_text(encoding="utf-8"))
    assert {int(number) for number in axes["axes"]} == {14, 15, 16, 17}
    assert axes["axes"][14]["name"] == "Acquisition Lifecycle"
    assert axes["axes"][17]["name"] == "FROST-Mode Selector"


def test_api_delta_accounts_for_every_canonical_path(tmp_path: Path):
    outputs = generate_spec_exports(root=ROOT, output_dir=tmp_path)
    text = outputs["api_delta"].read_text(encoding="utf-8")

    assert "| Canonical paths | **45** |" in text
    assert "| Live documented paths | **67** |" in text
    rows = [line for line in text.splitlines() if line.startswith("| `/")]
    assert len(rows) == 45
    assert all(any(status in row for status in ("exact", "candidate mapping", "absent")) for row in rows)


# Keep this identifier longer than the Lob detector's exact token-shaped length;
# TruffleHog otherwise treats an ordinary Python test name as a verified key.
def test_checked_in_spec_exports_match_the_generator_output(tmp_path: Path):
    generated = generate_spec_exports(root=ROOT, output_dir=tmp_path)
    checked_in = ROOT / "docs" / "spec-exports"

    for path in generated.values():
        assert path.read_bytes() == (checked_in / path.name).read_bytes()
