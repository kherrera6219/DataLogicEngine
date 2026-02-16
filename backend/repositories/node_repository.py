import logging
from typing import Dict, Optional
from sqlalchemy.exc import SQLAlchemyError
from models import Node
from extensions import db, cache

logger = logging.getLogger(__name__)

class NodeRepository:
    """
    Repository for managing Node entities.
    Handles persistence and caching for knowledge graph nodes.
    """
    
    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id

    def create(self, node_data: Dict) -> Optional[Dict]:
        """Create a new node."""
        try:
            node = Node(
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
            
            db.session.add(node)
            db.session.commit()
            
            # Cache the new node
            self._cache_node(node)
            
            return self._to_dict(node)
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"NodeRepo: Error creating node: {str(e)}")
            return None

    def get_by_uid(self, uid: str) -> Optional[Dict]:
        """Get a node by its UID with caching."""
        cache_key = self._get_cache_key(uid)
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            query = db.session.query(Node).filter(Node.uid == uid)
            if self.tenant_id:
                query = query.filter(Node.tenant_id == self.tenant_id)
            
            node = query.first()
            if node:
                data = self._to_dict(node)
                cache.set(cache_key, data, timeout=300)
                return data
            return None
        except SQLAlchemyError as e:
            logger.error(f"NodeRepo: Error fetching node {uid}: {str(e)}")
            return None

    def _cache_node(self, node: Node):
        """Helper to cache a node."""
        if node.uid:
            cache_key = self._get_cache_key(node.uid)
            cache.set(cache_key, self._to_dict(node), timeout=300)

    def _get_cache_key(self, uid: str) -> str:
        return f"node:{uid}:{self.tenant_id or 'global'}"

    def _to_dict(self, node: Node) -> Dict:
        return {
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
