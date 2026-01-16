"""
Search Service for DataLogicEngine

Provides full-text search functionality using PostgreSQL FTS.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text, func, cast, String
from extensions import db

logger = logging.getLogger(__name__)


def search_knowledge_nodes(
    query: str,
    limit: int = 20,
    offset: int = 0,
    node_type: Optional[str] = None,
    axis_number: Optional[int] = None
) -> Dict[str, Any]:
    """
    Search knowledge graph nodes using PostgreSQL full-text search.
    
    Args:
        query: Search query string
        limit: Maximum results to return
        offset: Offset for pagination
        node_type: Optional filter by node type
        axis_number: Optional filter by axis number
    
    Returns:
        Dict with results and metadata
    """
    try:
        # Build the search query with tsvector and tsquery
        search_query = """
            SELECT 
                id,
                node_id,
                node_type,
                label,
                description,
                axis_number,
                ts_rank(
                    to_tsvector('english', COALESCE(label, '') || ' ' || COALESCE(description, '')),
                    plainto_tsquery('english', :query)
                ) as rank
            FROM kg_nodes
            WHERE 
                to_tsvector('english', COALESCE(label, '') || ' ' || COALESCE(description, ''))
                @@ plainto_tsquery('english', :query)
        """
        
        params = {'query': query, 'limit': limit, 'offset': offset}
        
        if node_type:
            search_query += " AND node_type = :node_type"
            params['node_type'] = node_type
        
        if axis_number is not None:
            search_query += " AND axis_number = :axis_number"
            params['axis_number'] = axis_number
        
        search_query += " ORDER BY rank DESC LIMIT :limit OFFSET :offset"
        
        result = db.session.execute(text(search_query), params)
        results = [dict(row._mapping) for row in result]
        
        # Get total count
        count_query = """
            SELECT COUNT(*) 
            FROM kg_nodes
            WHERE to_tsvector('english', COALESCE(label, '') || ' ' || COALESCE(description, ''))
                @@ plainto_tsquery('english', :query)
        """
        count_params = {'query': query}
        if node_type:
            count_query = count_query.replace("WHERE", "WHERE node_type = :node_type AND")
            count_params['node_type'] = node_type
        
        total = db.session.execute(text(count_query), count_params).scalar()
        
        return {
            'success': True,
            'results': results,
            'total': total,
            'limit': limit,
            'offset': offset,
            'query': query
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            'success': False,
            'error': str(e),
            'results': [],
            'total': 0
        }


def search_ukg_nodes(
    query: str,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """Search UKG nodes using full-text search."""
    try:
        search_query = """
            SELECT 
                id,
                uid,
                node_type,
                label,
                axis_number,
                description,
                ts_rank(
                    to_tsvector('english', COALESCE(label, '') || ' ' || COALESCE(description, '')),
                    plainto_tsquery('english', :query)
                ) as rank
            FROM ukg_nodes
            WHERE 
                to_tsvector('english', COALESCE(label, '') || ' ' || COALESCE(description, ''))
                @@ plainto_tsquery('english', :query)
                AND active = true
            ORDER BY rank DESC
            LIMIT :limit OFFSET :offset
        """
        
        result = db.session.execute(
            text(search_query),
            {'query': query, 'limit': limit, 'offset': offset}
        )
        
        return {
            'success': True,
            'results': [dict(row._mapping) for row in result],
            'query': query
        }
        
    except Exception as e:
        logger.error(f"UKG search error: {e}")
        return {'success': False, 'error': str(e), 'results': []}


def search_algorithms(
    query: str,
    limit: int = 20
) -> Dict[str, Any]:
    """Search knowledge algorithms."""
    try:
        search_query = """
            SELECT 
                id,
                uid,
                algorithm_id,
                name,
                description,
                language,
                version,
                ts_rank(
                    to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(description, '')),
                    plainto_tsquery('english', :query)
                ) as rank
            FROM ukg_knowledge_algorithms
            WHERE 
                to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(description, ''))
                @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit
        """
        
        result = db.session.execute(text(search_query), {'query': query, 'limit': limit})
        
        return {
            'success': True,
            'results': [dict(row._mapping) for row in result],
            'query': query
        }
        
    except Exception as e:
        logger.error(f"Algorithm search error: {e}")
        return {'success': False, 'error': str(e), 'results': []}


def global_search(
    query: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Perform global search across all searchable entities.
    
    Returns categorized results from nodes, algorithms, etc.
    """
    results = {
        'nodes': search_knowledge_nodes(query, limit=limit),
        'ukg_nodes': search_ukg_nodes(query, limit=limit),
        'algorithms': search_algorithms(query, limit=limit)
    }
    
    return {
        'success': True,
        'query': query,
        'results': results
    }
