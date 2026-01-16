"""
Structured Memory Manager

This module provides the memory management system for the UKG application.
It manages persistent memory storage, retrieval, and organization.
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

class StructuredMemoryManager:
    """
    Structured Memory Manager
    
    This component manages all memory operations for the UKG system, including
    storing, retrieving, and organizing memory entries. It provides a unified
    interface for memory operations across the system.
    """
    
    def __init__(self, config=None):
        """
        Initialize the Structured Memory Manager.
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        logging.info(f"[{datetime.now()}] Initializing StructuredMemoryManager...")
        self.config = config or {}
        
        # Configure memory manager settings
        self.memory_config = self.config.get('memory_manager', {})
        
        # Memory cache for performance
        self.memory_cache = {}
        
        # Database manager reference (will be set by system initializer)
        self.db_manager = None
        
        # Stats
        self.stats = {
            'entries_created': 0,
            'entries_retrieved': 0,
            'entries_updated': 0,
            'entries_deleted': 0
        }
        
        logging.info(f"[{datetime.now()}] StructuredMemoryManager initialized")
    
    def set_db_manager(self, db_manager):
        """
        Set the database manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        logging.info(f"[{datetime.now()}] SMM: Database manager set")
    
    def store_memory(self, memory_type: str, content: Dict, 
                   session_id: Optional[str] = None,
                   key: Optional[str] = None,
                   confidence: Optional[float] = None,
                   expiration: Optional[datetime] = None,
                   meta_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Store a memory entry.
        
        Args:
            memory_type: Type of memory (e.g., "knowledge", "context")
            content: Memory content
            session_id: Optional session ID
            key: Optional key for direct lookup
            confidence: Optional confidence score
            expiration: Optional expiration time
            meta_data: Optional metadata
            
        Returns:
            dict: Stored memory entry or None if storage failed
        """
        # Generate UID
        uid = f"MEM_{memory_type.upper()}_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
        
        # Create memory entry
        memory_entry = {
            'uid': uid,
            'memory_type': memory_type,
            'content': content,
            'session_id': session_id,
            'key': key,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat(),
            'expiration': expiration.isoformat() if expiration else None,
            'meta_data': meta_data or {}
        }
        
        # Store in database
        if self.db_manager:
            stored_entry = self.db_manager.create_memory_entry(memory_entry)
            
            if stored_entry:
                # Add to cache
                self.memory_cache[uid] = stored_entry
                
                # Update stats
                self.stats['entries_created'] += 1
                
                return stored_entry
            
            return None
        
        # For testing/development without database
        self.memory_cache[uid] = memory_entry
        self.stats['entries_created'] += 1
        return memory_entry
    
    def get_memory(self, uid: str) -> Optional[Dict]:
        """
        Get a memory entry by UID.
        
        Args:
            uid: Memory entry UID
            
        Returns:
            dict: Memory entry or None if not found
        """
        # Check cache first
        if uid in self.memory_cache:
            memory = self.memory_cache[uid]
            
            # Check if expired
            if memory.get('expiration'):
                try:
                    expiration = datetime.fromisoformat(memory['expiration'])
                    if expiration < datetime.now():
                        # Memory has expired, remove from cache
                        del self.memory_cache[uid]
                        return None
                except (ValueError, TypeError):
                    pass  # Invalid date format, assume not expired
            
            self.stats['entries_retrieved'] += 1
            return memory
        
        # Query database
        if self.db_manager:
            memory = self.db_manager.get_memory_entry_by_uid(uid)
            
            if memory:
                # Check if expired
                if memory.get('expiration'):
                    try:
                        expiration = datetime.fromisoformat(memory['expiration'])
                        if expiration < datetime.now():
                            return None
                    except (ValueError, TypeError):
                        pass  # Invalid date format, assume not expired
                
                # Add to cache
                self.memory_cache[uid] = memory
                self.stats['entries_retrieved'] += 1
                return memory
        
        return None
    
    def get_memory_by_key(self, key: str, memory_type: Optional[str] = None) -> Optional[Dict]:
        """
        Get a memory entry by key.
        
        Args:
            key: Memory entry key
            memory_type: Optional memory type to filter by
            
        Returns:
            dict: Memory entry or None if not found
        """
        # Query database
        if self.db_manager:
            filters = {'key': key}
            if memory_type:
                filters['memory_type'] = memory_type
            
            entries = self.db_manager.find_memory_entries(filters, limit=1)
            
            if entries:
                memory = entries[0]
                
                # Check if expired
                if memory.get('expiration'):
                    try:
                        expiration = datetime.fromisoformat(memory['expiration'])
                        if expiration < datetime.now():
                            return None
                    except (ValueError, TypeError):
                        pass  # Invalid date format, assume not expired
                
                # Add to cache
                uid = memory.get('uid')
                if uid:
                    self.memory_cache[uid] = memory
                
                self.stats['entries_retrieved'] += 1
                return memory
        
        # For testing/development without database
        # Search through cache
        for uid, memory in self.memory_cache.items():
            if memory.get('key') == key and (not memory_type or memory.get('memory_type') == memory_type):
                # Check if expired
                if memory.get('expiration'):
                    try:
                        expiration = datetime.fromisoformat(memory['expiration'])
                        if expiration < datetime.now():
                            continue
                    except (ValueError, TypeError):
                        pass  # Invalid date format, assume not expired
                
                self.stats['entries_retrieved'] += 1
                return memory
        
        return None
    
    def update_memory(self, uid: str, updates: Dict) -> Optional[Dict]:
        """
        Update a memory entry.
        
        Args:
            uid: Memory entry UID
            updates: Dictionary of updates
            
        Returns:
            dict: Updated memory entry or None if update failed
        """
        # Update in database
        if self.db_manager:
            updated_memory = self.db_manager.update_memory_entry(uid, updates)
            
            if updated_memory:
                # Update cache
                self.memory_cache[uid] = updated_memory
                
                # Update stats
                self.stats['entries_updated'] += 1
                
                return updated_memory
            
            return None
        
        # For testing/development without database
        if uid in self.memory_cache:
            memory = self.memory_cache[uid].copy()
            memory.update(updates)
            self.memory_cache[uid] = memory
            self.stats['entries_updated'] += 1
            return memory
        
        return None
    
    def delete_memory(self, uid: str) -> bool:
        """
        Delete a memory entry.
        
        Args:
            uid: Memory entry UID
            
        Returns:
            bool: True if deletion was successful
        """
        # Delete from database
        if self.db_manager:
            success = self.db_manager.delete_memory_entry(uid)
            
            if success:
                # Remove from cache
                if uid in self.memory_cache:
                    del self.memory_cache[uid]
                
                # Update stats
                self.stats['entries_deleted'] += 1
                
                return True
            
            return False
        
        # For testing/development without database
        if uid in self.memory_cache:
            del self.memory_cache[uid]
            self.stats['entries_deleted'] += 1
            return True
        
        return False
    
    def find_memories(self, filters: Dict, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Find memory entries matching filters.
        
        Args:
            filters: Dictionary of filter conditions
            limit: Maximum number of entries to return
            offset: Offset for pagination
            
        Returns:
            list: List of matching memory entries
        """
        # Query database
        if self.db_manager:
            memories = self.db_manager.find_memory_entries(filters, limit, offset)
            
            # Filter out expired memories
            valid_memories = []
            for memory in memories:
                if memory.get('expiration'):
                    try:
                        expiration = datetime.fromisoformat(memory['expiration'])
                        if expiration < datetime.now():
                            continue
                    except (ValueError, TypeError):
                        pass  # Invalid date format, assume not expired
                
                # Add to cache
                uid = memory.get('uid')
                if uid:
                    self.memory_cache[uid] = memory
                
                valid_memories.append(memory)
            
            self.stats['entries_retrieved'] += len(valid_memories)
            return valid_memories
        
        # For testing/development without database
        # Filter memories in cache
        result = []
        for uid, memory in self.memory_cache.items():
            # Check filters
            matches = True
            for key, value in filters.items():
                if key not in memory or memory[key] != value:
                    matches = False
                    break
            
            if matches:
                # Check if expired
                if memory.get('expiration'):
                    try:
                        expiration = datetime.fromisoformat(memory['expiration'])
                        if expiration < datetime.now():
                            continue
                    except (ValueError, TypeError):
                        pass  # Invalid date format, assume not expired
                
                result.append(memory)
        
        # Apply pagination
        paginated = result[offset:offset+limit]
        self.stats['entries_retrieved'] += len(paginated)
        return paginated
    
    def find_by_content(self, content_query: Dict, memory_type: Optional[str] = None,
                      session_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Find memory entries by content query.
        
        Args:
            content_query: Dictionary of content fields to match
            memory_type: Optional memory type to filter by
            session_id: Optional session ID to filter by
            limit: Maximum number of entries to return
            
        Returns:
            list: List of matching memory entries
        """
        # Build filters
        filters = {}
        if memory_type:
            filters['memory_type'] = memory_type
        if session_id:
            filters['session_id'] = session_id
        
        # Query database
        if self.db_manager:
            memories = self.db_manager.find_memory_entries(filters)
            
            # Filter by content fields
            matching_memories = []
            for memory in memories:
                content = memory.get('content', {})
                
                # Check if content matches query
                matches = True
                for key, value in content_query.items():
                    if key not in content or content[key] != value:
                        matches = False
                        break
                
                if matches:
                    # Check if expired
                    if memory.get('expiration'):
                        try:
                            expiration = datetime.fromisoformat(memory['expiration'])
                            if expiration < datetime.now():
                                continue
                        except (ValueError, TypeError):
                            pass  # Invalid date format, assume not expired
                    
                    # Add to cache
                    uid = memory.get('uid')
                    if uid:
                        self.memory_cache[uid] = memory
                    
                    matching_memories.append(memory)
                    
                    if len(matching_memories) >= limit:
                        break
            
            self.stats['entries_retrieved'] += len(matching_memories)
            return matching_memories
        
        # For testing/development without database
        matching_memories = []
        for uid, memory in self.memory_cache.items():
            # Check filters
            if memory_type and memory.get('memory_type') != memory_type:
                continue
            if session_id and memory.get('session_id') != session_id:
                continue
            
            # Check content fields
            content = memory.get('content', {})
            matches = True
            for key, value in content_query.items():
                if key not in content or content[key] != value:
                    matches = False
                    break
            
            if matches:
                # Check if expired
                if memory.get('expiration'):
                    try:
                        expiration = datetime.fromisoformat(memory['expiration'])
                        if expiration < datetime.now():
                            continue
                    except (ValueError, TypeError):
                        pass  # Invalid date format, assume not expired
                
                matching_memories.append(memory)
                
                if len(matching_memories) >= limit:
                    break
        
        self.stats['entries_retrieved'] += len(matching_memories)
        return matching_memories
    
    def get_session_memories(self, session_id: str, memory_type: Optional[str] = None,
                          limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get memory entries for a session.
        
        Args:
            session_id: Session ID
            memory_type: Optional memory type to filter by
            limit: Maximum number of entries to return
            offset: Offset for pagination
            
        Returns:
            list: List of memory entries for the session
        """
        # Build filters
        filters = {'session_id': session_id}
        if memory_type:
            filters['memory_type'] = memory_type
        
        return self.find_memories(filters, limit, offset)
    
    def clear_expired_memories(self) -> int:
        """
        Clear all expired memory entries.
        
        Returns:
            int: Number of entries cleared
        """
        # Get current time
        now = datetime.now()
        cleared_count = 0
        
        # Clear from database
        if self.db_manager:
            cleared_count = self.db_manager.clear_expired_memories(now)
        
        # Clear from cache
        expired_uids = []
        for uid, memory in self.memory_cache.items():
            if memory.get('expiration'):
                try:
                    expiration = datetime.fromisoformat(memory['expiration'])
                    if expiration < now:
                        expired_uids.append(uid)
                except (ValueError, TypeError):
                    pass  # Invalid date format, assume not expired
        
        # Remove expired entries from cache
        for uid in expired_uids:
            del self.memory_cache[uid]
        
        if not self.db_manager:
            cleared_count = len(expired_uids)
        
        return cleared_count