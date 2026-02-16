# DataLogicEngine LLM Model Matrix (2026-02)

This matrix is used by the gateway routing defaults and env overrides.

## Verified Provider Families

### OpenAI
- `gpt-5.2` (general high-quality default)
- `gpt-5.2-pro` (complex reasoning)
- `gpt-5-mini` (fast/cheap)
- `gpt-5-nano` (ultra-fast fallback)
- `o3-deep-research` (research-oriented workflows)

### Anthropic
- `claude-opus-4-6` (latest flagship family)
- `claude-opus-4-5`
- `claude-opus-4-1`
- `claude-sonnet-4-5` (balanced)
- `claude-sonnet-4`

### Google Gemini
- `gemini-2.5-pro` (default primary; broad availability)
- `gemini-2.5-flash` (default fast path)
- `gemini-3-pro` (optional when account access is enabled)
- `gemini-3-flash` (optional when account access is enabled)

## Gateway Env Overrides

The gateway now supports model selection via environment variables:

- `OPENAI_MODEL_PRIMARY`
- `OPENAI_MODEL_STANDARD`
- `OPENAI_MODEL_FAST`
- `OPENAI_MODEL_NANO`
- `OPENAI_MODEL_LONG_CONTEXT`
- `OPENAI_MODEL_RESEARCH`
- `GOOGLE_MODEL_PRIMARY`
- `GOOGLE_MODEL_FAST`
- `ANTHROPIC_MODEL_PRIMARY`

## Operational Recommendation

Run this before changing defaults:

```powershell
.venv\Scripts\python.exe .\scripts\verify_api_keys.py
```

That script performs live model probes against configured API keys and shows a sample of visible models per provider.

## Latest Live Probe Snapshot (2026-02-07)

Using current local keys in this repository environment:

- OpenAI probe succeeded with `gpt-5.2`
- Anthropic probe succeeded with `claude-opus-4-6`
- Gemini probe succeeded with `gemini-2.5-pro`

Use these as safe defaults unless your account visibility indicates newer/alternate IDs.
