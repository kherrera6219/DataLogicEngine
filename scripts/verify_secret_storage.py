#!/usr/bin/env python3
"""Verify high-confidence desktop and provider secret-storage boundaries."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "backend/security/dpapi_store.py": (
        ("CryptProtectData", True, "DPAPI encryption support"),
        ("CryptUnprotectData", True, "DPAPI decryption support"),
    ),
    "backend/llm_gateway/api.py": (
        ("include_key=True", False, "provider API key returned by an API response"),
    ),
    "models.py": (
        ('dpapi:v1:', True, "DPAPI-protected provider credentials"),
        ("'default-secret'", False, "default provider credential encryption secret"),
    ),
    "backend/storage/runtime_settings.py": (
        ("PROTECTED_CLOUD_SETTING_KEYS", True, "protected internal-service credential fields"),
        ("DPAPI_SETTING_PREFIX", True, "DPAPI marker for protected storage settings"),
        ("ensure_restricted_user_acl", True, "settings-file ACL enforcement"),
    ),
    "backend/security/desktop_local_auth.py": (
        ("desktop_install_secret.txt", False, "plaintext desktop install-secret file"),
        ("write_text(generated", False, "plaintext desktop install-secret write"),
        ("ensure_restricted_user_acl", True, "desktop install-secret ACL enforcement"),
        ("DESKTOP_INSTALL_SECRET_ROTATION_DAYS", True, "desktop install-secret rotation policy"),
    ),
    "frontend/electron/main.ts": (
        ("loadOrCreatePlainSecretFile", False, "plaintext Electron secret-file helper"),
        ("safeStorage.encryptString", True, "Electron Windows protected storage"),
        ("migrateAndLoadPackagedDotenvSecrets", True, "packaged plaintext dotenv migration"),
        ("secureWindowsAclBestEffort", True, "Electron per-user ACL enforcement"),
    ),
    "backend/security/encryption_manager.py": (
        ("Add to .env:", False, "generated KEK written to logs"),
    ),
}


def main() -> int:
    findings: list[dict[str, object]] = []
    for relative, rules in CHECKS.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for token, required, description in rules:
            present = token in source
            if present != required:
                findings.append(
                    {
                        "file": relative,
                        "rule": description,
                        "token": token,
                        "expected": "present" if required else "absent",
                    }
                )
    result = {"findings": findings, "passed": not findings}
    print(json.dumps(result, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
