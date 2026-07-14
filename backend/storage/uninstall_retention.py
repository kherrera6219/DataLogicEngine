"""Explicit retained-data choices for installer and uninstaller workflows."""

from __future__ import annotations

from collections.abc import Callable
import json
import os
from pathlib import Path
import shutil
import uuid


UNINSTALL_DATA_CHOICES = ("keep", "export_then_delete", "delete")


class UninstallRetentionError(RuntimeError):
    """Redaction-safe retained-data disposition failure."""


def _validated_runtime_root(runtime_root: str | Path) -> Path:
    root = Path(runtime_root).expanduser().resolve()
    identity_path = root / "installation.json"
    try:
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        raise UninstallRetentionError("uninstall_runtime_identity_invalid") from exc
    if identity.get("product") != "DataLogicEngine" or not identity.get("installation_id"):
        raise UninstallRetentionError("uninstall_runtime_identity_invalid")
    if root == Path(root.anchor) or root == Path.home().resolve():
        raise UninstallRetentionError("uninstall_runtime_root_unsafe")
    return root


def apply_uninstall_data_choice(
    runtime_root: str | Path,
    choice: str,
    *,
    backup_path: str | Path | None = None,
    backup_verifier: Callable[[Path], bool] | None = None,
) -> dict[str, object]:
    """Apply one owner-selected data disposition without claiming SSD erasure."""
    root = _validated_runtime_root(runtime_root)
    normalized = str(choice or "").strip().lower()
    if normalized not in UNINSTALL_DATA_CHOICES:
        raise UninstallRetentionError("uninstall_data_choice_invalid")
    if normalized == "keep":
        return {
            "choice": normalized,
            "runtime_root": str(root),
            "data_retained": True,
            "secure_delete_guaranteed": False,
        }
    if normalized == "export_then_delete":
        archive = Path(backup_path or "").expanduser().resolve()
        if not archive.is_file() or backup_verifier is None:
            raise UninstallRetentionError("verified_uninstall_backup_required")
        try:
            verified = bool(backup_verifier(archive))
        except Exception as exc:
            raise UninstallRetentionError("uninstall_backup_verification_failed") from exc
        if not verified:
            raise UninstallRetentionError("uninstall_backup_verification_failed")

    staged = root.parent / f".{root.name}.delete-{uuid.uuid4().hex}"
    try:
        os.replace(root, staged)
        shutil.rmtree(staged)
    except Exception as exc:
        if staged.exists() and not root.exists():
            os.replace(staged, root)
        raise UninstallRetentionError("uninstall_data_delete_failed") from exc
    return {
        "choice": normalized,
        "runtime_root": str(root),
        "data_retained": False,
        "backup_path": str(Path(backup_path).resolve()) if backup_path else None,
        "secure_delete_guaranteed": False,
        "residual_risk": "ssd_snapshot_or_backup_remnants_may_persist",
    }
