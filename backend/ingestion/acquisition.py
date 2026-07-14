"""Bounded, local-only acquisition into app-owned ingestion staging."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
import shutil
import stat
from typing import Iterable


_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
_WINDOWS_REPARSE_POINT = 0x0400


class AcquisitionLimitError(ValueError):
    """A stable failure raised before an acquisition can exceed its budget."""


@dataclass(frozen=True, slots=True)
class AcquiredFile:
    source_path: Path
    staged_path: Path
    relative_path: str
    size_bytes: int
    sha256: str
    detected_type: str


@dataclass(frozen=True, slots=True)
class RejectedAcquisitionFile:
    source_path: Path
    relative_path: str
    reason: str


@dataclass(slots=True)
class AcquisitionResult:
    files: list[AcquiredFile] = field(default_factory=list)
    rejected: list[RejectedAcquisitionFile] = field(default_factory=list)
    total_bytes: int = 0


class SecureAcquisitionSession:
    """Copy approved files into one bounded app-owned staging directory."""

    def __init__(
        self,
        *,
        ingestion_id: str,
        source: str | os.PathLike[str],
        staging_root: str | os.PathLike[str],
        supported_extensions: Iterable[str],
        max_file_bytes: int,
        max_total_bytes: int,
        max_files: int,
        recursive: bool,
    ) -> None:
        safe_id = str(ingestion_id or "").strip()
        if not safe_id or not all(character.isalnum() or character in "-_" for character in safe_id):
            raise ValueError("unsafe_ingestion_id")
        raw_source = os.fspath(source).strip()
        if raw_source.startswith(("\\\\", "//")):
            raise ValueError("network_ingestion_source_not_allowed")
        # Keep the lexical path so link/reparse checks cannot be bypassed by
        # resolving the selected source before it is inspected.
        self.source = Path(os.path.abspath(Path(source).expanduser()))
        self.staging_root = Path(staging_root).expanduser().resolve()
        self.session_root = (self.staging_root / safe_id).resolve()
        if self.session_root.parent != self.staging_root:
            raise ValueError("unsafe_ingestion_staging_path")
        self.source_root = self.session_root / "source"
        self.supported_extensions = {
            value.lower() if str(value).startswith(".") else f".{str(value).lower()}"
            for value in supported_extensions
        }
        self.max_file_bytes = self._positive_limit(max_file_bytes, "max_file_bytes")
        self.max_total_bytes = self._positive_limit(max_total_bytes, "max_total_bytes")
        self.max_files = self._positive_limit(max_files, "max_files")
        self.recursive = bool(recursive)

    @staticmethod
    def _positive_limit(value: int, name: str) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid_{name}") from exc
        if parsed <= 0:
            raise ValueError(f"invalid_{name}")
        return parsed

    @staticmethod
    def validate_relative_path(relative_path: Path) -> str:
        """Return a normalized safe relative path or fail closed."""
        candidate = Path(relative_path)
        if candidate.is_absolute() or not candidate.parts:
            raise ValueError("unsafe_ingestion_filename")
        safe_parts: list[str] = []
        for part in candidate.parts:
            if part in {"", ".", ".."}:
                raise ValueError("unsafe_ingestion_filename")
            if part.endswith((" ", ".")) or any(ord(character) < 32 for character in part):
                raise ValueError("unsafe_ingestion_filename")
            if any(character in '<>:"|?*' for character in part):
                raise ValueError("unsafe_ingestion_filename")
            stem = part.split(".", 1)[0].upper()
            if stem in _WINDOWS_RESERVED_NAMES:
                raise ValueError("unsafe_ingestion_filename")
            safe_parts.append(part)
        return Path(*safe_parts).as_posix()

    @staticmethod
    def _is_link_or_reparse(path: Path) -> bool:
        try:
            metadata = path.lstat()
        except OSError:
            return True
        if stat.S_ISLNK(metadata.st_mode):
            return True
        return bool(getattr(metadata, "st_file_attributes", 0) & _WINDOWS_REPARSE_POINT)

    def _source_chain_has_link_or_reparse(self, path: Path) -> bool:
        """Reject links or reparse points in the source and every parent."""
        for candidate in (path, *path.parents):
            if candidate == Path(candidate.anchor):
                break
            if self._is_link_or_reparse(candidate):
                return True
        return False

    def acquire(self) -> AcquisitionResult:
        """Stage and content-check every supported file without following links."""
        result = AcquisitionResult()
        try:
            if not self.source.exists():
                raise ValueError("ingestion_source_not_found")
            if self._source_chain_has_link_or_reparse(self.source):
                raise ValueError("ingestion_source_link_or_reparse_not_allowed")
            if self.source.is_file():
                candidates = [(self.source, Path(self.source.name))]
            elif self.source.is_dir():
                candidates = list(self._walk_directory(self.source, Path()))
            else:
                raise ValueError("ingestion_source_special_file_not_allowed")

            self.source_root.mkdir(parents=True, exist_ok=False)
            for source_path, relative_path in candidates:
                if source_path.suffix.lower() not in self.supported_extensions:
                    continue
                if self._is_link_or_reparse(source_path):
                    result.rejected.append(
                        RejectedAcquisitionFile(
                            source_path=source_path,
                            relative_path=relative_path.as_posix(),
                            reason="link_or_reparse_not_allowed",
                        )
                    )
                    continue
                safe_relative = self.validate_relative_path(relative_path)
                if len(result.files) + 1 > self.max_files:
                    raise AcquisitionLimitError("ingestion_file_count_exceeded")
                try:
                    source_size = source_path.stat().st_size
                except OSError:
                    result.rejected.append(
                        RejectedAcquisitionFile(source_path, safe_relative, "file_stat_failed")
                    )
                    continue
                if source_size <= 0:
                    result.rejected.append(
                        RejectedAcquisitionFile(source_path, safe_relative, "empty_file")
                    )
                    continue
                if source_size > self.max_file_bytes:
                    result.rejected.append(
                        RejectedAcquisitionFile(source_path, safe_relative, "file_size_exceeded")
                    )
                    continue
                if result.total_bytes + source_size > self.max_total_bytes:
                    raise AcquisitionLimitError("ingestion_total_bytes_exceeded")

                staged_path = (self.source_root / Path(safe_relative)).resolve()
                if os.path.commonpath((str(self.source_root), str(staged_path))) != str(self.source_root):
                    raise ValueError("unsafe_ingestion_staging_path")
                staged_path.parent.mkdir(parents=True, exist_ok=True)
                size_bytes, digest = self._copy_bounded(source_path, staged_path)
                detected_type, rejection = self._detect_type(staged_path, source_path.suffix.lower())
                if rejection:
                    staged_path.unlink(missing_ok=True)
                    result.rejected.append(
                        RejectedAcquisitionFile(source_path, safe_relative, rejection)
                    )
                    continue
                result.files.append(
                    AcquiredFile(
                        source_path=source_path.resolve(),
                        staged_path=staged_path,
                        relative_path=safe_relative,
                        size_bytes=size_bytes,
                        sha256=digest,
                        detected_type=detected_type,
                    )
                )
                result.total_bytes += size_bytes
            return result
        except Exception:
            self.cleanup()
            raise

    def _walk_directory(self, directory: Path, relative: Path):
        with os.scandir(directory) as entries:
            for entry in sorted(entries, key=lambda item: item.name.casefold()):
                path = Path(entry.path)
                child_relative = relative / entry.name
                if entry.is_symlink() or self._is_link_or_reparse(path):
                    yield path, child_relative
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if self.recursive:
                        yield from self._walk_directory(path, child_relative)
                    continue
                if entry.is_file(follow_symlinks=False):
                    yield path, child_relative

    def _copy_bounded(self, source: Path, destination: Path) -> tuple[int, str]:
        digest = hashlib.sha256()
        copied = 0
        try:
            with source.open("rb") as source_handle, destination.open("xb") as destination_handle:
                while chunk := source_handle.read(1024 * 1024):
                    copied += len(chunk)
                    if copied > self.max_file_bytes:
                        raise AcquisitionLimitError("ingestion_file_bytes_exceeded")
                    destination_handle.write(chunk)
                    digest.update(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return copied, digest.hexdigest()

    @staticmethod
    def _detect_type(path: Path, suffix: str) -> tuple[str, str | None]:
        with path.open("rb") as handle:
            sample = handle.read(8192)
        if suffix == ".pdf":
            return ("pdf", None) if sample.startswith(b"%PDF-") else ("unknown", "content_type_mismatch")
        if suffix == ".docx":
            return ("docx", None) if sample.startswith(b"PK\x03\x04") else ("unknown", "content_type_mismatch")
        if b"\x00" in sample:
            return "unknown", "binary_text_content"
        prohibited = sum(
            1 for value in sample if value < 32 and value not in {9, 10, 13}
        )
        if sample and prohibited / len(sample) > 0.01:
            return "unknown", "binary_text_content"
        return "text", None

    def cleanup(self) -> None:
        """Remove only this validated acquisition staging directory."""
        if self.session_root.parent != self.staging_root:
            raise RuntimeError("unsafe_ingestion_staging_cleanup")
        shutil.rmtree(self.session_root, ignore_errors=True)
