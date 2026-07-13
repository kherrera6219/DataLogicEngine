"""
Unified Connection Manager for DataLogicEngine Storage Layer.

Provides centralized configuration and connection routing for all storage backends,
using application-owned local database services. A Windows VM deployment runs the
same internal stack as the desktop app; externally hosted database sources are not
part of the runtime model.
"""

import os
import logging
import json
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from urllib.parse import unquote, urlparse
import urllib.request

logger = logging.getLogger(__name__)


class ConnectionMode(Enum):
    """Storage connection mode."""
    LOCAL = "local"      # Use portable/embedded databases
    VM = "vm"            # Same Windows app stack running inside a Windows VM
    AUTO = "auto"        # Auto-detect based on availability


@dataclass
class PostgresConfig:
    """PostgreSQL connection configuration."""
    host: str = "127.0.0.1"
    port: int = 5432
    database: str = "datalogic"
    user: str = "postgres"
    password: str = ""
    
    # Deprecated compatibility field; external database URLs are ignored.
    cloud_url: Optional[str] = None
    
    @property
    def local_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def connection_url(self) -> str:
        return self.local_url


@dataclass
class RedisConfig:
    """Redis connection configuration."""
    host: str = "127.0.0.1"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    
    # Deprecated compatibility field; external database URLs are ignored.
    cloud_url: Optional[str] = None
    
    @property
    def local_url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"
    
    @property
    def connection_url(self) -> str:
        return self.local_url


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    host: str = "127.0.0.1"
    port: int = 7687
    user: str = "neo4j"
    password: str = "password"
    
    # Deprecated compatibility fields; external database URLs are ignored.
    cloud_url: Optional[str] = None
    cloud_user: Optional[str] = None
    cloud_password: Optional[str] = None
    
    @property
    def local_url(self) -> str:
        return f"bolt://{self.host}:{self.port}"
    
    @property
    def connection_url(self) -> str:
        return self.local_url
    
    @property
    def credentials(self) -> tuple:
        return (self.user, self.password)


@dataclass
class VectorDBConfig:
    """Vector database configuration."""
    # Local/app-owned ChromaDB.
    local_path: str = "./databases/chroma"
    host: str = "127.0.0.1"
    port: Optional[int] = None
    
    # Deprecated compatibility fields; external vector database sources are ignored.
    provider: Optional[str] = None  # "pinecone", "qdrant", "weaviate"
    cloud_url: Optional[str] = None
    api_key: Optional[str] = None
    environment: Optional[str] = None  # For Pinecone
    
    @property
    def is_cloud(self) -> bool:
        return False


@dataclass
class ObjectStorageConfig:
    """Object/blob storage configuration."""
    # Local/app-owned filesystem object store.
    local_path: str = "./databases/objects"
    
    # Deprecated compatibility fields; external object stores are ignored by
    # ConnectionManager. Internal MinIO/S3-compatible work uses local app storage.
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    bucket: str = "datalogic"
    region: str = "us-east-1"
    buckets: tuple[str, ...] = ()
    
    @property
    def is_cloud(self) -> bool:
        return False


@dataclass
class StorageConfig:
    """Complete storage configuration."""
    mode: ConnectionMode = ConnectionMode.AUTO
    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    vector: VectorDBConfig = field(default_factory=VectorDBConfig)
    object_storage: ObjectStorageConfig = field(default_factory=ObjectStorageConfig)


