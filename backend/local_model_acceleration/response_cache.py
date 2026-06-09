"""
Exact-match SQLite response cache for local model responses.

Cache key construction
----------------------
The cache key is a SHA-256 hex digest of the pipe-separated concatenation of:

    model_name | provider_type | task_type | mode | run_ukg_pipeline
    | temperature (2 dp) | max_tokens | sha256(system)[:16]
    | sha256(prompt)[:16] | sha256(rag_context)[:16]

Including the RAG-context hash is critical: the same user query submitted
twice with different knowledge-base chunks retrieved must NOT collide.

Thread safety
-------------
SQLite in WAL mode allows concurrent readers.  Writes are serialised through
a threading.Lock.  ``check_same_thread=False`` is safe because we never share
a Connection object across threads — we open a new connection per call.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS llm_response_cache (
    cache_key        TEXT    PRIMARY KEY,
    model_name       TEXT    NOT NULL,
    provider_type    TEXT    NOT NULL,
    task_type        TEXT    NOT NULL,
    prompt_sha256    TEXT    NOT NULL,
    rag_ctx_sha256   TEXT    NOT NULL,
    options_json     TEXT    NOT NULL,
    response         TEXT    NOT NULL,
    metadata_json    TEXT,
    created_at       TEXT    NOT NULL,
    expires_at       TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_expires_at ON llm_response_cache (expires_at);
"""


class ResponseCache:
    """Thread-safe SQLite-backed exact-match response cache."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = str(db_path)
        self._write_lock = threading.Lock()
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._write_lock, self._connect() as conn:
            conn.executescript(_SCHEMA_SQL)

    # ------------------------------------------------------------------
    # Cache key construction (static — callable without an instance)
    # ------------------------------------------------------------------

    @staticmethod
    def build_cache_key(
        model_name: str,
        provider_type: str,
        task_type: str,
        system: str | None,
        prompt: str,
        rag_context: str | None,
        options: dict[str, Any],
    ) -> str:
        """
        Build a deterministic SHA-256 cache key for this request.

        The key encodes every dimension that affects the model output so
        that two requests with identical user text but different RAG chunks
        never collide.
        """

        def _h(text: str) -> str:
            return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]

        parts = [
            model_name or "",
            provider_type or "",
            (task_type or "").lower(),
            str(options.get("mode", "")),
            str(bool(options.get("run_ukg_pipeline", True))),
            f"{float(options.get('temperature', 0.7)):.2f}",
            str(int(options.get("max_tokens", 1024) or 1024)),
            _h(system or ""),
            _h(prompt or ""),
            _h(rag_context or ""),
        ]
        composite = "|".join(parts)
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, cache_key: str) -> dict[str, Any] | None:
        """
        Return a cached response dict or ``None`` on miss / expiry.

        Expired rows are NOT deleted here (deleted lazily by
        ``delete_expired``).  The WHERE clause filters them out so they
        behave as misses.
        """
        try:
            with self._connect() as conn:
                row = conn.execute(
                    """
                    SELECT response, metadata_json, created_at
                    FROM   llm_response_cache
                    WHERE  cache_key = ?
                      AND  expires_at > strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                    """,
                    (cache_key,),
                ).fetchone()

            if row is None:
                return None

            metadata: dict = {}
            if row["metadata_json"]:
                try:
                    metadata = json.loads(row["metadata_json"])
                except Exception:
                    pass

            return {
                "response": row["response"],
                "metadata": metadata,
                "created_at": row["created_at"],
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("ResponseCache.get error (non-fatal): %s", exc)
            return None

    def set(
        self,
        *,
        cache_key: str,
        response: str,
        metadata: dict[str, Any] | None,
        ttl_days: int,
        model_name: str,
        provider_type: str,
        task_type: str,
        system: str | None,
        prompt: str,
        rag_context: str | None,
        options: dict[str, Any],
    ) -> None:
        """Insert or replace a cached response.  Silently ignores errors."""

        def _h(text: str) -> str:
            return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()

        now = datetime.now(UTC)
        expires_at = now + timedelta(days=max(1, ttl_days))
        try:
            with self._write_lock, self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO llm_response_cache
                        (cache_key, model_name, provider_type, task_type,
                         prompt_sha256, rag_ctx_sha256, options_json,
                         response, metadata_json, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cache_key,
                        model_name,
                        provider_type,
                        task_type,
                        _h(prompt or ""),
                        _h(rag_context or ""),
                        json.dumps(options, default=str),
                        response,
                        json.dumps(metadata or {}, default=str),
                        now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    ),
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("ResponseCache.set error (non-fatal): %s", exc)

    def delete_expired(self) -> int:
        """Remove expired rows and return the count deleted."""
        try:
            with self._write_lock, self._connect() as conn:
                cur = conn.execute(
                    "DELETE FROM llm_response_cache "
                    "WHERE expires_at <= strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"
                )
                return cur.rowcount
        except Exception as exc:  # noqa: BLE001
            logger.warning("ResponseCache.delete_expired error: %s", exc)
            return 0

    def clear_all(self) -> int:
        """Wipe the entire cache.  Returns the number of rows deleted."""
        try:
            with self._write_lock, self._connect() as conn:
                cur = conn.execute("DELETE FROM llm_response_cache")
                return cur.rowcount
        except Exception as exc:  # noqa: BLE001
            logger.warning("ResponseCache.clear_all error: %s", exc)
            return 0

    def stats(self) -> dict[str, Any]:
        """Return row counts and size information for monitoring."""
        try:
            with self._connect() as conn:
                total = conn.execute(
                    "SELECT COUNT(*) FROM llm_response_cache"
                ).fetchone()[0]
                active = conn.execute(
                    "SELECT COUNT(*) FROM llm_response_cache "
                    "WHERE expires_at > strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"
                ).fetchone()[0]
                expired = total - active
            import os
            size_bytes = os.path.getsize(self._db_path) if os.path.exists(self._db_path) else 0
            return {
                "total_rows": total,
                "active_rows": active,
                "expired_rows": expired,
                "db_size_bytes": size_bytes,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("ResponseCache.stats error: %s", exc)
            return {"total_rows": 0, "active_rows": 0, "expired_rows": 0, "db_size_bytes": 0}
