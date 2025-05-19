import logging
from datetime import datetime
from .models import db, UkgNode, UkgEdge, KnowledgeAlgorithm, KaExecution, UkgSession, MemoryEntry

class UkgDatabaseManager:
    """
    Database manager for the Universal Knowledge Graph (UKG) system.
    Provides methods to interact with UKG-specific database models.
    """
    
    @staticmethod
    def add_node(uid, node_type, label, description=None, original_id=None, 
               axis_number=None, level=None, attributes=None):
        """
        Add a new node to the UKG.
        
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
            UkgNode: The created node, or None if creation failed
        """
        try:
            node = UkgNode()
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
            logging.info(f"Added UKG node with UID: {uid}")
            return node
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to add UKG node: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def get_node_by_uid(uid):
        """
        Retrieve a node by its UID.
        
        Args:
            uid (str): The UID of the node to retrieve
            
        Returns:
            UkgNode: The node object, or None if not found
        """
        return UkgNode.query.filter_by(uid=uid).first()
    
    @staticmethod
    def get_nodes_by_type(node_type):
        """
        Retrieve all nodes of a specific type.
        
        Args:
            node_type (str): The type of nodes to retrieve
            
        Returns:
            list: List of UkgNode objects
        """
        return UkgNode.query.filter_by(node_type=node_type).all()
    
    @staticmethod
    def get_nodes_by_axis(axis_number):
        """
        Retrieve all nodes belonging to a specific axis.
        
        Args:
            axis_number (int): The axis number (1-13)
            
        Returns:
            list: List of UkgNode objects
        """
        return UkgNode.query.filter_by(axis_number=axis_number).all()
    
    @staticmethod
    def add_edge(uid, edge_type, source_uid, target_uid, label=None, weight=1.0, attributes=None):
        """
        Add a new edge between two nodes in the UKG.
        
        Args:
            uid (str): Unique identifier for the edge
            edge_type (str): Type of edge (e.g., 'CONNECTS_TO', 'DEPENDS_ON')
            source_uid (str): UID of the source node
            target_uid (str): UID of the target node
            label (str, optional): Human-readable label for the edge
            weight (float, optional): Weight or strength of the connection
            attributes (dict, optional): Additional attributes as a JSON-serializable dict
            
        Returns:
            UkgEdge: The created edge, or None if creation failed
        """
        try:
            # Get the source and target nodes
            source_node = UkgDatabaseManager.get_node_by_uid(source_uid)
            target_node = UkgDatabaseManager.get_node_by_uid(target_uid)
            
            if not source_node or not target_node:
                logging.error(f"Failed to add edge: source or target node not found. Source: {source_uid}, Target: {target_uid}")
                return None
            
            edge = UkgEdge()
            edge.uid = uid
            edge.edge_type = edge_type
            edge.source_id = source_node.id
            edge.target_id = target_node.id
            edge.label = label
            edge.weight = weight
            edge.attributes = attributes
            
            db.session.add(edge)
            db.session.commit()
            logging.info(f"Added UKG edge with UID: {uid}")
            return edge
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to add UKG edge: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def create_session(session_id, user_id=None, query=None, target_confidence=0.85):
        """
        Create a new UKG session.
        
        Args:
            session_id (str): Unique identifier for the session
            user_id (int, optional): ID of the user if authenticated
            query (str, optional): The user's query text
            target_confidence (float, optional): Target confidence level
            
        Returns:
            UkgSession: The created session, or None if creation failed
        """
        try:
            session = UkgSession()
            session.session_id = session_id
            session.user_id = user_id
            session.user_query = query
            session.target_confidence = target_confidence
            session.status = 'active'
            session.started_at = datetime.utcnow()
            
            db.session.add(session)
            db.session.commit()
            logging.info(f"Created UKG session with ID: {session_id}")
            return session
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to create UKG session: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def complete_session(session_id, final_confidence=None):
        """
        Mark a UKG session as completed.
        
        Args:
            session_id (str): The session ID
            final_confidence (float, optional): Final confidence level achieved
            
        Returns:
            bool: True if successfully completed, False otherwise
        """
        try:
            session = UkgSession.query.filter_by(session_id=session_id).first()
            if not session:
                logging.error(f"UKG session not found: {session_id}")
                return False
            
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            if final_confidence is not None:
                session.final_confidence = final_confidence
            
            db.session.commit()
            logging.info(f"Completed UKG session with ID: {session_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to complete UKG session: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def add_memory_entry(uid, session_id, entry_type, content, pass_num=0, layer_num=0, confidence=1.0):
        """
        Add a new memory entry to the UKG.
        
        Args:
            uid (str): Unique identifier for the memory entry
            session_id (str): The session ID this entry belongs to
            entry_type (str): Type of entry (e.g., 'ka_output', 'simulation_state')
            content (dict): The content to store (JSON-serializable)
            pass_num (int, optional): Pass number within the session
            layer_num (int, optional): Layer number
            confidence (float, optional): Confidence score for this entry
            
        Returns:
            MemoryEntry: The created memory entry, or None if creation failed
        """
        try:
            # Check if the session exists
            session = UkgSession.query.filter_by(session_id=session_id).first()
            if not session:
                logging.error(f"UKG session not found: {session_id}")
                return None
            
            entry = MemoryEntry()
            entry.uid = uid
            entry.session_id = session_id
            entry.entry_type = entry_type
            entry.content = content
            entry.pass_num = pass_num
            entry.layer_num = layer_num
            entry.confidence = confidence
            
            db.session.add(entry)
            db.session.commit()
            logging.info(f"Added memory entry with UID: {uid}")
            return entry
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to add memory entry: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def register_knowledge_algorithm(ka_id, name, description=None, input_schema=None, output_schema=None, version="1.0"):
        """
        Register a knowledge algorithm in the UKG.
        
        Args:
            ka_id (str): Unique identifier for the KA
            name (str): Name of the KA
            description (str, optional): Description of what the KA does
            input_schema (dict, optional): JSON schema describing expected inputs
            output_schema (dict, optional): JSON schema describing expected outputs
            version (str, optional): Version of the KA
            
        Returns:
            KnowledgeAlgorithm: The registered KA, or None if registration failed
        """
        try:
            ka = KnowledgeAlgorithm()
            ka.ka_id = ka_id
            ka.name = name
            ka.description = description
            ka.input_schema = input_schema
            ka.output_schema = output_schema
            ka.version = version
            
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
            KaExecution: The recorded execution, or None if recording failed
        """
        try:
            # Get the KA
            ka = KnowledgeAlgorithm.query.filter_by(ka_id=ka_id).first()
            if not ka:
                logging.error(f"KA not found: {ka_id}")
                return None
            
            execution = KaExecution()
            execution.algorithm_id = ka.id
            execution.session_id = session_id
            execution.input_data = input_data
            execution.output_data = output_data
            execution.confidence = confidence
            execution.execution_time = execution_time
            execution.status = status
            execution.error_message = error_message
            execution.pass_num = pass_num
            execution.layer_num = layer_num
            
            db.session.add(execution)
            db.session.commit()
            logging.info(f"Recorded execution of KA {ka_id} in session {session_id}")
            return execution
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to record KA execution: {str(e)}", exc_info=True)
            return None