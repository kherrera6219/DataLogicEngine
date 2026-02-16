import logging
import uuid
from datetime import datetime, UTC
from typing import Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Import models and extensions
from models import Node, Edge, KnowledgeAlgorithm, KAExecution, UkgSession as Session, MemoryEntry
from extensions import db, cache

class UkgDatabaseManager:
    """
    UKG Database Manager
    
    This component manages all database operations for the UKG system, providing
    a unified interface for creating, reading, updating, and deleting data in the 
    PostgreSQL database. It handles operations for nodes, edges, algorithms, 
    executions, sessions, and memory entries.
    """
    
    def __init__(self, tenant_id: Optional[str] = None, db_session=None, models_module=None, cache_client=None):
        """
        Initialize the UKG Database Manager.
        
        Args:
            tenant_id (str, optional): The active tenant ID for isolation
            db_session: Optional SQLAlchemy session factory (dependency injection)
            models_module: Optional module containing data models (dependency injection)
            cache_client: Optional cache client (dependency injection)
        """
        self.tenant_id = tenant_id
        
        # Dependency Injection / Defaults
        self.db = db_session if db_session else db
        self.cache = cache_client if cache_client else cache
        
        # Setup Models
        if models_module:
            self.Node = getattr(models_module, 'Node', Node)
            self.Edge = getattr(models_module, 'Edge', Edge)
            self.KnowledgeAlgorithm = getattr(models_module, 'KnowledgeAlgorithm', KnowledgeAlgorithm)
            self.KAExecution = getattr(models_module, 'KAExecution', KAExecution)
            # Handle aliased import
            self.Session = getattr(models_module, 'UkgSession', getattr(models_module, 'Session', Session))
            self.MemoryEntry = getattr(models_module, 'MemoryEntry', MemoryEntry)
        else:
            self.Node = Node
            self.Edge = Edge
            self.KnowledgeAlgorithm = KnowledgeAlgorithm
            self.KAExecution = KAExecution
            self.Session = Session
            self.MemoryEntry = MemoryEntry

        logging.info(f"UkgDatabaseManager initialized for tenant: {tenant_id}")
    
    # Node operations
    
    def create_node(self, node_data: Dict) -> Optional[Dict]:
        """
        Create a new node in the database.
        
        Args:
            node_data: Node data dictionary
            
        Returns:
            dict: Created node data or None if creation failed
        """
        try:
            # Create a new Node object
            node = self.Node(
                uid=node_data.get('uid'),
                node_type=node_data.get('node_type'),
                label=node_data.get('label'),
                description=node_data.get('description'),
                original_id=node_data.get('original_id'),
                axis_number=node_data.get('axis_number'),
                level=node_data.get('level'),
                attributes=node_data.get('attributes'),
                tenant_id=self.tenant_id
            )
            
            # Add to session and commit
            self.db.session.add(node)
            self.db.session.commit()
            
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
            self.db.session.rollback()
            logging.error(f"UKGDB: Error creating node: {str(e)}")
            return None
    
    def get_node_by_uid(self, uid: str) -> Optional[Dict]:
        """
        Get a node by its UID with caching.
        """
        # 1. Check Cache
        cache_key = f"node:{uid}:{self.tenant_id or 'global'}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            # 2. Query DB
            query = self.db.session.query(self.Node).filter(self.Node.uid == uid)
            if self.tenant_id:
                query = query.filter(self.Node.tenant_id == self.tenant_id)
            
            node = query.first()
            if not node:
                return None
            
            # 3. Cache and Return
            result = node.to_dict()
            self.cache.set(cache_key, result, timeout=300)
            return result
            
        except SQLAlchemyError as e:
            logging.error(f"UKGDB: Error getting node {uid}: {str(e)}")
            return None
    
    def update_node(self, uid: str, updates: Dict) -> Optional[Dict]:
        """
        Update a node.
        
        Args:
            uid: Node UID
            updates: Dictionary of updates
            
        Returns:
            dict: Updated node data or None if update failed
        """
        try:
            # Query the node with tenant isolation
            query = self.db.session.query(self.Node).filter(self.Node.uid == uid)
            if self.tenant_id:
                query = query.filter(self.Node.tenant_id == self.tenant_id)
            
            node = query.first()
            
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
            node.updated_at = datetime.now(UTC)
            
            # Commit changes
            self.db.session.commit()
            
            # Invalidate Cache
            cache_key = f"node:{uid}:{self.tenant_id or 'global'}"
            self.cache.delete(cache_key)
            
            return node.to_dict()
            
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logging.error(f"UKGDB: Error updating node {uid}: {str(e)}")
            return None
    
    def delete_node(self, uid: str) -> bool:
        """
        Delete a node.
        
        Args:
            uid: Node UID
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            # Query the node with tenant isolation
            query = self.db.session.query(self.Node).filter(self.Node.uid == uid)
            if self.tenant_id:
                query = query.filter(self.Node.tenant_id == self.tenant_id)
            
            node = query.first()
            
            if not node:
                return False
            
            # Delete node
            self.db.session.delete(node)
            self.db.session.commit()
            
            # Invalidate Cache
            cache_key = f"node:{uid}:{self.tenant_id or 'global'}"
            self.cache.delete(cache_key)
            
            return True
            
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logging.error(f"UKGDB: Error deleting node {uid}: {str(e)}")
            return False
    
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
        try:
            # Query nodes with tenant isolation
            query = self.db.session.query(self.Node).filter(self.Node.node_type == node_type)
            if self.tenant_id:
                query = query.filter(self.Node.tenant_id == self.tenant_id)
            
            nodes = query.offset(offset).limit(limit).all()
            
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
            logging.error(f"UKGDB: Error getting nodes by type {node_type}: {str(e)}")
            return []
    
    # Edge operations
    
    def create_edge(self, edge_data: Dict) -> Optional[Dict]:
        """
        Create a new edge in the database.
        
        Args:
            edge_data: Edge data dictionary
            
        Returns:
            dict: Created edge data or None if creation failed
        """
        try:
            # Get source and target nodes with tenant isolation
            source_query = self.db.session.query(self.Node).filter(self.Node.uid == edge_data.get('source_uid'))
            target_query = self.db.session.query(self.Node).filter(self.Node.uid == edge_data.get('target_uid'))
            
            if self.tenant_id:
                source_query = source_query.filter(self.Node.tenant_id == self.tenant_id)
                target_query = target_query.filter(self.Node.tenant_id == self.tenant_id)
                
            source_node = source_query.first()
            target_node = target_query.first()
            
            if not source_node or not target_node:
                logging.error(f"UKGDB: Source or target node not found for edge in tenant {self.tenant_id}")
                return None
            
            # Create a new Edge object
            edge = self.Edge(
                uid=edge_data.get('uid'),
                edge_type=edge_data.get('edge_type'),
                source_id=source_node.id,
                target_id=target_node.id,
                label=edge_data.get('label'),
                weight=edge_data.get('weight', 1.0),
                attributes=edge_data.get('attributes'),
                tenant_id=self.tenant_id
            )
            
            # Add to session and commit
            self.db.session.add(edge)
            self.db.session.commit()
            
            # Invalidate Cache
            cache_key = f"edge:{edge.uid}:{self.tenant_id or 'global'}"
            self.cache.delete(cache_key)
            
            return edge.to_dict()
            
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logging.error(f"UKGDB: Error creating edge: {str(e)}")
            return None
    
    def get_edge_by_uid(self, uid: str) -> Optional[Dict]:
        """
        Get an edge by its UID with caching.
        
        Args:
            uid: Edge UID
            
        Returns:
            dict: Edge data or None if not found
        """
        # 1. Check Cache
        cache_key = f"edge:{uid}:{self.tenant_id or 'global'}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            # 2. Query the edge with tenant isolation
            query = self.db.session.query(self.Edge).filter(self.Edge.uid == uid)
            if self.tenant_id:
                query = query.filter(self.Edge.tenant_id == self.tenant_id)
            
            edge = query.first()
            
            if not edge:
                return None
            
            # 3. Cache and Return
            result = edge.to_dict()
            self.cache.set(cache_key, result, timeout=300)
            return result
            
        except SQLAlchemyError as e:
            logging.error(f"UKGDB: Error getting edge {uid}: {str(e)}")
            return None
    
    def update_edge(self, uid: str, updates: Dict) -> Optional[Dict]:
        """
        Update an edge.
        
        Args:
            uid: Edge UID
            updates: Dictionary of updates
            
        Returns:
            dict: Updated edge data or None if update failed
        """
        try:
            # Query the edge with tenant isolation
            query = self.db.session.query(self.Edge).filter(self.Edge.uid == uid)
            if self.tenant_id:
                query = query.filter(self.Edge.tenant_id == self.tenant_id)
            
            edge = query.first()
            
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
                source_query = self.db.session.query(self.Node).filter(self.Node.uid == updates['source_uid'])
                if self.tenant_id:
                    source_query = source_query.filter(self.Node.tenant_id == self.tenant_id)
                source_node = source_query.first()
                if source_node:
                    edge.source_id = source_node.id
            
            if 'target_uid' in updates:
                target_query = self.db.session.query(self.Node).filter(self.Node.uid == updates['target_uid'])
                if self.tenant_id:
                    target_query = target_query.filter(self.Node.tenant_id == self.tenant_id)
                target_node = target_query.first()
                if target_node:
                    edge.target_id = target_node.id
            
            # Update timestamp
            edge.updated_at = datetime.now(UTC)
            
            # Commit changes
            self.db.session.commit()
            
            # Invalidate Cache
            cache_key = f"edge:{uid}:{self.tenant_id or 'global'}"
            self.cache.delete(cache_key)
            
            return edge.to_dict()
            
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logging.error(f"UKGDB: Error updating edge {uid}: {str(e)}")
            return None
    
    def delete_edge(self, uid: str) -> bool:
        """
        Delete an edge.
        
        Args:
            uid: Edge UID
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            # Query the edge with tenant isolation
            query = self.db.session.query(self.Edge).filter(self.Edge.uid == uid)
            if self.tenant_id:
                query = query.filter(self.Edge.tenant_id == self.tenant_id)
            
            edge = query.first()
            
            if not edge:
                return False
            
            # Delete edge
            self.db.session.delete(edge)
            self.db.session.commit()
            
            # Invalidate Cache
            cache_key = f"edge:{uid}:{self.tenant_id or 'global'}"
            self.cache.delete(cache_key)
            
            return True
            
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logging.error(f"UKGDB: Error deleting edge {uid}: {str(e)}")
            return False
    
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
        try:
            # Query edges with tenant isolation
            query = self.db.session.query(self.Edge).filter(self.Edge.edge_type == edge_type)
            if self.tenant_id:
                query = query.filter(self.Edge.tenant_id == self.tenant_id)
                
            edges = query.offset(offset).limit(limit).all()
            
            # Convert to dictionaries
            results = []
            for edge in edges:
                # Get source and target node UIDs
                source_node = self.db.session.query(self.Node).filter(self.Node.id == edge.source_id).first()
                target_node = self.db.session.query(self.Node).filter(self.Node.id == edge.target_id).first()
                
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
            logging.error(f"UKGDB: Error getting edges by type {edge_type}: {str(e)}")
            return []
    
    def get_outgoing_edges(self, node_uid: str) -> List[Dict]:
        """
        Get outgoing edges from a node.
        
        Args:
            node_uid: Node UID
            
        Returns:
            list: List of edge dictionaries
        """
        try:
            # Get node with tenant isolation
            query = self.db.session.query(self.Node).filter(self.Node.uid == node_uid)
            if self.tenant_id:
                query = query.filter(self.Node.tenant_id == self.tenant_id)
            node = query.first()
            
            if not node:
                return []
            
            # Query outgoing edges with tenant isolation
            edge_query = self.db.session.query(self.Edge).filter(self.Edge.source_id == node.id)
            if self.tenant_id:
                edge_query = edge_query.filter(self.Edge.tenant_id == self.tenant_id)
            edges = edge_query.all()
            
            # Convert to dictionaries
            results = []
            for edge in edges:
                # Get target node
                target_node = self.db.session.query(self.Node).filter(self.Node.id == edge.target_id).first()
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
            logging.error(f"UKGDB: Error getting outgoing edges for node {node_uid}: {str(e)}")
            return []
    
    def get_incoming_edges(self, node_uid: str) -> List[Dict]:
        """
        Get incoming edges to a node.
        
        Args:
            node_uid: Node UID
            
        Returns:
            list: List of edge dictionaries
        """
        try:
            # Get node with tenant isolation
            query = self.db.session.query(self.Node).filter(self.Node.uid == node_uid)
            if self.tenant_id:
                query = query.filter(self.Node.tenant_id == self.tenant_id)
            node = query.first()
            
            if not node:
                return []
            
            # Query incoming edges with tenant isolation
            edge_query = self.db.session.query(self.Edge).filter(self.Edge.target_id == node.id)
            if self.tenant_id:
                edge_query = edge_query.filter(self.Edge.tenant_id == self.tenant_id)
            edges = edge_query.all()
            
            # Convert to dictionaries
            results = []
            for edge in edges:
                # Get source node
                source_node = self.db.session.query(self.Node).filter(self.Node.id == edge.source_id).first()
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
            logging.error(f"UKGDB: Error getting incoming edges for node {node_uid}: {str(e)}")
            return []
    
    # Knowledge Algorithm operations
    
    def create_knowledge_algorithm(self, algorithm_data: Dict) -> Optional[Dict]:
        """
        Create a new knowledge algorithm in the database.
        
        Args:
            algorithm_data: Algorithm data dictionary
            
        Returns:
            dict: Created algorithm data or None if creation failed
        """
        try:
            # Create a new KnowledgeAlgorithm object
            algorithm = self.KnowledgeAlgorithm(
                ka_id=algorithm_data.get('ka_id'),
                name=algorithm_data.get('name'),
                description=algorithm_data.get('description'),
                input_schema=algorithm_data.get('input_schema'),
                output_schema=algorithm_data.get('output_schema'),
                version=algorithm_data.get('version'),
                tenant_id=self.tenant_id
            )
            
            # Add to session and commit
            self.db.session.add(algorithm)
            self.db.session.commit()
            
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
            logging.error(f"UKGDB: Error creating knowledge algorithm: {str(e)}")
            return None
    
    def get_knowledge_algorithm(self, ka_id: str) -> Optional[Dict]:
        """
        Get a knowledge algorithm by its KA ID.
        
        Args:
            ka_id: Knowledge Algorithm ID
            
        Returns:
            dict: Algorithm data or None if not found
        """
        try:
            # Query the algorithm with tenant isolation
            query = self.db.session.query(self.KnowledgeAlgorithm).filter(self.KnowledgeAlgorithm.ka_id == ka_id)
            if self.tenant_id:
                query = query.filter(self.KnowledgeAlgorithm.tenant_id == self.tenant_id)
            
            algorithm = query.first()
            
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
            logging.error(f"UKGDB: Error getting knowledge algorithm {ka_id}: {str(e)}")
            return None
    
    def create_ka_execution(self, execution_data: Dict) -> Optional[Dict]:
        """
        Create a new knowledge algorithm execution record.
        
        Args:
            execution_data: Execution data dictionary
            
        Returns:
            dict: Created execution data or None if creation failed
        """
        try:
            # Get algorithm ID with tenant isolation
            ka_id = execution_data.get('ka_id')
            ka_query = self.db.session.query(self.KnowledgeAlgorithm).filter(self.KnowledgeAlgorithm.ka_id == ka_id)
            if self.tenant_id:
                ka_query = ka_query.filter(self.KnowledgeAlgorithm.tenant_id == self.tenant_id)
            algorithm = ka_query.first()
            
            if not algorithm:
                logging.error(f"UKGDB: Knowledge algorithm {ka_id} not found in tenant {self.tenant_id}")
                return None
            
            # Create a new KAExecution object
            execution = self.KAExecution(
                algorithm_id=algorithm.id,
                session_id=execution_data.get('session_id'),
                pass_num=execution_data.get('pass_num', 0),
                layer_num=execution_data.get('layer_num', 0),
                input_data=execution_data.get('input_data'),
                output_data=execution_data.get('output_data'),
                confidence=execution_data.get('confidence', 0.0),
                execution_time=execution_data.get('execution_time'),
                status=execution_data.get('status', 'pending'),
                error_message=execution_data.get('error_message'),
                tenant_id=self.tenant_id
            )
            
            # Add to session and commit
            self.db.session.add(execution)
            self.db.session.commit()
            
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
            self.db.session.rollback()
            logging.error(f"UKGDB: Error creating KA execution: {str(e)}")
            return None
    
    # Session operations
    
    def create_session(self, session_id: Optional[str] = None, user_query: Optional[str] = None,
                     target_confidence: float = 0.85) -> Optional[Dict]:
        """
        Create a new session with tenant isolation.
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = f"SS_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
            
            # Create a new Session object
            session_obj = self.Session(
                session_id=session_id,
                user_query=user_query,
                target_confidence=target_confidence,
                status='active',
                tenant_id=self.tenant_id
            )
            
            # Add to session and commit
            self.db.session.add(session_obj)
            self.db.session.commit()
            
            return session_obj.to_dict()
            
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logging.error(f"UKGDB: Error creating session: {str(e)}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get a session by its ID with tenant isolation.
        """
        try:
            # Query the session with tenant isolation
            query = self.db.session.query(self.Session).filter(self.Session.session_id == session_id)
            if self.tenant_id:
                query = query.filter(self.Session.tenant_id == self.tenant_id)
            
            session_obj = query.first()
            if not session_obj:
                return None
            
            return session_obj.to_dict()
            
        except SQLAlchemyError as e:
            logging.error(f"UKGDB: Error getting session {session_id}: {str(e)}")
            return None
    
    def complete_session(self, session_id: str, final_confidence: float,
                       status: str = 'completed') -> Optional[Dict]:
        """
        Mark a session as completed with tenant isolation.
        """
        try:
            # Query the session with tenant isolation
            query = self.db.session.query(self.Session).filter(self.Session.session_id == session_id)
            if self.tenant_id:
                query = query.filter(self.Session.tenant_id == self.tenant_id)
            
            session_obj = query.first()
            if not session_obj:
                return None
            
            # Update session
            session_obj.final_confidence = final_confidence
            session_obj.status = status
            session_obj.completed_at = datetime.now(UTC)
            
            # Commit changes
            self.db.session.commit()
            return session_obj.to_dict()
            
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logging.error(f"UKGDB: Error completing session {session_id}: {str(e)}")
            return None
    
    # Memory entry operations
    
    def add_memory_entry(self, session_id: str, entry_type: str, content: Optional[Dict] = None,
                      pass_num: int = 0, layer_num: int = 0, confidence: float = 1.0,
                      uid: Optional[str] = None) -> Optional[Dict]:
        """
        Add a memory entry with tenant isolation.
        """
        try:
            # Verify session exists for this tenant
            session_query = self.db.session.query(self.Session).filter(self.Session.session_id == session_id)
            if self.tenant_id:
                session_query = session_query.filter(self.Session.tenant_id == self.tenant_id)
            
            if not session_query.first():
                logging.error(f"UKGDB: Session {session_id} not found or access denied for tenant")
                return None

            # Generate UID if not provided
            if not uid:
                uid = f"MEM_{entry_type.upper()}_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
            
            # Create a new MemoryEntry object
            memory_entry = self.MemoryEntry(
                uid=uid,
                session_id=session_id,
                entry_type=entry_type,
                pass_num=pass_num,
                layer_num=layer_num,
                content=content or {},
                confidence=confidence,
                tenant_id=self.tenant_id
            )
            
            # Add to session and commit
            self.db.session.add(memory_entry)
            self.db.session.commit()
            return memory_entry.to_dict()
            
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logging.error(f"UKGDB: Error adding memory entry: {str(e)}")
            return None
    
    def get_memory_entries(self, session_id: str, entry_type: Optional[str] = None,
                        pass_num: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """
        Get memory entries for a session with tenant isolation.
        """
        try:
            # Build query with tenant isolation
            query = self.db.session.query(self.MemoryEntry).filter(self.MemoryEntry.session_id == session_id)
            if self.tenant_id:
                query = query.filter(self.MemoryEntry.tenant_id == self.tenant_id)
            
            if entry_type:
                query = query.filter(self.MemoryEntry.entry_type == entry_type)
                
            if pass_num is not None:
                query = query.filter(self.MemoryEntry.pass_num == pass_num)
                
            # Order by created_at (newest first) and apply limit
            memory_entries = query.order_by(self.MemoryEntry.created_at.desc()).limit(limit).all()
            return [entry.to_dict() for entry in memory_entries]
            
        except SQLAlchemyError as e:
            logging.error(f"UKGDB: Error getting memory entries for session {session_id}: {str(e)}")
            return []
    
    # Graph operations
    
    def search_nodes(self, query: str, node_types: Optional[List[str]] = None,
                  axis_numbers: Optional[List[int]] = None, limit: int = 100) -> List[Dict]:
        """
        Search for nodes with tenant isolation.
        """
        try:
            # Build base query - Using the correct table name 'ukg_nodes'
            sql_query = """
                SELECT * FROM ukg_nodes
                WHERE (label ILIKE :query OR description ILIKE :query)
            """
            
            params = {'query': f'%{query}%'}
            
            if self.tenant_id:
                sql_query += " AND tenant_id = :tenant_id"
                params['tenant_id'] = self.tenant_id

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
            results = self.db.session.execute(text(sql_query), params).fetchall()
            
            # Convert to dictionaries
            nodes = []
            for row in results:
                node = dict(row._mapping)
                # Convert datetime objects to ISO strings
                for k, v in node.items():
                    if isinstance(v, datetime):
                        node[k] = v.isoformat()
                nodes.append(node)
            
            return nodes
            
        except SQLAlchemyError as e:
            logging.error(f"UKGDB: Error searching nodes: {str(e)}")
            return []
    
    def get_neighbors(self, node_uid: str, edge_types: Optional[List[str]] = None,
                    direction: str = 'both', max_depth: int = 1) -> Dict:
        """
        Get neighboring nodes with tenant isolation.
        """
        try:
            # Get starting node with tenant isolation
            query = self.db.session.query(self.Node).filter(self.Node.uid == node_uid)
            if self.tenant_id:
                query = query.filter(self.Node.tenant_id == self.tenant_id)
            start_node = query.first()
            
            if not start_node:
                return {'nodes': [], 'edges': []}
            
            # Initialize result sets
            node_ids = set([start_node.id])
            edge_ids = set()
            current_node_ids = set([start_node.id])
            
            # Traverse the graph
            for _ in range(max_depth):
                next_node_ids = set()
                
                if direction in ('outgoing', 'both'):
                    edge_query = self.db.session.query(self.Edge).filter(self.Edge.source_id.in_(current_node_ids))
                    if self.tenant_id:
                        edge_query = edge_query.filter(self.Edge.tenant_id == self.tenant_id)
                    if edge_types:
                        edge_query = edge_query.filter(self.Edge.edge_type.in_(edge_types))
                    
                    edges = edge_query.all()
                    for edge in edges:
                        edge_ids.add(edge.id)
                        next_node_ids.add(edge.target_id)
                
                if direction in ('incoming', 'both'):
                    edge_query = self.db.session.query(self.Edge).filter(self.Edge.target_id.in_(current_node_ids))
                    if self.tenant_id:
                        edge_query = edge_query.filter(self.Edge.tenant_id == self.tenant_id)
                    if edge_types:
                        edge_query = edge_query.filter(self.Edge.edge_type.in_(edge_types))
                    
                    edges = edge_query.all()
                    for edge in edges:
                        edge_ids.add(edge.id)
                        next_node_ids.add(edge.source_id)
                
                node_ids.update(next_node_ids)
                current_node_ids = next_node_ids
                if not current_node_ids: break
            
            # Batch fetch all discovered nodes and edges
            nodes = self.db.session.query(self.Node).filter(self.Node.id.in_(node_ids)).all()
            edges = self.db.session.query(self.Edge).filter(self.Edge.id.in_(edge_ids)).all()
            
            return {
                'nodes': [n.to_dict() for n in nodes],
                'edges': [e.to_dict() for e in edges]
            }
            
        except SQLAlchemyError as e:
            logging.error(f"UKGDB: Error getting neighbors: {str(e)}")
            return {'nodes': [], 'edges': []}
    
    # Database operations
    
    def execute_raw_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a raw SQL query.
        """
        try:
            # Execute query
            result = self.db.session.execute(text(query), params or {})
            
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
            logging.error(f"UKGDB: Error executing raw query: {str(e)}")
            return []
    
    def close(self):
        """
        Cleanup (stub for backward compatibility).
        """
        pass