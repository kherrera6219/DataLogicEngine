from pathlib import Path

from scripts import inventory_scan


def test_inventory_scan_excludes_nested_worktrees_and_build_outputs(tmp_path: Path):
    kept = tmp_path / "backend" / "live.py"
    ignored = [
        tmp_path / ".claude" / "worktrees" / "old" / "backend" / "duplicate.py",
        tmp_path / "frontend" / "dist-smoke" / "bundle.js",
        tmp_path / "frontend" / "dist-electron" / "main.js",
        tmp_path / "htmlcov-backend" / "index.html",
    ]

    kept.parent.mkdir(parents=True)
    kept.write_text("live = True\n", encoding="utf-8")
    for path in ignored:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated = True\n", encoding="utf-8")

    inventory, _, _ = inventory_scan.scan_directory(tmp_path)

    assert [entry["path"].replace("\\", "/") for entry in inventory] == [
        "backend/live.py"
    ]
