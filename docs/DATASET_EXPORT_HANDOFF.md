# Dataset export handoff (no in-app trainer)

| Field | Value |
|---|---|
| Date | 2026-08-12 |
| Product stance | **Export-only** (owner gate G-TRAIN) |

## What the product does

- Export **SFT** / **PRM** candidate datasets from released TraceRuns (owner-only APIs).
- Record training admissions / evaluation / release-preparation metadata.
- **Does not** fine-tune or host a model trainer inside the app.

## What operators should say

Use **“Dataset preparation / export”**, not “train model in app”.

## External handoff

1. Run export from Settings → Dataset exporter (or `/api/v1/dataset/export`).
2. Artifacts land under the runtime datasets root.
3. Load Parquet/export into your chosen offline trainer (outside DLE).
4. Re-import evaluation results only through documented admission APIs if used.

## DPO

DPO export remains **fail-closed** without reject pairs — by design.
