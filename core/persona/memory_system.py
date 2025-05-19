"""
Universal Knowledge Graph (UKG) System - Memory Management System

This module implements a memory management system for the quad persona engine
to store, retrieve, and utilize contextual information across sessions.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import deque

logger = logging.getLogger(__name__)

class MemoryEntry:
    """Represents a single memory entry in the UKG memory system."""
    
    def __init__(self, content: str, memory_type: str, source: str, metadata: Dict[str, Any] = None):
        """Initialize a memory entry."""
        self.uid = str(uuid.uuid4())
        self.content = content
        self.memory_type = memory_type  # e.g., "fact", "insight", "feedback", "rule"
        self.source = source  # e.g., "user", "system", "knowledge_expert", "compliance_expert"
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.accessed_at = datetime.utcnow()
        self.access_count = 0
        self.importance = 1.0
        self.confidence = 1.0
    
    def access(self):
        """Record an access to this memory entry."""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1
    
    def update_importance(self, new_importance: float):
        """Update the importance score of this memory entry."""
        self.importance = max(0.0, min(1.0, new_importance))
    
    def update_confidence(self, new_confidence: float):
        """Update the confidence score of this memory entry."""
        self.confidence = max(0.0, min(1.0, new_confidence))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory entry to a dictionary."""
        return {
            "uid": self.uid,
            "content": self.content,
            "memory_type": self.memory_type,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "access_count": self.access_count,
            "importance": self.importance,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create a memory entry from a dictionary."""
        entry = cls(
            content=data.get("content", ""),
            memory_type=data.get("memory_type", "fact"),
            source=data.get("source", "system"),
            metadata=data.get("metadata", {})
        )
        entry.uid = data.get("uid", entry.uid)
        entry.created_at = datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat()))
        entry.accessed_at = datetime.fromisoformat(data.get("accessed_at", datetime.utcnow().isoformat()))
        entry.access_count = data.get("access_count", 0)
        entry.importance = data.get("importance", 1.0)
        entry.confidence = data.get("confidence", 1.0)
        return entry


class MemoryContext:
    """Represents a specific context for memories in the UKG memory system."""
    
    def __init__(self, name: str, context_type: str, metadata: Dict[str, Any] = None):
        """Initialize a memory context."""
        self.uid = str(uuid.uuid4())
        self.name = name
        self.context_type = context_type  # e.g., "conversation", "user", "domain", "persona"
        self.metadata = metadata or {}
        self.memories = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_memory(self, memory: MemoryEntry) -> bool:
        """Add a memory entry to this context."""
        self.memories.append(memory)
        self.updated_at = datetime.utcnow()
        return True
    
    def find_memories(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        Find relevant memories based on a query string.
        
        In a real implementation, this would use semantic search or similar techniques.
        For now, we use a simple keyword matching approach.
        """
        # Simple keyword matching for demonstration
        query_words = set(query.lower().split())
        relevant_memories = []
        
        for memory in self.memories:
            content_words = set(memory.content.lower().split())
            # Calculate a simple relevance score based on word overlap
            overlap = len(query_words.intersection(content_words))
            if overlap > 0:
                relevance = overlap / len(query_words)
                relevant_memories.append((memory, relevance))
        
        # Sort by relevance and importance
        relevant_memories.sort(key=lambda x: x[1] * x[0].importance, reverse=True)
        
        # Return the top memories
        return [memory for memory, _ in relevant_memories[:limit]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory context to a dictionary."""
        return {
            "uid": self.uid,
            "name": self.name,
            "context_type": self.context_type,
            "metadata": self.metadata,
            "memories": [memory.to_dict() for memory in self.memories],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryContext':
        """Create a memory context from a dictionary."""
        context = cls(
            name=data.get("name", ""),
            context_type=data.get("context_type", "general"),
            metadata=data.get("metadata", {})
        )
        context.uid = data.get("uid", context.uid)
        context.created_at = datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat()))
        context.updated_at = datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat()))
        
        for memory_data in data.get("memories", []):
            memory = MemoryEntry.from_dict(memory_data)
            context.add_memory(memory)
        
        return context


class WorkingMemory:
    """Represents the working memory for a UKG session."""
    
    def __init__(self, capacity: int = 10):
        """Initialize a working memory."""
        self.items = deque(maxlen=capacity)
        self.capacity = capacity
    
    def add(self, item: Any) -> bool:
        """Add an item to working memory."""
        self.items.append(item)
        return True
    
    def get_recent(self, count: int = None) -> List[Any]:
        """Get the most recent items from working memory."""
        if count is None:
            return list(self.items)
        return list(self.items)[-count:]
    
    def clear(self):
        """Clear the working memory."""
        self.items.clear()


class MemoryManager:
    """
    Manages the memory system for the quad persona engine.
    
    The memory system maintains long-term memories across conversations and
    working memory for the current session.
    """
    
    def __init__(self):
        """Initialize the memory manager."""
        self.contexts = {}  # Dictionary of memory contexts
        self.working_memory = WorkingMemory()
        
        # Create default contexts for each persona type
        self._create_default_contexts()
    
    def _create_default_contexts(self):
        """Create default memory contexts for the system."""
        default_contexts = [
            ("general", "general", "System-wide general memory context"),
            ("knowledge_expert", "persona", "Memory context for the Knowledge Expert persona"),
            ("sector_expert", "persona", "Memory context for the Sector Expert persona"),
            ("regulatory_expert", "persona", "Memory context for the Regulatory Expert persona"),
            ("compliance_expert", "persona", "Memory context for the Compliance Expert persona")
        ]
        
        for name, context_type, description in default_contexts:
            context = MemoryContext(name, context_type, {"description": description})
            self.contexts[name] = context
    
    def create_context(self, name: str, context_type: str, metadata: Dict[str, Any] = None) -> MemoryContext:
        """Create a new memory context."""
        if name in self.contexts:
            logger.warning(f"Memory context '{name}' already exists, returning existing context")
            return self.contexts[name]
        
        context = MemoryContext(name, context_type, metadata)
        self.contexts[name] = context
        return context
    
    def get_context(self, name: str) -> Optional[MemoryContext]:
        """Get a memory context by name."""
        return self.contexts.get(name)
    
    def add_memory(self, content: str, memory_type: str, source: str, 
                 context_name: str = "general", metadata: Dict[str, Any] = None) -> Optional[MemoryEntry]:
        """
        Add a memory entry to a specific context.
        
        Args:
            content: The content of the memory
            memory_type: The type of memory (e.g., "fact", "insight")
            source: The source of the memory (e.g., "user", "system")
            context_name: The name of the context to add the memory to
            metadata: Additional metadata for the memory
            
        Returns:
            The created memory entry, or None if the context doesn't exist
        """
        context = self.get_context(context_name)
        if not context:
            logger.warning(f"Memory context '{context_name}' not found")
            return None
        
        memory = MemoryEntry(content, memory_type, source, metadata)
        context.add_memory(memory)
        
        # Add to working memory as well
        self.working_memory.add({
            "content": content,
            "memory_type": memory_type,
            "source": source,
            "context": context_name,
            "uid": memory.uid
        })
        
        return memory
    
    def find_relevant_memories(self, query: str, context_names: List[str] = None, 
                             limit: int = 5) -> Dict[str, List[MemoryEntry]]:
        """
        Find relevant memories across specified contexts.
        
        Args:
            query: The query to search for
            context_names: The names of contexts to search in, or None for all contexts
            limit: The maximum number of memories to return per context
            
        Returns:
            A dictionary mapping context names to lists of relevant memories
        """
        if context_names is None:
            context_names = list(self.contexts.keys())
        
        results = {}
        for name in context_names:
            context = self.get_context(name)
            if context:
                memories = context.find_memories(query, limit)
                if memories:
                    # Mark memories as accessed
                    for memory in memories:
                        memory.access()
                    results[name] = memories
        
        return results
    
    def get_working_memory(self, count: int = None) -> List[Dict[str, Any]]:
        """Get items from working memory."""
        return self.working_memory.get_recent(count)
    
    def clear_working_memory(self):
        """Clear the working memory."""
        self.working_memory.clear()
    
    def extract_insights(self, query: str, persona_responses: Dict[str, Dict[str, Any]]) -> List[MemoryEntry]:
        """
        Extract insights from persona responses and store them in memory.
        
        This method analyzes the responses from different personas and extracts
        key insights to be stored in memory for future reference.
        
        Args:
            query: The original query
            persona_responses: The responses from different personas
            
        Returns:
            A list of the memory entries created
        """
        created_memories = []
        
        for persona_type, response_data in persona_responses.items():
            # Skip if no response content
            if not response_data.get("response"):
                continue
                
            # Create a memory entry for the persona's response
            context_name = f"{persona_type}_expert" if persona_type != "knowledge" else "knowledge_expert"
            memory = self.add_memory(
                content=response_data["response"],
                memory_type="insight",
                source=persona_type,
                context_name=context_name,
                metadata={
                    "query": query,
                    "confidence": response_data.get("confidence", 0.7),
                    "components_used": response_data.get("components_used", [])
                }
            )
            
            if memory:
                created_memories.append(memory)
        
        return created_memories
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory manager to a dictionary."""
        return {
            "contexts": {name: context.to_dict() for name, context in self.contexts.items()},
            "working_memory": self.get_working_memory()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryManager':
        """Create a memory manager from a dictionary."""
        manager = cls()
        
        # Clear default contexts
        manager.contexts = {}
        
        # Load contexts
        for name, context_data in data.get("contexts", {}).items():
            manager.contexts[name] = MemoryContext.from_dict(context_data)
        
        # Load working memory
        for item in data.get("working_memory", []):
            manager.working_memory.add(item)
        
        return manager


# Singleton instance for global access
_memory_manager_instance = None

def get_memory_manager() -> MemoryManager:
    """Get the singleton instance of the memory manager."""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance