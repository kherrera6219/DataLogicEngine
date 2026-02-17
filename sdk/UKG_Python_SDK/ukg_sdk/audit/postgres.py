from __future__ import annotations


from .base import AuditEvent, AuditStore

try:
    import asyncpg  # type: ignore
except Exception:  # pragma: no cover
    asyncpg = None


CREATE_TABLE_SQL = """CREATE TABLE IF NOT EXISTS ukg_audit_events (
  event_id TEXT PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL,
  kind TEXT NOT NULL,
  actor TEXT NOT NULL,
  session_id TEXT NOT NULL,
  ka_id TEXT NULL,
  layer TEXT NULL,
  coordinate TEXT NULL,
  payload JSONB NOT NULL,
  prev_hash TEXT NULL,
  hash TEXT NOT NULL
);
"""


class PostgresAuditStore(AuditStore):
    def __init__(self, dsn: str):
        if asyncpg is None:
            raise ImportError("asyncpg is required for PostgresAuditStore. Install with: pip install ukg-sdk[postgres]")
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

    async def append(self, event: AuditEvent) -> AuditEvent:
        if self._pool is None:
            await self.connect()
        # event.hash should already be set by caller if they want a chain;
        # if not, we accept it as-is.
        async with self._pool.acquire() as conn:
            await conn.execute(
                """                INSERT INTO ukg_audit_events(event_id, ts, kind, actor, session_id, ka_id, layer, coordinate, payload, prev_hash, hash)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                ON CONFLICT (event_id) DO NOTHING
                """,
                event.event_id,
                event.ts,
                event.kind,
                event.actor,
                event.session_id,
                event.ka_id,
                event.layer,
                event.coordinate,
                event.payload or {},
                event.prev_hash,
                event.hash or "",
            )
        return event
