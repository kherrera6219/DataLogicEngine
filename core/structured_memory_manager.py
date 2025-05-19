import json
import os
from datetime import datetime
import logging
import uuid

class StructuredMemoryManager:
    """
    The StructuredMemoryManager (SMM) manages the Universal Simulated Knowledge Database (USKD).
    It provides methods to store, retrieve, and query simulation states, KA outputs, and other
    information needed by the UKG system.
    """
    
    def __init__(self, config):
        """
        Initialize the StructuredMemoryManager.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.memory_file_path = config.get('memory_file_path', 'data/memory_store.json')
        
        # Ensure memory directory exists
        os.makedirs(os.path.dirname(self.memory_file_path), exist_ok=True)
        
        # Initialize or load memory store
        if os.path.exists(self.memory_file_path):
            try:
                with open(self.memory_file_path, 'r') as f:
                    self.memory_store = json.load(f)
                logging.info(f"[{datetime.now()}] SMM: Loaded memory store from {self.memory_file_path}")
            except Exception as e:
                logging.error(f"[{datetime.now()}] SMM: Error loading memory store: {str(e)}")
                self.memory_store = {'entries': []}
        else:
            self.memory_store = {'entries': []}
            logging.info(f"[{datetime.now()}] SMM: Initialized new memory store")
        
        self._save_memory_store()  # Ensure it's saved initially
    
    def add_memory_entry(self, session_id, entry_type, content, pass_num=0, layer_num=0, uid=None, confidence=1.0):
        """
        Add a new entry to the memory store.
        
        Args:
            session_id (str): ID of the session this entry belongs to
            entry_type (str): Type of entry (e.g., 'ka_output', 'simulation_state')
            content (dict): The content to store
            pass_num (int): Pass number within the session
            layer_num (int): Layer number
            uid (str, optional): Optional UID for the entry
            confidence (float): Confidence score for this entry
            
        Returns:
            str: The UID of the created entry
        """
        if uid is None:
            uid = str(uuid.uuid4())
        
        timestamp = datetime.now().isoformat()
        
        entry = {
            'uid': uid,
            'session_id': session_id,
            'pass_num': pass_num,
            'layer_num': layer_num,
            'entry_type': entry_type,
            'timestamp': timestamp,
            'confidence': confidence,
            'content': content
        }
        
        self.memory_store['entries'].append(entry)
        self._save_memory_store()
        
        logging.debug(f"[{datetime.now()}] SMM: Added memory entry {uid[:8]}... for session {session_id[:8]}..., type: {entry_type}")
        
        return uid
    
    def get_memory_entry(self, uid):
        """
        Get a memory entry by its UID.
        
        Args:
            uid (str): The UID of the entry to retrieve
            
        Returns:
            dict: The entry or None if not found
        """
        for entry in self.memory_store['entries']:
            if entry['uid'] == uid:
                return entry
        return None
    
    def get_session_entries(self, session_id, entry_type=None, max_entries=None):
        """
        Get all entries for a session, optionally filtered by type.
        
        Args:
            session_id (str): The session ID
            entry_type (str, optional): Filter by entry type
            max_entries (int, optional): Maximum number of entries to return
            
        Returns:
            list: List of matching entries
        """
        entries = []
        for entry in self.memory_store['entries']:
            if entry['session_id'] == session_id:
                if entry_type is None or entry['entry_type'] == entry_type:
                    entries.append(entry)
        
        # Sort by timestamp (newest first)
        entries.sort(key=lambda x: x['timestamp'], reverse=True)
        
        if max_entries is not None:
            entries = entries[:max_entries]
        
        return entries
    
    def query_memory(self, filters=None, order_by=None, limit=None):
        """
        Query the memory store with complex filters.
        
        Args:
            filters (dict, optional): Dictionary of filters to apply
            order_by (str, optional): Field to order by
            limit (int, optional): Maximum number of entries to return
            
        Returns:
            list: List of matching entries
        """
        if filters is None:
            filters = {}
        
        results = []
        
        for entry in self.memory_store['entries']:
            match = True
            
            for key, value in filters.items():
                if key not in entry:
                    match = False
                    break
                
                if entry[key] != value:
                    match = False
                    break
            
            if match:
                results.append(entry)
        
        # Apply ordering if specified
        if order_by:
            reverse = False
            if order_by.startswith('-'):
                reverse = True
                order_by = order_by[1:]
            
            results.sort(key=lambda x: x.get(order_by, ''), reverse=reverse)
        
        # Apply limit if specified
        if limit is not None:
            results = results[:limit]
        
        return results
    
    def update_memory_entry(self, uid, updates):
        """
        Update an existing memory entry.
        
        Args:
            uid (str): The UID of the entry to update
            updates (dict): Dictionary of updates to apply
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        for i, entry in enumerate(self.memory_store['entries']):
            if entry['uid'] == uid:
                # Update the entry
                for key, value in updates.items():
                    if key == 'uid':  # Don't allow changing the UID
                        continue
                    entry[key] = value
                
                self.memory_store['entries'][i] = entry
                self._save_memory_store()
                
                logging.debug(f"[{datetime.now()}] SMM: Updated memory entry {uid[:8]}...")
                
                return True
        
        logging.warning(f"[{datetime.now()}] SMM: Attempted to update non-existent entry {uid[:8]}...")
        return False
    
    def delete_memory_entry(self, uid):
        """
        Delete a memory entry.
        
        Args:
            uid (str): The UID of the entry to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        for i, entry in enumerate(self.memory_store['entries']):
            if entry['uid'] == uid:
                del self.memory_store['entries'][i]
                self._save_memory_store()
                
                logging.debug(f"[{datetime.now()}] SMM: Deleted memory entry {uid[:8]}...")
                
                return True
        
        logging.warning(f"[{datetime.now()}] SMM: Attempted to delete non-existent entry {uid[:8]}...")
        return False
    
    def clear_session_memory(self, session_id):
        """
        Clear all memory entries for a session.
        
        Args:
            session_id (str): The session ID
            
        Returns:
            int: Number of entries deleted
        """
        entries_before = len(self.memory_store['entries'])
        
        self.memory_store['entries'] = [
            entry for entry in self.memory_store['entries']
            if entry['session_id'] != session_id
        ]
        
        entries_after = len(self.memory_store['entries'])
        deleted_count = entries_before - entries_after
        
        if deleted_count > 0:
            self._save_memory_store()
            logging.info(f"[{datetime.now()}] SMM: Cleared {deleted_count} entries for session {session_id[:8]}...")
        
        return deleted_count
    
    def get_statistics(self):
        """
        Get statistics about the memory store.
        
        Returns:
            dict: Various statistics about the memory store
        """
        total_entries = len(self.memory_store['entries'])
        
        # Count entries by type
        entry_types = {}
        for entry in self.memory_store['entries']:
            entry_type = entry.get('entry_type', 'Unknown')
            entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
        
        # Count entries by session
        session_counts = {}
        for entry in self.memory_store['entries']:
            session_id = entry.get('session_id', 'Unknown')
            session_counts[session_id] = session_counts.get(session_id, 0) + 1
        
        # Get the total size of the memory store (approximation)
        memory_size = len(json.dumps(self.memory_store))
        
        return {
            'total_entries': total_entries,
            'entry_types': entry_types,
            'session_counts': session_counts,
            'memory_size_bytes': memory_size
        }
    
    def _save_memory_store(self):
        """Save the memory store to disk."""
        try:
            with open(self.memory_file_path, 'w') as f:
                json.dump(self.memory_store, f)
            logging.debug(f"[{datetime.now()}] SMM: Saved memory store to {self.memory_file_path}")
        except Exception as e:
            logging.error(f"[{datetime.now()}] SMM: Error saving memory store: {str(e)}")
