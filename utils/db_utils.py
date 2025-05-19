import logging
from datetime import datetime
from models import db, Node, Edge, KnowledgeAlgorithm, KAExecution, Session, MemoryEntry

class DatabaseManager:
    """
    The DatabaseManager provides utility methods for interacting with the database.
    It offers functions for common operations like adding, retrieving, and updating
    nodes, edges, and other entities in the UKG system.
    """
    
    @staticmethod
    def add_node(uid, node_type, label, description=None, original_id=None, 
               axis_number=None, level=None, attributes=None):
        """
        Add a new node to the database.
        
        Args:
            uid (str): Unique identifier for the node
            node_type (str): Type of node (e.g., 'Axis', 'PillarLevel', 'Topic')
            label (str): Human-readable label for the node
            description (str, optional): Detailed description of the node
            original_id (str, optional): Original ID from source data
            axis_number (int, optional): Axis number (1-13) if applicable
            level (int, optional): Level number if applicable
            attributes (dict, optional): Additional attributes as a JSON-serializable dict
            
        Returns:
            Node: The created Node object, or None if creation failed
        """
        try:
            node = Node()
            node.uid = uid
            node.node_type = node_type
            node.label = label
            node.description = description
            node.original_id = original_id
            node.axis_number = axis_number
            node.level = level
            node.attributes = attributes
            db.session.add(node)
            db.session.commit()
            logging.info(f"Added node with UID: {uid}")
            return node
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to add node: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def get_node_by_uid(uid):
        """
        Retrieve a node by its UID.
        
        Args:
            uid (str): The UID of the node to retrieve
            
        Returns:
            Node: The Node object, or None if not found
        """
        return Node.query.filter_by(uid=uid).first()
    
    @staticmethod
    def get_nodes_by_type(node_type):
        """
        Retrieve all nodes of a specific type.
        
        Args:
            node_type (str): The type of nodes to retrieve
            
        Returns:
            list: List of Node objects
        """
        return Node.query.filter_by(node_type=node_type).all()
    
    @staticmethod
    def get_nodes_by_axis(axis_number):
        """
        Retrieve all nodes belonging to a specific axis.
        
        Args:
            axis_number (int): The axis number (1-13)
            
        Returns:
            list: List of Node objects
        """
        return Node.query.filter_by(axis_number=axis_number).all()
    
    @staticmethod
    def add_edge(uid, edge_type, source_uid, target_uid, label=None, weight=1.0, attributes=None):
        """
        Add a new edge between two nodes in the database.
        
        Args:
            uid (str): Unique identifier for the edge
            edge_type (str): Type of edge (e.g., 'CONNECTS_TO', 'DEPENDS_ON')
            source_uid (str): UID of the source node
            target_uid (str): UID of the target node
            label (str, optional): Human-readable label for the edge
            weight (float, optional): Weight or strength of the connection
            attributes (dict, optional): Additional attributes as a JSON-serializable dict
            
        Returns:
            Edge: The created Edge object, or None if creation failed
        """
        try:
            # Get the source and target nodes
            source_node = DatabaseManager.get_node_by_uid(source_uid)
            target_node = DatabaseManager.get_node_by_uid(target_uid)
            
            if not source_node or not target_node:
                logging.error(f"Failed to add edge: source or target node not found. Source: {source_uid}, Target: {target_uid}")
                return None
            
            edge = Edge()
            edge.uid = uid
            edge.edge_type = edge_type
            edge.source_id = source_node.id
            edge.target_id = target_node.id
            edge.label = label
            edge.weight = weight
            edge.attributes = attributes
            db.session.add(edge)
            db.session.commit()
            logging.info(f"Added edge with UID: {uid}")
            return edge
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to add edge: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def get_edge_by_uid(uid):
        """
        Retrieve an edge by its UID.
        
        Args:
            uid (str): The UID of the edge to retrieve
            
        Returns:
            Edge: The Edge object, or None if not found
        """
        return Edge.query.filter_by(uid=uid).first()
    
    @staticmethod
    def get_edges_by_type(edge_type):
        """
        Retrieve all edges of a specific type.
        
        Args:
            edge_type (str): The type of edges to retrieve
            
        Returns:
            list: List of Edge objects
        """
        return Edge.query.filter_by(edge_type=edge_type).all()
    
    @staticmethod
    def get_outgoing_edges(node_uid):
        """
        Get all outgoing edges from a specific node.
        
        Args:
            node_uid (str): The UID of the source node
            
        Returns:
            list: List of Edge objects
        """
        node = DatabaseManager.get_node_by_uid(node_uid)
        if not node:
            return []
        return node.outgoing_edges
    
    @staticmethod
    def get_incoming_edges(node_uid):
        """
        Get all incoming edges to a specific node.
        
        Args:
            node_uid (str): The UID of the target node
            
        Returns:
            list: List of Edge objects
        """
        node = DatabaseManager.get_node_by_uid(node_uid)
        if not node:
            return []
        return node.incoming_edges
    
    @staticmethod
    def create_session(session_id, query=None, target_confidence=0.85):
        """
        Create a new session record.
        
        Args:
            session_id (str): Unique identifier for the session
            query (str, optional): The user's query text
            target_confidence (float, optional): Target confidence level
            
        Returns:
            Session: The created Session object, or None if creation failed
        """
        try:
            session = Session(
                session_id=session_id,
                user_query=query,
                target_confidence=target_confidence,
                status='active',
                started_at=datetime.utcnow()
            )
            db.session.add(session)
            db.session.commit()
            logging.info(f"Created session with ID: {session_id}")
            return session
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to create session: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def complete_session(session_id, final_confidence=None):
        """
        Mark a session as completed.
        
        Args:
            session_id (str): The session ID
            final_confidence (float, optional): Final confidence level achieved
            
        Returns:
            bool: True if successfully completed, False otherwise
        """
        try:
            session = Session.query.filter_by(session_id=session_id).first()
            if not session:
                logging.error(f"Session not found: {session_id}")
                return False
            
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            if final_confidence is not None:
                session.final_confidence = final_confidence
            
            db.session.commit()
            logging.info(f"Completed session with ID: {session_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to complete session: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def add_memory_entry(uid, session_id, entry_type, content, pass_num=0, layer_num=0, confidence=1.0):
        """
        Add a new memory entry to the database.
        
        Args:
            uid (str): Unique identifier for the memory entry
            session_id (str): The session ID this entry belongs to
            entry_type (str): Type of entry (e.g., 'ka_output', 'simulation_state')
            content (dict): The content to store (JSON-serializable)
            pass_num (int, optional): Pass number within the session
            layer_num (int, optional): Layer number
            confidence (float, optional): Confidence score for this entry
            
        Returns:
            MemoryEntry: The created MemoryEntry object, or None if creation failed
        """
        try:
            # Check if the session exists
            session = Session.query.filter_by(session_id=session_id).first()
            if not session:
                logging.error(f"Session not found: {session_id}")
                return None
            
            memory_entry = MemoryEntry(
                uid=uid,
                session_id=session_id,
                entry_type=entry_type,
                content=content,
                pass_num=pass_num,
                layer_num=layer_num,
                confidence=confidence
            )
            db.session.add(memory_entry)
            db.session.commit()
            logging.info(f"Added memory entry with UID: {uid}")
            return memory_entry
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to add memory entry: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def get_memory_entries_by_session(session_id, entry_type=None):
        """
        Get all memory entries for a specific session.
        
        Args:
            session_id (str): The session ID
            entry_type (str, optional): Filter by entry type
            
        Returns:
            list: List of MemoryEntry objects
        """
        query = MemoryEntry.query.filter_by(session_id=session_id)
        if entry_type:
            query = query.filter_by(entry_type=entry_type)
        return query.all()
    
    @staticmethod
    def register_knowledge_algorithm(ka_id, name, description=None, input_schema=None, output_schema=None, version="1.0"):
        """
        Register a knowledge algorithm in the database.
        
        Args:
            ka_id (str): Unique identifier for the KA
            name (str): Name of the KA
            description (str, optional): Description of what the KA does
            input_schema (dict, optional): JSON schema describing expected inputs
            output_schema (dict, optional): JSON schema describing expected outputs
            version (str, optional): Version of the KA
            
        Returns:
            KnowledgeAlgorithm: The created KnowledgeAlgorithm object, or None if creation failed
        """
        try:
            ka = KnowledgeAlgorithm(
                ka_id=ka_id,
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                version=version
            )
            db.session.add(ka)
            db.session.commit()
            logging.info(f"Registered KA with ID: {ka_id}")
            return ka
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to register KA: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def record_ka_execution(ka_id, session_id, input_data, output_data=None, confidence=0.0, 
                          execution_time=None, status="completed", error_message=None, 
                          pass_num=0, layer_num=0):
        """
        Record the execution of a knowledge algorithm.
        
        Args:
            ka_id (str): ID of the KA
            session_id (str): The session ID
            input_data (dict): Input data provided to the KA
            output_data (dict, optional): Output data produced by the KA
            confidence (float, optional): Confidence score for the execution
            execution_time (float, optional): Execution time in milliseconds
            status (str, optional): Status of the execution
            error_message (str, optional): Error message if execution failed
            pass_num (int, optional): Pass number within the session
            layer_num (int, optional): Layer number
            
        Returns:
            KAExecution: The created KAExecution object, or None if creation failed
        """
        try:
            # Get the KA
            ka = KnowledgeAlgorithm.query.filter_by(ka_id=ka_id).first()
            if not ka:
                logging.error(f"KA not found: {ka_id}")
                return None
            
            execution = KAExecution(
                algorithm_id=ka.id,
                session_id=session_id,
                input_data=input_data,
                output_data=output_data,
                confidence=confidence,
                execution_time=execution_time,
                status=status,
                error_message=error_message,
                pass_num=pass_num,
                layer_num=layer_num
            )
            db.session.add(execution)
            db.session.commit()
            logging.info(f"Recorded execution of KA {ka_id} in session {session_id}")
            return execution
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to record KA execution: {str(e)}", exc_info=True)
            return None