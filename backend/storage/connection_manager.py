"""
Unified Connection Manager for DataLogicEngine Storage Layer.

Provides centralized configuration and connection routing for all storage backends,
supporting both local (portable) and cloud-hosted database deployments.
"""

import os
import logging
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ConnectionMode(Enum):
    """Storage connection mode."""
    LOCAL = "local"      # Use portable/embedded databases
    CLOUD = "cloud"      # Use cloud-hosted services
    HYBRID = "hybrid"    # Use local with cloud fallback
    AUTO = "auto"        # Auto-detect based on availability


@dataclass
class PostgresConfig:
    """PostgreSQL connection configuration."""
    host: str = "127.0.0.1"
    port: int = 5432
    database: str = "datalogic"
    user: str = "postgres"
    password: str = ""
    
    # Cloud override
    cloud_url: Optional[str] = None
    
    @property
    def local_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def connection_url(self) -> str:
        return self.cloud_url or self.local_url


@dataclass
class RedisConfig:
    """Redis connection configuration."""
    host: str = "127.0.0.1"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    
    # Cloud override
    cloud_url: Optional[str] = None
    
    @property
    def local_url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"
    
    @property
    def connection_url(self) -> str:
        return self.cloud_url or self.local_url


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    host: str = "127.0.0.1"
    port: int = 7687
    user: str = "neo4j"
    password: str = "password"
    
    # Cloud override (Neo4j Aura)
    cloud_url: Optional[str] = None
    cloud_user: Optional[str] = None
    cloud_password: Optional[str] = None
    
    @property
    def local_url(self) -> str:
        return f"bolt://{self.host}:{self.port}"
    
    @property
    def connection_url(self) -> str:
        return self.cloud_url or self.local_url
    
    @property
    def credentials(self) -> tuple:
        if self.cloud_url:
            return (self.cloud_user or self.user, self.cloud_password or self.password)
        return (self.user, self.password)


@dataclass
class VectorDBConfig:
    """Vector database configuration."""
    # Local (ChromaDB)
    local_path: str = "./databases/chroma"
    
    # Cloud options
    provider: Optional[str] = None  # "pinecone", "qdrant", "weaviate"
    cloud_url: Optional[str] = None
    api_key: Optional[str] = None
    environment: Optional[str] = None  # For Pinecone
    
    @property
    def is_cloud(self) -> bool:
        return bool(self.cloud_url or self.api_key)


