# Canonical UKG API vs. current documented API

| Field | Value |
|---|---|
| Status | Historical roadmap comparison; no compatibility or release claim |
| Historical roadmap source | `docs/archive/api/ukg_api_v3_2-roadmap-2026-01.yaml` |
| Supported integration authority | `docs/openapi.yaml` |
| Canonical paths | **45** |
| Live documented paths | **67** |
| Exact paths | **1** |
| Candidate mappings | **11** |
| Absent from live document | **33** |

Candidate mappings are name-level review leads, not assertions of request/response
compatibility. D-3 formally selects docs/openapi.yaml and the live /api/v1
routes as the supported product contract; the UKG v3.2 source is roadmap history.

| Canonical path | Methods | Disposition | Live documented path |
|---|---|---|---|
| `/enhance` | POST | candidate mapping | `/gateway/chat`, `/v1/chat/completions` |
| `/enhance/estimate` | POST | absent | — |
| `/enhance/stream` | POST | candidate mapping | `/gateway/chat/stream` |
| `/enhance/batch` | POST | absent | — |
| `/enhance/batch/{batch_id}/status` | GET | absent | — |
| `/enhance/batch/{batch_id}/results` | GET | absent | — |
| `/knowledge/ingest` | POST | candidate mapping | `/ingestion/local` |
| `/knowledge/ingest/{ingestion_id}/status` | GET | candidate mapping | `/ingestion/status/{ingestion_id}` |
| `/knowledge/graph/snapshot` | POST | absent | — |
| `/knowledge/graph/snapshot/{snapshot_id}` | GET | absent | — |
| `/knowledge/graph/diff` | POST | absent | — |
| `/axis/resolve` | POST | absent | — |
| `/axis/{axis_number}` | GET | absent | — |
| `/axis/coordinate/{coordinate}` | GET | absent | — |
| `/personas` | GET | absent | — |
| `/personas/{persona_id}/profile` | GET | absent | — |
| `/personas/activate` | POST | absent | — |
| `/simulation/layers` | GET | absent | — |
| `/simulation/execute` | POST | absent | — |
| `/simulation/trace/{request_id}` | GET | absent | — |
| `/refinement/steps` | GET | absent | — |
| `/refinement/validate` | POST | absent | — |
| `/refinement/confidence/{request_id}` | GET | absent | — |
| `/truth/gate/check` | POST | candidate mapping | `/truth/gate/evaluate` |
| `/truth/core/models` | GET | absent | — |
| `/truth/memory/audit/{audit_id}` | GET | absent | — |
| `/truth/link/health` | GET | absent | — |
| `/knowledge/node/{node_id}` | GET | absent | — |
| `/knowledge/pillar/{pillar_id}` | GET | absent | — |
| `/knowledge/query` | POST | absent | — |
| `/audit/{request_id}` | GET | candidate mapping | `/trace/runs/{run_id}/bundle` |
| `/audit/{request_id}/download` | GET | candidate mapping | `/trace/runs/{run_id}/export` |
| `/audit/{request_id}/export` | GET | candidate mapping | `/trace/runs/{run_id}/export` |
| `/compliance/frameworks` | GET | absent | — |
| `/compliance/check` | POST | absent | — |
| `/analytics/confidence-trends` | GET | absent | — |
| `/analytics/persona-usage` | GET | absent | — |
| `/analytics/cost-breakdown` | GET | absent | — |
| `/health` | GET | exact | /health |
| `/status` | GET | candidate mapping | `/ready` |
| `/workflow/route` | POST | absent | — |
| `/workflow/run` | POST | candidate mapping | `/ka/runs` |
| `/truth/gate` | POST | candidate mapping | `/truth/gate/evaluate` |
| `/truth/core/validate` | POST | absent | — |
| `/truth/memory/promote` | POST | absent | — |
