#!/usr/bin/env python3
"""Verify the Electron window, preload, navigation, and IPC security contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "frontend/electron/main.ts"
PRELOAD = ROOT / "frontend/electron/preload.ts"
PACKAGED_RENDERER = ROOT / "frontend/out/index.html"
PACKAGED_MAIN = ROOT / "frontend/dist-electron/main.js"
PACKAGED_PRELOAD = ROOT / "frontend/dist-electron/preload.js"


def browser_window_blocks(source: str) -> list[str]:
    blocks: list[str] = []
    for match in re.finditer(r"new\s+BrowserWindow\s*\(\s*\{", source):
        start = match.start()
        end = source.find("\n  });", start)
        blocks.append(source[start : end if end >= 0 else start + 1200])
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-packaged-renderer", action="store_true")
    args = parser.parse_args()
    main_source = MAIN.read_text(encoding="utf-8")
    preload_source = PRELOAD.read_text(encoding="utf-8")
    findings: list[dict[str, object]] = []
    required_preferences = {
        "nodeIntegration": "false",
        "contextIsolation": "true",
        "sandbox": "true",
        "webSecurity": "true",
    }
    windows = browser_window_blocks(main_source)
    for index, block in enumerate(windows, 1):
        for preference, value in required_preferences.items():
            if not re.search(rf"\b{preference}\s*:\s*{value}\b", block):
                findings.append(
                    {
                        "rule": "browser-window-preference",
                        "window": index,
                        "expected": f"{preference}: {value}",
                    }
                )
    for pattern, rule in (
        (r"webContents\.on\(['\"]will-navigate['\"]", "navigation-allowlist"),
        (r"setWindowOpenHandler", "new-window-denial"),
        (r"contextBridge\.exposeInMainWorld", "narrow-preload-bridge"),
    ):
        if not re.search(pattern, main_source + preload_source):
            findings.append({"rule": rule, "expected": "present"})
    if re.search(r"exposeInMainWorld\([^\n]+ipcRenderer", preload_source):
        findings.append({"rule": "raw-ipc-renderer-exposure"})
    for token, rule in (
        ("senderUrl.startsWith", "prefix-based-ipc-origin-check"),
        ("consumePathCapability", "path-capability-consumption"),
        ("cancel-desktop-operation", "ipc-cancellation"),
        ("IPC_CHANNEL_TIMEOUTS", "per-channel-timeout"),
        ("responseDataRecord", "ipc-return-schema"),
        ("safeStorage.encryptString", "electron-secret-protection"),
        ("secureWindowsAclBestEffort", "electron-secret-acl"),
    ):
        present = token in main_source + preload_source
        if rule == "prefix-based-ipc-origin-check":
            if present:
                findings.append({"rule": rule, "expected": "absent"})
        elif not present:
            findings.append({"rule": rule, "expected": "present"})

    if args.require_packaged_renderer:
        artifacts = (PACKAGED_RENDERER, PACKAGED_MAIN, PACKAGED_PRELOAD)
        newest_source = max(MAIN.stat().st_mtime, PRELOAD.stat().st_mtime)
        for artifact in artifacts:
            if not artifact.exists():
                findings.append({"rule": "packaged-renderer-artifact", "path": str(artifact.relative_to(ROOT))})
            elif artifact.stat().st_mtime < newest_source:
                findings.append({"rule": "stale-packaged-renderer-artifact", "path": str(artifact.relative_to(ROOT))})

    main_channels = set(re.findall(r"ipcMain\.handle\(\s*['\"]([^'\"]+)", main_source))
    preload_channels = set(re.findall(r"invokeWithTimeout\(\s*['\"]([^'\"]+)", preload_source))
    for channel in sorted(preload_channels - main_channels):
        findings.append({"rule": "preload-channel-without-handler", "channel": channel})
    for match in re.finditer(r"ipcMain\.handle\(\s*['\"]([^'\"]+)[\s\S]*?\n\}\);", main_source):
        channel, block = match.group(1), match.group(0)
        if "assertTrustedIpc" not in block:
            findings.append({"rule": "ipc-sender-validation", "channel": channel})

    result = {
        "windows": len(windows),
        "main_channels": len(main_channels),
        "preload_channels": len(preload_channels),
        "packaged_renderer_required": args.require_packaged_renderer,
        "findings": findings,
        "passed": not findings,
    }
    print(json.dumps(result, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
