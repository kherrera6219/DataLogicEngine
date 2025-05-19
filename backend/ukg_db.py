import logging
import os
import uuid
from datetime import datetime
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError

# Import models
from models import Node, Edge, KnowledgeAlgorithm, KAExecution, Session, MemoryEntry

class UkgDatabaseManager:
    """
    UKG Database Manager
    
    This component manages all database operations for the UKG system, providing
    a unified interface for creating, reading, updating, and deleting data in the 
    PostgreSQL database. It handles operations for nodes, edges, algorithms, 
    executions, sessions, and memory entries.
    """
    
    def __init__(self, database_url=None):
        """
        Initialize the UKG Database Manager.
        
        Args:
            database_url (str, optional): Database connection URL
        """
        logging.info(f"[{datetime.now()}] Initializing UkgDatabaseManager...")
        
        # Get database URL from environment if not provided
        if not database_url:
            database_url = os.environ.get('DATABASE_URL')
            
            if not database_url:
                logging.warning(f"[{datetime.now()}] UKGDB: DATABASE_URL not found in environment")
                raise ValueError("Database URL not provided and not found in environment")
        
        # Create engine and session
        self.engine = create_engine(database_url)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        
        logging.info(f"[{datetime.now()}] UkgDatabaseManager initialized")
    
    # Node operations
    
    def create_node(self, node_data: Dict) -> Optional[Dict]:
        """
        Create a new node in the database.
        
        Args:
            node_data: Node data dictionary
            
        Returns:
            dict: Created node data or None if creation failed
        """
        session = self.Session()
        
        try:
            # Create a new Node object
            node = Node(
                uid=node_data.get('uid'),
                node_type=node_data.get('node_type'),
                label=node_data.get('label'),
                description=node_data.get('description'),
                original_id=node_data.get('original_id'),
                axis_number=node_data.get('axis_number'),
                level=node_data.get('level'),
                attributes=node_data.get('attributes')
            )
            
            # Add to session and commit
            session.add(node)
            session.commit()
            
            # Get the created node as a dictionary
            result = {
                'uid': node.uid,
                'node_type': node.node_type,
                'label': node.label,
                'description': node.description,
                'original_id': node.original_id,
                'axis_number': node.axis_number,
                'level': node.level,
                'attributes': node.attributes,
                'created_at': node.created_at.isoformat() if node.created_at else None,
                'updated_at': node.updated_at.isoformat() if node.updated_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"[{datetime.now()}] UKGDB: Error creating node: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def get_node_by_uid(self, uid: str) -> Optional[Dict]:
        """
        Get a node by its UID.
        
        Args:
            uid: Node UID
            
        Returns:
            dict: Node data or None if not found
        """
        session = self.Session()
        
        try:
            # Query the node
            node = session.query(Node).filter(Node.uid == uid).first()
            
            if not node:
                return None
            
            # Convert to dictionary
            result = {
                'uid': node.uid,
                'node_type': node.node_type,
                'label': node.label,
                'description': node.description,
                'original_id': node.original_id,
                'axis_number': node.axis_number,
                'level': node.level,
                'attributes': node.attributes,
                'created_at': node.created_at.isoformat() if node.created_at else None,
                'updated_at': node.updated_at.isoformat() if node.updated_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error getting node {uid}: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def update_node(self, uid: str, updates: Dict) -> Optional[Dict]:
        """
        Update a node.
        
        Args:
            uid: Node UID
            updates: Dictionary of updates
            
        Returns:
            dict: Updated node data or None if update failed
        """
        session = self.Session()
        
        try:
            # Query the node
            node = session.query(Node).filter(Node.uid == uid).first()
            
            if not node:
                return None
            
            # Apply updates
            if 'node_type' in updates:
                node.node_type = updates['node_type']
            if 'label' in updates:
                node.label = updates['label']
            if 'description' in updates:
                node.description = updates['description']
            if 'original_id' in updates:
                node.original_id = updates['original_id']
            if 'axis_number' in updates:
                node.axis_number = updates['axis_number']
            if 'level' in updates:
                node.level = updates['level']
            if 'attributes' in updates:
                node.attributes = updates['attributes']
            
            # Update timestamp
            node.updated_at = datetime.utcnow()
            
            # Commit changes
            session.commit()
            
            # Get the updated node as a dictionary
            result = {
                'uid': node.uid,
                'node_type': node.node_type,
                'label': node.label,
                'description': node.description,
                'original_id': node.original_id,
                'axis_number': node.axis_number,
                'level': node.level,
                'attributes': node.attributes,
                'created_at': node.created_at.isoformat() if node.created_at else None,
                'updated_at': node.updated_at.isoformat() if node.updated_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"[{datetime.now()}] UKGDB: Error updating node {uid}: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def delete_node(self, uid: str) -> bool:
        """
        Delete a node.
        
        Args:
            uid: Node UID
            
        Returns:
            bool: True if deletion was successful
        """
        session = self.Session()
        
        try:
            # Query the node
            node = session.query(Node).filter(Node.uid == uid).first()
            
            if not node:
                return False
            
            # Delete node
            session.delete(node)
            session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"[{datetime.now()}] UKGDB: Error deleting node {uid}: {str(e)}")
            return False
            
        finally:
            session.close()
    
    def get_nodes_by_type(self, node_type: str, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """
        Get nodes by type.
        
        Args:
            node_type: Node type
            limit: Maximum number of nodes to return
            offset: Offset for pagination
            
        Returns:
            list: List of node dictionaries
        """
        session = self.Session()
        
        try:
            # Query nodes
            nodes = session.query(Node).filter(Node.node_type == node_type).offset(offset).limit(limit).all()
            
            # Convert to dictionaries
            results = []
            for node in nodes:
                results.append({
                    'uid': node.uid,
                    'node_type': node.node_type,
                    'label': node.label,
                    'description': node.description,
                    'original_id': node.original_id,
                    'axis_number': node.axis_number,
                    'level': node.level,
                    'attributes': node.attributes,
                    'created_at': node.created_at.isoformat() if node.created_at else None,
                    'updated_at': node.updated_at.isoformat() if node.updated_at else None
                })
            
            return results
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error getting nodes by type {node_type}: {str(e)}")
            return []
            
        finally:
            session.close()
    
    # Edge operations
    
    def create_edge(self, edge_data: Dict) -> Optional[Dict]:
        """
        Create a new edge in the database.
        
        Args:
            edge_data: Edge data dictionary
            
        Returns:
            dict: Created edge data or None if creation failed
        """
        session = self.Session()
        
        try:
            # Get source and target node IDs
            source_node = session.query(Node).filter(Node.uid == edge_data.get('source_uid')).first()
            target_node = session.query(Node).filter(Node.uid == edge_data.get('target_uid')).first()
            
            if not source_node or not target_node:
                logging.error(f"[{datetime.now()}] UKGDB: Source or target node not found for edge")
                return None
            
            # Create a new Edge object
            edge = Edge(
                uid=edge_data.get('uid'),
                edge_type=edge_data.get('edge_type'),
                source_id=source_node.id,
                target_id=target_node.id,
                label=edge_data.get('label'),
                weight=edge_data.get('weight', 1.0),
                attributes=edge_data.get('attributes')
            )
            
            # Add to session and commit
            session.add(edge)
            session.commit()
            
            # Get the created edge as a dictionary
            result = {
                'uid': edge.uid,
                'edge_type': edge.edge_type,
                'source_uid': edge_data.get('source_uid'),
                'target_uid': edge_data.get('target_uid'),
                'label': edge.label,
                'weight': edge.weight,
                'attributes': edge.attributes,
                'created_at': edge.created_at.isoformat() if edge.created_at else None,
                'updated_at': edge.updated_at.isoformat() if edge.updated_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"[{datetime.now()}] UKGDB: Error creating edge: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def get_edge_by_uid(self, uid: str) -> Optional[Dict]:
        """
        Get an edge by its UID.
        
        Args:
            uid: Edge UID
            
        Returns:
            dict: Edge data or None if not found
        """
        session = self.Session()
        
        try:
            # Query the edge
            edge = session.query(Edge).filter(Edge.uid == uid).first()
            
            if not edge:
                return None
            
            # Get source and target node UIDs
            source_node = session.query(Node).filter(Node.id == edge.source_id).first()
            target_node = session.query(Node).filter(Node.id == edge.target_id).first()
            
            source_uid = source_node.uid if source_node else None
            target_uid = target_node.uid if target_node else None
            
            # Convert to dictionary
            result = {
                'uid': edge.uid,
                'edge_type': edge.edge_type,
                'source_uid': source_uid,
                'target_uid': target_uid,
                'label': edge.label,
                'weight': edge.weight,
                'attributes': edge.attributes,
                'created_at': edge.created_at.isoformat() if edge.created_at else None,
                'updated_at': edge.updated_at.isoformat() if edge.updated_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error getting edge {uid}: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def update_edge(self, uid: str, updates: Dict) -> Optional[Dict]:
        """
        Update an edge.
        
        Args:
            uid: Edge UID
            updates: Dictionary of updates
            
        Returns:
            dict: Updated edge data or None if update failed
        """
        session = self.Session()
        
        try:
            # Query the edge
            edge = session.query(Edge).filter(Edge.uid == uid).first()
            
            if not edge:
                return None
            
            # Apply updates
            if 'edge_type' in updates:
                edge.edge_type = updates['edge_type']
            if 'label' in updates:
                edge.label = updates['label']
            if 'weight' in updates:
                edge.weight = updates['weight']
            if 'attributes' in updates:
                edge.attributes = updates['attributes']
            
            # Update source/target IDs if UIDs provided
            if 'source_uid' in updates:
                source_node = session.query(Node).filter(Node.uid == updates['source_uid']).first()
                if source_node:
                    edge.source_id = source_node.id
            
            if 'target_uid' in updates:
                target_node = session.query(Node).filter(Node.uid == updates['target_uid']).first()
                if target_node:
                    edge.target_id = target_node.id
            
            # Update timestamp
            edge.updated_at = datetime.utcnow()
            
            # Commit changes
            session.commit()
            
            # Get source and target node UIDs
            source_node = session.query(Node).filter(Node.id == edge.source_id).first()
            target_node = session.query(Node).filter(Node.id == edge.target_id).first()
            
            source_uid = source_node.uid if source_node else None
            target_uid = target_node.uid if target_node else None
            
            # Get the updated edge as a dictionary
            result = {
                'uid': edge.uid,
                'edge_type': edge.edge_type,
                'source_uid': source_uid,
                'target_uid': target_uid,
                'label': edge.label,
                'weight': edge.weight,
                'attributes': edge.attributes,
                'created_at': edge.created_at.isoformat() if edge.created_at else None,
                'updated_at': edge.updated_at.isoformat() if edge.updated_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"[{datetime.now()}] UKGDB: Error updating edge {uid}: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def delete_edge(self, uid: str) -> bool:
        """
        Delete an edge.
        
        Args:
            uid: Edge UID
            
        Returns:
            bool: True if deletion was successful
        """
        session = self.Session()
        
        try:
            # Query the edge
            edge = session.query(Edge).filter(Edge.uid == uid).first()
            
            if not edge:
                return False
            
            # Delete edge
            session.delete(edge)
            session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"[{datetime.now()}] UKGDB: Error deleting edge {uid}: {str(e)}")
            return False
            
        finally:
            session.close()
    
    def get_edges_by_type(self, edge_type: str, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """
        Get edges by type.
        
        Args:
            edge_type: Edge type
            limit: Maximum number of edges to return
            offset: Offset for pagination
            
        Returns:
            list: List of edge dictionaries
        """
        session = self.Session()
        
        try:
            # Query edges
            edges = session.query(Edge).filter(Edge.edge_type == edge_type).offset(offset).limit(limit).all()
            
            # Convert to dictionaries
            results = []
            for edge in edges:
                # Get source and target node UIDs
                source_node = session.query(Node).filter(Node.id == edge.source_id).first()
                target_node = session.query(Node).filter(Node.id == edge.target_id).first()
                
                source_uid = source_node.uid if source_node else None
                target_uid = target_node.uid if target_node else None
                
                results.append({
                    'uid': edge.uid,
                    'edge_type': edge.edge_type,
                    'source_uid': source_uid,
                    'target_uid': target_uid,
                    'label': edge.label,
                    'weight': edge.weight,
                    'attributes': edge.attributes,
                    'created_at': edge.created_at.isoformat() if edge.created_at else None,
                    'updated_at': edge.updated_at.isoformat() if edge.updated_at else None
                })
            
            return results
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error getting edges by type {edge_type}: {str(e)}")
            return []
            
        finally:
            session.close()
    
    def get_outgoing_edges(self, node_uid: str) -> List[Dict]:
        """
        Get outgoing edges from a node.
        
        Args:
            node_uid: Node UID
            
        Returns:
            list: List of edge dictionaries
        """
        session = self.Session()
        
        try:
            # Get node ID
            node = session.query(Node).filter(Node.uid == node_uid).first()
            
            if not node:
                return []
            
            # Query outgoing edges
            edges = session.query(Edge).filter(Edge.source_id == node.id).all()
            
            # Convert to dictionaries
            results = []
            for edge in edges:
                # Get target node UID
                target_node = session.query(Node).filter(Node.id == edge.target_id).first()
                target_uid = target_node.uid if target_node else None
                
                results.append({
                    'uid': edge.uid,
                    'edge_type': edge.edge_type,
                    'source_uid': node_uid,
                    'target_uid': target_uid,
                    'label': edge.label,
                    'weight': edge.weight,
                    'attributes': edge.attributes,
                    'created_at': edge.created_at.isoformat() if edge.created_at else None,
                    'updated_at': edge.updated_at.isoformat() if edge.updated_at else None
                })
            
            return results
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error getting outgoing edges for node {node_uid}: {str(e)}")
            return []
            
        finally:
            session.close()
    
    def get_incoming_edges(self, node_uid: str) -> List[Dict]:
        """
        Get incoming edges to a node.
        
        Args:
            node_uid: Node UID
            
        Returns:
            list: List of edge dictionaries
        """
        session = self.Session()
        
        try:
            # Get node ID
            node = session.query(Node).filter(Node.uid == node_uid).first()
            
            if not node:
                return []
            
            # Query incoming edges
            edges = session.query(Edge).filter(Edge.target_id == node.id).all()
            
            # Convert to dictionaries
            results = []
            for edge in edges:
                # Get source node UID
                source_node = session.query(Node).filter(Node.id == edge.source_id).first()
                source_uid = source_node.uid if source_node else None
                
                results.append({
                    'uid': edge.uid,
                    'edge_type': edge.edge_type,
                    'source_uid': source_uid,
                    'target_uid': node_uid,
                    'label': edge.label,
                    'weight': edge.weight,
                    'attributes': edge.attributes,
                    'created_at': edge.created_at.isoformat() if edge.created_at else None,
                    'updated_at': edge.updated_at.isoformat() if edge.updated_at else None
                })
            
            return results
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error getting incoming edges for node {node_uid}: {str(e)}")
            return []
            
        finally:
            session.close()
    
    # Knowledge Algorithm operations
    
    def create_knowledge_algorithm(self, algorithm_data: Dict) -> Optional[Dict]:
        """
        Create a new knowledge algorithm in the database.
        
        Args:
            algorithm_data: Algorithm data dictionary
            
        Returns:
            dict: Created algorithm data or None if creation failed
        """
        session = self.Session()
        
        try:
            # Create a new KnowledgeAlgorithm object
            algorithm = KnowledgeAlgorithm(
                ka_id=algorithm_data.get('ka_id'),
                name=algorithm_data.get('name'),
                description=algorithm_data.get('description'),
                input_schema=algorithm_data.get('input_schema'),
                output_schema=algorithm_data.get('output_schema'),
                version=algorithm_data.get('version')
            )
            
            # Add to session and commit
            session.add(algorithm)
            session.commit()
            
            # Get the created algorithm as a dictionary
            result = {
                'id': algorithm.id,
                'ka_id': algorithm.ka_id,
                'name': algorithm.name,
                'description': algorithm.description,
                'input_schema': algorithm.input_schema,
                'output_schema': algorithm.output_schema,
                'version': algorithm.version,
                'created_at': algorithm.created_at.isoformat() if algorithm.created_at else None,
                'updated_at': algorithm.updated_at.isoformat() if algorithm.updated_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"[{datetime.now()}] UKGDB: Error creating knowledge algorithm: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def get_knowledge_algorithm(self, ka_id: str) -> Optional[Dict]:
        """
        Get a knowledge algorithm by its KA ID.
        
        Args:
            ka_id: Knowledge Algorithm ID
            
        Returns:
            dict: Algorithm data or None if not found
        """
        session = self.Session()
        
        try:
            # Query the algorithm
            algorithm = session.query(KnowledgeAlgorithm).filter(KnowledgeAlgorithm.ka_id == ka_id).first()
            
            if not algorithm:
                return None
            
            # Convert to dictionary
            result = {
                'id': algorithm.id,
                'ka_id': algorithm.ka_id,
                'name': algorithm.name,
                'description': algorithm.description,
                'input_schema': algorithm.input_schema,
                'output_schema': algorithm.output_schema,
                'version': algorithm.version,
                'created_at': algorithm.created_at.isoformat() if algorithm.created_at else None,
                'updated_at': algorithm.updated_at.isoformat() if algorithm.updated_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error getting knowledge algorithm {ka_id}: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def create_ka_execution(self, execution_data: Dict) -> Optional[Dict]:
        """
        Create a new knowledge algorithm execution record.
        
        Args:
            execution_data: Execution data dictionary
            
        Returns:
            dict: Created execution data or None if creation failed
        """
        session = self.Session()
        
        try:
            # Get algorithm ID
            ka_id = execution_data.get('ka_id')
            algorithm = session.query(KnowledgeAlgorithm).filter(KnowledgeAlgorithm.ka_id == ka_id).first()
            
            if not algorithm:
                logging.error(f"[{datetime.now()}] UKGDB: Knowledge algorithm {ka_id} not found")
                return None
            
            # Create a new KAExecution object
            execution = KAExecution(
                algorithm_id=algorithm.id,
                session_id=execution_data.get('session_id'),
                pass_num=execution_data.get('pass_num', 0),
                layer_num=execution_data.get('layer_num', 0),
                input_data=execution_data.get('input_data'),
                output_data=execution_data.get('output_data'),
                confidence=execution_data.get('confidence', 0.0),
                execution_time=execution_data.get('execution_time'),
                status=execution_data.get('status', 'pending'),
                error_message=execution_data.get('error_message')
            )
            
            # Add to session and commit
            session.add(execution)
            session.commit()
            
            # Get the created execution as a dictionary
            result = {
                'id': execution.id,
                'ka_id': ka_id,
                'session_id': execution.session_id,
                'pass_num': execution.pass_num,
                'layer_num': execution.layer_num,
                'input_data': execution.input_data,
                'output_data': execution.output_data,
                'confidence': execution.confidence,
                'execution_time': execution.execution_time,
                'status': execution.status,
                'error_message': execution.error_message,
                'created_at': execution.created_at.isoformat() if execution.created_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"[{datetime.now()}] UKGDB: Error creating KA execution: {str(e)}")
            return None
            
        finally:
            session.close()
    
    # Session operations
    
    def create_session(self, session_id: Optional[str] = None, user_query: Optional[str] = None,
                     target_confidence: float = 0.85) -> Optional[Dict]:
        """
        Create a new session.
        
        Args:
            session_id: Optional session ID (auto-generated if None)
            user_query: The user's query text
            target_confidence: Target confidence level for this session
            
        Returns:
            dict: Session data or None if creation failed
        """
        session = self.Session()
        
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = f"SS_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
            
            # Create a new Session object
            session_obj = Session(
                session_id=session_id,
                user_query=user_query,
                target_confidence=target_confidence,
                status='active'
            )
            
            # Add to session and commit
            session.add(session_obj)
            session.commit()
            
            # Get the created session as a dictionary
            result = {
                'id': session_obj.id,
                'session_id': session_obj.session_id,
                'user_query': session_obj.user_query,
                'target_confidence': session_obj.target_confidence,
                'final_confidence': session_obj.final_confidence,
                'status': session_obj.status,
                'started_at': session_obj.started_at.isoformat() if session_obj.started_at else None,
                'completed_at': session_obj.completed_at.isoformat() if session_obj.completed_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"[{datetime.now()}] UKGDB: Error creating session: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get a session by its ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            dict: Session data or None if not found
        """
        session = self.Session()
        
        try:
            # Query the session
            session_obj = session.query(Session).filter(Session.session_id == session_id).first()
            
            if not session_obj:
                return None
            
            # Convert to dictionary
            result = {
                'id': session_obj.id,
                'session_id': session_obj.session_id,
                'user_query': session_obj.user_query,
                'target_confidence': session_obj.target_confidence,
                'final_confidence': session_obj.final_confidence,
                'status': session_obj.status,
                'started_at': session_obj.started_at.isoformat() if session_obj.started_at else None,
                'completed_at': session_obj.completed_at.isoformat() if session_obj.completed_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error getting session {session_id}: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def complete_session(self, session_id: str, final_confidence: float,
                       status: str = 'completed') -> Optional[Dict]:
        """
        Mark a session as completed.
        
        Args:
            session_id: Session ID
            final_confidence: Final confidence score
            status: Final status (completed, error, etc.)
            
        Returns:
            dict: Updated session data or None if update failed
        """
        session = self.Session()
        
        try:
            # Query the session
            session_obj = session.query(Session).filter(Session.session_id == session_id).first()
            
            if not session_obj:
                return None
            
            # Update session
            session_obj.final_confidence = final_confidence
            session_obj.status = status
            session_obj.completed_at = datetime.utcnow()
            
            # Commit changes
            session.commit()
            
            # Get the updated session as a dictionary
            result = {
                'id': session_obj.id,
                'session_id': session_obj.session_id,
                'user_query': session_obj.user_query,
                'target_confidence': session_obj.target_confidence,
                'final_confidence': session_obj.final_confidence,
                'status': session_obj.status,
                'started_at': session_obj.started_at.isoformat() if session_obj.started_at else None,
                'completed_at': session_obj.completed_at.isoformat() if session_obj.completed_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"[{datetime.now()}] UKGDB: Error completing session {session_id}: {str(e)}")
            return None
            
        finally:
            session.close()
    
    # Memory entry operations
    
    def add_memory_entry(self, session_id: str, entry_type: str, content: Optional[Dict] = None,
                      pass_num: int = 0, layer_num: int = 0, confidence: float = 1.0,
                      uid: Optional[str] = None) -> Optional[Dict]:
        """
        Add a memory entry.
        
        Args:
            session_id: Session ID
            entry_type: Type of memory entry
            content: Memory entry content
            pass_num: Simulation pass number
            layer_num: Layer number
            confidence: Confidence score (0.0-1.0)
            uid: Optional entry UID (auto-generated if None)
            
        Returns:
            dict: Created memory entry or None if creation failed
        """
        session = self.Session()
        
        try:
            # Generate UID if not provided
            if not uid:
                uid = f"MEM_{entry_type.upper()}_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
            
            # Create a new MemoryEntry object
            memory_entry = MemoryEntry(
                uid=uid,
                session_id=session_id,
                entry_type=entry_type,
                pass_num=pass_num,
                layer_num=layer_num,
                content=content or {},
                confidence=confidence
            )
            
            # Add to session and commit
            session.add(memory_entry)
            session.commit()
            
            # Get the created memory entry as a dictionary
            result = {
                'id': memory_entry.id,
                'uid': memory_entry.uid,
                'session_id': memory_entry.session_id,
                'entry_type': memory_entry.entry_type,
                'pass_num': memory_entry.pass_num,
                'layer_num': memory_entry.layer_num,
                'content': memory_entry.content,
                'confidence': memory_entry.confidence,
                'created_at': memory_entry.created_at.isoformat() if memory_entry.created_at else None
            }
            
            return result
            
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"[{datetime.now()}] UKGDB: Error adding memory entry: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def get_memory_entries(self, session_id: str, entry_type: Optional[str] = None,
                        pass_num: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """
        Get memory entries for a session.
        
        Args:
            session_id: Session ID
            entry_type: Optional entry type filter
            pass_num: Optional pass number filter
            limit: Maximum number of entries to return
            
        Returns:
            list: Memory entry dictionaries
        """
        session = self.Session()
        
        try:
            # Build query
            query = session.query(MemoryEntry).filter(MemoryEntry.session_id == session_id)
            
            if entry_type:
                query = query.filter(MemoryEntry.entry_type == entry_type)
                
            if pass_num is not None:
                query = query.filter(MemoryEntry.pass_num == pass_num)
                
            # Order by created_at (newest first) and apply limit
            query = query.order_by(MemoryEntry.created_at.desc()).limit(limit)
            
            # Execute query
            memory_entries = query.all()
            
            # Convert to dictionaries
            results = []
            for entry in memory_entries:
                results.append({
                    'id': entry.id,
                    'uid': entry.uid,
                    'session_id': entry.session_id,
                    'entry_type': entry.entry_type,
                    'pass_num': entry.pass_num,
                    'layer_num': entry.layer_num,
                    'content': entry.content,
                    'confidence': entry.confidence,
                    'created_at': entry.created_at.isoformat() if entry.created_at else None
                })
            
            return results
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error getting memory entries for session {session_id}: {str(e)}")
            return []
            
        finally:
            session.close()
    
    # Graph operations
    
    def search_nodes(self, query: str, node_types: Optional[List[str]] = None,
                  axis_numbers: Optional[List[int]] = None, limit: int = 100) -> List[Dict]:
        """
        Search for nodes matching a query.
        
        Args:
            query: Search query
            node_types: Optional list of node types to filter by
            axis_numbers: Optional list of axis numbers to filter by
            limit: Maximum number of nodes to return
            
        Returns:
            list: List of matching node dictionaries
        """
        session = self.Session()
        
        try:
            # Build base query
            sql_query = """
                SELECT * FROM nodes
                WHERE (label ILIKE :query OR description ILIKE :query)
            """
            
            params = {'query': f'%{query}%'}
            
            # Add node type filter if provided
            if node_types:
                placeholders = []
                for i, node_type in enumerate(node_types):
                    param_name = f'node_type_{i}'
                    placeholders.append(f':node_type_{i}')
                    params[param_name] = node_type
                
                sql_query += f" AND node_type IN ({', '.join(placeholders)})"
            
            # Add axis number filter if provided
            if axis_numbers:
                placeholders = []
                for i, axis_num in enumerate(axis_numbers):
                    param_name = f'axis_num_{i}'
                    placeholders.append(f':axis_num_{i}')
                    params[param_name] = axis_num
                
                sql_query += f" AND axis_number IN ({', '.join(placeholders)})"
            
            # Add limit
            sql_query += f" LIMIT {limit}"
            
            # Execute query
            results = session.execute(text(sql_query), params).fetchall()
            
            # Convert to dictionaries
            nodes = []
            for row in results:
                node = dict(row._mapping)
                
                # Convert datetime objects to ISO strings
                if node.get('created_at'):
                    node['created_at'] = node['created_at'].isoformat()
                if node.get('updated_at'):
                    node['updated_at'] = node['updated_at'].isoformat()
                
                nodes.append(node)
            
            return nodes
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error searching nodes: {str(e)}")
            return []
            
        finally:
            session.close()
    
    def get_neighbors(self, node_uid: str, edge_types: Optional[List[str]] = None,
                    direction: str = 'both', max_depth: int = 1) -> Dict:
        """
        Get neighboring nodes up to a specified depth.
        
        Args:
            node_uid: Starting node UID
            edge_types: Optional list of edge types to filter by
            direction: Direction of traversal ('outgoing', 'incoming', or 'both')
            max_depth: Maximum traversal depth
            
        Returns:
            dict: Dictionary with 'nodes' and 'edges' lists
        """
        session = self.Session()
        
        try:
            # Get starting node
            start_node = session.query(Node).filter(Node.uid == node_uid).first()
            
            if not start_node:
                return {'nodes': [], 'edges': []}
            
            # Initialize result sets
            node_ids = set([start_node.id])
            edge_ids = set()
            
            # Initialize first level frontiers
            current_node_ids = set([start_node.id])
            
            # Traverse the graph up to max_depth
            for depth in range(max_depth):
                next_node_ids = set()
                
                # Get outgoing edges if direction is 'outgoing' or 'both'
                if direction in ('outgoing', 'both'):
                    outgoing_query = session.query(Edge).filter(Edge.source_id.in_(current_node_ids))
                    
                    if edge_types:
                        outgoing_query = outgoing_query.filter(Edge.edge_type.in_(edge_types))
                    
                    outgoing_edges = outgoing_query.all()
                    
                    for edge in outgoing_edges:
                        edge_ids.add(edge.id)
                        next_node_ids.add(edge.target_id)
                
                # Get incoming edges if direction is 'incoming' or 'both'
                if direction in ('incoming', 'both'):
                    incoming_query = session.query(Edge).filter(Edge.target_id.in_(current_node_ids))
                    
                    if edge_types:
                        incoming_query = incoming_query.filter(Edge.edge_type.in_(edge_types))
                    
                    incoming_edges = incoming_query.all()
                    
                    for edge in incoming_edges:
                        edge_ids.add(edge.id)
                        next_node_ids.add(edge.source_id)
                
                # Add new node IDs to the set and update frontier
                node_ids.update(next_node_ids)
                current_node_ids = next_node_ids
                
                # If no more nodes to explore, break early
                if not current_node_ids:
                    break
            
            # Get all nodes
            nodes = session.query(Node).filter(Node.id.in_(node_ids)).all()
            
            # Get all edges
            edges = session.query(Edge).filter(Edge.id.in_(edge_ids)).all()
            
            # Convert nodes to dictionaries
            node_dicts = []
            uid_to_id_map = {}
            
            for node in nodes:
                uid_to_id_map[node.uid] = node.id
                
                node_dict = {
                    'uid': node.uid,
                    'node_type': node.node_type,
                    'label': node.label,
                    'description': node.description,
                    'original_id': node.original_id,
                    'axis_number': node.axis_number,
                    'level': node.level,
                    'attributes': node.attributes,
                    'created_at': node.created_at.isoformat() if node.created_at else None,
                    'updated_at': node.updated_at.isoformat() if node.updated_at else None
                }
                
                node_dicts.append(node_dict)
            
            # Convert edges to dictionaries
            edge_dicts = []
            
            for edge in edges:
                # Get source and target UIDs
                source_node = next((n for n in nodes if n.id == edge.source_id), None)
                target_node = next((n for n in nodes if n.id == edge.target_id), None)
                
                source_uid = source_node.uid if source_node else None
                target_uid = target_node.uid if target_node else None
                
                edge_dict = {
                    'uid': edge.uid,
                    'edge_type': edge.edge_type,
                    'source_uid': source_uid,
                    'target_uid': target_uid,
                    'label': edge.label,
                    'weight': edge.weight,
                    'attributes': edge.attributes,
                    'created_at': edge.created_at.isoformat() if edge.created_at else None,
                    'updated_at': edge.updated_at.isoformat() if edge.updated_at else None
                }
                
                edge_dicts.append(edge_dict)
            
            return {
                'nodes': node_dicts,
                'edges': edge_dicts
            }
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error getting neighbors for node {node_uid}: {str(e)}")
            return {'nodes': [], 'edges': []}
            
        finally:
            session.close()
    
    # Database operations
    
    def execute_raw_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Optional parameters dictionary
            
        Returns:
            list: List of result dictionaries
        """
        session = self.Session()
        
        try:
            # Execute query
            result = session.execute(text(query), params or {})
            
            # Convert results to dictionaries
            rows = []
            for row in result:
                row_dict = dict(row._mapping)
                
                # Convert datetime objects to ISO strings
                for key, value in row_dict.items():
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                
                rows.append(row_dict)
            
            return rows
            
        except SQLAlchemyError as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error executing raw query: {str(e)}")
            return []
            
        finally:
            session.close()
    
    def close(self):
        """
        Close the database connection.
        """
        try:
            self.Session.remove()
            self.engine.dispose()
            logging.info(f"[{datetime.now()}] UKGDB: Database connection closed")
        except Exception as e:
            logging.error(f"[{datetime.now()}] UKGDB: Error closing database connection: {str(e)}")