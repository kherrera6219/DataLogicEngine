import logging
import os
import re
import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver
from backend.storage.runtime_endpoints import runtime_neo4j_settings, runtime_redis_url

logger = logging.getLogger(__name__)

_CYPHER_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
_DISALLOWED_DEFAULT_PASSWORDS = {"password", "neo4j", "changeme", "default"}

class GraphStore:
    """
    Interface for interacting with the Neo4j Graph Database.
    Used by the Universal Knowledge Graph (UKG) simulation stack.
    """
    
    def __init__(self):
        self.uri, self.user, self.password = runtime_neo4j_settings()
        self.driver: Optional[Driver] = None
        self.allowed_labels = self._parse_allowlist(os.getenv("NEO4J_ALLOWED_LABELS"))
        self.allowed_relationship_types = self._parse_allowlist(os.getenv("NEO4J_ALLOWED_REL_TYPES"))

    @staticmethod
    def _parse_allowlist(value: Optional[str]) -> Optional[set[str]]:
        if not value:
            return None
        entries = {entry.strip() for entry in value.split(",") if entry.strip()}
        return entries or None

    @staticmethod
    def _is_production_env() -> bool:
        env = (os.getenv("FLASK_ENV") or os.getenv("ENV") or "").strip().lower()
        return env in {"production", "prod"}

    def _validate_identifier(
        self,
        value: str,
        *,
        identifier_type: str,
        allowlist: Optional[set[str]] = None,
    ) -> str:
        identifier = str(value or "").strip()
        if not _CYPHER_IDENTIFIER_RE.fullmatch(identifier):
            raise ValueError(f"Invalid {identifier_type} identifier: {value!r}")
        if allowlist and identifier not in allowlist:
            raise ValueError(f"{identifier_type} '{identifier}' is not allowed by policy")
        return identifier

    def connect(self):
        """Establish connection to the Neo4j instance."""
        try:
            if self._is_production_env() and str(self.password).strip().lower() in _DISALLOWED_DEFAULT_PASSWORDS:
                logger.error("Refusing Neo4j connection with default password in production")
                self.driver = None
                return

            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
            self.ensure_schema()
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    _SCHEMA_STATEMENTS = [
        "CREATE CONSTRAINT pillar_uid IF NOT EXISTS FOR (p:Pillar) REQUIRE p.uid IS UNIQUE",
        "CREATE CONSTRAINT node_uid IF NOT EXISTS FOR (n:KnowledgeNode) REQUIRE n.uid IS UNIQUE",
        "CREATE INDEX pillar_code IF NOT EXISTS FOR (p:Pillar) ON (p.code)",
        "CREATE INDEX node_axis IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.axis_number)",
    ]

    def ensure_schema(self) -> None:
        """Idempotently create required Neo4j constraints and indexes."""
        if not self.driver:
            return
        try:
            with self.driver.session() as session:
                for stmt in self._SCHEMA_STATEMENTS:
                    session.run(stmt)
            logger.info("Neo4j schema constraints and indexes ensured")
        except Exception as exc:
            logger.warning("Neo4j schema setup skipped (may require Enterprise or older syntax): %s", exc)

    def close(self):
        """Close the Neo4j driver."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed.")

    def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run a Cypher query and return results as a list of dictionaries."""
        if not self.driver:
            self.connect()
            if not self.driver:
                return []

        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Cypher query failed: {e}")
            return []

    def delete_knowledge_node(self, uid: str) -> bool:
        """Delete one knowledge node and its relationships by stable UID."""
        if not self.driver:
            self.connect()
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run(
                    "MATCH (n:KnowledgeNode {uid: $uid}) DETACH DELETE n",
                    {"uid": str(uid)},
                ).consume()
            return True
        except Exception as exc:
            logger.error("Neo4j knowledge-node deletion failed: %s", exc)
            return False

    def cached_run_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        *,
        cache_key_prefix: str = "subgraph",
        timeout: int = 300,
    ) -> List[Dict[str, Any]]:
        """Run a Cypher query with optional Flask cache/Redis caching."""
        parameters = parameters or {}
        cache_key = self._cache_key(cache_key_prefix, query, parameters)
        redis_result = self._redis_cache_get(cache_key)
        if redis_result is not None:
            return redis_result
        try:
            from extensions import cache

            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            result = self.run_query(query, parameters)
            cache.set(cache_key, result, timeout=timeout)
            self._redis_cache_set(cache_key, result, timeout)
            return result
        except Exception:
            result = self.run_query(query, parameters)
            self._redis_cache_set(cache_key, result, timeout)
            return result

    @staticmethod
    def _redis_enabled() -> bool:
        return os.environ.get("USE_REDIS", "false").lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _redis_client():
        if not GraphStore._redis_enabled():
            return None
        try:
            import redis

            client = redis.Redis.from_url(runtime_redis_url(), decode_responses=True)
            client.ping()
            return client
        except Exception as exc:
            logger.debug("GraphStore Redis cache unavailable: %s", exc)
            return None

    @classmethod
    def _redis_cache_get(cls, key: str) -> Optional[List[Dict[str, Any]]]:
        client = cls._redis_client()
        if client is None:
            return None
        try:
            raw = client.hget(key, "value")
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.debug("GraphStore Redis cache get failed for %s: %s", key, exc)
            return None

    @classmethod
    def _redis_cache_set(cls, key: str, value: List[Dict[str, Any]], ttl: int) -> None:
        client = cls._redis_client()
        if client is None:
            return
        try:
            client.hset(key, mapping={
                "value": json.dumps(value, sort_keys=True, default=str),
                "expires_at": str(time.time() + ttl),
            })
            client.expire(key, ttl)
        except Exception as exc:
            logger.debug("GraphStore Redis cache set failed for %s: %s", key, exc)

    def find_coordinate_nodes(
        self,
        *,
        axis_number: Optional[int] = None,
        text: str = "",
        limit: int = 25,
        cached: bool = True,
    ) -> List[Dict[str, Any]]:
        """Find Pillar/KnowledgeNode anchors for coordinate resolution."""
        query = """
        MATCH (n)
        WHERE (n:Pillar OR n:KnowledgeNode)
          AND ($axis_number IS NULL OR n.axis_number = $axis_number OR n:Pillar)
          AND (
            $text = '' OR
            toLower(coalesce(n.name, '')) CONTAINS $text OR
            toLower(coalesce(n.title, '')) CONTAINS $text OR
            toLower(coalesce(n.description, '')) CONTAINS $text OR
            toLower(coalesce(n.content, '')) CONTAINS $text OR
            toLower(coalesce(n.code, '')) CONTAINS $text
          )
        RETURN labels(n) AS labels, properties(n) AS props
        LIMIT $limit
        """
        params = {
            "axis_number": axis_number,
            "text": str(text or "").strip().lower(),
            "limit": int(limit),
        }
        runner = self.cached_run_query if cached else self.run_query
        return runner(query, params, cache_key_prefix="subgraph", timeout=300)

    def get_subgraph(
        self,
        uid: str,
        *,
        depth: int = 1,
        limit: int = 100,
        cached: bool = True,
    ) -> List[Dict[str, Any]]:
        """Return a bounded Neo4j subgraph around a node uid."""
        query = """
        MATCH (center {uid: $uid})
        MATCH path = (center)-[*0..2]-(neighbor)
        WHERE length(path) <= $depth
        RETURN path
        LIMIT $limit
        """
        params = {"uid": uid, "depth": max(0, int(depth)), "limit": int(limit)}
        runner = self.cached_run_query if cached else self.run_query
        return runner(query, params, cache_key_prefix="subgraph", timeout=300)

    def get_knowledge_relationships(
        self,
        uid: str,
        *,
        limit: int = 12,
        cached: bool = True,
    ) -> List[Dict[str, Any]]:
        """Return bounded, projection-only relationship context for retrieval."""
        query = """
        MATCH (center {uid: $uid})-[relationship]-(neighbor)
        RETURN type(relationship) AS relationship_type,
               neighbor.uid AS neighbor_uid,
               coalesce(neighbor.title, neighbor.name, neighbor.label, neighbor.uid) AS neighbor_title,
               labels(neighbor) AS neighbor_labels
        ORDER BY relationship_type, neighbor_uid
        LIMIT $limit
        """
        params = {"uid": str(uid), "limit": max(1, min(int(limit), 50))}
        runner = self.cached_run_query if cached else self.run_query
        records = runner(
            query,
            params,
            cache_key_prefix="retrieval-relationships",
            timeout=300,
        )
        return [
            {
                "relationship_type": str(record.get("relationship_type") or "RELATED_TO"),
                "neighbor_uid": str(record.get("neighbor_uid") or ""),
                "neighbor_title": str(record.get("neighbor_title") or ""),
                "neighbor_labels": [str(value) for value in (record.get("neighbor_labels") or [])],
            }
            for record in records
            if isinstance(record, dict) and record.get("neighbor_uid")
        ]

    def merge_knowledge_node(self, properties: Dict[str, Any]) -> bool:
        """Idempotently merge a KnowledgeNode by uid."""
        uid = properties.get("uid") or properties.get("node_id")
        if not uid:
            return False
        props = {k: v for k, v in properties.items() if v is not None}
        props["uid"] = str(uid)
        query = """
        MERGE (n:KnowledgeNode {uid: $uid})
        SET n += $props
        RETURN n
        """
        return bool(self.run_query(query, {"uid": str(uid), "props": props}))

    def merge_relationship_by_uid(
        self,
        source_uid: str,
        target_uid: str,
        rel_type: str,
        props: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Idempotently merge a relationship between uid-addressed nodes."""
        try:
            safe_rel_type = self._validate_identifier(
                rel_type,
                identifier_type="relationship type",
                allowlist=self.allowed_relationship_types,
            )
        except ValueError as exc:
            logger.warning(f"Rejected merge_relationship_by_uid request: {exc}")
            return False
        query = (
            "MATCH (a {uid: $source_uid}), (b {uid: $target_uid}) "
            f"MERGE (a)-[r:{safe_rel_type}]->(b) "
            "SET r += $props "
            "RETURN r"
        )
        return bool(self.run_query(query, {
            "source_uid": source_uid,
            "target_uid": target_uid,
            "props": props or {},
        }))

    @staticmethod
    def _cache_key(prefix: str, query: str, parameters: Dict[str, Any]) -> str:
        payload = json.dumps({"query": query, "parameters": parameters}, sort_keys=True, default=str)
        digest = hashlib.sha256(payload.encode()).hexdigest()
        return f"{prefix}:{digest}"

    def create_node(self, label: str, properties: Dict[str, Any]) -> bool:
        """Create a single node in the graph."""
        try:
            safe_label = self._validate_identifier(
                label,
                identifier_type="label",
                allowlist=self.allowed_labels,
            )
        except ValueError as exc:
            logger.warning(f"Rejected create_node request: {exc}")
            return False

        query = f"CREATE (n:{safe_label} $props) RETURN n"
        results = self.run_query(query, {"props": properties or {}})
        return len(results) > 0

    def create_relationship(self, from_id: str, to_id: str, rel_type: str, props: Optional[Dict[str, Any]] = None) -> bool:
        """Create a directed relationship between two nodes identified by their 'id' property."""
        try:
            safe_rel_type = self._validate_identifier(
                rel_type,
                identifier_type="relationship type",
                allowlist=self.allowed_relationship_types,
            )
        except ValueError as exc:
            logger.warning(f"Rejected create_relationship request: {exc}")
            return False

        query = (
            f"MATCH (a), (b) "
            f"WHERE a.id = $from_id AND b.id = $to_id "
            f"CREATE (a)-[r:{safe_rel_type} $props]->(b) "
            f"RETURN r"
        )
        results = self.run_query(query, {
            "from_id": from_id,
            "to_id": to_id,
            "props": props or {}
        })
        return len(results) > 0

graph_store: Optional[GraphStore] = None

def get_graph_store() -> GraphStore:
    """Return a graph client owned by the active application instance."""
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            store = current_app.extensions.get("dle_graph_store")
            if store is None:
                store = GraphStore()
                current_app.extensions["dle_graph_store"] = store
            return store
    except ImportError:
        pass

    global graph_store
    if graph_store is None:
        graph_store = GraphStore()
    return graph_store
