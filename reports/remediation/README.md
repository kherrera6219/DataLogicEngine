# reports/remediation/

**Generated evidence for the compliance remediation program. Do not hand-edit anything in this directory.**

Every file here is produced by a task step in `docs/compliance/REMEDIATION_PLAN.md` and is cited by that task's exit gate. A hand-edited evidence file is worse than a missing one — it looks like proof and is not.

---

## Expected artifacts

| File | Produced by | Contents |
|---|---|---|
| `BASELINE.md` | `CR-A0` | Commit SHA, working-tree state, full pytest summary, ERROR vs FAILED breakdown, ruff/mypy counts, line counts. Every later gate compares against this. |
| `baseline_pytest.txt` | `CR-A0` | Verbatim pytest output at baseline |
| `a1_pytest.txt` | `CR-A1` | Verbatim pytest output after the conftest fix. Gate requires zero `^ERROR` lines and zero `WinError 32`. |
| `A3_TRIAGE.md` | `CR-A3` | Per-test determination for the 40 previously-unexecuted tests: test wrong or code wrong, with evidence. **Includes the count of genuine security defects found** — the honest measure of what the Windows gap was hiding. |
| `EGRESS_INVENTORY.md` | `CR-B0` | Every outbound call site: file, line, library, destination, whether it runs on the governed request path |
| `D4_SUPPRESSIONS.md` | `CR-D4` | Verdict for each of the 19 `# inversion:ok` suppressions: evidenced by a test, or removed |

Related but stored elsewhere:

- `/reports/egress/egress-attestation-<sha>.json` — `CR-B5`, the CI egress attestation. Dated, renewable, and the artifact you hand a customer's security team.
- `/reports/sbom/*.cdx.json` — `CR-E1`, CycloneDX 1.6 SBOM per build
- `/reports/evals/` — `CR-F3`/`CR-F4`, calibration (ECE, Brier) and hallucination rate

---

## Why this directory is separate from `docs/compliance/`

`docs/compliance/` is authored: plans, blueprints, standards mappings. This directory is produced: command output, measurements, inventories.

Keeping them apart is the point. When an assessor asks "how do you know?", the answer is a path under `reports/`, with a commit SHA and a timestamp — not a paragraph under `docs/`. The program exists because a January 2026 assessment described capabilities the code did not have; the structural fix is that claims live in one directory and evidence lives in another, and gates cite the second.

---

## Regenerating

Every artifact here is reproducible from the task steps in the plan. If one is stale, missing, or disagrees with the tree, rerun the task rather than editing the file.
