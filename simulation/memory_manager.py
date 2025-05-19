"""
Universal Knowledge Graph (UKG) System - Memory Manager

This module implements a memory management system for the UKG system,
allowing it to maintain conversational context, store and retrieve
insights, and improve responses over time.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import deque

logger = logging.getLogger(__name__)

class MemoryEntry:
    """
    Represents a single memory entry in the UKG system.
    """
    
    def __init__(self, entry_id: str, content: str, memory_type: str, source: str, 
                 metadata: Dict[str, Any] = None, timestamp: datetime = None):
        """
        Initialize a memory entry.
        
        Args:
            entry_id: Unique identifier for the entry
            content: The memory content
            memory_type: Type of memory (e.g., "fact", "insight", "observation")
            source: Source of the memory (e.g., "user", "system", "persona_knowledge")
            metadata: Additional metadata for the memory
            timestamp: When the memory was created (default: now)
        """
        self.entry_id = entry_id
        self.content = content
        self.memory_type = memory_type
        self.source = source
        self.metadata = metadata or {}
        self.created_at = timestamp or datetime.utcnow()
        self.last_accessed = self.created_at
        self.access_count = 0
        self.salience = 1.0  # How important/relevant this memory is (0.0-1.0)
        self.confidence = 1.0  # Confidence in this memory's accuracy (0.0-1.0)
    
    def access(self):
        """Record an access to this memory entry."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
    
    def update_salience(self, new_salience: float):
        """Update the salience (importance) of this memory."""
        self.salience = max(0.0, min(1.0, new_salience))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory entry to a dictionary."""
        return {
            "entry_id": self.entry_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "salience": self.salience,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create a memory entry from a dictionary."""
        entry = cls(
            entry_id=data.get("entry_id", str(uuid.uuid4())),
            content=data.get("content", ""),
            memory_type=data.get("memory_type", "insight"),
            source=data.get("source", "system"),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat()))
        )
        if "last_accessed" in data:
            entry.last_accessed = datetime.fromisoformat(data["last_accessed"])
        entry.access_count = data.get("access_count", 0)
        entry.salience = data.get("salience", 1.0)
        entry.confidence = data.get("confidence", 1.0)
        return entry


