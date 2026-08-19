"""Run bounded, content-free provider-refresh availability checks.

The validator uses credentials already present in the local environment or
``.env`` file. It never prints or records a credential or provider response
body. The resulting report is suitable for CP19-M source-level evidence; it
does not claim installed, signed-artifact, corpus, or human acceptance.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


PROVIDER_MODELS = {
    "google": "gemini-3.7-flash",
    "openai": "gpt-5.6-sol",
}
PROMPT = "Reply with the single word ONLINE."
DEFAULT_REPORT = (
    REPO_ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-19"
    / "cu-2-provider-acceptance"
    / "provider-refresh-live-acceptance.json"
)


def _credential_for_provider(provider: str) -> tuple[str | None, str]:
    if provider == "openai":
        value = os.getenv("OPENAI_API_KEY")
    else:
        value = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    return value, "existing_local_environment" if value else "missing"


def _git_state() -> dict[str, Any]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return {"head_commit": head, "working_tree_clean": not bool(status.strip())}


def _build_adapter(provider: str, api_key: str, timeout_seconds: float) -> Any:
    if provider == "openai":
        from backend.llm_gateway.providers.openai import OpenAIProvider

        return OpenAIProvider(api_key=api_key, timeout_seconds=timeout_seconds)

    from backend.llm_gateway.providers.google import GoogleProvider

    return GoogleProvider(api_key=api_key, timeout_seconds=timeout_seconds)


async def _close_adapter(adapter: Any) -> None:
    close_result = adapter.close()
    if asyncio.iscoroutine(close_result):
        await close_result


async def _run_case(
    *,
    provider: str,
    model: str,
    api_key: str,
    credential_source: str,
    timeout_seconds: float,
    max_tokens: int,
) -> dict[str, Any]:
    from backend.llm_gateway.provider_errors import classify_provider_failure
    from backend.llm_gateway.provider_manifest import provider_model_definition

    contract = provider_model_definition(provider, model)
    reasoning_effort = contract.reasoning_effort
    result: dict[str, Any] = {
        "provider": provider,
        "requested_model": model,
        "credential_source": credential_source,
        "credential_present": True,
        "credential_or_response_content_recorded": False,
        "reasoning_effort": reasoning_effort,
        "status": "fail",
    }
    if provider == "openai" and reasoning_effort != "high":
        result["failure_class"] = "contract_mismatch"
        return result

    adapter = _build_adapter(provider, api_key, timeout_seconds)
    started = perf_counter()
    try:
        response = await asyncio.wait_for(
            adapter.complete(
                messages=[{"role": "user", "content": PROMPT}],
                model=model,
                temperature=0.0,
                max_tokens=max_tokens,
            ),
            timeout=timeout_seconds,
        )
        text = str(response.text or "")
        usage = response.usage if isinstance(response.usage, dict) else {}
        result.update(
            {
                "status": "pass" if text.strip() else "fail",
                "response_model": str(response.model or ""),
                "response_text_length": len(text),
                "response_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "latency_ms": round((perf_counter() - started) * 1000, 2),
                "usage": {
                    "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
                    "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
                    "total_tokens": int(usage.get("total_tokens", 0) or 0),
                },
            }
        )
        if not text.strip():
            result["failure_class"] = "malformed_response"
    except Exception as exc:  # noqa: BLE001 - normalize arbitrary provider SDK failures
        classified = classify_provider_failure(exc)
        result.update(
            {
                "latency_ms": round((perf_counter() - started) * 1000, 2),
                "failure_class": classified.failure_class.value,
            }
        )
    finally:
        await _close_adapter(adapter)
    return result


async def _run(args: argparse.Namespace) -> int:
    load_dotenv(REPO_ROOT / ".env")
    providers = list(PROVIDER_MODELS) if args.provider == "both" else [args.provider]
    cases: list[dict[str, Any]] = []

    for provider in providers:
        api_key, credential_source = _credential_for_provider(provider)
        if not api_key:
            cases.append(
                {
                    "provider": provider,
                    "requested_model": PROVIDER_MODELS[provider],
                    "credential_source": credential_source,
                    "credential_present": False,
                    "credential_or_response_content_recorded": False,
                    "status": "fail",
                    "failure_class": "credential_missing",
                }
            )
            continue
        cases.append(
            await _run_case(
                provider=provider,
                model=PROVIDER_MODELS[provider],
                api_key=api_key,
                credential_source=credential_source,
                timeout_seconds=args.timeout_seconds,
                max_tokens=args.max_tokens,
            )
        )

    passed = all(case["status"] == "pass" for case in cases)
    report = {
        "schema_version": "dle.cp19m-provider-refresh-live-acceptance.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "source_live_provider_pass" if passed else "source_live_provider_fail",
        "source_binding": _git_state(),
        "prompt_sha256": hashlib.sha256(PROMPT.encode("utf-8")).hexdigest(),
        "provider_calls_bounded_to": len(providers),
        "secrets_or_response_content_recorded": False,
        "cases": cases,
        "limitations": [
            "Source-level availability only; no installed or signed-artifact acceptance is claimed.",
            "No corpus, blinded-human, accessibility, lifecycle, recovery, pilot, or soak gate is closed.",
        ],
    }
    report_path = (REPO_ROOT / args.report_path).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for case in cases:
        suffix = case.get("failure_class") or f"{case.get('latency_ms', 0)} ms"
        print(f"{case['provider']} / {case['requested_model']}: {case['status']} ({suffix})")
    print(f"Report: {report_path.relative_to(REPO_ROOT)}")
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["both", "google", "openai"], default="both")
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument(
        "--report-path",
        default=str(DEFAULT_REPORT.relative_to(REPO_ROOT)),
    )
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
