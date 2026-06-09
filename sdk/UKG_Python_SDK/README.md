# UKG SDK (Python) — v0.5.0

This SDK is the **public API overlay** for the UKG/USKD system:

- 🔁 **Wire KA registry JSON → live execution map** (register handlers, run pipelines)
- 🧠 **17-axis coordinate resolver** (deterministic coordinate generation + optional catalog validation)
- 🗄️ **Memory adapters**: In-memory (default), Postgres, Redis
- 🔐 **Compliance-grade audit storage**: append-only, hash-chained logs (File or Postgres)
- 🤖 **LLM providers**: OpenAI, Azure OpenAI, Anthropic, Google Gemini, Ollama (local; no API key required)
- 📦 Bundled canonical configs + datasets in `ukg_sdk/data/`:
  - workflow v2.5 (Truth17 + TruthEngine)
  - TruthEngine v7.3 config tree
  - registries (KA 1–114, AXIS2, PL1–107)
  - OpenAPI v3.1/3.2 reference specs

## Install (local)

```bash
pip install -e .
pip install -e ".[postgres,redis,registries]"
```

## Quick start (Overlay → Provider → Answer)

```python
import asyncio
from ukg_sdk import UKGOverlay
from ukg_sdk.providers import OpenAIProvider

async def main():
    provider = OpenAIProvider()  # reads OPENAI_API_KEY
    ukg = UKGOverlay(provider=provider, model="gpt-4.1-mini")

    result = await ukg.run(
        query="Explain how the UKG tier router decides what to run.",
        user_id="kevin",
        meta={"pillar": "PL-001", "axis2": "NAICS", "date": "2026-01-05"},
    )
    print(result["answer"])
    print(result["tier"], result["coordinate"])

asyncio.run(main())
```

- `docs/API_REFERENCE.md` — developer API reference

## Local Ollama provider

`OllamaProvider` targets a locally running [Ollama](https://ollama.com) instance. No API key required.

```python
import asyncio
from ukg_sdk.providers import OllamaProvider

async def main():
    provider = OllamaProvider(
        base_url="http://localhost:11434",   # default
        default_model="gemma4:12b",          # T1 primary
        fast_model="gemma4:latest",          # T0 ultra-light
    )

    # Check which models are available
    health = await provider.health_check()
    print(health["models"])          # ['gemma4:latest', 'gemma4:12b', ...]

    # Single-turn chat (same interface as all other providers)
    response = await provider.chat_async(
        messages=[{"role": "user", "content": "Explain REST in one sentence."}],
        model="gemma4:latest",
        max_tokens=256,
    )
    print(response.text)

    # JSON generation with optional key validation
    data = await provider.generate_json_async(
        prompt='Return {"name": "Alice", "age": 30} as JSON.',
        schema={"required": ["name", "age"]},
    )
    print(data)   # {"name": "Alice", "age": 30}

asyncio.run(main())
```

**Thinking models** (`gemma4:12b`, `qwen3:14b`) emit a reasoning chain before the visible content. Always request `max_tokens >= 512` for these models or the content field may be empty.

## Included Data And Reference Specs

The installable SDK package includes runtime data under `ukg_sdk/data/`, including workflow, TruthEngine, registry, taxonomy, DSQP template, and OpenAPI reference files. The repository also keeps original reference spreadsheets under `docs/specs/` for maintainers; those documents are not package data in the default wheel.
