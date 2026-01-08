from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone

from .base import MemoryAdapter, MemoryRecord

try:
    import asyncpg  # type: ignore
except Exception:  # pragma: no cover
    asyncpg = None


CREATE_TABLE_SQL = """CREATE TABLE IF NOT EXISTS ukg_memory (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  tier TEXT NOT NULL,
  coordinate TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


class PostgresMemoryAdapter(MemoryAdapter):
    """Postgres-backed memory adapter (asyncpg).

    Environment-friendly defaults (you can pass a DSN).
    """

    def __init__(self, dsn: str):
        if asyncpg is None:
            raise ImportError("asyncpg is required for PostgresMemoryAdapter. Install with: pip install ukg-sdk[postgres]")
        self.dsn = dsn
        self._pool = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(dsn=self.dsn, min_size=1, max_size=10)
        async with self._pool.acquire() as conn:
            await conn.execute(CREATE_TABLE_SQL)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def get(self, key: str) -> Optional[MemoryRecord]:
        if self._pool is None:
            await self.connect()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT key, value, tier, coordinate, created_at, updated_at FROM ukg_memory WHERE key=$1", key)
            if not row:
                return None
            return MemoryRecord(
                key=row["key"],
                value=dict(row["value"]),
                tier=row["tier"],
                coordinate=row["coordinate"],
                created_at=row["created_at"].isoformat(),
                updated_at=row["updated_at"].isoformat(),
            )

    async def set(self, record: MemoryRecord) -> None:
        if self._pool is None:
            await self.connect()
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            await conn.execute(
                """                INSERT INTO ukg_memory(key, value, tier, coordinate, created_at, updated_at)
                VALUES($1, $2, $3, $4, COALESCE($5, now()), $6)
                ON CONFLICT (key)
                DO UPDATE SET value=EXCLUDED.value, tier=EXCLUDED.tier, coordinate=EXCLUDED.coordinate, updated_at=EXCLUDED.updated_at
                """,
                record.key,
                record.value,
                record.tier,
                record.coordinate,
                now,
                now,
            )
