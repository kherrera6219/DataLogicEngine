"""
RAG (Retrieval Augmented Generation) Service

Enhanced with LlamaIndex for better document parsing, chunking, and retrieval.
Falls back to basic implementation if LlamaIndex is not installed.
"""

import logging
import hashlib
import os
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Check for LlamaIndex availability
LLAMAINDEX_AVAILABLE = False
try:
    from llama_index.core import Document
    from llama_index.core.node_parser import SentenceSplitter
    LLAMAINDEX_AVAILABLE = True
    logger.info("LlamaIndex available - using enhanced RAG")
except ImportError:
    logger.info("LlamaIndex not installed - using basic RAG")


@dataclass
class DocumentChunk:
    """A chunk of a document for embedding."""
    id: str
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class RAGService:
    """
    Retrieval Augmented Generation service.
    
    Uses VectorStore with optional LlamaIndex enhancement for:
    - Smart document chunking (sentence-based with LlamaIndex)
    - Semantic search
    - Context retrieval for LLM prompts
    """
    
    COLLECTION_DOCUMENTS = "documents"
    COLLECTION_KNOWLEDGE = "knowledge_nodes"
    COLLECTION_CHAT_HISTORY = "chat_history"
    COLLECTION_PERSONA_PROFILES = "persona_profiles"
    COLLECTION_CITATION_CACHE = "citation_cache"
    COLLECTION_AUDIT_EVIDENCE = "audit_evidence"
    SUSPICIOUS_RETRIEVAL_MARKERS = (
        "ignore previous instructions",
        "system prompt",
        "developer message",
        "tool call",
        "BEGIN PROMPT",
        "END PROMPT",
    )
    
    def __init__(
        self,
        vector_store=None,
        embedding_provider=None,
        *,
        embedding_revision: str | None = None,
        embedding_dimensions: int = 384,
    ):
        """
        Initialize RAG service.
        
        Args:
            vector_store: VectorStore instance (uses global if None)
            embedding_provider: Function to generate embeddings (uses mock if None)
        """
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider or self._default_embedding
        self.embedding_revision = str(
            embedding_revision
            or os.environ.get("DLE_EMBEDDING_REVISION")
            or (
                "local-sha256-projection-v1"
                if embedding_provider is None
                else "configured-embedding-provider-v1"
            )
        )
        self.embedding_dimensions = max(1, int(embedding_dimensions))
        self._initialized = False
        self._sentence_splitter = None
        
        if LLAMAINDEX_AVAILABLE:
            # Configure LlamaIndex sentence splitter
            self._sentence_splitter = SentenceSplitter(
                chunk_size=512,
                chunk_overlap=50,
                paragraph_separator="\n\n",
                secondary_chunking_regex="[.。!?！？]"
            )
        
    def _get_vector_store(self):
        """Lazy load vector store."""
        if self._vector_store is None:
            try:
                from backend.storage import get_vector_store
                self._vector_store = get_vector_store()
            except Exception as e:
                logger.warning(f"VectorStore not available: {e}")
                return None
        return self._vector_store
    
    def _default_embedding(self, text: str) -> List[float]:
        """
        Generate a local deterministic projection without provider egress.

        Cloud embeddings are never implicit. A workflow that needs them must
        inject an explicitly budgeted and disclosed provider function.
        """
        cache_key = self._embedding_cache_key(text)
        cached_embedding = self._get_cached_embedding(cache_key)
        if cached_embedding is not None:
            return cached_embedding

        embedding = self._deterministic_embedding(text)
        self._set_cached_embedding(cache_key, embedding)
        return embedding

    @staticmethod
    def _embedding_cache_key(text: str) -> str:
        return f"embedding:{hashlib.sha256(text.encode()).hexdigest()}"

    @staticmethod
    def _redis_embedding_client():
        if os.environ.get("USE_REDIS", "false").lower() not in {"1", "true", "yes", "on"}:
            return None
        try:
            import redis

            from backend.storage.runtime_endpoints import runtime_redis_url

            client = redis.Redis.from_url(runtime_redis_url(), decode_responses=True)
            client.ping()
            return client
        except Exception as exc:
            logger.debug("Embedding Redis cache unavailable: %s", exc)
            return None

    @classmethod
    def _get_cached_embedding(cls, cache_key: str) -> Optional[List[float]]:
        client = cls._redis_embedding_client()
        if client is None:
            return None
        try:
            raw = client.hget(cache_key, "value")
            if raw is None:
                return None
            value = json.loads(raw)
            return value if isinstance(value, list) else None
        except Exception as exc:
            logger.debug("Embedding Redis cache get failed for %s: %s", cache_key, exc)
            return None

    @classmethod
    def _set_cached_embedding(cls, cache_key: str, embedding: List[float]) -> None:
        client = cls._redis_embedding_client()
        if client is None:
            return
        try:
            ttl = 3600
            client.hset(cache_key, mapping={
                "value": json.dumps(embedding),
                "expires_at": str(time.time() + ttl),
            })
            client.expire(cache_key, ttl)
        except Exception as exc:
            logger.debug("Embedding Redis cache set failed for %s: %s", cache_key, exc)
    
    def _deterministic_embedding(self, text: str) -> List[float]:
        """Generate a stable 384-dimension local projection."""
        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = []
        for i in range(self.embedding_dimensions):
            byte_idx = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_idx] - 128) / 128.0)
        return embedding

    # Test compatibility alias; production code uses the explicit name above.
    _mock_embedding = _deterministic_embedding
    
    def set_embedding_provider(self, provider):
        """Set the embedding provider function."""
        self._embedding_provider = provider
        
    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """
        Split text into chunks for embedding.
        
        Uses LlamaIndex SentenceSplitter if available, otherwise
        falls back to basic character-based splitting.
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Use LlamaIndex for better chunking
        if LLAMAINDEX_AVAILABLE and self._sentence_splitter:
            try:
                # Create a LlamaIndex Document
                doc = Document(text=text)
                nodes = self._sentence_splitter.get_nodes_from_documents([doc])
                return [node.get_content() for node in nodes]
            except Exception as e:
                logger.warning(f"LlamaIndex chunking failed, falling back: {e}")
        
        # Fallback to basic chunking
        return self._basic_chunk_text(text, chunk_size, overlap)
    
    def _basic_chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Basic character-based text chunking with sentence boundary awareness."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            # Try to break at sentence boundary
            if end < len(text):
                for sep in ['. ', '.\n', '! ', '? ', '\n\n', '\n', ' ']:
                    last_sep = text.rfind(sep, start + chunk_size // 2, end)
                    if last_sep > start:
                        end = last_sep + len(sep)
                        break
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap if end < len(text) else end
        return chunks
    
    def ingest_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 512
    ) -> int:
        """
        Ingest a document into the vector store.
        
        Args:
            doc_id: Unique document identifier
            text: Full document text
            metadata: Document metadata
            chunk_size: Size of text chunks
            
        Returns:
            Number of chunks ingested
        """
        store = self._get_vector_store()
        if store is None:
            logger.warning("VectorStore not available, skipping ingestion")
            return 0
        
        chunks = self.chunk_text(text, chunk_size)
        
        if not chunks:
            logger.warning(f"No chunks generated for document {doc_id}")
            return 0
        
        try:
            ids = []
            texts = []
            embeddings = []
            chunk_metadata = []

            for i, chunk_text in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                ids.append(chunk_id)
                texts.append(chunk_text)
                embeddings.append(self._embedding_provider(chunk_text))
                chunk_metadata.append({
                    **(metadata or {}),
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "chunk_count": len(chunks)
                })

            store.add_embeddings(
                collection=self.COLLECTION_DOCUMENTS,
                ids=ids,
                texts=texts,
                embeddings=embeddings,
                metadata=chunk_metadata
            )
            logger.info(f"Ingested document {doc_id}: {len(chunks)} chunks")
            return len(chunks)
        except Exception as e:
            logger.error(f"Failed to ingest document {doc_id}: {e}")
            return 0
    
    def search_documents(
        self,
        query: str,
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        collection: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks.
        
        Args:
            query: Search query text
            k: Number of results to return
            filters: Optional metadata filters
            collection: Collection to search (default: documents)
            
        Returns:
            List of matching chunks with scores
        """
        store = self._get_vector_store()
        if store is None:
            logger.warning("VectorStore not available")
            return []

        try:
            query_embedding = self._embedding_provider(query)
        except Exception as e:
            logger.error(f"Embedding generation failed for retrieval query: {e}")
            return []
        target_collection = collection or self.COLLECTION_DOCUMENTS
        
        try:
            results = store.search(
                collection=target_collection,
                query_embedding=query_embedding,
                k=k,
                filters=filters
            )
            return [
                {
                    "id": r.id,
                    "text": r.text,
                    "score": r.score,
                    "metadata": r.metadata,
                    "citation": self._citation_from_result(r.id, r.metadata),
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 2000,
        k: int = 5,
        include_sources: bool = False
    ) -> str:
        """
        Get relevant context for a query (for LLM).
        
        Args:
            query: User query
            max_tokens: Approximate max tokens for context
            k: Number of chunks to retrieve
            include_sources: Whether to include source document references
            
        Returns:
            Formatted context string
        """
        results = self.search_documents(query, k=k)
        
        if not results:
            return ""
        
        context_parts = []
        char_count = 0
        max_chars = max_tokens * 4  # Approximate chars per token
        min_score = float(os.environ.get("RAG_MIN_SCORE", "0.15"))
        
        for r in results:
            text = r.get("text", "")
            score = float(r.get("score", 0.0) or 0.0)
            lowered = text.lower()
            if score < min_score:
                continue
            if any(marker.lower() in lowered for marker in self.SUSPICIOUS_RETRIEVAL_MARKERS):
                logger.warning("Skipping suspicious retrieval chunk id=%s", r.get("id", "unknown"))
                continue
            if char_count + len(text) > max_chars:
                break
            
            if include_sources:
                citation = r.get("citation") or self._citation_from_result(
                    str(r.get("id", "")),
                    r.get("metadata", {}),
                )
                source = citation.get("source_title") or citation.get("source_path") or "Unknown"
                locator = citation.get("locator") or {}
                chunk = locator.get("chunk_index")
                chunk_count = locator.get("chunk_count")
                chunk_suffix = f" chunk {chunk + 1}/{chunk_count}" if isinstance(chunk, int) and chunk_count else ""
                context_parts.append(f"[Source: {source}{chunk_suffix}]\n{text}")
            else:
                context_parts.append(text)
            
            char_count += len(text)
        
        return "\n\n---\n\n".join(context_parts)
    
    def store_chat_message(
        self,
        session_id: str,
        message_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """Store chat message embedding for semantic history search."""
        store = self._get_vector_store()
        if store is None:
            return False
        
        try:
            embedding = self._embedding_provider(content)
            store.add_embeddings(
                collection=self.COLLECTION_CHAT_HISTORY,
                ids=[message_id],
                texts=[content],
                embeddings=[embedding],
                metadata=[{
                    "session_id": session_id,
                    "role": role,
                    "user_id": user_id or "",
                }]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store chat message: {e}")
            return False
    
    def search_chat_history(
        self,
        session_id: str,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search chat history semantically."""
        return self.search_documents(
            query,
            k=k,
            filters={"session_id": session_id},
            collection=self.COLLECTION_CHAT_HISTORY
        )

    def search_user_chat_history(
        self,
        user_id: str,
        query: str,
        k: int = 8,
        exclude_session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search semantically relevant chat history across all sessions for a user."""
        results = self.search_documents(
            query,
            k=k,
            filters={"user_id": user_id},
            collection=self.COLLECTION_CHAT_HISTORY
        )
        if not exclude_session_id:
            return results
        return [r for r in results if r.get("metadata", {}).get("session_id") != exclude_session_id]

    @staticmethod
    def _metadata_for_chroma(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Normalize metadata to Chroma-compatible scalar values."""
        normalized = {}
        for key, value in (metadata or {}).items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                normalized[key] = value
            else:
                normalized[key] = json.dumps(value, sort_keys=True, default=str)
        return normalized

    @staticmethod
    def _loads_json_like(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if not stripped or stripped[0] not in "[{":
            return value
        try:
            return json.loads(stripped)
        except Exception:
            return value

    @classmethod
    def _citation_from_result(cls, result_id: str, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build trace-friendly citation metadata from a vector search hit."""
        raw = {key: cls._loads_json_like(value) for key, value in (metadata or {}).items()}
        source_path = raw.get("source_path") or raw.get("filename") or raw.get("source")
        source_title = raw.get("title") or raw.get("file_name") or raw.get("node_id") or source_path
        return {
            "evidence_id": result_id,
            "source_type": raw.get("source") or "vector",
            "source_path": source_path,
            "source_title": source_title,
            "content_hash": raw.get("content_hash"),
            "chunk_hash": raw.get("chunk_hash"),
            "locator": {
                "chunk_index": raw.get("chunk_index"),
                "chunk_count": raw.get("chunk_count"),
                "node_id": raw.get("node_id"),
                "uid": raw.get("uid"),
            },
            "ingestion_id": raw.get("ingestion_id"),
        }
    
    def ingest_knowledge_node(
        self,
        node_id: str,
        content: str,
        node_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Ingest a knowledge graph node for semantic search.
        
        Args:
            node_id: Node identifier
            content: Node content/description
            node_type: Type of knowledge node
            metadata: Additional metadata
        """
        store = self._get_vector_store()
        if store is None:
            return False
        try:
            embedding = self._embedding_provider(content)
            store.add_embeddings(
                collection=self.COLLECTION_KNOWLEDGE,
                ids=[node_id],
                texts=[content],
                embeddings=[embedding],
                metadata=[{
                    **self._metadata_for_chroma(metadata),
                    "node_type": node_type
                }]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to ingest knowledge node: {e}")
            return False

    def delete_knowledge_node(self, node_id: str) -> bool:
        """Delete one versioned knowledge-node vector by stable identifier."""
        store = self._get_vector_store()
        if store is None:
            return False
        try:
            return bool(store.delete(self.COLLECTION_KNOWLEDGE, [str(node_id)]))
        except Exception as exc:
            logger.error("Failed to delete knowledge node: %s", exc)
            return False
    
    def search_knowledge(
        self,
        query: str,
        k: int = 5,
        node_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search knowledge graph nodes semantically."""
        filters = {"node_type": node_type} if node_type else None
        return self.search_documents(
            query,
            k=k,
            filters=filters,
            collection=self.COLLECTION_KNOWLEDGE
        )

    def ingest_text(
        self,
        collection: str,
        item_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Ingest one text item into a named vector collection."""
        store = self._get_vector_store()
        if store is None or not text:
            return False
        try:
            store.add_embeddings(
                collection=collection,
                ids=[item_id],
                texts=[text],
                embeddings=[self._embedding_provider(text)],
                metadata=[self._metadata_for_chroma(metadata)],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to ingest text item {item_id} into {collection}: {e}")
            return False

    def search_collection(
        self,
        collection: str,
        query: str,
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search an arbitrary named vector collection."""
        return self.search_documents(query, k=k, filters=filters, collection=collection)


# Global instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