@dataclass
class ObjectStorageConfig:
    """Object/blob storage configuration."""
    # Local filesystem
    local_path: str = "./databases/objects"
    
    # Cloud (S3/MinIO compatible)
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    bucket: str = "datalogic"
    region: str = "us-east-1"
    
    @property
    def is_cloud(self) -> bool:
        return bool(self.endpoint_url and self.access_key)


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
    
    Handles connection pooling, health checks, and failover between
    local and cloud backends.
    """
    
    _instance: Optional['ConnectionManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config = self._load_config()
        self._connections: Dict[str, Any] = {}
        self._health_status: Dict[str, bool] = {}
        self._initialized = True
        
        logger.info(f"ConnectionManager initialized in {self.config.mode.value} mode")
    
    def _load_config(self) -> StorageConfig:
        """Load configuration from environment variables."""
        config = StorageConfig()
        
        # Mode
        mode_str = os.environ.get('DB_MODE', 'auto').lower()
        config.mode = ConnectionMode(mode_str) if mode_str in [m.value for m in ConnectionMode] else ConnectionMode.AUTO
        
        # PostgreSQL
        config.postgres.host = os.environ.get('POSTGRES_HOST', '127.0.0.1')
        config.postgres.port = int(os.environ.get('POSTGRES_LOCAL_PORT', '5432'))
        config.postgres.database = os.environ.get('POSTGRES_DB', 'datalogic')
        config.postgres.user = os.environ.get('POSTGRES_USER', 'postgres')
        config.postgres.password = os.environ.get('POSTGRES_PASSWORD', '')
        config.postgres.cloud_url = os.environ.get('POSTGRES_CLOUD_URL')

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
            # If explicit cloud URL not provided, reuse DATABASE_URL for parity.
            if not config.postgres.cloud_url:
                config.postgres.cloud_url = database_url
        
        # Redis
        config.redis.host = os.environ.get('REDIS_HOST', '127.0.0.1')
        config.redis.port = int(os.environ.get('REDIS_LOCAL_PORT', '6379'))
        config.redis.password = os.environ.get('REDIS_PASSWORD')
        config.redis.cloud_url = os.environ.get('REDIS_CLOUD_URL')

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
            if not config.redis.cloud_url:
                config.redis.cloud_url = redis_url
        
        # Neo4j
        config.neo4j.host = os.environ.get('NEO4J_HOST', '127.0.0.1')
        config.neo4j.port = int(os.environ.get('NEO4J_LOCAL_PORT', '7687'))
        config.neo4j.user = os.environ.get('NEO4J_USER', 'neo4j')
        config.neo4j.password = os.environ.get('NEO4J_PASSWORD', 'password')
        config.neo4j.cloud_url = os.environ.get('NEO4J_CLOUD_URL')
        config.neo4j.cloud_user = os.environ.get('NEO4J_CLOUD_USER')
        config.neo4j.cloud_password = os.environ.get('NEO4J_CLOUD_PASSWORD')

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
            if not config.neo4j.cloud_url:
                config.neo4j.cloud_url = neo4j_uri
        
        # Vector DB
        config.vector.local_path = os.environ.get('VECTOR_LOCAL_PATH', os.environ.get('CHROMA_PERSIST_DIR', './databases/chroma'))
        config.vector.provider = os.environ.get('VECTOR_PROVIDER')
        config.vector.cloud_url = os.environ.get('VECTOR_CLOUD_URL')
        config.vector.api_key = os.environ.get('VECTOR_API_KEY')
        config.vector.environment = os.environ.get('VECTOR_ENVIRONMENT')
        
        # Object Storage
        config.object_storage.local_path = os.environ.get('OBJECT_LOCAL_PATH', './databases/objects')
        config.object_storage.endpoint_url = (
            os.environ.get('OBJECT_ENDPOINT_URL')
            or os.environ.get('OBJECT_STORAGE_ENDPOINT')
            or os.environ.get('S3_ENDPOINT_URL')
            or os.environ.get('MINIO_ENDPOINT')
        )
        config.object_storage.access_key = (
            os.environ.get('OBJECT_ACCESS_KEY')
            or os.environ.get('AWS_ACCESS_KEY_ID')
            or os.environ.get('MINIO_ACCESS_KEY')
        )
        config.object_storage.secret_key = (
            os.environ.get('OBJECT_SECRET_KEY')
            or os.environ.get('AWS_SECRET_ACCESS_KEY')
            or os.environ.get('MINIO_SECRET_KEY')
        )
        config.object_storage.bucket = os.environ.get('OBJECT_BUCKET', os.environ.get('S3_BUCKET', 'datalogic'))
        config.object_storage.region = os.environ.get('OBJECT_REGION', os.environ.get('AWS_REGION', 'us-east-1'))
        
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
        """Check PostgreSQL connectivity."""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.config.postgres.host, self.config.postgres.port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _check_redis_health(self) -> bool:
        """Check Redis connectivity."""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.config.redis.host, self.config.redis.port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _check_neo4j_health(self) -> bool:
        """Check Neo4j connectivity."""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.config.neo4j.host, self.config.neo4j.port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _check_vector_health(self) -> bool:
        """Check vector database availability."""
        if self.config.vector.is_cloud:
            # Cloud health check would require API call
            return bool(self.config.vector.api_key)
        else:
            # Local ChromaDB - check if directory exists or can be created
            import os
            try:
                os.makedirs(self.config.vector.local_path, exist_ok=True)
                return True
            except Exception:
                return False
    
    def _check_object_health(self) -> bool:
        """Check object storage availability."""
        if self.config.object_storage.is_cloud:
            # Cloud health check would require API call
            return bool(self.config.object_storage.access_key)
        else:
            # Local filesystem - check if directory exists or can be created
            import os
            try:
                os.makedirs(self.config.object_storage.local_path, exist_ok=True)
                return True
            except Exception:
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
                    'is_cloud': bool(self.config.postgres.cloud_url)
                },
                'redis': {
                    'healthy': health.get('redis', False),
                    'url': self.config.redis.connection_url.replace(self.config.redis.password, '***') if self.config.redis.password else self.config.redis.connection_url,
                    'is_cloud': bool(self.config.redis.cloud_url)
                },
                'neo4j': {
                    'healthy': health.get('neo4j', False),
                    'url': self.config.neo4j.connection_url,
                    'is_cloud': bool(self.config.neo4j.cloud_url)
                },
                'vector': {
                    'healthy': health.get('vector', False),
                    'provider': self.config.vector.provider or 'chromadb',
                    'is_cloud': self.config.vector.is_cloud
                },
                'object': {
                    'healthy': health.get('object', False),
                    'endpoint': self.config.object_storage.endpoint_url or 'local',
                    'is_cloud': self.config.object_storage.is_cloud
                }
            }
        }


# Singleton accessor
def get_connection_manager() -> ConnectionManager:
    """Get the singleton ConnectionManager instance."""
    return ConnectionManager()
