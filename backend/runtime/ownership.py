"""Installation identity and exclusive process runtime ownership."""

from __future__ import annotations

import getpass
import json
import os
import platform
import time
import uuid
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import BinaryIO


class RuntimeOwnershipError(RuntimeError):
    """Raised when another process or invalid metadata blocks ownership."""


def _windows_session_id() -> str:
    if os.name != "nt":
        return str(os.getsid(0)) if hasattr(os, "getsid") else "unknown"
    try:
        import ctypes

        session_id = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(session_id))
        return str(session_id.value) if ok else "unknown"
    except Exception:
        return "unknown"


@dataclass(frozen=True, slots=True)
class InstallationIdentity:
    installation_id: str
    product: str
    version: str
    owner: str
    platform: str

    @classmethod
    def load(cls, path: Path) -> "InstallationIdentity":
        """Load and validate an existing installation identity without writing."""
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            identity = cls(**payload)
        except Exception as exc:
            raise RuntimeOwnershipError("installation_identity_invalid") from exc
        if identity.product != "DataLogicEngine":
            raise RuntimeOwnershipError("installation_identity_product_mismatch")
        if identity.owner != getpass.getuser():
            raise RuntimeOwnershipError("installation_identity_owner_mismatch")
        return identity

    @classmethod
    def new(cls, *, version: str) -> "InstallationIdentity":
        """Prepare a new identity in memory so startup can lock before persisting it."""
        return cls(
            installation_id=uuid.uuid4().hex,
            product="DataLogicEngine",
            version=version,
            owner=getpass.getuser(),
            platform=platform.platform(),
        )

    def persist(self, path: Path) -> None:
        """Persist this identity atomically after runtime ownership is acquired."""
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        try:
            temporary.write_text(json.dumps(asdict(self), sort_keys=True), encoding="utf-8")
            os.replace(temporary, path)
            if os.name != "nt":
                path.chmod(0o600)
            else:
                from backend.security.windows_acl import ensure_restricted_user_acl

                ensure_restricted_user_acl(path, required=True)
        finally:
            temporary.unlink(missing_ok=True)

    @classmethod
    def load_or_create(cls, path: Path, *, version: str) -> "InstallationIdentity":
        if path.exists():
            return cls.load(path)

        identity = cls.new(version=version)
        identity.persist(path)
        return identity


class RuntimeLock:
    """OS-released exclusive lock with diagnostic owner metadata."""

    def __init__(self, path: Path, identity: InstallationIdentity) -> None:
        self.path = path
        self.identity = identity
        self._file: BinaryIO | None = None
        self.owner_record: dict | None = None

    @property
    def acquired(self) -> bool:
        return self._file is not None

    def acquire(self) -> None:
        if self._file is not None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = self.path.open("a+b")
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"\0")
            lock_file.flush()
        lock_file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            owner = self._read_owner_record()
            lock_file.close()
            detail = owner.get("pid") if isinstance(owner, dict) else "unknown"
            raise RuntimeOwnershipError(f"runtime_already_owned:pid={detail}") from exc

        self._file = lock_file
        if os.name == "nt":
            from backend.security.windows_acl import ensure_restricted_user_acl

            ensure_restricted_user_acl(self.path, required=True)
        self.owner_record = {
            "pid": os.getpid(),
            "windows_session_id": _windows_session_id(),
            "owner": getpass.getuser(),
            "installation_id": self.identity.installation_id,
            "product_version": self.identity.version,
            "acquired_at_unix": time.time(),
        }
        self._write_owner_record(self.owner_record)

    def release(self) -> None:
        lock_file = self._file
        if lock_file is None:
            return
        try:
            lock_file.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            lock_file.close()
            self._file = None

    def _metadata_path(self) -> Path:
        return self.path.with_suffix(".owner.json")

    def _read_owner_record(self) -> dict | None:
        metadata_path = self._metadata_path()
        try:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _write_owner_record(self, payload: dict) -> None:
        metadata_path = self._metadata_path()
        temporary = metadata_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        os.replace(temporary, metadata_path)
        if os.name != "nt":
            metadata_path.chmod(0o600)
        else:
            from backend.security.windows_acl import ensure_restricted_user_acl

            ensure_restricted_user_acl(metadata_path, required=True)


class RuntimeOwnership:
    """Resolve installation identity and own one runtime lock."""

    def __init__(self, runtime_root: Path, *, version: str) -> None:
        self.runtime_root = runtime_root
        self.identity_path = runtime_root / "installation.json"
        self.lock_path = runtime_root / "runtime.lock"
        self.version = version
        self.identity: InstallationIdentity | None = None
        self.lock: RuntimeLock | None = None

    def prepare(self, *, initial_version: str | None = None) -> InstallationIdentity:
        """Resolve identity without mutating disk; persistence occurs under the lock."""
        if self.identity is not None:
            return self.identity
        if self.identity_path.exists():
            self.identity = InstallationIdentity.load(self.identity_path)
        else:
            self.identity = InstallationIdentity.new(
                version=str(initial_version or self.version),
            )
        return self.identity

    def acquire(self) -> None:
        identity_existed = self.identity_path.exists()
        self.identity = self.prepare()
        self.lock = RuntimeLock(self.lock_path, self.identity)
        self.lock.acquire()
        try:
            if identity_existed:
                persisted = InstallationIdentity.load(self.identity_path)
                if persisted != self.identity:
                    raise RuntimeOwnershipError("installation_identity_changed_before_lock")
            else:
                self.identity.persist(self.identity_path)
        except Exception:
            self.lock.release()
            raise

    def release(self) -> None:
        if self.lock is not None:
            self.lock.release()

    def record_completed_upgrade(self, target_version: str) -> InstallationIdentity:
        """Atomically advance the retained identity only after migrations pass."""
        if self.identity is None or self.lock is None or not self.lock.acquired:
            raise RuntimeOwnershipError("installation_upgrade_requires_runtime_lock")
        normalized = str(target_version or "").strip()
        if not normalized:
            raise RuntimeOwnershipError("installation_upgrade_target_invalid")
        upgraded = replace(self.identity, version=normalized)
        temporary = self.identity_path.with_suffix(".upgrade.tmp")
        try:
            temporary.write_text(
                json.dumps(asdict(upgraded), sort_keys=True),
                encoding="utf-8",
            )
            os.replace(temporary, self.identity_path)
            if os.name != "nt":
                self.identity_path.chmod(0o600)
            else:
                from backend.security.windows_acl import ensure_restricted_user_acl

                ensure_restricted_user_acl(self.identity_path, required=True)
        finally:
            temporary.unlink(missing_ok=True)
        self.identity = upgraded
        self.lock.identity = upgraded
        return upgraded
