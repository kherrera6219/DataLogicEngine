"""Encrypted, signed, all-or-nothing coordinated backup and restore primitives."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import shutil
import tempfile
from typing import Any, Protocol
import uuid
import zipfile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


BACKUP_MANIFEST_SCHEMA_VERSION = "1.0.0"
PORTABLE_ARCHIVE_MAGIC = b"DLEBACKUP1\n"
ARCHIVE_TAG_BYTES = 16
STREAM_CHUNK_BYTES = 1024 * 1024


class CoordinatedBackupError(RuntimeError):
    """Redaction-safe coordinated backup or restore failure."""


@dataclass(frozen=True, slots=True)
class BackupComponent:
    name: str
    schema_version: str
    service_version: str
    source_revision: str
    item_count: int
    logical_size_bytes: int
    dependencies: tuple[str, ...] = ()
    outstanding_work: int = 0
    disposable_state: tuple[str, ...] = ()


class CoordinatedStoreAdapter(Protocol):
    """Store-native export/restore contract used by the coordinator."""

    def export(self, destination: Path) -> BackupComponent: ...

    def restore(self, source: Path, isolated_root: Path) -> None: ...

    def verify_restore(
        self,
        isolated_root: Path,
        component: BackupComponent,
    ) -> Mapping[str, Any]: ...


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _derive_keys(recovery_secret: str, salt: bytes) -> tuple[bytes, bytes]:
    normalized = str(recovery_secret or "").encode("utf-8")
    if len(normalized) < 12:
        raise CoordinatedBackupError("portable_recovery_secret_too_short")
    key_material = hashlib.scrypt(
        normalized,
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=64,
    )
    return key_material[:32], key_material[32:]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(STREAM_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _component_files(root: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    return files


def _safe_archive_member(member: zipfile.ZipInfo) -> bool:
    path = Path(member.filename.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        return False
    unix_mode = (member.external_attr >> 16) & 0o170000
    return unix_mode != 0o120000


def _encrypt_file(source: Path, destination: Path, recovery_secret: str) -> dict[str, str]:
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    encryption_key, _ = _derive_keys(recovery_secret, salt)
    header = {
        "cipher": "AES-256-GCM",
        "kdf": "scrypt-n16384-r8-p1",
        "nonce": nonce.hex(),
        "salt": salt.hex(),
        "tag": "appended-16-bytes",
        "version": 1,
    }
    header_line = _canonical_json(header) + b"\n"
    encryptor = Cipher(algorithms.AES(encryption_key), modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data(PORTABLE_ARCHIVE_MAGIC + header_line)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        with source.open("rb") as readable, temporary.open("wb") as writable:
            writable.write(PORTABLE_ARCHIVE_MAGIC)
            writable.write(header_line)
            for chunk in iter(lambda: readable.read(STREAM_CHUNK_BYTES), b""):
                writable.write(encryptor.update(chunk))
            writable.write(encryptor.finalize())
            writable.write(encryptor.tag)
            writable.flush()
            os.fsync(writable.fileno())
        os.replace(temporary, destination)
    except Exception as exc:
        raise CoordinatedBackupError("portable_backup_encryption_failed") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return header


def _decrypt_file(source: Path, destination: Path, recovery_secret: str) -> None:
    try:
        total_size = source.stat().st_size
        with source.open("rb") as readable:
            if readable.readline() != PORTABLE_ARCHIVE_MAGIC:
                raise CoordinatedBackupError("portable_backup_header_invalid")
            header_line = readable.readline()
            header = json.loads(header_line)
            if header.get("cipher") != "AES-256-GCM" or header.get("version") != 1:
                raise CoordinatedBackupError("portable_backup_version_unsupported")
            salt = bytes.fromhex(str(header["salt"]))
            nonce = bytes.fromhex(str(header["nonce"]))
            encryption_key, _ = _derive_keys(recovery_secret, salt)
            ciphertext_start = readable.tell()
            ciphertext_bytes = total_size - ciphertext_start - ARCHIVE_TAG_BYTES
            if ciphertext_bytes < 0:
                raise CoordinatedBackupError("portable_backup_truncated")
            readable.seek(total_size - ARCHIVE_TAG_BYTES)
            tag = readable.read(ARCHIVE_TAG_BYTES)
            readable.seek(ciphertext_start)
            decryptor = Cipher(
                algorithms.AES(encryption_key),
                modes.GCM(nonce, tag),
            ).decryptor()
            decryptor.authenticate_additional_data(PORTABLE_ARCHIVE_MAGIC + header_line)
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            try:
                with temporary.open("wb") as writable:
                    remaining = ciphertext_bytes
                    while remaining:
                        chunk = readable.read(min(STREAM_CHUNK_BYTES, remaining))
                        if not chunk:
                            raise CoordinatedBackupError("portable_backup_truncated")
                        remaining -= len(chunk)
                        writable.write(decryptor.update(chunk))
                    writable.write(decryptor.finalize())
                    writable.flush()
                    os.fsync(writable.fileno())
                os.replace(temporary, destination)
            finally:
                temporary.unlink(missing_ok=True)
    except CoordinatedBackupError:
        raise
    except Exception as exc:
        raise CoordinatedBackupError("portable_backup_authentication_failed") from exc


class CoordinatedBackupCoordinator:
    """Create and restore one verified recovery set for all required stores."""

    def __init__(
        self,
        *,
        adapters: Mapping[str, CoordinatedStoreAdapter],
        product_version: str,
        migration_versions: Mapping[str, str],
        required_components: tuple[str, ...],
        compatibility_check: Callable[[Mapping[str, Any]], bool] | None = None,
        cross_store_verifier: Callable[[Path, Mapping[str, Any]], Mapping[str, Any]] | None = None,
    ) -> None:
        if set(adapters) != set(required_components):
            raise ValueError("backup_required_component_mismatch")
        self.adapters = dict(adapters)
        self.product_version = str(product_version)
        self.migration_versions = dict(migration_versions)
        self.required_components = tuple(required_components)
        self.compatibility_check = compatibility_check
        self.cross_store_verifier = cross_store_verifier

    def create_backup(
        self,
        destination_directory: str | Path,
        *,
        recovery_secret: str,
    ) -> dict[str, Any]:
        """Export every component, sign the manifest, encrypt, and re-verify."""

        destination = Path(destination_directory).expanduser().resolve()
        destination.mkdir(parents=True, exist_ok=True)
        backup_id = uuid.uuid4().hex
        staging = Path(tempfile.mkdtemp(prefix=f".dle-backup-{backup_id}-", dir=destination))
        plaintext_zip = staging / "recovery-set.zip"
        archive = destination / f"datalogic-{backup_id}.dlebackup"
        try:
            salt = secrets.token_bytes(16)
            _, signing_key = _derive_keys(recovery_secret, salt)
            components: dict[str, Any] = {}
            for name in sorted(self.adapters):
                component_root = staging / "components" / name
                component_root.mkdir(parents=True, exist_ok=False)
                component = self.adapters[name].export(component_root)
                if component.name != name:
                    raise CoordinatedBackupError(f"backup_component_name_mismatch:{name}")
                files = _component_files(component_root)
                if not files:
                    raise CoordinatedBackupError(f"backup_component_empty:{name}")
                components[name] = {**asdict(component), "files": files}

            unsigned_manifest: dict[str, Any] = {
                "backup_id": backup_id,
                "created_at": datetime.now(UTC).isoformat(),
                "manifest_schema_version": BACKUP_MANIFEST_SCHEMA_VERSION,
                "migration_versions": self.migration_versions,
                "product_version": self.product_version,
                "required_components": sorted(self.required_components),
                "components": components,
                "portable_encryption": True,
                "machine_bound_key_required": False,
                "automatic_downgrade": False,
                "signing_salt": salt.hex(),
            }
            signature = hmac.new(
                signing_key,
                _canonical_json(unsigned_manifest),
                hashlib.sha256,
            ).hexdigest()
            manifest = {**unsigned_manifest, "signature": signature}
            (staging / "manifest.json").write_text(
                json.dumps(manifest, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            with zipfile.ZipFile(plaintext_zip, "w", zipfile.ZIP_DEFLATED) as zipped:
                zipped.write(staging / "manifest.json", "manifest.json")
                for path in sorted((staging / "components").rglob("*")):
                    if path.is_file():
                        zipped.write(path, path.relative_to(staging).as_posix())
            _encrypt_file(plaintext_zip, archive, recovery_secret)
            self.inspect_archive(archive, recovery_secret=recovery_secret)
            return {
                "artifact_path": str(archive),
                "backup_id": backup_id,
                "component_count": len(components),
                "encrypted": True,
                "integrity_verified": True,
                "size_bytes": archive.stat().st_size,
                "sha256": _sha256_file(archive),
            }
        except CoordinatedBackupError:
            archive.unlink(missing_ok=True)
            raise
        except Exception as exc:
            archive.unlink(missing_ok=True)
            raise CoordinatedBackupError("coordinated_backup_failed") from exc
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def inspect_archive(
        self,
        archive: str | Path,
        *,
        recovery_secret: str,
    ) -> dict[str, Any]:
        """Authenticate and verify every archived component without restoring it."""

        archive_path = Path(archive).expanduser().resolve()
        temporary_root = Path(tempfile.mkdtemp(prefix=".dle-inspect-"))
        plaintext = temporary_root / "recovery-set.zip"
        try:
            _decrypt_file(archive_path, plaintext, recovery_secret)
            with zipfile.ZipFile(plaintext, "r") as zipped:
                if any(not _safe_archive_member(member) for member in zipped.infolist()):
                    raise CoordinatedBackupError("backup_archive_path_invalid")
                zipped.extractall(temporary_root / "extracted")
            return self._verify_extracted(temporary_root / "extracted", recovery_secret)
        finally:
            shutil.rmtree(temporary_root, ignore_errors=True)

    def restore_to_clean_root(
        self,
        archive: str | Path,
        target_root: str | Path,
        *,
        recovery_secret: str,
        post_swap_validator: Callable[[Path], bool] | None = None,
    ) -> dict[str, Any]:
        """Restore into isolation, verify, then swap while retaining the prior root."""

        target = Path(target_root).expanduser().resolve()
        parent = target.parent
        parent.mkdir(parents=True, exist_ok=True)
        restore_id = uuid.uuid4().hex
        working = Path(tempfile.mkdtemp(prefix=f".dle-restore-{restore_id}-", dir=parent))
        extracted = working / "extracted"
        isolated = working / "isolated-root"
        plaintext = working / "recovery-set.zip"
        prior = parent / f".{target.name}.previous-{restore_id}"
        swapped = False
        try:
            _decrypt_file(Path(archive).expanduser().resolve(), plaintext, recovery_secret)
            with zipfile.ZipFile(plaintext, "r") as zipped:
                if any(not _safe_archive_member(member) for member in zipped.infolist()):
                    raise CoordinatedBackupError("backup_archive_path_invalid")
                zipped.extractall(extracted)
            manifest = self._verify_extracted(extracted, recovery_secret)
            if self.compatibility_check is not None and not self.compatibility_check(manifest):
                raise CoordinatedBackupError("backup_restore_incompatible")
            isolated.mkdir(parents=True, exist_ok=False)
            restore_checks: dict[str, Any] = {}
            for name in sorted(self.adapters):
                component_data = manifest["components"][name]
                component = BackupComponent(
                    **{key: component_data[key] for key in BackupComponent.__dataclass_fields__}
                )
                self.adapters[name].restore(extracted / "components" / name, isolated)
                result = dict(self.adapters[name].verify_restore(isolated, component))
                if result.get("status") != "pass":
                    raise CoordinatedBackupError(f"backup_restore_verification_failed:{name}")
                restore_checks[name] = result
            cross_store = (
                dict(self.cross_store_verifier(isolated, manifest))
                if self.cross_store_verifier is not None
                else {"status": "pass"}
            )
            if cross_store.get("status") != "pass":
                raise CoordinatedBackupError("backup_cross_store_verification_failed")

            if target.exists():
                os.replace(target, prior)
            os.replace(isolated, target)
            swapped = True
            if post_swap_validator is not None and not post_swap_validator(target):
                raise CoordinatedBackupError("backup_post_restore_validation_failed")
            return {
                "backup_id": manifest["backup_id"],
                "restored_root": str(target),
                "prior_root": str(prior) if prior.exists() else None,
                "component_checks": restore_checks,
                "cross_store": cross_store,
                "status": "restored",
            }
        except CoordinatedBackupError:
            if swapped:
                failed = parent / f".{target.name}.failed-{restore_id}"
                if target.exists():
                    os.replace(target, failed)
                if prior.exists():
                    os.replace(prior, target)
                shutil.rmtree(failed, ignore_errors=True)
            raise
        except Exception as exc:
            raise CoordinatedBackupError("coordinated_restore_failed") from exc
        finally:
            shutil.rmtree(working, ignore_errors=True)

    def _verify_extracted(
        self,
        extracted: Path,
        recovery_secret: str,
    ) -> dict[str, Any]:
        manifest_path = extracted / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CoordinatedBackupError("backup_manifest_invalid") from exc
        signature = str(manifest.pop("signature", ""))
        try:
            salt = bytes.fromhex(str(manifest["signing_salt"]))
        except (KeyError, ValueError) as exc:
            raise CoordinatedBackupError("backup_manifest_invalid") from exc
        _, signing_key = _derive_keys(recovery_secret, salt)
        expected = hmac.new(
            signing_key,
            _canonical_json(manifest),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise CoordinatedBackupError("backup_manifest_signature_invalid")
        manifest["signature"] = signature
        required = set(manifest.get("required_components") or [])
        if required != set(self.required_components):
            raise CoordinatedBackupError("backup_component_set_invalid")
        components = manifest.get("components")
        if not isinstance(components, dict) or set(components) != required:
            raise CoordinatedBackupError("backup_component_set_invalid")
        for name, component in components.items():
            root = extracted / "components" / name
            for file_entry in component.get("files") or []:
                relative = Path(str(file_entry.get("path", "")).replace("\\", "/"))
                if relative.is_absolute() or ".." in relative.parts:
                    raise CoordinatedBackupError("backup_manifest_path_invalid")
                path = root / relative
                if not path.is_file():
                    raise CoordinatedBackupError(f"backup_component_file_missing:{name}")
                if path.stat().st_size != int(file_entry.get("size_bytes", -1)):
                    raise CoordinatedBackupError(f"backup_component_size_mismatch:{name}")
                if _sha256_file(path) != file_entry.get("sha256"):
                    raise CoordinatedBackupError(f"backup_component_hash_mismatch:{name}")
        return manifest
