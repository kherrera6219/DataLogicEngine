"""
RAG (Retrieval Augmented Generation) Service

Enhanced with LlamaIndex for better document parsing, chunking, and retrieval.
Falls back to basic implementation if LlamaIndex is not installed.
"""

import logging
import hashlib
import os
import json
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
    
    def __init__(self, vector_store=None, embedding_provider=None):
        """
        Initialize RAG service.
        
        Args:
            vector_store: VectorStore instance (uses global if None)
            embedding_provider: Function to generate embeddings (uses mock if None)
        """
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider or self._default_embedding
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
        Generate embedding using strict 3-Layer Failover Strategy.
        
        Layer 1: OpenAI (text-embedding-3-small) - Fast, standard.
        Layer 2: Google Gemini (models/text-embedding-004) - High quality fallback.
        Layer 3: Local HuggingFace (all-MiniLM-L6-v2) - Startup safe/Total outage safe.
        """
        errors = []
        
        # --- Layer 1: OpenAI ---
        try:
            import os
            # Check env dynamically
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                try:
                    response = client.embeddings.create(
                        model="text-embedding-3-small",
                        input=text
                    )
                    return response.data[0].embedding
                finally:
                    close_client = getattr(client, "close", None)
                    if callable(close_client):
                        close_client()
        except Exception as e:
            errors.append(f"OpenAI Failed: {str(e)}")
            logger.warning(f"Embedding Layer 1 (OpenAI) failed: {e}")

        # --- Layer 2: Google Gemini ---
        try:
            import os
            google_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
            if google_key:
                from google import genai
                client = genai.Client(api_key=google_key)
                try:
                    # Use models/text-embedding-004 which is standard for genai sdk
                    result = client.models.embed_content(
                        model="text-embedding-004",
                        contents=text,
                    )
                    return result.embeddings[0].values
                finally:
                    close_client = getattr(client, "close", None)
                    if callable(close_client):
                        close_client()
        except Exception as e:
            errors.append(f"Google Failed: {str(e)}")
            logger.warning(f"Embedding Layer 2 (Google) failed: {e}")

        # --- Layer 3: Local HuggingFace ---
        try:
            from sentence_transformers import SentenceTransformer
            if not hasattr(self, '_hf_model'):
                # Load efficient local model
                self._hf_model = SentenceTransformer('all-MiniLM-L6-v2')
            return self._hf_model.encode(text).tolist()
        except Exception as e:
            errors.append(f"Local Failed: {str(e)}")
            logger.error(f"Embedding Layer 3 (Local) failed: {e}")
            
        # --- Failed All Layers ---
        logger.error(f"All Embedding Layers Failed: {errors}")
        env = os.environ.get("FLASK_ENV", "").lower()
        allow_mock_embeddings = os.environ.get("ALLOW_MOCK_EMBEDDINGS", "false").lower() == "true"
        if allow_mock_embeddings or env in {"development", "testing"}:
            # Development/testing fallback only.
            return self._mock_embedding(text)
        raise RuntimeError("All embedding providers failed in production mode")
    
    def _mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for testing (384 dimensions like MiniLM)."""
        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = []
        for i in range(384):
            byte_idx = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_idx] - 128) / 128.0)
        return embedding
    
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
                    "metadata": r.metadata
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
                source = r.get("metadata", {}).get("filename", "Unknown")
                context_parts.append(f"[Source: {source}]\n{text}")
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
