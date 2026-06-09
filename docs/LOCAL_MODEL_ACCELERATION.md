# Local Model Acceleration

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.0.0 |
| Last updated | 2026-06-08 |
| Status | Active |
| Owner | Platform Engineering |
| Related commit | `437721c1` |

## Overview

Local Model Acceleration is a latency-reduction subsystem that transparently
wraps every gateway request that targets a **local Ollama model** (T0–T3)
with two complementary features:

1. **Keep-alive daemon** — prevents model eviction from VRAM between requests.
2. **Exact response cache** — returns a stored answer instantly when the same
   deterministic query is seen again.

Both features are fail-open: any internal exception falls through to the
standard gateway call. No LLM output is ever blocked or altered by this layer.

---

## Architecture

```
LLM Gateway request (local provider only)
        │
        ▼
LocalModelAccelerationManager.generate_with_cache()
        │
        ├─► start_keepalive(model)          ← tells daemon to ping this model
        │
        ├─► safety.should_cache_prompt()    ← credential / task-type filter
        │         │ cacheable=False ──────────────────────────────────────────┐
        │         │ cacheable=True                                            │
        │         ▼                                                           │
        ├─► ResponseCache.get(cache_key)   ← SHA-256 keyed SQLite lookup     │
        │         │ HIT ─────► return cached answer immediately              │
        │         │ MISS                                                      │
        │         ▼                                                           │
        ├─► call_model()  (the original asyncio.wait_for coroutine)  ◄───────┘
        │         │
        │         ▼
        └─► ResponseCache.set(...)  ← store response for next time
```

### File layout

```
backend/local_model_acceleration/
    __init__.py          ← get_local_model_acceleration_manager() singleton
    config.py            ← LocalModelAccelerationConfig dataclass
    paths.py             ← cache dir resolution (APPDATA/DataLogicEngine/cache/…)
    ollama_client.py     ← canonical thin HTTP wrapper (health_check, list_models,
                           generate, unload_model) — canonical /api/tags caller
    keepalive.py         ← daemon thread; pings MRU model every heartbeat_seconds
    response_cache.py    ← SQLite WAL-mode exact cache (llm_response_cache.db)
    safety.py            ← should_cache_prompt() safety filter
    manager.py           ← orchestrates all; generate_with_cache() main API
```

### Cache file location

| OS | Default path |
|---|---|
| Windows | `%APPDATA%\DataLogicEngine\cache\local_model_acceleration\llm_response_cache.db` |
| macOS/Linux | `~/.datalogicengine/cache/local_model_acceleration/llm_response_cache.db` |

Override with `DATALOGIC_ACCELERATION_CACHE_DIR` environment variable.

---

## Feature 1 — Keep-alive daemon

When Ollama is idle for its configured period (default: 5 min), it evicts
loaded models from VRAM.  The next request then incurs a cold-load penalty of
5–30 seconds for 7B–14B quantised models.

The keepalive thread runs as a **daemon thread** (does not block process exit)
and sends a 1-token `POST /api/generate` every `heartbeat_seconds` (default:
240 s) with `keep_alive="60m"`.  This resets Ollama's internal eviction timer.

**Only one model is kept warm at a time** — the most-recently-used one, updated
atomically on every gateway request.  Keeping multiple models would consume VRAM
for tiers that may not be used again.

### Configuration

| Setting | Default | Effect |
|---|---|---|
| `local_model_keepalive_enabled` | `true` | Toggle the daemon thread |
| `local_model_keepalive_minutes` | `60` | `keep_alive` value sent to Ollama |
| `local_model_heartbeat_seconds` | `240` | How often the thread pings |

---

## Feature 2 — Exact response cache

A SQLite database stores previous responses keyed by a SHA-256 hash of all
dimensions that affect the model output.

### Cache key

The key is SHA-256 of the pipe-joined tuple:

```
model_name | provider_type | task_type | mode | run_ukg_pipeline
| temperature (2 dp) | max_tokens | SHA-256(system)[:16]
| SHA-256(prompt)[:16] | SHA-256(rag_context)[:16]
```

Including `SHA-256(rag_context)` is critical: the same user question submitted
twice with different RAG chunks retrieved (different knowledge base state) must
NOT hit the same cache entry.

