import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.ukg_db import UkgDatabaseManager

class StructuredMemoryManager:
    """
    Structured Memory Manager (SMM)
    
    This component manages the system's memory, storing and retrieving structured
    information about reasoning processes, session history, and knowledge evolution.
    It provides a unified interface for memory operations across the UKG system.
    """
    
    def __init__(self, config=None):
        """
        Initialize the Structured Memory Manager.
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        logging.info(f"[{datetime.now()}] Initializing StructuredMemoryManager...")
        self.config = config or {}
        self.db_manager = UkgDatabaseManager()
        
        # Memory entry types
        self.entry_types = {
            # Session state entries
            'session_start': 'Session started',
            'session_end': 'Session completed',
            'pass_start': 'Simulation pass started',
            'pass_complete': 'Simulation pass completed',
            'pass_error': 'Error in simulation pass',
            'layer_start': 'Layer execution started',
            'layer_complete': 'Layer execution completed',
            'layer_error': 'Error in layer execution',
            
            # Knowledge processing entries
            'query_analysis': 'Query analysis results',
            'knowledge_retrieval': 'Retrieved knowledge',
            'reasoning_step': 'Reasoning process step',
            'inference_result': 'Inference result',
            'validation_check': 'Validation check result',
            
            # Final output entries
            'final_compiled_answer': 'Final compiled answer',
            'confidence_assessment': 'Confidence assessment',
            
            # SEKRE entries
            'sekre_action_log': 'SEKRE action log',
            'sekre_ontology_proposal': 'SEKRE ontology proposal',
            
            # Location context entries
            'location_filter_applied': 'Location context filter applied',
            'location_context_changed': 'Location context changed'
        }
        
        logging.info(f"[{datetime.now()}] StructuredMemoryManager initialized with {len(self.entry_types)} entry types")
    
    def add_memory_entry(self, session_id: str, entry_type: str, content: Optional[Dict] = None,
                       pass_num: int = 0, layer_num: int = 0, confidence: float = 1.0,
                       uid: Optional[str] = None) -> Optional[str]:
        """
        Add an entry to the structured memory.
        
        Args:
            session_id: ID of the session
            entry_type: Type of memory entry
            content: Memory entry content
            pass_num: Simulation pass number
            layer_num: Layer number
            confidence: Confidence score (0.0-1.0)
            uid: Optional entry UID (auto-generated if None)
            
        Returns:
            str: UID of the created memory entry or None if creation failed
        """
        if entry_type not in self.entry_types:
            logging.warning(f"[{datetime.now()}] SMM: Unknown entry type: {entry_type}")
            # Still allow it, but with a warning
        
        try:
            # Add entry to the database
            entry_data = self.db_manager.add_memory_entry(
                session_id=session_id,
                entry_type=entry_type,
                content=content,
                pass_num=pass_num,
                layer_num=layer_num,
                confidence=confidence,
                uid=uid
            )
            
            if not entry_data:
                logging.error(f"[{datetime.now()}] SMM: Failed to create memory entry in database")
                return None
            
            entry_uid = entry_data.get('uid')
            logging.info(f"[{datetime.now()}] SMM: Added memory entry {entry_uid} of type {entry_type} to session {session_id}")
            
            return entry_uid
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] SMM: Error adding memory entry: {str(e)}")
            return None
    
    def get_memory_entries(self, session_id: str, entry_type: Optional[str] = None,
                         pass_num: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """
        Get memory entries for a session.
        
        Args:
            session_id: ID of the session
            entry_type: Optional entry type filter
            pass_num: Optional pass number filter
            limit: Maximum number of entries to return
            
        Returns:
            list: Memory entry dictionaries
        """
        try:
            # Get entries from the database
            entries = self.db_manager.get_memory_entries(
                session_id=session_id,
                entry_type=entry_type,
                pass_num=pass_num,
                limit=limit
            )
            
            return entries
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] SMM: Error retrieving memory entries: {str(e)}")
            return []
    
    def get_session_history(self, session_id: str) -> Dict:
        """
        Get a complete history of a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            dict: Session history with all memory entries
        """
        try:
            # Get session info from the database
            session_data = self.db_manager.get_session(session_id)
            
            if not session_data:
                logging.warning(f"[{datetime.now()}] SMM: Session {session_id} not found")
                return {'session_id': session_id, 'status': 'not_found', 'memory_entries': []}
            
            # Get all memory entries for the session
            memory_entries = self.get_memory_entries(session_id, limit=1000)
            
            # Organize entries by pass and layer
            organized_entries = {}
            for entry in memory_entries:
                pass_num = entry.get('pass_num', 0)
                layer_num = entry.get('layer_num', 0)
                
                if pass_num not in organized_entries:
                    organized_entries[pass_num] = {}
                    
                if layer_num not in organized_entries[pass_num]:
                    organized_entries[pass_num][layer_num] = []
                    
                organized_entries[pass_num][layer_num].append(entry)
            
            # Prepare session history
            session_history = {
                **session_data,
                'organized_memory': organized_entries,
                'raw_memory_entries': memory_entries
            }
            
            return session_history
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] SMM: Error retrieving session history: {str(e)}")
            return {'session_id': session_id, 'status': 'error', 'error': str(e)}
    
    def search_memory(self, query: str, entry_types: Optional[List[str]] = None,
                    confidence_threshold: float = 0.0, limit: int = 50) -> List[Dict]:
        """
        Search memory entries across all sessions.
        
        Args:
            query: Search query
            entry_types: Optional list of entry types to filter by
            confidence_threshold: Minimum confidence score for entries
            limit: Maximum number of entries to return
            
        Returns:
            list: Matching memory entries
        """
        # In a full implementation, this would be a sophisticated search
        # For now, we'll return an empty list
        return []
    
    def clear_session_memory(self, session_id: str) -> bool:
        """
        Clear all memory entries for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            bool: True if successful
        """
        # In a full implementation, this would delete session memory entries
        # For now, just return True
        logging.info(f"[{datetime.now()}] SMM: Cleared memory for session {session_id}")
        return True
    
    def create_session(self, session_id: Optional[str] = None, user_query: Optional[str] = None,
                     target_confidence: float = 0.85) -> Dict:
        """
        Create a new session.
        
        Args:
            session_id: Optional session ID (auto-generated if None)
            user_query: The user's query text
            target_confidence: Target confidence level for this session
            
        Returns:
            dict: Session data
        """
        try:
            # Create session in database
            session_data = self.db_manager.create_session(
                session_id=session_id,
                user_query=user_query,
                target_confidence=target_confidence
            )
            
            if not session_data:
                raise Exception("Failed to create session in database")
            
            # Add session start entry
            self.add_memory_entry(
                session_id=session_data['session_id'],
                entry_type='session_start',
                content={
                    'user_query': user_query,
                    'target_confidence': target_confidence,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            return session_data
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] SMM: Error creating session: {str(e)}")
            # Return a minimal session data object
            return {
                'session_id': session_id or str(uuid.uuid4()),
                'status': 'error',
                'error': str(e)
            }
    
    def complete_session(self, session_id: str, final_confidence: float,
                       status: str = 'completed') -> Optional[Dict]:
        """
        Mark a session as completed.
        
        Args:
            session_id: ID of the session
            final_confidence: Final confidence score
            status: Final status (completed, error, etc.)
            
        Returns:
            dict: Updated session data or None if session not found
        """
        try:
            # Complete session in database
            session_data = self.db_manager.complete_session(
                session_id=session_id,
                final_confidence=final_confidence,
                status=status
            )
            
            if not session_data:
                logging.warning(f"[{datetime.now()}] SMM: Session {session_id} not found")
                return None
            
            # Add session end entry
            self.add_memory_entry(
                session_id=session_id,
                entry_type='session_end',
                content={
                    'final_confidence': final_confidence,
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                },
                confidence=final_confidence
            )
            
            return session_data
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] SMM: Error completing session: {str(e)}")
            return None