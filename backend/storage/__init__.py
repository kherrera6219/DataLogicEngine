"""
Storage Layer for DataLogicEngine.

Provides unified interfaces for:
- ConnectionManager: Configuration and health monitoring
- VectorStore: Embedding storage (ChromaDB local, Pinecone cloud)
- ObjectStore: Blob storage (Local filesystem, S3/MinIO cloud)
- GraphStore: Graph database (Neo4j)
- DatabaseLifecycleManager: Portable database management
"""

from backend.storage.connection_manager import (
    ConnectionManager,
    ConnectionMode,
    StorageConfig,
    get_connection_manager
)

from backend.storage.vector_store import (
    VectorStore,
    SearchResult,
    get_vector_store
)

from backend.storage.object_store import (
    ObjectStore,
    ObjectInfo,
    get_object_store
)

from backend.storage.graph_store import (
    GraphStore,
    get_graph_store
)

from backend.storage.uskd_memory_graph import (
    UskdGraphStats,
    UskdMemoryGraph,
    get_uskd_memory_graph
)

from backend.storage.database_manager import (
    DatabaseLifecycleManager,
    get_db_manager
)

__all__ = [
    # Connection Management
    'ConnectionManager',
    'ConnectionMode',
    'StorageConfig',
    'get_connection_manager',
    
    # Vector Store
    'VectorStore',
    'SearchResult',
    'get_vector_store',
    
    # Object Store
    'ObjectStore',
    'ObjectInfo',
    'get_object_store',
    
    # Graph Store
    'GraphStore',
    'get_graph_store',

    # In-memory USKD graph
    'UskdGraphStats',
    'UskdMemoryGraph',
    'get_uskd_memory_graph',
    
    # Database Lifecycle
    'DatabaseLifecycleManager',
    'get_db_manager',
]
