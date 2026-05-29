"""Local-first raw document ingestion into SQL knowledge nodes and Chroma."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
from typing import Any, Iterable
from uuid import uuid4

from extensions import db
from models import KnowledgeGraphNode


SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".yaml", ".yml", ".log"}
PROMPT_INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?(system|developer)\s+prompt", re.IGNORECASE),
    re.compile(r"BEGIN\s+PROMPT", re.IGNORECASE),
    re.compile(r"END\s+PROMPT", re.IGNORECASE),
    re.compile(r"<\s*script\b", re.IGNORECASE),
)


@dataclass
class RejectedFile:
    path: str
    reason: str


@dataclass
class IngestedChunk:
    node_uid: str
    node_id: str
    source_path: str
    chunk_index: int
    chunk_count: int
    content_hash: str
    chunk_hash: str
    indexed: bool


@dataclass
class IngestionResult:
    ingestion_id: str
    source: str
    files_scanned: int = 0
    files_ingested: int = 0
    files_rejected: int = 0
    chunks_created: int = 0
    chunks_indexed: int = 0
    rejected_files: list[RejectedFile] = field(default_factory=list)
    chunks: list[IngestedChunk] = field(default_factory=list)
    manifest_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rejected_files"] = [asdict(item) for item in self.rejected_files]
        payload["chunks"] = [asdict(item) for item in self.chunks]
        return payload


class LocalKnowledgeIngestionService:
    """Ingest local files into the app-owned knowledge corpus."""

    def __init__(
        self,
        *,
        rag_service: Any | None = None,
        chunk_size: int = 1200,
        max_file_bytes: int = 10 * 1024 * 1024,
        supported_extensions: Iterable[str] | None = None,
    ) -> None:
        self.rag_service = rag_service
        self.chunk_size = chunk_size
        self.max_file_bytes = max_file_bytes
        self.supported_extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in (supported_extensions or SUPPORTED_TEXT_EXTENSIONS)
        }

    def ingest_path(
        self,
        source_path: str | os.PathLike[str],
        *,
        recursive: bool = True,
        tenant_id: str | None = None,
        source_label: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IngestionResult:
        """Ingest one local file or directory into SQL and vector search."""
        source = Path(source_path).expanduser().resolve()
        result = IngestionResult(ingestion_id=str(uuid4()), source=str(source))
        files = list(self._iter_files(source, recursive=recursive))

        if not files:
            result.rejected_files.append(RejectedFile(path=str(source), reason="No supported files found"))
            result.files_rejected = 1
            self._write_manifest(result)
            return result

        rag = self._get_rag_service()
        for file_path in files:
            result.files_scanned += 1
            text, rejection = self._extract_text(file_path)
            if rejection:
                result.files_rejected += 1
                result.rejected_files.append(RejectedFile(path=str(file_path), reason=rejection))
                continue

            cleaned_text, injection_hits = self._scrub_text(text)
            chunks = rag.chunk_text(cleaned_text, chunk_size=self.chunk_size) if rag else [cleaned_text]
            chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
            if not chunks:
                result.files_rejected += 1
                result.rejected_files.append(RejectedFile(path=str(file_path), reason="No text after normalization"))
                continue

            content_hash = self._sha256(cleaned_text)
            created_for_file = 0
            for index, chunk in enumerate(chunks):
                chunk_hash = self._sha256(chunk)
                uid = f"ki_{chunk_hash[:24]}"
                existing = KnowledgeGraphNode.query.filter_by(uid=uid).first()
                if existing:
                    continue

                node_id = f"KI-{chunk_hash[:16]}"
                title = f"{source_label or file_path.name} [{index + 1}/{len(chunks)}]"
                node_metadata = {
                    **(metadata or {}),
                    "ingestion_id": result.ingestion_id,
                    "source": "local_file_ingestion",
                    "source_path": str(file_path),
                    "file_name": file_path.name,
                    "mime_type": mimetypes.guess_type(file_path.name)[0] or "text/plain",
                    "content_hash": content_hash,
                    "chunk_hash": chunk_hash,
                    "chunk_index": index,
                    "chunk_count": len(chunks),
                    "prompt_injection_markers_removed": injection_hits,
                    "ingested_at": datetime.now(UTC).isoformat(),
                }
                node = KnowledgeGraphNode(
                    uid=uid,
                    node_id=node_id,
                    node_type="ingested_document_chunk",
                    label=title,
                    title=title,
                    description=chunk[:500],
                    content=chunk,
                    content_type="text/plain",
                    node_metadata=node_metadata,
                    tenant_id=tenant_id,
                )
                db.session.add(node)
                created_for_file += 1
                result.chunks_created += 1

                indexed = bool(
                    rag
                    and rag.ingest_knowledge_node(
                        uid,
                        chunk,
                        "ingested_document_chunk",
                        {
                            **node_metadata,
                            "node_id": node_id,
                            "title": title,
                            "tenant_id": tenant_id or "",
                        },
                    )
                )
                if indexed:
                    result.chunks_indexed += 1
                result.chunks.append(
                    IngestedChunk(
                        node_uid=uid,
                        node_id=node_id,
                        source_path=str(file_path),
                        chunk_index=index,
                        chunk_count=len(chunks),
                        content_hash=content_hash,
                        chunk_hash=chunk_hash,
                        indexed=indexed,
                    )
                )

            if created_for_file:
                result.files_ingested += 1

        db.session.commit()
        self._write_manifest(result)
        return result

    def _get_rag_service(self) -> Any | None:
        if self.rag_service is not None:
            return self.rag_service
        try:
            from backend.services.rag_service import get_rag_service

            self.rag_service = get_rag_service()
            return self.rag_service
        except Exception:
            return None

    def _iter_files(self, source: Path, *, recursive: bool) -> Iterable[Path]:
        if source.is_file():
            if source.suffix.lower() in self.supported_extensions:
                yield source
            return
        if not source.is_dir():
            return
        iterator = source.rglob("*") if recursive else source.glob("*")
        for file_path in iterator:
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                yield file_path

    def _extract_text(self, file_path: Path) -> tuple[str, str | None]:
        try:
            size = file_path.stat().st_size
        except OSError as exc:
            return "", f"Cannot stat file: {exc}"
        if size <= 0:
            return "", "Empty file"
        if size > self.max_file_bytes:
            return "", f"File exceeds max size of {self.max_file_bytes} bytes"
        try:
            return file_path.read_text(encoding="utf-8"), None
        except UnicodeDecodeError:
            try:
                return file_path.read_text(encoding="utf-8-sig"), None
            except UnicodeDecodeError:
                return file_path.read_text(encoding="latin-1"), None
        except OSError as exc:
            return "", f"Cannot read file: {exc}"

    @staticmethod
    def _scrub_text(text: str) -> tuple[str, list[str]]:
        hits: list[str] = []
        cleaned = text.replace("\x00", "")
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(cleaned):
                hits.append(pattern.pattern)
                cleaned = pattern.sub("[removed]", cleaned)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned).strip()
        return cleaned, hits

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _manifest_dir() -> Path:
        explicit = os.environ.get("DATALOGIC_INGESTION_MANIFEST_DIR")
        if explicit:
            return Path(explicit).expanduser().resolve()
        settings_path = os.environ.get("DATALOGIC_STORAGE_SETTINGS_PATH")
        if settings_path:
            return Path(settings_path).expanduser().resolve().parent / "ingestion" / "manifests"
        return Path.cwd() / "reports" / "ingestion"

    def _write_manifest(self, result: IngestionResult) -> None:
        manifest_dir = self._manifest_dir()
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / f"{result.ingestion_id}.json"
        result.manifest_path = str(manifest_path)
        manifest_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
