# UKG SDK v0.2.0 — How to use

## 1) Concept: “API overlay in / API out”

You mount **UKGOverlay** between:

- **LLM provider API in** (OpenAI / Azure OpenAI / Anthropic)
- **your app outputs** (chat UI, RAG endpoint, report generator, workflow runner, etc.)

The overlay does four things:

1. Validates and classifies the query (minimal built-ins in v0.2.0)
2. Resolves a **17-axis coordinate** from metadata (deterministic ID)
3. Runs a **tiered workflow** (how deep to go depends on difficulty/stakes)
4. Emits **audit + trace** artifacts for governance and debugging

---

## 2) Providers

### OpenAI

```bash
export OPENAI_API_KEY="..."
# optional
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

```python
from ukg_sdk.providers import OpenAIProvider
provider = OpenAIProvider()
```

### Azure OpenAI

```bash
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"  # your deployment name
# optional
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```

```python
from ukg_sdk.providers import AzureOpenAIProvider
provider = AzureOpenAIProvider()
```

### Anthropic

```bash
export ANTHROPIC_API_KEY="..."
# optional
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
export ANTHROPIC_VERSION="2023-06-01"
```

```python
from ukg_sdk.providers import AnthropicProvider
provider = AnthropicProvider()
```

---

## 3) Run the overlay

```python
from ukg_sdk import UKGOverlay
from ukg_sdk.providers import OpenAIProvider

ukg = UKGOverlay(provider=OpenAIProvider(), model="gpt-4.1-mini")

result = await ukg.run(
  query="Draft a SOC 2 audit evidence request list for access control.",
  user_id="kevin",
  meta={"pillar": "PL-002", "axis2": "SOC2", "date": "2026-01-05"},
)
print(result["tier"])
print(result["coordinate"])
print(result["answer"])
```

### Tier override

If you want to force deeper or shallower execution:

```python
result = await ukg.run(query="...", tier_override="T4")
```

---

## 4) 17-axis coordinate resolver

The default resolver is deterministic and accepts:
- `pillar` (e.g., `PL-001`)
- `axis2` (e.g., `NAICS`, `PSC`, `SOC2`, etc.)
- `date` (e.g., `2026-01-05`)

You can also provide explicit `axisN` values:

```python
meta = {"axis1": "PL-001", "axis2": "NAICS", "axis13": "2026.01.05"}
```

To enforce catalog validation, instantiate your own resolver:

```python
from ukg_sdk.coordinates17 import CoordinateResolver17

resolver = CoordinateResolver17(
  axis2_catalog_xlsx="path/to/AXIS2.xlsx",
  pillar_catalog_xlsx="path/to/PL1_107.xlsx",
  strict_validation=True,
)
ukg = UKGOverlay(provider=..., model=..., coordinate_resolver=resolver)
```

---

## 5) Memory adapters (Postgres / Redis)

### Postgres

Install extras:

```bash
pip install ".[postgres]"
```

Use:

```python
from ukg_sdk.memory import PostgresMemoryAdapter
mem = PostgresMemoryAdapter(dsn="postgresql://user:pass@localhost:5432/ukg")
ukg = UKGOverlay(provider=..., model=..., memory=mem)
```

### Redis

```bash
pip install ".[redis]"
```

```python
from ukg_sdk.memory import RedisMemoryAdapter
mem = RedisMemoryAdapter(url="redis://localhost:6379/0")
```

---

## 6) Compliance-grade audit storage

### File audit (default)

Writes append-only JSONL to:

`ukg_sdk/data/audit/ukg_audit.jsonl`

### Postgres audit

```bash
pip install ".[postgres]"
```

```python
from ukg_sdk.audit import PostgresAuditStore
audit = PostgresAuditStore(dsn="postgresql://user:pass@localhost:5432/ukg")
ukg = UKGOverlay(provider=..., model=..., audit=audit)
```

---

## 7) Wire KA registry JSON → execution map

The registry provides KA metadata, but **execution handlers** are what make KAs “real”.

You can register your own handler:

```python
from ukg_sdk.ka.executor import KAExecutionResult

def my_ka_handler(ctx):
    # ctx.input, ctx.state, ctx.memory, ctx.audit available
    return KAExecutionResult(ok=True, output={"result": "hello"})

ukg.executor.register("KA-011", my_ka_handler)
```

The SDK ships a minimal set of built-in handlers (KA-004, KA-005, KA-113, KA-001, KA-019, KA-056).
Everything else is a stub until you register a handler.

---

## 8) Where to plug your full TruthEngine

Your project already has:
- workflow v2.5 (Truth17 + TruthEngine)
- TruthEngine v7.3 JSON/YAML configs

The intended pattern is:

1. Parse query → route tier (KA-113)
2. Execute KAs according to workflow tier
3. At Truth checkpoints, call TruthEngine modules:
   - TruthGate / TruthLink / TruthMemory / TruthCore (as you define them)
4. Commit validated knowledge → memory tiers (short/long/archive)
5. Write audit events for every gate + commit

v0.2.0 lays the **SDK scaffolding** for those hooks without forcing a single monolithic implementation.
