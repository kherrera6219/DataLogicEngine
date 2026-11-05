# CR-A0 Windows remediation baseline

- Source commit: `a64603a9e75ac682559dda5f429d2b5e67f492d7`; working tree was clean before the baseline began.
- Captured: 2026-11-01T23:16:07-08:00
- Python: isolated `.venv-test-chroma-r3` (Python 3.11); includes the separately approved test-only Chroma lock and must never be used for packaging. `pip check` passed.
- Full command: `python -m pytest tests/ --no-cov -q --tb=no -rEf`.
- Full output: `baseline_pytest.txt`. Pytest summary and failure/setup error lines follow:

```text
3535 passed, 18 skipped, 35 warnings in 705.11s (0:11:45)
```

- Ruff: `python -m ruff check . --statistics`; full output: `baseline_ruff.txt`.
- Mypy 1.18.2: isolated tool, `--no-incremental --python-executable` pointing at the test environment; full output: `baseline_mypy.txt`. This is baseline evidence, not a passing gate unless its output says so.
- First-party tracked Python files: 719; lines: 161441 (backend, core, sdk; tracked `.py` files).
- This captures the baseline only; it does not disposition Phase A or qualify an installed build.
