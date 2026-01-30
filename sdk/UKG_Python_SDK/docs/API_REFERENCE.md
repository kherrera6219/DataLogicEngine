# UKG SDK v0.3.1 — Developer API Reference

## `ukg_sdk.UKGOverlay`

**Purpose:** main orchestrator that mounts the UKG overlay around an LLM provider.

```python
class UKGOverlay:
  def __init__(
      self,
      *,
      provider: LLMProvider,
      model: str,
      registry: KARegistry | None = None,
      registry_path: str | Path | None = None,
      data_dir: str | Path | None = None,
      coordinate_resolver: CoordinateResolver17 | None = None,
      memory: MemoryAdapter | None = None,
      audit: AuditStore | None = None,
      actor: str = "ukg-sdk",
  )

  async def run(
      self,
      *,
      query: str,
      user_id: str = "anonymous",
      session_id: str | None = None,
      meta: dict | None = None,
      temperature: float = 0.2,
      max_tokens: int = 1024,
      tier_override: str | None = None,
  ) -> dict
```

**Return:** dict with:

- `ok: bool`
- `answer: str` (if ok)
- `coordinate: str` (17-axis compact string)
- `tier: str`
- `layers: list[str]`
- `trace: list[dict]`
- `explainability: dict | None`

---

## Providers (`ukg_sdk.providers.*`)

### `LLMProvider`

```python
class LLMProvider(ABC):
  async def complete(
    self,
    *,
    messages: list[dict[str,str]],
    model: str,
    temperature: float = 0.2,
    max_tokens: int = 1024,
  ) -> LLMResponse
```

### Built-in providers

- `OpenAIProvider` (env: `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`)
- `AzureOpenAIProvider` (env: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, optional `AZURE_OPENAI_DEPLOYMENT`)
- `AnthropicProvider` (env: `ANTHROPIC_API_KEY`, optional `ANTHROPIC_BASE_URL`)

---

## KA system (`ukg_sdk.ka.*`)

### Registry

- `KAInfo` — metadata model
- `KARegistry` — `items: dict[str, KAInfo]`

Loaders:

- `ukg_sdk.ka.registry.load_registry_from_json(path)`
- `ukg_sdk.ka.registry.load_default_registry(package_data_dir)`

### Execution hooks

```python
class KAExecutor:
  def register(self, ka_id: str, handler: KAHandler) -> None
  def execute(
    self,
    ka_id: str,
    *,
    input: dict,
    layer: str,
    state: dict,
    memory: Any = None,
    audit: Any = None,
    strict: bool = True,
  ) -> KAExecutionResult
```

Types:

- `KAExecutionContext` (ka, input, layer, state, memory, audit)
- `KAExecutionResult` (ok, output, next_layer, veto_reason)

Built-in handlers:

- `KA-004` validation/normalization
- `KA-005` query classification
- `KA-113` tier router
- `KA-001` Algorithm of Thought (light)
- `KA-019` synthesis (light)
- `KA-056` explainability (light)

---

## 17-axis coordinates (`ukg_sdk.coordinates17`)

- `UKGCoordinate17` — container with `as_compact_string()`
- `CoordinateResolver17.resolve(meta: dict) -> UKGCoordinate17`

---

## Memory adapters (`ukg_sdk.memory.*`)

Base:

- `MemoryAdapter`
- `MemoryRecord`

Implementations:

- `InMemoryMemoryAdapter`
- `PostgresMemoryAdapter` (requires `asyncpg`)
- `RedisMemoryAdapter` (requires `redis` asyncio)

---

## Audit storage (`ukg_sdk.audit.*`)

Base:

- `AuditStore`
- `AuditEvent`

Implementations:

- `FileAuditStore` (JSONL, hash-chained)
- `PostgresAuditStore` (requires `asyncpg`)

---

## Workflow & Truth Engine (`ukg_sdk.truth_engine.*`, `ukg_sdk.workflow.*`)

### `TruthEngine`

**Purpose:** Composite engine combining properties of Gate, Core, Link, and Memory.

```python
class TruthEngine:
    def evaluate(self, claim: str, context: dict | None = None) -> TruthResult
    def summarize(self) -> dict
```

### `WorkflowRunner`

**Purpose:** Load and execute KA pipelines defined in `workflow.json`.

```python
class WorkflowRunner:
    @classmethod
    def load_default(cls) -> WorkflowRunner
    def choose_tier(self, complexity_score: float) -> ComplexityTier
    def run_local_stub(self, query: str, tier: ComplexityTier) -> WorkflowResult
```
