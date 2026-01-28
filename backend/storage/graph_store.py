import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver
from config import get_config

logger = logging.getLogger(__name__)

class GraphStore:
    """
    Interface for interacting with the Neo4j Graph Database.
    Used by the Universal Knowledge Graph (UKG) simulation stack.
    """
    
    def __init__(self):
        config = get_config()
        self.uri = getattr(config, 'NEO4J_URI', 'bolt://localhost:7687')
        self.user = getattr(config, 'NEO4J_USER', 'neo4j')
        self.password = getattr(config, 'NEO4J_PASSWORD', 'password')
        self.driver: Optional[Driver] = None

    def connect(self):
        """Establish connection to the Neo4j instance."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    def close(self):
        """Close the Neo4j driver."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed.")

    def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run a Cypher query and return results as a list of dictionaries."""
        if not self.driver:
            self.connect()
            if not self.driver:
                return []

        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Cypher query failed: {e}")
            return []

    def create_node(self, label: str, properties: Dict[str, Any]) -> bool:
        """Create a single node in the graph."""
        query = f"CREATE (n:{label} $props) RETURN n"
        results = self.run_query(query, {"props": properties})
        return len(results) > 0

    def create_relationship(self, from_id: str, to_id: str, rel_type: str, props: Optional[Dict[str, Any]] = None) -> bool:
        """Create a directed relationship between two nodes identified by their 'id' property."""
        query = (
            f"MATCH (a), (b) "
            f"WHERE a.id = $from_id AND b.id = $to_id "
            f"CREATE (a)-[r:{rel_type} $props]->(b) "
            f"RETURN r"
        )
        results = self.run_query(query, {
            "from_id": from_id,
            "to_id": to_id,
            "props": props or {}
        })
        return len(results) > 0

# Singleton instance for easy access
graph_store = GraphStore()

def get_graph_store() -> GraphStore:
    return graph_store
