"""Adversarial stdio MCP fixture used only by Phase 11 tests."""

from __future__ import annotations

import json
import subprocess
import sys
import time


def send(payload) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def result(message, payload) -> None:
    send({"jsonrpc": "2.0", "id": message.get("id"), "result": payload})


def main() -> None:
    for raw_line in sys.stdin:
        message = json.loads(raw_line)
        method = message.get("method")
        params = message.get("params") or {}
        if method == "initialize":
            result(
                message,
                {
                    "protocolVersion": "2025-11-25",
                    "serverInfo": {"name": "phase11-fixture", "version": "1.0.0"},
                    "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                },
            )
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            result(
                message,
                {
                    "tools": [
                        {"name": "echo", "description": "Echo", "inputSchema": {"type": "object"}},
                        {"name": "delay", "description": "Delay", "inputSchema": {"type": "object"}},
                        {"name": "oversized", "description": "Oversized", "inputSchema": {"type": "object"}},
                        {"name": "malformed", "description": "Malformed", "inputSchema": {"type": "object"}},
                        {"name": "spawn_child", "description": "Spawn", "inputSchema": {"type": "object"}},
                    ]
                },
            )
        elif method == "resources/list":
            result(message, {"resources": [{"uri": "fixture://real", "name": "Real fixture"}]})
        elif method == "prompts/list":
            result(message, {"prompts": [{"name": "fixture_prompt", "description": "Fixture prompt"}]})
        elif method == "resources/read":
            result(message, {"contents": [{"uri": params.get("uri"), "text": "real resource"}]})
        elif method == "prompts/get":
            result(
                message,
                {"messages": [{"role": "user", "content": {"type": "text", "text": "real prompt"}}]},
            )
        elif method == "tools/call":
            name = params.get("name")
            if name == "echo":
                result(message, {"content": [{"type": "text", "text": "real echo"}]})
            elif name == "delay":
                time.sleep(5)
                result(message, {"content": [{"type": "text", "text": "late"}]})
            elif name == "oversized":
                result(message, {"content": [{"type": "text", "text": "x" * 100_000}]})
            elif name == "malformed":
                sys.stdout.write("not-json-rpc\n")
                sys.stdout.flush()
            elif name == "spawn_child":
                child = subprocess.Popen(
                    [sys.executable, "-c", "import time; time.sleep(60)"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                result(message, {"content": [{"type": "text", "text": str(child.pid)}]})
            else:
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "error": {"code": -32601, "message": "unknown tool"},
                    }
                )


if __name__ == "__main__":
    main()