class ConnectionManager:
    """
    Unified connection manager for all storage backends.
    
    Handles configuration and health checks for the app-owned internal storage
    stack. VM mode is the same Windows application running inside a Windows VM,
    not a switch to externally hosted databases.
    """
    
    _instance: Optional['ConnectionManager'] = None

    def __init__(
        self,
        *,
        runtime_root: str | Path | None = None,
        data_plane: Optional[Dict[str, Any]] = None,
    ):
        self.config = self._load_config()
        if runtime_root is not None:
            database_root = Path(runtime_root).resolve() / "databases"
            self.config.vector.local_path = str(database_root / "chroma")
            self.config.object_storage.local_path = str(database_root / "objects")
        if data_plane:
            self._apply_data_plane(data_plane)
        self._connections: Dict[str, Any] = {}
        self._health_status: Dict[str, bool] = {}
        
        logger.info(f"ConnectionManager initialized in {self.config.mode.value} mode")

    def _apply_data_plane(self, data_plane: Dict[str, Any]) -> None:
        """Apply supervisor-owned endpoints and credentials without cloud settings."""
        postgres_url = urlparse(str(data_plane["database_url"]))
        self.config.postgres.host = postgres_url.hostname or "127.0.0.1"
        self.config.postgres.port = postgres_url.port or 5432
        self.config.postgres.database = postgres_url.path.lstrip("/") or "datalogic"
        self.config.postgres.user = unquote(postgres_url.username or "dle_app")
        self.config.postgres.password = unquote(postgres_url.password or "")

        redis_url = urlparse(str(data_plane["redis_url"]))
        self.config.redis.host = redis_url.hostname or "127.0.0.1"
        self.config.redis.port = redis_url.port or 6379
        self.config.redis.password = unquote(redis_url.password or "") or None
        self.config.redis.db = int(redis_url.path.strip("/") or 0)

        self.config.neo4j.host = "127.0.0.1"
        self.config.neo4j.port = int(urlparse(str(data_plane["neo4j_uri"])).port or 7687)
        self.config.neo4j.user = str(data_plane["neo4j_user"])
        self.config.neo4j.password = str(data_plane["neo4j_password"])

        self.config.vector.host = str(data_plane["chroma_host"])
        self.config.vector.port = int(data_plane["chroma_port"])

        self.config.object_storage.endpoint_url = str(data_plane["object_endpoint"])
        self.config.object_storage.access_key = str(data_plane["object_access_key"])
        self.config.object_storage.secret_key = str(data_plane["object_secret_key"])
        self.config.object_storage.region = str(data_plane["object_region"])
        self.config.object_storage.buckets = tuple(data_plane["object_buckets"])
    
    def _load_config(self) -> StorageConfig:
        """Load configuration from environment variables."""
        config = StorageConfig()
        
        # Mode
        mode_str = os.environ.get('DB_MODE', 'auto').lower()
        if mode_str in {"cloud", "hybrid"}:
            logger.warning("DB_MODE=%s is deprecated; using internal app-owned storage mode.", mode_str)
            mode_str = "auto"
        config.mode = ConnectionMode(mode_str) if mode_str in [m.value for m in ConnectionMode] else ConnectionMode.AUTO
        
        # PostgreSQL
        config.postgres.host = os.environ.get('POSTGRES_HOST', '127.0.0.1')
        config.postgres.port = int(os.environ.get('POSTGRES_LOCAL_PORT', '5432'))
        config.postgres.database = os.environ.get('POSTGRES_DB', 'datalogic')
        config.postgres.user = os.environ.get('POSTGRES_USER', 'postgres')
        config.postgres.password = os.environ.get('POSTGRES_PASSWORD', '')

        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith(("postgresql://", "postgres://")):
            parsed = urlparse(database_url)
            if parsed.hostname:
                config.postgres.host = parsed.hostname
            if parsed.port:
                config.postgres.port = parsed.port
            if parsed.path and len(parsed.path) > 1:
                config.postgres.database = parsed.path.lstrip("/")
            if parsed.username:
                config.postgres.user = parsed.username
            if parsed.password:
                config.postgres.password = parsed.password
        
        # Redis
        config.redis.host = os.environ.get('REDIS_HOST', '127.0.0.1')
        config.redis.port = int(os.environ.get('REDIS_LOCAL_PORT', '6379'))
        config.redis.password = os.environ.get('REDIS_PASSWORD')

        redis_url = os.environ.get('REDIS_URL')
        if redis_url and redis_url.startswith(("redis://", "rediss://")):
            parsed = urlparse(redis_url)
            if parsed.hostname:
                config.redis.host = parsed.hostname
            if parsed.port:
                config.redis.port = parsed.port
            if parsed.password:
                config.redis.password = parsed.password
            if parsed.path and parsed.path.strip("/").isdigit():
                config.redis.db = int(parsed.path.strip("/"))
        
        # Neo4j
        config.neo4j.host = os.environ.get('NEO4J_HOST', '127.0.0.1')
        config.neo4j.port = int(os.environ.get('NEO4J_LOCAL_PORT', '7687'))
        config.neo4j.user = os.environ.get('NEO4J_USER', 'neo4j')
        config.neo4j.password = os.environ.get('NEO4J_PASSWORD', 'password')

        neo4j_uri = os.environ.get('NEO4J_URI')
        if neo4j_uri and neo4j_uri.startswith(("bolt://", "neo4j://", "neo4j+s://", "neo4j+ssc://")):
            parsed = urlparse(neo4j_uri)
            if parsed.hostname:
                config.neo4j.host = parsed.hostname
            if parsed.port:
                config.neo4j.port = parsed.port
            if parsed.username:
                config.neo4j.user = parsed.username
            if parsed.password:
                config.neo4j.password = parsed.password
        
        # Vector DB
        config.vector.local_path = os.environ.get('VECTOR_LOCAL_PATH', os.environ.get('CHROMA_PERSIST_DIR', './databases/chroma'))
        
        # Object Storage
        config.object_storage.local_path = os.environ.get('OBJECT_LOCAL_PATH', './databases/objects')
        config.object_storage.bucket = os.environ.get('OBJECT_BUCKET', 'datalogic')
        config.object_storage.region = os.environ.get('OBJECT_REGION', 'us-east-1')
        
        return config
    
    def check_health(self, service: str) -> bool:
        """Check health of a specific service."""
        try:
            if service == 'postgres':
                return self._check_postgres_health()
            elif service == 'redis':
                return self._check_redis_health()
            elif service == 'neo4j':
                return self._check_neo4j_health()
            elif service == 'vector':
                return self._check_vector_health()
            elif service == 'object':
                return self._check_object_health()
            else:
                logger.warning(f"Unknown service: {service}")
                return False
        except Exception as e:
            logger.error(f"Health check failed for {service}: {e}")
            return False
    
    def check_all_health(self) -> Dict[str, bool]:
        """Check health of all services."""
        services = ['postgres', 'redis', 'neo4j', 'vector', 'object']
        self._health_status = {s: self.check_health(s) for s in services}
        return self._health_status
    
    def _check_postgres_health(self) -> bool:
        """Check authenticated PostgreSQL identity and query execution."""
        try:
            import psycopg2

            with psycopg2.connect(
                self.config.postgres.connection_url,
                connect_timeout=3,
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT current_database(), current_user")
                    database, user = cursor.fetchone()
            return database == self.config.postgres.database and user == self.config.postgres.user
        except Exception as exc:
            logger.warning("PostgreSQL health check failed: %s", exc)
            return False
    
    def _check_redis_health(self) -> bool:
        """Check authenticated Redis command execution."""
        try:
            import redis

            client = redis.Redis.from_url(
                self.config.redis.connection_url,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            return client.ping() is True
        except Exception as exc:
            logger.warning("Redis health check failed: %s", exc)
            return False
    
    def _check_neo4j_health(self) -> bool:
        """Check authenticated Neo4j connectivity."""
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                self.config.neo4j.connection_url,
                auth=self.config.neo4j.credentials,
                connection_timeout=3,
            )
            try:
                driver.verify_connectivity()
            finally:
                driver.close()
            return True
        except Exception as exc:
            logger.warning("Neo4j health check failed: %s", exc)
            return False
    
    def _check_vector_health(self) -> bool:
        """Check that Chroma can open and query a real collection."""
        try:
            if self.config.vector.port is not None:
                url = (
                    f"http://{self.config.vector.host}:"
                    f"{self.config.vector.port}/api/v2/heartbeat"
                )
                with urllib.request.urlopen(url, timeout=3) as response:  # noqa: S310 - loopback only
                    payload = json.loads(response.read().decode("utf-8"))
                return "nanosecond heartbeat" in payload
            from backend.storage.vector_store import ChromaDBBackend

            backend = ChromaDBBackend(self.config.vector.local_path)
            collection = backend._get_collection("healthcheck")
            collection.count()
            return True
        except Exception as exc:
            logger.warning("Vector health check failed: %s", exc)
            return False
    
    def _check_object_health(self) -> bool:
        """Check the app-owned S3 contract or the bounded development backend."""
        try:
            if self.config.object_storage.endpoint_url:
                import boto3
                from botocore.config import Config

                client = boto3.client(
                    "s3",
                    endpoint_url=self.config.object_storage.endpoint_url,
                    aws_access_key_id=self.config.object_storage.access_key,
                    aws_secret_access_key=self.config.object_storage.secret_key,
                    region_name=self.config.object_storage.region,
                    config=Config(
                        signature_version="s3v4",
                        s3={"addressing_style": "path"},
                        connect_timeout=3,
                        read_timeout=3,
                        retries={"max_attempts": 1},
                    ),
                )
                for bucket in self.config.object_storage.buckets:
                    client.list_objects_v2(Bucket=bucket, MaxKeys=1)
                return bool(self.config.object_storage.buckets)
            root = Path(self.config.object_storage.local_path)
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".healthcheck"
            probe.write_bytes(b"ok")
            probe.unlink()
            return True
        except Exception as exc:
            logger.warning("Object storage health check failed: %s", exc)
            return False
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report of all storage services."""
        health = self.check_all_health()
        
        return {
            'mode': self.config.mode.value,
            'services': {
                'postgres': {
                    'healthy': health.get('postgres', False),
                    'url': self.config.postgres.connection_url.replace(self.config.postgres.password, '***') if self.config.postgres.password else self.config.postgres.connection_url,
                    'is_cloud': False,
                    'source': 'internal'
                },
                'redis': {
                    'healthy': health.get('redis', False),
                    'url': self.config.redis.connection_url.replace(self.config.redis.password, '***') if self.config.redis.password else self.config.redis.connection_url,
                    'is_cloud': False,
                    'source': 'internal'
                },
                'neo4j': {
                    'healthy': health.get('neo4j', False),
                    'url': self.config.neo4j.connection_url,
                    'is_cloud': False,
                    'source': 'internal'
                },
                'vector': {
                    'healthy': health.get('vector', False),
                    'provider': self.config.vector.provider or 'chromadb',
                    'is_cloud': False,
                    'source': 'internal'
                },
                'object': {
                    'healthy': health.get('object', False),
                    'endpoint': self.config.object_storage.endpoint_url or 'local',
                    'is_cloud': False,
                    'source': 'internal'
                }
            }
        }


# Singleton accessor
def get_connection_manager() -> ConnectionManager:
    """Return the manager owned by the active application instance."""
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            manager = current_app.extensions.get("dle_connection_manager")
            if manager is None:
                runtime = current_app.extensions.get("dle_runtime")
                manager = ConnectionManager(
                    runtime_root=runtime.runtime_root if runtime is not None else None
                )
                current_app.extensions["dle_connection_manager"] = manager
            return manager
    except ImportError:
        pass

    if ConnectionManager._instance is None:
        ConnectionManager._instance = ConnectionManager()
    return ConnectionManager._instance