class MemoryStream:
    """
    Represents a stream of related memories in the UKG system.
    """
    
    def __init__(self, stream_id: str, name: str, stream_type: str, metadata: Dict[str, Any] = None):
        """
        Initialize a memory stream.
        
        Args:
            stream_id: Unique identifier for the stream
            name: Name of the stream
            stream_type: Type of stream (e.g., "conversation", "topic", "persona")
            metadata: Additional metadata for the stream
        """
        self.stream_id = stream_id
        self.name = name
        self.stream_type = stream_type
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.last_updated = self.created_at
        self.entries: Dict[str, MemoryEntry] = {}
    
    def add_entry(self, entry: MemoryEntry) -> bool:
        """Add a memory entry to the stream."""
        self.entries[entry.entry_id] = entry
        self.last_updated = datetime.utcnow()
        return True
    
    def get_entry(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get a memory entry by ID."""
        entry = self.entries.get(entry_id)
        if entry:
            entry.access()
        return entry
    
    def find_entries(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        Find relevant memory entries based on the query.
        
        In a real implementation, this would use semantic search or similar techniques.
        For now, we use simple keyword matching.
        """
        query_words = set(query.lower().split())
        relevant_entries = []
        
        for entry in self.entries.values():
            # Simple keyword matching
            content_words = set(entry.content.lower().split())
            keyword_overlap = len(query_words.intersection(content_words)) / max(1, len(query_words))
            
            # Combine with recency and salience for an overall score
            recency_factor = 1.0  # Could decay based on time since last access
            score = keyword_overlap * entry.salience * recency_factor
            
            if score > 0:
                relevant_entries.append((entry, score))
        
        # Sort by relevance score
        relevant_entries.sort(key=lambda x: x[1], reverse=True)
        
        # Return top entries
        entries = [entry for entry, _ in relevant_entries[:limit]]
        
        # Mark entries as accessed
        for entry in entries:
            entry.access()
        
        return entries
    
    def get_recent_entries(self, limit: int = 10) -> List[MemoryEntry]:
        """Get the most recent memory entries."""
        # Sort by creation time, newest first
        sorted_entries = sorted(
            self.entries.values(),
            key=lambda entry: entry.created_at,
            reverse=True
        )
        return sorted_entries[:limit]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory stream to a dictionary."""
        return {
            "stream_id": self.stream_id,
            "name": self.name,
            "stream_type": self.stream_type,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "entries": {entry_id: entry.to_dict() for entry_id, entry in self.entries.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryStream':
        """Create a memory stream from a dictionary."""
        stream = cls(
            stream_id=data.get("stream_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            stream_type=data.get("stream_type", "general"),
            metadata=data.get("metadata", {})
        )
        if "created_at" in data:
            stream.created_at = datetime.fromisoformat(data["created_at"])
        if "last_updated" in data:
            stream.last_updated = datetime.fromisoformat(data["last_updated"])
        
        # Load entries
        entries_data = data.get("entries", {})
        for entry_id, entry_data in entries_data.items():
            entry = MemoryEntry.from_dict(entry_data)
            stream.entries[entry_id] = entry
        
        return stream


class WorkingMemory:
    """
    Represents the working memory of the UKG system.
    
    Working memory contains recently accessed or created information
    that is actively being used in the current processing context.
    """
    
    def __init__(self, capacity: int = 20):
        """Initialize working memory with a specified capacity."""
        self.items = deque(maxlen=capacity)
        self.capacity = capacity
        self.metadata = {}
    
    def add(self, item: Any) -> bool:
        """Add an item to working memory."""
        self.items.append({
            "content": item,
            "timestamp": datetime.utcnow().isoformat()
        })
        return True
    
    def get_recent(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get the most recent items from working memory."""
        items = list(self.items)
        return items[-limit:] if limit is not None else items
    
    def clear(self):
        """Clear working memory."""
        self.items.clear()
        return True


class MemoryManager:
    """
    Manages memory for the UKG system, including both long-term and working memory.
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the memory manager.
        
        Args:
            storage_path: Path for persistent memory storage
        """
        self.storage_path = storage_path or os.path.join('data', 'memory.json')
        self.streams: Dict[str, MemoryStream] = {}
        self.working_memory = WorkingMemory()
        
        # Create default memory streams for each persona type
        self._initialize_default_streams()
        
        # Try to load memories from storage
        self._load_memories()
    
    def _initialize_default_streams(self):
        """Initialize default memory streams."""
        default_streams = [
            ("general", "General Memory", "system"),
            ("knowledge_expert", "Knowledge Expert Memory", "persona"),
            ("sector_expert", "Sector Expert Memory", "persona"),
            ("regulatory_expert", "Regulatory Expert Memory", "persona"),
            ("compliance_expert", "Compliance Expert Memory", "persona")
        ]
        
        for stream_id, name, stream_type in default_streams:
            if stream_id not in self.streams:
                stream = MemoryStream(stream_id, name, stream_type)
                self.streams[stream_id] = stream
    
    def _load_memories(self):
        """Load memories from storage."""
        if not os.path.exists(self.storage_path):
            logger.info(f"No memory storage found at {self.storage_path}, starting with empty memory")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                
                # Load memory streams
                streams_data = data.get("streams", {})
                for stream_id, stream_data in streams_data.items():
                    self.streams[stream_id] = MemoryStream.from_dict(stream_data)
                
                logger.info(f"Loaded {len(self.streams)} memory streams from {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to load memories from {self.storage_path}: {e}")
    
    def save_memories(self):
        """Save memories to storage."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # Prepare data for saving
            data = {
                "streams": {stream_id: stream.to_dict() for stream_id, stream in self.streams.items()},
                "last_saved": datetime.utcnow().isoformat()
            }
            
            # Write to file
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(self.streams)} memory streams to {self.storage_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save memories to {self.storage_path}: {e}")
            return False
    
    def create_memory_stream(self, name: str, stream_type: str, stream_id: str = None, 
                           metadata: Dict[str, Any] = None) -> str:
        """
        Create a new memory stream.
        
        Args:
            name: Name of the stream
            stream_type: Type of stream
            stream_id: Optional ID for the stream (generated if not provided)
            metadata: Additional metadata for the stream
            
        Returns:
            The ID of the created stream
        """
        stream_id = stream_id or str(uuid.uuid4())
        
        if stream_id in self.streams:
            logger.warning(f"Memory stream with ID {stream_id} already exists, will not overwrite")
            return stream_id
        
        stream = MemoryStream(stream_id, name, stream_type, metadata)
        self.streams[stream_id] = stream
        
        logger.info(f"Created memory stream: {name} (ID: {stream_id}, Type: {stream_type})")
        return stream_id
    
    def get_memory_stream(self, stream_id: str) -> Optional[MemoryStream]:
        """Get a memory stream by ID."""
        return self.streams.get(stream_id)
    
    def add_memory(self, content: str, memory_type: str, source: str, stream_id: str = "general", 
                 metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Add a memory to a specific stream.
        
        Args:
            content: The memory content
            memory_type: Type of memory
            source: Source of the memory
            stream_id: ID of the stream to add to
            metadata: Additional metadata for the memory
            
        Returns:
            The ID of the created memory entry, or None if the stream doesn't exist
        """
        stream = self.get_memory_stream(stream_id)
        if not stream:
            logger.warning(f"Cannot add memory: stream {stream_id} not found")
            return None
        
        entry_id = str(uuid.uuid4())
        entry = MemoryEntry(entry_id, content, memory_type, source, metadata)
        
        if stream.add_entry(entry):
            # Also add to working memory
            self.working_memory.add({
                "entry_id": entry_id,
                "content": content,
                "stream_id": stream_id,
                "type": memory_type,
                "source": source
            })
            
            logger.debug(f"Added memory to stream {stream_id}: {content[:50]}...")
            return entry_id
        
        return None
    
    def find_memories(self, query: str, stream_ids: List[str] = None, 
                    limit: int = 5) -> Dict[str, List[MemoryEntry]]:
        """
        Find relevant memories across specified streams.
        
        Args:
            query: The query to search for
            stream_ids: IDs of streams to search
            limit: Maximum number of memories to return per stream
            
        Returns:
            A dictionary mapping stream IDs to lists of relevant memories
        """
        results = {}
        stream_ids = stream_ids or list(self.streams.keys())
        
        for stream_id in stream_ids:
            stream = self.get_memory_stream(stream_id)
            if stream:
                entries = stream.find_entries(query, limit)
                if entries:
                    results[stream_id] = entries
        
        return results
    
    def get_conversation_memories(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get memories from a specific conversation.
        
        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of memories to return
            
        Returns:
            A list of conversation memory entries
        """
        stream_id = f"conversation_{conversation_id}"
        stream = self.get_memory_stream(stream_id)
        
        if not stream:
            return []
        
        entries = stream.get_recent_entries(limit)
        return [entry.to_dict() for entry in entries]
    
    def extract_insights(self, query: str, response: str, persona_responses: Dict[str, str]) -> List[str]:
        """
        Extract insights from a query and response, and store them in memory.
        
        Args:
            query: The original query
            response: The final synthesized response
            persona_responses: Responses from different personas
            
        Returns:
            List of created memory entry IDs
        """
        created_entries = []
        
        # Store the query itself as a memory
        query_entry_id = self.add_memory(
            content=query,
            memory_type="query",
            source="user",
            stream_id="general",
            metadata={"timestamp": datetime.utcnow().isoformat()}
        )
        if query_entry_id:
            created_entries.append(query_entry_id)
        
        # Store insights from each persona
        for persona_type, persona_response in persona_responses.items():
            stream_id = f"{persona_type}_expert"
            
            # Add to the persona's memory stream if it exists
            if stream_id in self.streams:
                entry_id = self.add_memory(
                    content=persona_response,
                    memory_type="insight",
                    source=persona_type,
                    stream_id=stream_id,
                    metadata={
                        "query": query,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                if entry_id:
                    created_entries.append(entry_id)
        
        return created_entries
    
    def create_conversation_memory(self, conversation_id: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Create a memory stream for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            metadata: Additional metadata for the conversation
            
        Returns:
            True if created successfully, False otherwise
        """
        stream_id = f"conversation_{conversation_id}"
        
        # Check if already exists
        if stream_id in self.streams:
            return True
        
        # Create the stream
        name = f"Conversation {conversation_id}"
        self.create_memory_stream(name, "conversation", stream_id, metadata)
        return stream_id in self.streams
    
    def add_conversation_memory(self, conversation_id: str, role: str, content: str, 
                              metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Add a memory to a conversation stream.
        
        Args:
            conversation_id: ID of the conversation
            role: Role of the message sender (e.g., "user", "system")
            content: Content of the message
            metadata: Additional metadata for the memory
            
        Returns:
            The ID of the created memory entry, or None if the stream doesn't exist
        """
        # Ensure conversation stream exists
        stream_id = f"conversation_{conversation_id}"
        if stream_id not in self.streams:
            if not self.create_conversation_memory(conversation_id):
                return None
        
        # Add the memory
        memory_type = "message"
        source = role
        entry_id = self.add_memory(content, memory_type, source, stream_id, metadata)
        return entry_id
    
    def get_working_memory(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get items from working memory."""
        return self.working_memory.get_recent(limit)
    
    def clear_working_memory(self):
        """Clear working memory."""
        return self.working_memory.clear()
    
    def generate_memory_context(self, query: str, conversation_id: str = None) -> Dict[str, Any]:
        """
        Generate a context object with relevant memories for a query.
        
        Args:
            query: The query to generate context for
            conversation_id: Optional conversation ID for conversation-specific memories
            
        Returns:
            A context dictionary with relevant memories
        """
        context = {
            "memories": {},
            "working_memory": self.get_working_memory(5),  # Last 5 items
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Determine which memory streams to search
        search_streams = ["general", "knowledge_expert", "sector_expert", "regulatory_expert", "compliance_expert"]
        
        # Add conversation-specific stream if provided
        if conversation_id:
            conversation_stream = f"conversation_{conversation_id}"
            if conversation_stream in self.streams:
                search_streams.append(conversation_stream)
        
        # Find relevant memories
        memory_results = self.find_memories(query, search_streams)
        
        # Add to context
        for stream_id, entries in memory_results.items():
            context["memories"][stream_id] = [entry.to_dict() for entry in entries]
        
        return context