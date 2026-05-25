"""
Vector Store for DataLogicEngine.

Provides unified interface for vector/embedding storage with support for:
- Local: ChromaDB (embedded, no server required)
- Cloud: Pinecone, Qdrant, Weaviate
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from vector search."""
    id: str
    score: float
    text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


class VectorBackend(ABC):
    """Abstract base class for vector storage backends."""
    
    @abstractmethod
    def add_embeddings(
        self,
        collection: str,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add embeddings to the store."""
        pass
    
    @abstractmethod
    def search(
        self,
        collection: str,
        query_embedding: List[float],
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    def delete(self, collection: str, ids: List[str]) -> bool:
        """Delete vectors by ID."""
        pass
    
    @abstractmethod
    def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        pass

    @abstractmethod
    def list_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all required collections."""
        pass
    
    @abstractmethod
    def create_collection(self, collection: str, dimension: int = 1536) -> bool:
        """Create a new collection."""
        pass
    
    @abstractmethod
    def delete_collection(self, collection: str) -> bool:
        """Delete a collection."""
        pass


class ChromaDBBackend(VectorBackend):
    """ChromaDB backend for local vector storage."""
    
    def __init__(self, persist_directory: str = "./databases/chroma"):
        self.persist_directory = persist_directory
        self._client = None
        self._collections: Dict[str, Any] = {}
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
    
    @property
    def client(self):
        """Lazy initialization of ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                logger.info(f"ChromaDB initialized at {self.persist_directory}")
            except ImportError:
                logger.warning("ChromaDB not installed. Install with: pip install chromadb")
                raise
        return self._client
    
    def _get_collection(self, name: str):
        """Get or create a collection."""
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(name=name)
        return self._collections[name]
    
    def add_embeddings(
        self,
        collection: str,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add embeddings to ChromaDB."""
        try:
            coll = self._get_collection(collection)
            write = getattr(coll, "upsert", coll.add)
            write(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadata or [{}] * len(ids)
            )
            logger.debug(f"Added {len(ids)} embeddings to collection {collection}")
            return ids
        except Exception as e:
            logger.error(f"Failed to add embeddings: {e}")
            return []
    
    def search(
        self,
        collection: str,
        query_embedding: List[float],
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors in ChromaDB."""
        try:
            coll = self._get_collection(collection)
            
            results = coll.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filters,
                include=["documents", "metadatas", "distances"]
            )
            
            search_results = []
            if results and results['ids'] and results['ids'][0]:
                for i, id_ in enumerate(results['ids'][0]):
                    search_results.append(SearchResult(
                        id=id_,
                        score=1.0 - (results['distances'][0][i] if results['distances'] else 0),
                        text=results['documents'][0][i] if results['documents'] else None,
                        metadata=results['metadatas'][0][i] if results['metadatas'] else {}
                    ))
            
            return search_results
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def delete(self, collection: str, ids: List[str]) -> bool:
        """Delete vectors from ChromaDB."""
        try:
            coll = self._get_collection(collection)
            coll.delete(ids=ids)
            return True
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False
    
    def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get collection statistics from ChromaDB."""
        try:
            coll = self._get_collection(collection)
            return {
                "name": collection,
                "count": coll.count(),
                "backend": "chromadb"
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"name": collection, "count": 0, "error": str(e)}

    def list_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for the required ChromaDB collections."""
        return {name: self.get_collection_stats(name) for name in REQUIRED_COLLECTIONS}
    
    def create_collection(self, collection: str, dimension: int = 1536) -> bool:
        """Create a new collection in ChromaDB."""
        try:
            self.client.get_or_create_collection(name=collection)
            return True
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def delete_collection(self, collection: str) -> bool:
        """Delete a collection from ChromaDB."""
        try:
            self.client.delete_collection(name=collection)
            if collection in self._collections:
                del self._collections[collection]
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False


class PineconeBackend(VectorBackend):
    """Pinecone backend for cloud vector storage."""
    
    def __init__(self, api_key: str, environment: str, index_name: str = "datalogic"):
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self._index = None
    
    @property
    def index(self):
        """Lazy initialization of Pinecone index."""
        if self._index is None:
            try:
                from pinecone import Pinecone
                
                pc = Pinecone(api_key=self.api_key)
                self._index = pc.Index(self.index_name)
                logger.info(f"Connected to Pinecone index: {self.index_name}")
            except ImportError:
                logger.warning("Pinecone not installed. Install with: pip install pinecone-client")
                raise
        return self._index
    
    def add_embeddings(
        self,
        collection: str,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add embeddings to Pinecone."""
        try:
            vectors = []
            for i, (id_, emb) in enumerate(zip(ids, embeddings)):
                meta = (metadata[i] if metadata else {}).copy()
                meta['text'] = texts[i]
                meta['collection'] = collection
                vectors.append({
                    'id': f"{collection}_{id_}",
                    'values': emb,
                    'metadata': meta
                })
            
            self.index.upsert(vectors=vectors)
            return ids
        except Exception as e:
            logger.error(f"Pinecone upsert failed: {e}")
            return []
    
    def search(
        self,
        collection: str,
        query_embedding: List[float],
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search Pinecone index."""
        try:
            filter_dict = filters.copy() if filters else {}
            filter_dict['collection'] = collection
            
            results = self.index.query(
                vector=query_embedding,
                top_k=k,
                filter=filter_dict,
                include_metadata=True
            )
            
            return [
                SearchResult(
                    id=match['id'].replace(f"{collection}_", ""),
                    score=match['score'],
                    text=match.get('metadata', {}).get('text'),
                    metadata={k: v for k, v in match.get('metadata', {}).items() if k not in ['text', 'collection']}
                )
                for match in results.get('matches', [])
            ]
        except Exception as e:
            logger.error(f"Pinecone search failed: {e}")
            return []
    
    def delete(self, collection: str, ids: List[str]) -> bool:
        """Delete from Pinecone."""
        try:
            prefixed_ids = [f"{collection}_{id_}" for id_ in ids]
            self.index.delete(ids=prefixed_ids)
            return True
        except Exception as e:
            logger.error(f"Pinecone delete failed: {e}")
            return False
    
    def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get Pinecone index stats."""
        try:
            stats = self.index.describe_index_stats()
            return {
                "name": collection,
                "total_count": stats.get('total_vector_count', 0),
                "backend": "pinecone"
            }
        except Exception as e:
            logger.error(f"Failed to get Pinecone stats: {e}")
            return {"name": collection, "count": 0, "error": str(e)}

    def list_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for the required logical collections."""
        return {name: self.get_collection_stats(name) for name in REQUIRED_COLLECTIONS}
    
    def create_collection(self, collection: str, dimension: int = 1536) -> bool:
        """Collections are virtual in Pinecone (using metadata filtering)."""
        return True
    
    def delete_collection(self, collection: str) -> bool:
        """Delete all vectors in a collection."""
        try:
            self.index.delete(filter={"collection": collection})
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False


class VectorStore:
    """
    Unified vector store interface.
    
    Automatically selects between local (ChromaDB) and cloud (Pinecone) backends
    based on configuration.
    """
    
    def __init__(self, backend: Optional[VectorBackend] = None):
        if backend:
            self._backend = backend
        else:
            self._backend = self._create_backend()
    
    def _create_backend(self) -> VectorBackend:
        """Create appropriate backend based on configuration."""
        from backend.storage.connection_manager import get_connection_manager
        
        config = get_connection_manager().config.vector
        
        if config.is_cloud and config.provider == "pinecone" and config.api_key:
            logger.info("Using Pinecone cloud backend")
            return PineconeBackend(
                api_key=config.api_key,
                environment=config.environment or "us-east-1",
                index_name="datalogic"
            )
        else:
            logger.info("Using ChromaDB local backend")
            return ChromaDBBackend(persist_directory=config.local_path)
    
    def add_embeddings(
        self,
        collection: str,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add embeddings to the store."""
        return self._backend.add_embeddings(collection, ids, texts, embeddings, metadata)
    
    def search(
        self,
        collection: str,
        query_embedding: List[float],
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        return self._backend.search(collection, query_embedding, k, filters)
    
    def delete(self, collection: str, ids: List[str]) -> bool:
        """Delete vectors by ID."""
        return self._backend.delete(collection, ids)
    
    def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get collection statistics."""
        return self._backend.get_collection_stats(collection)

    def list_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all required collections."""
        return self._backend.list_collection_stats()
    
    def create_collection(self, collection: str, dimension: int = 1536) -> bool:
        """Create a new collection."""
        return self._backend.create_collection(collection, dimension)
    
    def delete_collection(self, collection: str) -> bool:
        """Delete a collection."""
        return self._backend.delete_collection(collection)


REQUIRED_COLLECTIONS = [
    "knowledge_nodes",
    "persona_profiles",
    "citation_cache",
    "audit_evidence",
]

# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get the singleton VectorStore instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def initialize_collections() -> None:
    """Ensure all required spec-defined collections exist. Idempotent."""
    store = get_vector_store()
    for name in REQUIRED_COLLECTIONS:
        try:
            store.create_collection(name)
        except Exception:
            pass  # collection already exists or backend unavailable — non-fatal


def get_collection_counts() -> Dict[str, int]:
    """Return document counts for required vector collections."""
    stats = get_vector_store().list_collection_stats()
    return {
        name: int((data or {}).get("count", (data or {}).get("total_count", 0)) or 0)
        for name, data in stats.items()
    }
