# Dataset export handoff (no in-app trainer)

| Field | Value |
|---|---|
| Date | 2026-08-21 |
| Product stance | **Export-only** (owner gate G-TRAIN) |

## What the product does

- Optionally stage redacted released traces at runtime when the owner enables
  `training_data_capture_enabled` (default **OFF**, audited, fail-closed).
- Export **SFT** / **PRM** candidate datasets from released TraceRuns or from
  staged capture files (owner-only APIs).
- Record training admissions / evaluation / release-preparation metadata.
- **Does not** fine-tune or host a model trainer inside the app.

## Runtime capture (optional)

1. Owner enables capture via Settings → Dataset exporter (**Runtime usage capture**)
   or `PUT /api/v1/dataset/capture-settings` with `{ "enabled": true, "reason": "..." }`.
2. After TruthGate release and successful trace persistence, the system may write one
   redacted row under `runtime_root/datasets/capture/<run_id>.jsonl`.
3. Capture never blocks the governed run. Quarantined / `never_persist` / incomplete
   runs are skipped. Credentials and pre-release drafts are never staged.
4. Leave the flag **OFF** for zero extra writes while the system runs.

## What operators should say

Use **“Dataset preparation / export”**, not “train model in app”.
Runtime capture is **usage staging for later export**, not training.

## External handoff

1. (Optional) Accumulate staged rows with capture enabled, or rely on TraceRun history.
2. Run export from Settings → Dataset exporter (or `/api/v1/dataset/export`).
   Default source is `db`; optional `source: "capture"` uses staged files only.
3. Artifacts land under the runtime datasets root.
4. Load Parquet/JSONL into your chosen offline trainer (outside DLE).
5. Re-import evaluation results only through documented admission APIs if used.

## DPO

DPO export remains **fail-closed** without reject pairs — by design.
