# UKG SDK (Python) — v2.3.1

This SDK is the **public API overlay** for the UKG/USKD system:

- 🔁 **Wire KA registry JSON → live execution map** (register handlers, run pipelines)
- 🧠 **17-axis coordinate resolver** (deterministic coordinate generation + optional catalog validation)
- 🗄️ **Memory adapters**: In-memory (default), Postgres, Redis
- 🔐 **Compliance-grade audit storage**: append-only, hash-chained logs (File or Postgres)
- 🤖 **LLM providers**: OpenAI, Azure OpenAI, Anthropic (HTTP-based; no extra SDKs required)
- 📦 Bundled canonical configs + datasets in `ukg_sdk/data/`:
  - workflow v2.5 (Truth17 + TruthEngine)
  - TruthEngine v7.3 config tree
  - registries (KA 1–114, AXIS2, PL1–107)
  - OpenAPI v3.2 spec

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

## Next docs

- `docs/HOWTO.md` — practical setup (providers, Postgres/Redis, audit, KA handlers)
- `docs/API_REFERENCE.md` — developer API reference


## Included Specs (Full Source Documents)

The SDK bundle includes the original source documents (PDF/DOCM/XLSX) under `docs/specs/` so you can ship the **complete** reference material alongside the executable overlay.
