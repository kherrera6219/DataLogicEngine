
import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Optional

import httpx
from dotenv import load_dotenv

# Load env vars first
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(".env")


def _normalize_env_aliases() -> None:
    """Normalize common env var aliases used in older local files."""
    if not os.getenv("ANTHROPIC_API_KEY") and os.getenv("anthropic_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = os.getenv("anthropic_API_KEY", "")
    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")


def _set_status(key_name: str) -> str:
    return "SET" if os.getenv(key_name) else "MISSING"


def _clean_error(err: Exception) -> str:
    raw = str(err).strip().replace("\n", " ")
    return raw if len(raw) < 240 else f"{raw[:240]}..."


@dataclass
class ProviderCheck:
    provider: str
    ok: bool
    tested_model: Optional[str] = None
    detail: str = ""
    model_sample: str = ""


async def check_openai() -> ProviderCheck:
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"Checking OpenAI Key: {_set_status('OPENAI_API_KEY')}")
    if not api_key:
        return ProviderCheck("OpenAI", False, detail="OPENAI_API_KEY missing.")

    try:
        from openai import AsyncOpenAI
    except ImportError:
        return ProviderCheck("OpenAI", False, detail="openai package not installed.")

    client = AsyncOpenAI(api_key=api_key, timeout=30.0)
    requested_model = os.getenv("OPENAI_TEST_MODEL", "gpt-5.2")
    candidate_models = [
        requested_model,
        "gpt-5.2",
        "gpt-5.2-pro",
        "gpt-5-mini",
        "gpt-4.1",
    ]

    visible_models = []
    try:
        page = await client.models.list()
        visible_models = [m.id for m in page.data if m.id.startswith(("gpt-", "o"))][:12]
    except Exception as e:
        print(f"   > OpenAI model list warning: {_clean_error(e)}")

    last_error = "No model probe attempted."
    for model_id in candidate_models:
        try:
            await client.responses.create(
                model=model_id,
                input="Return exactly: pong",
                max_output_tokens=16,
            )
            return ProviderCheck(
                "OpenAI",
                True,
                tested_model=model_id,
                detail="Responses API generation succeeded.",
                model_sample=", ".join(visible_models[:8]),
            )
        except Exception as e:
            last_error = _clean_error(e)
            if "does not exist" in last_error.lower() or "model_not_found" in last_error.lower():
                continue
            if "max_output_tokens" in last_error.lower():
                # Keep trying fallback models; this check should use >=16.
                continue

    return ProviderCheck(
        "OpenAI",
        False,
        tested_model=requested_model,
        detail=f"Generation failed across candidate models. Last error: {last_error}",
        model_sample=", ".join(visible_models[:8]),
    )


async def check_google() -> ProviderCheck:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    print(
        "Checking Google/Gemini Key: "
        f"GEMINI_API_KEY={_set_status('GEMINI_API_KEY')}, GOOGLE_API_KEY={_set_status('GOOGLE_API_KEY')}"
    )
    if not api_key:
        return ProviderCheck("Google Gemini", False, detail="GEMINI_API_KEY/GOOGLE_API_KEY missing.")

    try:
        from google import genai
    except ImportError:
        return ProviderCheck("Google Gemini", False, detail="google-genai package not installed.")

    try:
        client = genai.Client(api_key=api_key)
        available = []
        try:
            for model in client.models.list():
                name = getattr(model, "name", "")
                if "gemini" in name.lower():
                    available.append(name.replace("models/", ""))
                if len(available) >= 20:
                    break
        except Exception as e:
            print(f"   > Gemini model list warning: {_clean_error(e)}")

        requested_model = os.getenv("GEMINI_TEST_MODEL", "gemini-3-pro")
        candidates = [
            requested_model,
            "gemini-3-pro",
            "gemini-3-pro-latest",
            "gemini-3-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
        ]

        last_error = "No model probe attempted."
        for model_id in candidates:
            try:
                client.models.generate_content(
                    model=model_id,
                    contents="Reply with one word: pong",
                )
                return ProviderCheck(
                    "Google Gemini",
                    True,
                    tested_model=model_id,
                    detail="generate_content succeeded.",
                    model_sample=", ".join(available[:8]),
                )
            except Exception as e:
                last_error = _clean_error(e)
                if "not found" in last_error.lower() or "invalid model" in last_error.lower():
                    continue

        return ProviderCheck(
            "Google Gemini",
            False,
            tested_model=requested_model,
            detail=f"Generation failed across candidate models. Last error: {last_error}",
            model_sample=", ".join(available[:8]),
        )
    except Exception as e:
        return ProviderCheck("Google Gemini", False, detail=f"Client error: {_clean_error(e)}")


async def check_anthropic() -> ProviderCheck:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"Checking Anthropic Key: {_set_status('ANTHROPIC_API_KEY')}")
    if not api_key:
        return ProviderCheck("Anthropic", False, detail="ANTHROPIC_API_KEY missing.")

    base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    version = os.getenv("ANTHROPIC_VERSION", "2023-06-01")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": version,
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        available = []
        try:
            list_resp = await client.get(f"{base_url}/v1/models", headers=headers)
            list_resp.raise_for_status()
            items = (list_resp.json() or {}).get("data", [])
            available = [m.get("id", "") for m in items if m.get("id")]
        except Exception as e:
            print(f"   > Anthropic model list warning: {_clean_error(e)}")

        requested_model = os.getenv("ANTHROPIC_TEST_MODEL", "claude-opus-4-5")
        candidates = [
            requested_model,
            "claude-opus-4-5",
            "claude-opus-4-1",
            "claude-opus-4",
            "claude-sonnet-4-5",
            "claude-sonnet-4",
            "claude-3-5-sonnet-latest",
        ]

        if available:
            # Try available models first while preserving preferred order where possible.
            preferred = [m for m in candidates if m in available]
            remaining = [m for m in available if m.startswith("claude-")]
            candidates = preferred + remaining

        last_error = "No model probe attempted."
        for model_id in candidates:
            try:
                payload = {
                    "model": model_id,
                    "max_tokens": 32,
                    "messages": [{"role": "user", "content": "Reply with one word: pong"}],
                }
                resp = await client.post(f"{base_url}/v1/messages", headers=headers, json=payload)
                resp.raise_for_status()
                return ProviderCheck(
                    "Anthropic",
                    True,
                    tested_model=model_id,
                    detail="Messages API generation succeeded.",
                    model_sample=", ".join(available[:8]),
                )
            except Exception as e:
                last_error = _clean_error(e)
                if "not found" in last_error.lower() or "invalid model" in last_error.lower():
                    continue

        return ProviderCheck(
            "Anthropic",
            False,
            tested_model=requested_model,
            detail=f"Generation failed across candidate models. Last error: {last_error}",
            model_sample=", ".join(available[:8]),
        )


async def main() -> int:
    _normalize_env_aliases()
    print("=== Provider API Verification ===\n")

    checks = [
        await check_openai(),
        await check_google(),
        await check_anthropic(),
    ]

    print("\n=== Summary ===")
    all_ok = True
    for result in checks:
        status = "PASS" if result.ok else "FAIL"
        print(f"{result.provider}: {status}")
        if result.tested_model:
            print(f"  Model: {result.tested_model}")
        if result.detail:
            print(f"  Detail: {result.detail}")
        if result.model_sample:
            print(f"  Visible models (sample): {result.model_sample}")
        if not result.ok:
            all_ok = False

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
