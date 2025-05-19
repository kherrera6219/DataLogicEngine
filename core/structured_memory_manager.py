import json
import os
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

class StructuredMemoryManager:
    """
    Manages the Universal Simulated Knowledge Database (USKD).
    Provides methods to store and retrieve structured memory entries by session, pass,
    layer, UID, and more.
    """

    def __init__(self, config):
        """
        Initialize the Structured Memory Manager.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Define memory store file path
        self.memory_store_path = os.path.join(config.DATA_DIR, 'memory_store.json')

        # Initialize or load memory store
        self.memory_store = self._load_memory_store()

        self.logger.info(f"StructuredMemoryManager initialized with {len(self.memory_store)} entries")

    def _load_memory_store(self) -> List[Dict]:
        """
        Load the memory store from the JSON file.

        Returns:
            List of memory entries
        """
        if os.path.exists(self.memory_store_path):
            try:
                with open(self.memory_store_path, 'r', encoding='utf-8') as f:
                    memory_store = json.load(f)
                self.logger.info(f"Loaded memory store from {self.memory_store_path}")
                return memory_store
            except Exception as e:
                self.logger.error(f"Error loading memory store: {str(e)}")
                return []
        else:
            self.logger.info(f"Memory store file not found, initializing empty store")
            return []

    def _save_memory_store(self):
        """
        Save the memory store to the JSON file.
        """
        try:
            with open(self.memory_store_path, 'w', encoding='utf-8') as f:
                json.dump(self.memory_store, f, indent=2)
            self.logger.info(f"Saved memory store to {self.memory_store_path}")
        except Exception as e:
            self.logger.error(f"Error saving memory store: {str(e)}")

    def add_memory_entry(self, session_id: str, pass_num: int, layer_num: int, 
                      entry_type: str, content: Dict, confidence: float = 1.0,
                      uid: Optional[str] = None) -> Dict:
        """
        Add a new entry to the structured memory.

        Args:
            session_id: ID of the session
            pass_num: Simulation pass number
            layer_num: Simulation layer number
            entry_type: Type of memory entry
            content: Memory entry content (any JSON-serializable object)
            confidence: Confidence score (default: 1.0)
            uid: Optional unique identifier (auto-generated if None)

        Returns:
            The added memory entry
        """
        if uid is None:
            uid = f"mem_{str(uuid.uuid4())}"

        entry_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        memory_entry = {
            "id": entry_id,
            "uid": uid,
            "session_id": session_id,
            "pass_num": pass_num,
            "layer_num": layer_num,
            "entry_type": entry_type,
            "content": content,
            "confidence": confidence,
            "created_at": timestamp
        }

        self.memory_store.append(memory_entry)
        self._save_memory_store()

        self.logger.info(f"Added memory entry: session={session_id}, pass={pass_num}, layer={layer_num}, type={entry_type}")

        return memory_entry

    def query_memory(self, session_id: Optional[str] = None, pass_num: Optional[int] = None,
                  layer_num: Optional[int] = None, uid: Optional[str] = None,
                  entry_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Query memory entries by various filters.

        Args:
            session_id: Optional session ID filter
            pass_num: Optional pass number filter
            layer_num: Optional layer number filter
            uid: Optional UID filter
            entry_type: Optional entry type filter
            limit: Maximum number of entries to return

        Returns:
            List of matching memory entries
        """
        results = []

        for entry in self.memory_store:
            # Check if entry matches all provided filters
            match = True

            if session_id is not None and entry.get("session_id") != session_id:
                match = False

            if pass_num is not None and entry.get("pass_num") != pass_num:
                match = False

            if layer_num is not None and entry.get("layer_num") != layer_num:
                match = False

            if uid is not None and entry.get("uid") != uid:
                match = False

            if entry_type is not None and entry.get("entry_type") != entry_type:
                match = False

            if match:
                results.append(entry)

            if len(results) >= limit:
                break

        return results

    def get_memory_by_id(self, entry_id: str) -> Optional[Dict]:
        """
        Get a memory entry by its ID.

        Args:
            entry_id: The memory entry ID

        Returns:
            The memory entry or None if not found
        """
        for entry in self.memory_store:
            if entry.get("id") == entry_id:
                return entry
        return None

    def get_session_memory(self, session_id: str, limit: int = 100) -> List[Dict]:
        """
        Get all memory entries for a session.

        Args:
            session_id: Session ID
            limit: Maximum number of entries to return

        Returns:
            List of memory entries for the session
        """
        return self.query_memory(session_id=session_id, limit=limit)

    def get_latest_memory_by_type(self, entry_type: str, limit: int = 1) -> List[Dict]:
        """
        Get the latest memory entries of a specific type.

        Args:
            entry_type: Type of memory entry
            limit: Maximum number of entries to return

        Returns:
            List of latest memory entries of the specified type
        """
        entries = self.query_memory(entry_type=entry_type)

        # Sort by creation time (newest first)
        entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return entries[:limit]

    def delete_memory_entry(self, entry_id: str) -> bool:
        """
        Delete a memory entry by its ID.

        Args:
            entry_id: The memory entry ID

        Returns:
            True if deleted, False if not found
        """
        for i, entry in enumerate(self.memory_store):
            if entry.get("id") == entry_id:
                self.memory_store.pop(i)
                self._save_memory_store()
                self.logger.info(f"Deleted memory entry: {entry_id}")
                return True

        self.logger.warning(f"Memory entry not found for deletion: {entry_id}")
        return False

    def clear_session_memory(self, session_id: str) -> int:
        """
        Clear all memory entries for a session.

        Args:
            session_id: Session ID

        Returns:
            Number of entries deleted
        """
        count = 0
        indices_to_remove = []

        for i, entry in enumerate(self.memory_store):
            if entry.get("session_id") == session_id:
                indices_to_remove.append(i)
                count += 1

        # Remove entries from highest index to lowest to avoid shifting issues
        for i in sorted(indices_to_remove, reverse=True):
            self.memory_store.pop(i)

        if count > 0:
            self._save_memory_store()
            self.logger.info(f"Cleared {count} memory entries for session: {session_id}")

        return count