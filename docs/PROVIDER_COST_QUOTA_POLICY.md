# Provider Cost and Quota Policy

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.0.0 |
| Last updated | 2026-07-13 |
| Status | Active Phase 7 engineering contract |
| Owner | Local application owner |

## Purpose

Define the server-owned provider call, retry, token, warning, unknown-price, and
estimated-spend rules used by every `governed.v1` answer path. The renderer may
display or lower an allowance but cannot raise a hard ceiling.

## Provider-call contract

| Workflow | Maximum provider calls | Rule |
|---|---:|---|
| Standard chat | 1 | One answer call. |
| Enhanced chat | 2 | One answer call plus at most one bounded refinement/validation call. |
| Local review / deterministic DSQP | 0 | No provider answer call. |
| Simulation | Unavailable | Phase 10 must add an explicit scenario budget before execution. |

Retries and refinement consume the same request allowance. Retry is permitted
only for a typed idempotent transient failure and honors bounded provider retry
guidance when available. DataLogicEngine does not silently switch between
OpenAI and Google.

## Server-owned durable limits

| Environment setting | Default | Meaning |
|---|---:|---|
| `AI_PROVIDER_CALLS_PER_SESSION` | 100 | Calls attributed to one session. |
| `AI_PROVIDER_CALLS_PER_DAY` | 500 | Owner calls in the current UTC day. |
| `AI_PROVIDER_CALLS_PER_MONTH` | 5000 | Owner calls in the current UTC month. |
| `AI_PROVIDER_TOKENS_PER_DAY` | 2,000,000 | Input plus output tokens in the current UTC day. |
| `AI_PROVIDER_TOKENS_PER_MONTH` | 20,000,000 | Input plus output tokens in the current UTC month. |
| `AI_PROVIDER_SPEND_USD_PER_MONTH` | unset | Optional ceiling for known estimated spend. |

The backend evaluates projected input/output tokens before every attempt. A
ledger read/write failure is fail-closed: an apparently unused budget is never
inferred and a successful provider result is not released without its durable
usage record.

## Warning and hard-limit behavior

- At 80 percent of any applicable session/day/month call or token ceiling, or a
  known spend ceiling, the request returns
  `BUDGET_WARNING_CONFIRMATION_REQUIRED` until the owner explicitly confirms.
- Confirmation authorizes only that request; it cannot bypass a hard ceiling.
- Hard-limit failures end in a typed `*_HARD_LIMIT` state and HTTP 429.
- Cancellation, failed calls, and retries remain accounted attempts.

## Pricing and unknown cost

Cost is an estimate, never a bill or guaranteed provider price. Pricing is used
only when the owner supplies valid JSON in `AI_MODEL_PRICING_USD_PER_1K`, keyed
by normalized model ID:

```json
{
  "gpt-5.5": {"input": 0.0, "output": 0.0},
  "gemini-3.1-pro-preview": {"input": 0.0, "output": 0.0}
}
```

The numeric values are USD per 1,000 tokens and must be replaced with current,
owner-reviewed rates before use. This example deliberately makes no price claim.
Missing, malformed, stale, or unmatched metadata produces `pricing_status:
unknown`; the UI must show **Unknown**, not `$0`. Call/token ceilings still
apply. A spend ceiling is enforced only for calls whose estimate is known.

## Evidence and release boundary

Deterministic failure, retry, cancellation, warning, hard-limit, unknown-price,
and persistence tests support the Phase 7 engineering checkpoint. Rebuilt-
installed OpenAI/Google quota, latency, cancellation, restart reconciliation,
and account/billing behavior remain CP7-F/Phase 15 release evidence. Production
and public release remain **NO-GO**.
