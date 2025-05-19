import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

from models import db, Node, Edge, KnowledgeAlgorithm, KAExecution, Session, MemoryEntry

class UkgDatabaseManager:
    """
    Database manager for the Universal Knowledge Graph system.
    Provides methods for CRUD operations on UKG nodes and edges,
    as well as session and KA execution tracking.
    """
    
    def __init__(self):
        """Initialize the UKG Database Manager."""
        logging.info(f"[{datetime.now()}] UKG Database Manager initialized")
    
    # Node Management Methods
    def add_node(self, uid: Optional[str] = None, node_type: str = "GenericNode", 
                label: str = "", description: Optional[str] = None, 
                original_id: Optional[str] = None, axis_number: Optional[int] = None,
                level: Optional[int] = None, attributes: Optional[Dict] = None) -> Dict:
        """
        Add a new node to the UKG.
        
        Args:
            uid: Unique identifier (auto-generated if None)
            node_type: Type of node (e.g., "ConceptNode", "EntityNode")
            label: Human-readable name for the node
            description: Optional text description
            original_id: External identifier reference
            axis_number: UKG axis number (1-13)
            level: Hierarchical level within the axis
            attributes: Additional attributes as a dictionary
            
        Returns:
            Dict containing the created node data
        """
        if uid is None:
            uid = str(uuid.uuid4())
            
        try:
            new_node = Node(
                uid=uid,
                node_type=node_type,
                label=label,
                description=description,
                original_id=original_id,
                axis_number=axis_number,
                level=level,
                attributes=attributes
            )
            
            db.session.add(new_node)
            db.session.commit()
            
            logging.info(f"[{datetime.now()}] Added node {uid} of type {node_type}")
            
            return {
                "id": new_node.id,
                "uid": new_node.uid,
                "node_type": new_node.node_type,
                "label": new_node.label,
                "description": new_node.description,
                "original_id": new_node.original_id,
                "axis_number": new_node.axis_number,
                "level": new_node.level,
                "attributes": new_node.attributes,
                "created_at": new_node.created_at.isoformat() if new_node.created_at else None
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{datetime.now()}] Error adding node: {str(e)}")
            raise
    
    def get_node(self, uid: str) -> Optional[Dict]:
        """
        Retrieve a node by UID.
        
        Args:
            uid: Node's unique identifier
            
        Returns:
            Dict containing the node data or None if not found
        """
        node = Node.query.filter_by(uid=uid).first()
        
        if not node:
            return None
            
        return {
            "id": node.id,
            "uid": node.uid,
            "node_type": node.node_type,
            "label": node.label,
            "description": node.description,
            "original_id": node.original_id,
            "axis_number": node.axis_number,
            "level": node.level,
            "attributes": node.attributes,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at else None
        }
    
    def get_node_by_original_id(self, original_id: str, node_type: Optional[str] = None) -> Optional[Dict]:
        """
        Retrieve a node by its original ID (external reference ID).
        
        Args:
            original_id: The external original ID
            node_type: Optional node type filter
            
        Returns:
            Dict containing the node data or None if not found
        """
        query = Node.query.filter_by(original_id=original_id)
        
        if node_type:
            query = query.filter_by(node_type=node_type)
            
        node = query.first()
        
        if not node:
            return None
            
        return {
            "id": node.id,
            "uid": node.uid,
            "node_type": node.node_type,
            "label": node.label,
            "description": node.description,
            "original_id": node.original_id,
            "axis_number": node.axis_number,
            "level": node.level,
            "attributes": node.attributes,
            "created_at": node.created_at.isoformat() if node.created_at else None
        }
    
    def update_node(self, uid: str, **kwargs) -> Optional[Dict]:
        """
        Update a node's attributes.
        
        Args:
            uid: Node's unique identifier
            **kwargs: Attributes to update
            
        Returns:
            Dict containing the updated node data or None if not found
        """
        node = Node.query.filter_by(uid=uid).first()
        
        if not node:
            logging.warning(f"[{datetime.now()}] Update failed. Node {uid} not found")
            return None
            
        # Update allowed fields
        allowed_fields = ["node_type", "label", "description", "axis_number", "level", "attributes"]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(node, field, value)
        
        try:
            db.session.commit()
            logging.info(f"[{datetime.now()}] Updated node {uid}")
            
            return {
                "id": node.id,
                "uid": node.uid,
                "node_type": node.node_type,
                "label": node.label,
                "description": node.description,
                "original_id": node.original_id,
                "axis_number": node.axis_number,
                "level": node.level,
                "attributes": node.attributes,
                "updated_at": node.updated_at.isoformat() if node.updated_at else None
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{datetime.now()}] Error updating node {uid}: {str(e)}")
            raise
    
    def delete_node(self, uid: str) -> bool:
        """
        Delete a node and all its connected edges.
        
        Args:
            uid: Node's unique identifier
            
        Returns:
            bool: True if successful, False if node not found
        """
        node = Node.query.filter_by(uid=uid).first()
        
        if not node:
            logging.warning(f"[{datetime.now()}] Delete failed. Node {uid} not found")
            return False
            
        try:
            # Delete associated edges first
            Edge.query.filter((Edge.source_id == node.id) | (Edge.target_id == node.id)).delete()
            
            # Delete the node
            db.session.delete(node)
            db.session.commit()
            
            logging.info(f"[{datetime.now()}] Deleted node {uid} and its edges")
            return True
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{datetime.now()}] Error deleting node {uid}: {str(e)}")
            raise
    
    def get_nodes_by_type(self, node_type: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get nodes filtered by type.
        
        Args:
            node_type: Type of nodes to retrieve
            limit: Maximum number of nodes to return
            offset: Query offset for pagination
            
        Returns:
            List of node dictionaries
        """
        nodes = Node.query.filter_by(node_type=node_type).limit(limit).offset(offset).all()
        
        result = []
        for node in nodes:
            result.append({
                "id": node.id,
                "uid": node.uid,
                "node_type": node.node_type,
                "label": node.label,
                "description": node.description,
                "original_id": node.original_id,
                "axis_number": node.axis_number,
                "level": node.level,
                "attributes": node.attributes,
                "created_at": node.created_at.isoformat() if node.created_at else None
            })
            
        return result
    
    def get_nodes_by_axis(self, axis_number: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get nodes filtered by axis number.
        
        Args:
            axis_number: Axis number (1-13)
            limit: Maximum number of nodes to return
            offset: Query offset for pagination
            
        Returns:
            List of node dictionaries
        """
        nodes = Node.query.filter_by(axis_number=axis_number).limit(limit).offset(offset).all()
        
        result = []
        for node in nodes:
            result.append({
                "id": node.id,
                "uid": node.uid,
                "node_type": node.node_type,
                "label": node.label,
                "description": node.description,
                "original_id": node.original_id,
                "axis_number": node.axis_number,
                "level": node.level,
                "attributes": node.attributes,
                "created_at": node.created_at.isoformat() if node.created_at else None
            })
            
        return result
    
    # Edge Management Methods
    def add_edge(self, source_uid: str, target_uid: str, edge_type: str = "GenericRelation",
                label: Optional[str] = None, weight: float = 1.0, 
                attributes: Optional[Dict] = None, uid: Optional[str] = None) -> Optional[Dict]:
        """
        Add a new edge between two nodes.
        
        Args:
            source_uid: UID of the source node
            target_uid: UID of the target node
            edge_type: Type of edge (e.g., "IsA", "HasPart")
            label: Optional human-readable label
            weight: Edge weight/importance (default 1.0)
            attributes: Additional attributes as dictionary
            uid: Optional edge UID (auto-generated if None)
            
        Returns:
            Dict containing the created edge data or None if nodes not found
        """
        # Get the nodes
        source_node = Node.query.filter_by(uid=source_uid).first()
        target_node = Node.query.filter_by(uid=target_uid).first()
        
        if not source_node or not target_node:
            logging.warning(f"[{datetime.now()}] Edge creation failed. Source or target node not found")
            return None
        
        if uid is None:
            uid = str(uuid.uuid4())
            
        try:
            new_edge = Edge(
                uid=uid,
                edge_type=edge_type,
                source_id=source_node.id,
                target_id=target_node.id,
                label=label,
                weight=weight,
                attributes=attributes
            )
            
            db.session.add(new_edge)
            db.session.commit()
            
            logging.info(f"[{datetime.now()}] Added edge {uid} from {source_uid} to {target_uid}")
            
            return {
                "id": new_edge.id,
                "uid": new_edge.uid,
                "edge_type": new_edge.edge_type,
                "source_id": new_edge.source_id,
                "target_id": new_edge.target_id,
                "source_uid": source_uid,
                "target_uid": target_uid,
                "label": new_edge.label,
                "weight": new_edge.weight,
                "attributes": new_edge.attributes,
                "created_at": new_edge.created_at.isoformat() if new_edge.created_at else None
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{datetime.now()}] Error adding edge: {str(e)}")
            raise
    
    def get_edge(self, uid: str) -> Optional[Dict]:
        """
        Retrieve an edge by UID.
        
        Args:
            uid: Edge's unique identifier
            
        Returns:
            Dict containing the edge data or None if not found
        """
        edge = Edge.query.filter_by(uid=uid).first()
        
        if not edge:
            return None
            
        # Get the node UIDs
        source_uid = Node.query.get(edge.source_id).uid if edge.source_id else None
        target_uid = Node.query.get(edge.target_id).uid if edge.target_id else None
            
        return {
            "id": edge.id,
            "uid": edge.uid,
            "edge_type": edge.edge_type,
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "source_uid": source_uid,
            "target_uid": target_uid,
            "label": edge.label,
            "weight": edge.weight,
            "attributes": edge.attributes,
            "created_at": edge.created_at.isoformat() if edge.created_at else None,
            "updated_at": edge.updated_at.isoformat() if edge.updated_at else None
        }
    
    def update_edge(self, uid: str, **kwargs) -> Optional[Dict]:
        """
        Update an edge's attributes.
        
        Args:
            uid: Edge's unique identifier
            **kwargs: Attributes to update
            
        Returns:
            Dict containing the updated edge data or None if not found
        """
        edge = Edge.query.filter_by(uid=uid).first()
        
        if not edge:
            logging.warning(f"[{datetime.now()}] Update failed. Edge {uid} not found")
            return None
            
        # Update allowed fields
        allowed_fields = ["edge_type", "label", "weight", "attributes"]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(edge, field, value)
        
        try:
            db.session.commit()
            logging.info(f"[{datetime.now()}] Updated edge {uid}")
            
            # Get the node UIDs
            source_uid = Node.query.get(edge.source_id).uid if edge.source_id else None
            target_uid = Node.query.get(edge.target_id).uid if edge.target_id else None
            
            return {
                "id": edge.id,
                "uid": edge.uid,
                "edge_type": edge.edge_type,
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "source_uid": source_uid,
                "target_uid": target_uid,
                "label": edge.label,
                "weight": edge.weight,
                "attributes": edge.attributes,
                "updated_at": edge.updated_at.isoformat() if edge.updated_at else None
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{datetime.now()}] Error updating edge {uid}: {str(e)}")
            raise
    
    def delete_edge(self, uid: str) -> bool:
        """
        Delete an edge.
        
        Args:
            uid: Edge's unique identifier
            
        Returns:
            bool: True if successful, False if edge not found
        """
        edge = Edge.query.filter_by(uid=uid).first()
        
        if not edge:
            logging.warning(f"[{datetime.now()}] Delete failed. Edge {uid} not found")
            return False
            
        try:
            db.session.delete(edge)
            db.session.commit()
            
            logging.info(f"[{datetime.now()}] Deleted edge {uid}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{datetime.now()}] Error deleting edge {uid}: {str(e)}")
            raise
    
    def get_connected_nodes(self, node_uid: str, edge_type: Optional[str] = None, 
                          direction: str = "outgoing", limit: int = 100) -> List[Dict]:
        """
        Get nodes connected to a specific node.
        
        Args:
            node_uid: UID of the node
            edge_type: Optional edge type filter
            direction: "outgoing", "incoming", or "both"
            limit: Maximum number of nodes to return
            
        Returns:
            List of connected node dictionaries with edge information
        """
        node = Node.query.filter_by(uid=node_uid).first()
        
        if not node:
            logging.warning(f"[{datetime.now()}] Node {node_uid} not found")
            return []
            
        result = []
        
        # Get outgoing connections
        if direction in ["outgoing", "both"]:
            query = Edge.query.filter_by(source_id=node.id)
            
            if edge_type:
                query = query.filter_by(edge_type=edge_type)
                
            outgoing_edges = query.limit(limit).all()
            
            for edge in outgoing_edges:
                target_node = Node.query.get(edge.target_id)
                if target_node:
                    result.append({
                        "node": {
                            "uid": target_node.uid,
                            "node_type": target_node.node_type,
                            "label": target_node.label
                        },
                        "edge": {
                            "uid": edge.uid,
                            "edge_type": edge.edge_type,
                            "direction": "outgoing",
                            "weight": edge.weight,
                            "label": edge.label
                        }
                    })
        
        # Get incoming connections
        if direction in ["incoming", "both"] and len(result) < limit:
            remaining = limit - len(result)
            query = Edge.query.filter_by(target_id=node.id)
            
            if edge_type:
                query = query.filter_by(edge_type=edge_type)
                
            incoming_edges = query.limit(remaining).all()
            
            for edge in incoming_edges:
                source_node = Node.query.get(edge.source_id)
                if source_node:
                    result.append({
                        "node": {
                            "uid": source_node.uid,
                            "node_type": source_node.node_type,
                            "label": source_node.label
                        },
                        "edge": {
                            "uid": edge.uid,
                            "edge_type": edge.edge_type,
                            "direction": "incoming",
                            "weight": edge.weight,
                            "label": edge.label
                        }
                    })
                    
        return result
    
    # Knowledge Algorithm Methods
    def register_knowledge_algorithm(self, ka_id: str, name: str, description: Optional[str] = None,
                                  input_schema: Optional[Dict] = None, output_schema: Optional[Dict] = None,
                                  version: Optional[str] = None) -> Dict:
        """
        Register a Knowledge Algorithm in the system.
        
        Args:
            ka_id: Unique identifier for the Knowledge Algorithm
            name: Human-readable name
            description: Optional description
            input_schema: JSON schema for the KA's input
            output_schema: JSON schema for the KA's output
            version: Version string
            
        Returns:
            Dict containing the registered KA data
        """
        # Check if the KA already exists
        existing_ka = KnowledgeAlgorithm.query.filter_by(ka_id=ka_id).first()
        
        if existing_ka:
            # Update the existing KA
            existing_ka.name = name
            if description is not None:
                existing_ka.description = description
            if input_schema is not None:
                existing_ka.input_schema = input_schema
            if output_schema is not None:
                existing_ka.output_schema = output_schema
            if version is not None:
                existing_ka.version = version
                
            try:
                db.session.commit()
                logging.info(f"[{datetime.now()}] Updated Knowledge Algorithm {ka_id}")
                
                return {
                    "id": existing_ka.id,
                    "ka_id": existing_ka.ka_id,
                    "name": existing_ka.name,
                    "description": existing_ka.description,
                    "input_schema": existing_ka.input_schema,
                    "output_schema": existing_ka.output_schema,
                    "version": existing_ka.version,
                    "updated_at": existing_ka.updated_at.isoformat() if existing_ka.updated_at else None
                }
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"[{datetime.now()}] Error updating Knowledge Algorithm {ka_id}: {str(e)}")
                raise
        
        # Create a new KA
        try:
            new_ka = KnowledgeAlgorithm(
                ka_id=ka_id,
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                version=version
            )
            
            db.session.add(new_ka)
            db.session.commit()
            
            logging.info(f"[{datetime.now()}] Registered Knowledge Algorithm {ka_id}")
            
            return {
                "id": new_ka.id,
                "ka_id": new_ka.ka_id,
                "name": new_ka.name,
                "description": new_ka.description,
                "input_schema": new_ka.input_schema,
                "output_schema": new_ka.output_schema,
                "version": new_ka.version,
                "created_at": new_ka.created_at.isoformat() if new_ka.created_at else None
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{datetime.now()}] Error registering Knowledge Algorithm {ka_id}: {str(e)}")
            raise
    
    def record_ka_execution(self, ka_id: str, session_id: str, pass_num: int, layer_num: int,
                         input_data: Optional[Dict] = None, output_data: Optional[Dict] = None,
                         confidence: float = 0.0, execution_time: Optional[float] = None,
                         status: str = "completed", error_message: Optional[str] = None) -> Optional[Dict]:
        """
        Record an execution of a Knowledge Algorithm.
        
        Args:
            ka_id: ID of the Knowledge Algorithm
            session_id: ID of the session
            pass_num: Simulation pass number
            layer_num: Layer number within the pass
            input_data: KA input data
            output_data: KA output data
            confidence: Confidence score (0.0-1.0)
            execution_time: Time taken to execute (ms)
            status: Execution status (completed, error, etc.)
            error_message: Error message if status is error
            
        Returns:
            Dict containing the execution record or None if KA not found
        """
        # Get the KA
        ka = KnowledgeAlgorithm.query.filter_by(ka_id=ka_id).first()
        
        if not ka:
            logging.warning(f"[{datetime.now()}] Knowledge Algorithm {ka_id} not found")
            return None
            
        try:
            execution = KAExecution(
                algorithm_id=ka.id,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=layer_num,
                input_data=input_data,
                output_data=output_data,
                confidence=confidence,
                execution_time=execution_time,
                status=status,
                error_message=error_message
            )
            
            db.session.add(execution)
            db.session.commit()
            
            logging.info(f"[{datetime.now()}] Recorded execution of KA {ka_id} in session {session_id}")
            
            return {
                "id": execution.id,
                "ka_id": ka.ka_id,
                "session_id": execution.session_id,
                "pass_num": execution.pass_num,
                "layer_num": execution.layer_num,
                "confidence": execution.confidence,
                "status": execution.status,
                "created_at": execution.created_at.isoformat() if execution.created_at else None
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{datetime.now()}] Error recording KA execution: {str(e)}")
            raise
    
    # Session Management Methods
    def create_session(self, session_id: Optional[str] = None, user_query: Optional[str] = None,
                     target_confidence: float = 0.85) -> Dict:
        """
        Create a new UKG session.
        
        Args:
            session_id: Optional session ID (auto-generated if None)
            user_query: The user's query text
            target_confidence: Target confidence level for this session
            
        Returns:
            Dict containing the session data
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
            
        try:
            # Check if session already exists
            existing_session = Session.query.filter_by(session_id=session_id).first()
            
            if existing_session:
                logging.warning(f"[{datetime.now()}] Session {session_id} already exists")
                return {
                    "id": existing_session.id,
                    "session_id": existing_session.session_id,
                    "user_query": existing_session.user_query,
                    "target_confidence": existing_session.target_confidence,
                    "status": existing_session.status,
                    "started_at": existing_session.started_at.isoformat() if existing_session.started_at else None
                }
            
            new_session = Session(
                session_id=session_id,
                user_query=user_query,
                target_confidence=target_confidence,
                status="active"
            )
            
            db.session.add(new_session)
            db.session.commit()
            
            logging.info(f"[{datetime.now()}] Created session {session_id}")
            
            return {
                "id": new_session.id,
                "session_id": new_session.session_id,
                "user_query": new_session.user_query,
                "target_confidence": new_session.target_confidence,
                "status": new_session.status,
                "started_at": new_session.started_at.isoformat() if new_session.started_at else None
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{datetime.now()}] Error creating session: {str(e)}")
            raise
    
    def complete_session(self, session_id: str, final_confidence: float, status: str = "completed") -> Optional[Dict]:
        """
        Mark a session as completed.
        
        Args:
            session_id: ID of the session
            final_confidence: Final confidence score
            status: Final status (completed, error, etc.)
            
        Returns:
            Dict containing the session data or None if not found
        """
        session = Session.query.filter_by(session_id=session_id).first()
        
        if not session:
            logging.warning(f"[{datetime.now()}] Session {session_id} not found")
            return None
            
        try:
            session.final_confidence = final_confidence
            session.status = status
            session.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            logging.info(f"[{datetime.now()}] Completed session {session_id} with status {status}")
            
            return {
                "id": session.id,
                "session_id": session.session_id,
                "user_query": session.user_query,
                "target_confidence": session.target_confidence,
                "final_confidence": session.final_confidence,
                "status": session.status,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{datetime.now()}] Error completing session: {str(e)}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dict containing the session data or None if not found
        """
        session = Session.query.filter_by(session_id=session_id).first()
        
        if not session:
            return None
            
        return {
            "id": session.id,
            "session_id": session.session_id,
            "user_query": session.user_query,
            "target_confidence": session.target_confidence,
            "final_confidence": session.final_confidence,
            "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }
    
    # Memory Management Methods
    def add_memory_entry(self, session_id: str, entry_type: str, content: Optional[Dict] = None,
                       pass_num: int = 0, layer_num: int = 0, confidence: float = 1.0,
                       uid: Optional[str] = None) -> Optional[Dict]:
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
            Dict containing the memory entry or None if session not found
        """
        # Check if session exists
        session = Session.query.filter_by(session_id=session_id).first()
        
        if not session:
            logging.warning(f"[{datetime.now()}] Session {session_id} not found")
            return None
            
        if uid is None:
            uid = str(uuid.uuid4())
            
        try:
            entry = MemoryEntry(
                uid=uid,
                session_id=session_id,
                entry_type=entry_type,
                content=content,
                pass_num=pass_num,
                layer_num=layer_num,
                confidence=confidence
            )
            
            db.session.add(entry)
            db.session.commit()
            
            logging.info(f"[{datetime.now()}] Added memory entry {uid} of type {entry_type} to session {session_id}")
            
            return {
                "id": entry.id,
                "uid": entry.uid,
                "session_id": entry.session_id,
                "entry_type": entry.entry_type,
                "pass_num": entry.pass_num,
                "layer_num": entry.layer_num,
                "confidence": entry.confidence,
                "created_at": entry.created_at.isoformat() if entry.created_at else None
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{datetime.now()}] Error adding memory entry: {str(e)}")
            raise
    
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
            List of memory entry dictionaries
        """
        query = MemoryEntry.query.filter_by(session_id=session_id)
        
        if entry_type:
            query = query.filter_by(entry_type=entry_type)
            
        if pass_num is not None:
            query = query.filter_by(pass_num=pass_num)
            
        entries = query.order_by(MemoryEntry.created_at.desc()).limit(limit).all()
        
        result = []
        for entry in entries:
            result.append({
                "id": entry.id,
                "uid": entry.uid,
                "session_id": entry.session_id,
                "entry_type": entry.entry_type,
                "pass_num": entry.pass_num,
                "layer_num": entry.layer_num,
                "content": entry.content,
                "confidence": entry.confidence,
                "created_at": entry.created_at.isoformat() if entry.created_at else None
            })
            
        return result