# DataLogicEngine Developer Guide

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ENG-006 |
| Title | Developer build, test, packaging, and reproducibility guide |
| Document version | v3.7.1 |
| Product version | 4.4.2 |
| Status | active |
| Audience | Contributors, maintainers, quality engineers, release engineers, and reviewers |
| Owner | Platform Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Build scripts, exact dependency locks, CI workflows, architecture contracts |
| Last updated | 2026-08-21 |

## Purpose

This guide is the single source of truth for building, testing, packaging, and releasing DataLogicEngine. It is written for engineers who need reproducible local and CI workflows without relying on tribal knowledge.

## Runtime training-data capture (G-TRAIN)

Optional owner-controlled runtime usage capture stages **release-authorized** traces for the existing export-only dataset pipeline.

| Rule | Behavior |
|---|---|
| Default | **OFF** (`training_data_capture_enabled` FeatureFlag) |
| Who can enable | Owner / admin only (`@api_admin_required`) |
| What is staged | Redacted `query`, `released_answer`, confidence, stages — never credentials, pre-release drafts, or quarantined runs |
| Where | App-owned `runtime_root/datasets/capture/<run_id>.jsonl` |
| Failure posture | Fail-closed and non-blocking: capture errors never fail the governed run |
| Export path | Same hardened `DatasetExporter` (SFT/PRM); `source=capture` or default DB path |
| Training | **None** — capture is staging only; DPO remains disabled until real rejected-candidate provenance exists |

Toggle via Settings → Dataset exporter (**Runtime usage capture**) or:

```http
PUT /api/v1/dataset/capture-settings
{"enabled": true, "reason": "owner_enable_runtime_capture"}
```

See `docs/DATASET_EXPORT_HANDOFF.md` and `backend/dataset_exporter/runtime_capture.py`.

## Repository layout (high-signal areas)

- `backend/` — Flask API, governed execution (L1–L10 + TruthGate), dataset exporter, feature flags, routes
- `frontend/` — Next.js settings and operator surfaces
- `tests/backend/` — unit and route tests (including `test_runtime_capture.py`)
- `docs/` — architecture, handoff, privacy, lifecycle, and this guide

## Daily developer workflow

1. Create a branch from `main`.
2. Install exact lockfiles (backend + frontend).
3. Run targeted tests for the module you touched (`pytest tests/backend/test_runtime_capture.py` for capture changes).
4. Keep capture flag default-off in any local seed data.
5. Never disable the privacy redactor or path containment for convenience.
6. Update this guide and `DOCS_VERSION.json` when contracts change.

## Testing expectations for capture

- Flag off → zero writes
- Quarantine / `never_persist` / incomplete release evidence → skipped
- Secrets in released_answer → redacted before stage
- Staging failure → logged, governed run still succeeds
- Export from capture reapplies the same gates as export_from_db

## Change control

Document version bumps accompany material contract changes. Product owner approval is required for any change that alters default-off posture, redaction, or release-authorization gates.