### What is NOT cached (safety filter)

| Rule | Examples |
|---|---|
| Prompt longer than `max_prompt_chars` (24 000) | Very long document analysis |
| Unsafe task types | `emotional_chat`, `medical_advice`, `legal_advice`, `security_decision`, `live_web`, `current_events` |
| Sensitive keywords in prompt | `password`, `api_key`, `secret`, ` token`, `bearer `, `ssn`, `credit card` |
| Caller metadata flags | `no_cache: true`, `cache_policy: "off"`, `contains_sensitive_data: true` |

### TTL and cleanup

Rows expire after `local_model_cache_ttl_days` (default: 30 days).  Expired rows
are filtered by the `WHERE expires_at > strftime('now')` clause on read, and can
be purged explicitly via the `/local-acceleration/cache/purge-expired` API.

### Configuration

| Setting | Default | Effect |
|---|---|---|
| `local_model_exact_cache_enabled` | `true` | Toggle the cache |
| `local_model_cache_ttl_days` | `30` | Days before a cached response expires |
| `local_model_cache_max_prompt_chars` | `24000` | Prompts longer than this bypass cache |

---

## API endpoints

All endpoints require session authentication (`@api_session_login_required`).

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/gateway/local-acceleration/status` | Ollama reachability, keepalive model, cache stats, all settings |
| `POST` | `/api/v1/gateway/local-acceleration/settings` | Persist any LMA settings fields |
| `POST` | `/api/v1/gateway/local-acceleration/cache/clear` | Wipe all cached responses |
| `POST` | `/api/v1/gateway/local-acceleration/cache/purge-expired` | Remove expired rows only |
| `POST` | `/api/v1/gateway/local-acceleration/keepalive/stop` | Stop keepalive daemon (frees VRAM proactively) |

### Chat response field

Every `POST /api/v1/gateway/chat` response includes:

```json
"local_model_acceleration": {
    "acceleration_enabled": true,
    "cache_hit": true,
    "source": "exact_cache",
    "cache_key_prefix": "a3f9b2c1d4e5"
}
```

`null` for cloud providers (T4/T5) or when the feature is disabled.

---

## Semantic cache — Phase 2 (not yet built)

Semantic (embedding-based) cache is intentionally omitted from Phase 1.  The
DSQP persona system and RAG context retrieval mean that a 0.92 cosine similarity
threshold between two surface-identical queries is not sufficient to guarantee
the same correct answer.

Phase 2 will add a per-query gate: semantic similarity is allowed only when
`SHA-256(rag_context_A) == SHA-256(rag_context_B)` (same retrieval state).
`safety.semantic_cache_allowed()` currently returns `False` unconditionally.
`local_model_semantic_cache_enabled` is stored in settings (always `False`) so
the UI toggle can be added without a schema change.

---

## OllamaClient — canonical /api/tags caller

`backend/local_model_acceleration/ollama_client.py` is now the **single
authoritative caller** of `GET /api/tags` (Ollama's model-list endpoint).

Previously this endpoint was called in three places:
- `OllamaProvider.health_check()` in the SDK
- `tier_availability.probe_local_tiers()` (imported OllamaProvider)
- (planned) Local Model Acceleration health

`tier_availability.probe_local_tiers()` has been updated to call
`OllamaClient().list_models()` directly, eliminating the duplication.

---

## Singleton pattern

```python
from backend.local_model_acceleration import get_local_model_acceleration_manager

manager = get_local_model_acceleration_manager()  # lazy-init, thread-safe
```

Double-checked locking ensures only one `LocalModelAccelerationManager` is
created per process even under concurrent imports.  Config is reloaded from
`runtime_settings.json` on **every call** to `generate_with_cache()` — a ~1 ms
overhead that means UI settings changes take effect without restarting the app.

---

## Testing

```
tests/unit/test_local_model_acceleration.py   29 tests
tests/unit/test_tier_availability.py          17 tests (updated _ollama_patch)
```

Run with:

```bash
python -m pytest tests/unit/test_local_model_acceleration.py tests/unit/test_tier_availability.py -v
```

All 46 tests pass.  No Flask app context or database required.
