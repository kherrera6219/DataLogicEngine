"""
GraphQL Schema for DataLogicEngine

Provides a GraphQL API for querying:
- Knowledge Graph nodes and edges
- Simulations and their results  
- Trace runs and execution data
- User profiles

Uses graphene library for type definitions.
"""

import graphene
from graphene import ObjectType, String, Int, Float, List, Field, Boolean
from flask import Blueprint
from flask_graphql import GraphQLView
from flask_login import login_required, current_user
import logging

logger = logging.getLogger(__name__)


# ============ Type Definitions ============

class UserType(ObjectType):
    """GraphQL type for User."""
    id = Int()
    username = String()
    email = String()
    role = String()
    is_admin = Boolean()


class KnowledgeNodeType(ObjectType):
    """GraphQL type for Knowledge Graph Node."""
    uid = String()
    name = String()
    description = String()
    node_type = String()
    pillar_id = String()
    created_at = String()
    metadata = String()  # JSON serialized
    
    # Axis coordinates
    axis_1 = String()
    axis_2 = String()
    axis_3 = String()


class KnowledgeEdgeType(ObjectType):
    """GraphQL type for Knowledge Graph Edge."""
    uid = String()
    source_id = String()
    target_id = String()
    relationship_type = String()
    weight = Float()


class SimulationType(ObjectType):
    """GraphQL type for Simulation."""
    uid = String()
    name = String()
    status = String()
    current_step = Int()
    created_at = String()
    user_id = String()


class TraceRunType(ObjectType):
    """GraphQL type for Trace Run."""
    run_id = String()
    status = String()
    created_at = String()
    completed_at = String()
    input_message = String()
    confidence = Float()
    entropy = Float()


class KAExecutionType(ObjectType):
    """GraphQL type for Knowledge Algorithm Execution."""
    uid = String()
    algorithm_name = String()
    status = String()
    started_at = String()
    completed_at = String()
    execution_time_ms = Int()


# ============ Query Definitions ============

class Query(ObjectType):
    """Root GraphQL Query."""
    
    # User queries
    me = Field(UserType)
    
    # Knowledge graph queries
    nodes = List(KnowledgeNodeType, 
                 pillar=String(),
                 search=String(),
                 limit=Int(default_value=50))
    node = Field(KnowledgeNodeType, uid=String(required=True))
    edges = List(KnowledgeEdgeType, 
                 source_id=String(),
                 target_id=String(),
                 limit=Int(default_value=100))
    
    # Simulation queries
    simulations = List(SimulationType,
                       status=String(),
                       limit=Int(default_value=20))
    simulation = Field(SimulationType, uid=String(required=True))
    
    # Trace queries
    traces = List(TraceRunType,
                  status=String(),
                  limit=Int(default_value=20))
    trace = Field(TraceRunType, run_id=String(required=True))
    
    # Stats
    node_count = Int()
    edge_count = Int()
    simulation_count = Int()
    
    def resolve_me(self, info):
        """Get current authenticated user."""
        if current_user.is_authenticated:
            return UserType(
                id=current_user.id,
                username=current_user.username,
                email=current_user.email,
                role=getattr(current_user, 'role', 'user'),
                is_admin=getattr(current_user, 'is_admin', False)
            )
        return None
    
    def resolve_nodes(self, info, pillar=None, search=None, limit=50):
        """Query knowledge graph nodes."""
        try:
            from extensions import db
            from db_models import KnowledgeGraphNode
            
            query = db.session.query(KnowledgeGraphNode)
            
            if pillar:
                query = query.filter(KnowledgeGraphNode.pillar_id == pillar)
            if search:
                query = query.filter(
                    KnowledgeGraphNode.name.ilike(f'%{search}%')
                )
            
            nodes = query.limit(limit).all()
            return [
                KnowledgeNodeType(
                    uid=n.uid,
                    name=n.name,
                    description=getattr(n, 'description', None),
                    node_type=getattr(n, 'node_type', None),
                    pillar_id=getattr(n, 'pillar_id', None),
                    created_at=str(n.created_at) if hasattr(n, 'created_at') else None
                )
                for n in nodes
            ]
        except Exception as e:
            logger.error(f"GraphQL nodes query error: {e}")
            return []
    
    def resolve_node(self, info, uid):
        """Get single node by UID."""
        try:
            from extensions import db
            from db_models import KnowledgeGraphNode
            
            node = db.session.query(KnowledgeGraphNode).filter_by(uid=uid).first()
            if node:
                return KnowledgeNodeType(
                    uid=node.uid,
                    name=node.name,
                    description=getattr(node, 'description', None),
                    node_type=getattr(node, 'node_type', None),
                    pillar_id=getattr(node, 'pillar_id', None)
                )
            return None
        except Exception as e:
            logger.error(f"GraphQL node query error: {e}")
            return None
    
    def resolve_simulations(self, info, status=None, limit=20):
        """Query simulations."""
        try:
            from extensions import db
            from db_models import SimulationSession
            
            query = db.session.query(SimulationSession)
            if status:
                query = query.filter(SimulationSession.status == status)
            
            sims = query.order_by(SimulationSession.created_at.desc()).limit(limit).all()
            return [
                SimulationType(
                    uid=s.uid,
                    name=s.name,
                    status=s.status,
                    current_step=getattr(s, 'current_step', 0),
                    created_at=str(s.created_at)
                )
                for s in sims
            ]
        except Exception as e:
            logger.error(f"GraphQL simulations query error: {e}")
            return []
    
    def resolve_node_count(self, info):
        """Get total node count."""
        try:
            from extensions import db
            from db_models import KnowledgeGraphNode
            return db.session.query(KnowledgeGraphNode).count()
        except Exception:
            return 0
    
    def resolve_edge_count(self, info):
        """Get total edge count."""
        try:
            from extensions import db
            from db_models import KnowledgeGraphEdge
            return db.session.query(KnowledgeGraphEdge).count()
        except Exception:
            return 0


# ============ Mutation Definitions ============

class CreateSimulation(graphene.Mutation):
    """Create a new simulation."""
    class Arguments:
        name = String(required=True)
        mode = String(default_value='standard')
    
    simulation = Field(SimulationType)
    success = Boolean()
    error = String()
    
    def mutate(self, info, name, mode='standard'):
        try:
            from extensions import db
            from db_models import SimulationSession
            import uuid
            
            sim = SimulationSession(
                uid=str(uuid.uuid4()),
                name=name,
                status='active',
                user_id=str(current_user.id) if current_user.is_authenticated else None
            )
            db.session.add(sim)
            db.session.commit()
            
            return CreateSimulation(
                simulation=SimulationType(
                    uid=sim.uid,
                    name=sim.name,
                    status=sim.status
                ),
                success=True
            )
        except Exception as e:
            logger.error(f"GraphQL createSimulation error: {e}")
            return CreateSimulation(success=False, error=str(e))


class Mutation(ObjectType):
    """Root GraphQL Mutation."""
    create_simulation = CreateSimulation.Field()


# ============ Schema ============

schema = graphene.Schema(query=Query, mutation=Mutation)


# ============ Blueprint Registration ============

graphql_bp = Blueprint('graphql', __name__)


def register_graphql(app):
    """Register GraphQL endpoint with Flask app."""
    app.add_url_rule(
        '/graphql',
        view_func=GraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=True  # Enable GraphiQL IDE in development
        )
    )
    logger.info("GraphQL API registered at /graphql")
