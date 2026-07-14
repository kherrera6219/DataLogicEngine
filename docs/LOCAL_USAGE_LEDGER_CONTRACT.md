# Local Provider Usage Ledger Contract

## Document metadata

| Field | Value |
|---|---|
| Schema | `provider-usage-ledger.v1` |
| Document version | v1.0.0 |
| Last updated | 2026-07-13 |
| Status | Active Phase 7 engineering contract |
| Storage authority | App-owned PostgreSQL `llm_provider_usage` |

## Purpose

Provide durable, content-free evidence for each external provider attempt so the
owner can reconcile egress, retries, call/token ceilings, latency, failure
classes, and known cost estimates without storing provider secrets or prompt/
response content in the ledger.

## One row per provider attempt

Each attempted answer or refinement records:

- provider record/type and model;
- local user, external client key identity where applicable, run, and session;
- purpose and governed request stage;
- attempt number, retry index, status, success, and typed error class/code;
- input/output token counts and provider latency;
- nullable estimated USD cost and `available` or `unknown` pricing status;
- disclosed data-category names, never the disclosed content;
- idempotency key and start/end/create timestamps.

The ledger does not store provider credentials, authorization headers, raw
provider bodies, prompts, answers, retrieved passages, document chunks, persona
text, or tool-result content. Public error text must remain stable and redacted.

## Persistence and reconciliation invariants

1. The attempt consumes call budget before provider invocation.
2. Successful and failed attempts are recorded; retries are separate attempts.
3. A provider result is not released when ledger persistence fails.
4. Idempotency identity binds request, purpose, and call index.
5. Unknown pricing is nullable/unknown and never coerced to zero.
6. Ledger query failure blocks further provider work rather than appearing as
   unused allowance.
7. Offline replay re-enters current policy/budget checks and creates normal
   attempt rows; the queue is not a side door around the ledger.

## Owner API and UI contract

| Operation | Route | Boundary |
|---|---|---|
| Review | `GET /api/v1/gateway/usage-ledger` | Local authenticated owner/session |
| Export | `GET /api/v1/gateway/usage-ledger/export` | Redacted JSON; no content or secrets |
| Reset | `DELETE /api/v1/gateway/usage-ledger` | Owner/admin plus exact `RESET_PROVIDER_USAGE_LEDGER` confirmation |

Review responses include configured limits, remaining allowances, period/day/
month totals, pricing status, provider aggregates, and up to 100 recent rows.
Resetting usage data is an auditable owner action and changes subsequent durable
budget totals; it is not available to external gateway keys.

## Migration and retention

Migration `d3e4f5a6b7c8` extends the existing `llm_provider_usage` authority with
Phase 7 privacy/retry fields and indexes. Backup, restore, retention, deletion,
and protected-volume rules follow the Phase 4 data contract. The ledger contains
operational identifiers and disclosure categories, so exports still require
owner control even though prohibited content is excluded.

## Verification

Engineering tests cover per-attempt persistence, failures, retries, warning and
hard ceilings, unknown pricing, persistence fail-closed behavior, and the owner
API. Rebuilt-installed restart reconciliation and live-provider acceptance
remain CP7-F/Phase 15 release evidence. Production/public release remains
**NO-GO**.
