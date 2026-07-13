import graphene
from graphene import ObjectType, String, Int, Float, List, Field, Boolean
from flask import Blueprint, current_app, request, jsonify
from flask_login import current_user
import logging
import os
from graphql import GraphQLError, parse
from graphql.language.ast import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    OperationDefinitionNode,
    SelectionSetNode,
)
from backend.auth.api_decorators import api_login_required

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
                # Single-mode: the one authenticated OS user is the owner (Phase E).
                role='owner',
                is_admin=True
            )
        return None
    
    def resolve_nodes(self, info, pillar=None, search=None, limit=50):
        """Query knowledge graph nodes."""
        try:
            from extensions import db
            from models import KnowledgeGraphNode
            
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
                    uid=n.node_id,
                    name=n.label,
                    description=getattr(n, 'description', None),
                    node_type=getattr(n, 'node_type', None),
                    pillar_id=None,
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
            from models import KnowledgeGraphNode
            
            node = db.session.query(KnowledgeGraphNode).filter_by(node_id=uid).first()
            if node:
                return KnowledgeNodeType(
                    uid=node.node_id,
                    name=node.label,
                    description=getattr(node, 'description', None),
                    node_type=getattr(node, 'node_type', None),
                    pillar_id=None
                )
            return None
        except Exception as e:
            logger.error(f"GraphQL node query error: {e}")
            return None
    
    def resolve_simulations(self, info, status=None, limit=20):
        """Query simulations."""
        try:
            from extensions import db
            from models import SimulationSession
            
            query = db.session.query(SimulationSession)
            if status:
                query = query.filter(SimulationSession.status == status)
            
            sims = query.order_by(SimulationSession.created_at.desc()).limit(limit).all()
            return [
                SimulationType(
                    uid=s.session_id,
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
            from models import KnowledgeGraphNode
            return db.session.query(KnowledgeGraphNode).count()
        except Exception:
            return 0
    
    def resolve_edge_count(self, info):
        """Get total edge count."""
        try:
            from extensions import db
            from models import KnowledgeGraphEdge
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
            from models import SimulationSession
            import uuid
            
            sim = SimulationSession(
                session_id=str(uuid.uuid4()),
                name=name,
                status='active',
                user_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(sim)
            db.session.commit()
            
            return CreateSimulation(
                simulation=SimulationType(
                    uid=sim.session_id,
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


# ============ Custom GraphQL View ============

def _graphql_error(code: str, message: str, status: int = 400):
    return jsonify({'errors': [{'code': code, 'message': message}]}), status


def _bounded_graphql_limit(name: str, default: int, maximum: int) -> int:
    raw = current_app.config.get(name, os.environ.get(name, default))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    return max(1, min(value, maximum))


def _selection_metrics(
    selection_set: SelectionSetNode | None,
    fragments: dict[str, FragmentDefinitionNode],
    depth: int = 0,
    visited_fragments: frozenset[str] = frozenset(),
) -> tuple[int, int, bool]:
    if selection_set is None:
        return 0, depth, False
    field_count = 0
    max_depth = depth
    has_introspection = False
    for selection in selection_set.selections:
        if isinstance(selection, FieldNode):
            field_count += 1
            field_depth = depth + 1
            max_depth = max(max_depth, field_depth)
            has_introspection = has_introspection or selection.name.value.startswith('__')
            child_count, child_depth, child_introspection = _selection_metrics(
                selection.selection_set,
                fragments,
                field_depth,
                visited_fragments,
            )
            field_count += child_count
            max_depth = max(max_depth, child_depth)
            has_introspection = has_introspection or child_introspection
        elif isinstance(selection, InlineFragmentNode):
            child_count, child_depth, child_introspection = _selection_metrics(
                selection.selection_set,
                fragments,
                depth,
                visited_fragments,
            )
            field_count += child_count
            max_depth = max(max_depth, child_depth)
            has_introspection = has_introspection or child_introspection
        elif isinstance(selection, FragmentSpreadNode):
            name = selection.name.value
            if name in visited_fragments or name not in fragments:
                continue
            child_count, child_depth, child_introspection = _selection_metrics(
                fragments[name].selection_set,
                fragments,
                depth,
                visited_fragments | {name},
            )
            field_count += child_count
            max_depth = max(max_depth, child_depth)
            has_introspection = has_introspection or child_introspection
    return field_count, max_depth, has_introspection


def _validate_graphql_query(query: str):
    try:
        document = parse(query)
    except GraphQLError:
        return _graphql_error('GRAPHQL_INVALID_QUERY', 'GraphQL query is invalid')

    fragments = {
        definition.name.value: definition
        for definition in document.definitions
        if isinstance(definition, FragmentDefinitionNode)
    }
    field_count = 0
    max_depth = 0
    has_introspection = False
    for definition in document.definitions:
        if not isinstance(definition, OperationDefinitionNode):
            continue
        count, depth, introspection = _selection_metrics(
            definition.selection_set,
            fragments,
        )
        field_count += count
        max_depth = max(max_depth, depth)
        has_introspection = has_introspection or introspection

    allow_introspection = current_app.config.get('GRAPHQL_ALLOW_INTROSPECTION')
    if allow_introspection is None:
        allow_introspection = os.environ.get('FLASK_ENV', 'production') != 'production'
    if has_introspection and not bool(allow_introspection):
        return _graphql_error(
            'GRAPHQL_INTROSPECTION_DISABLED',
            'GraphQL introspection is disabled',
        )
    if max_depth > _bounded_graphql_limit('GRAPHQL_MAX_DEPTH', 8, 32):
        return _graphql_error('GRAPHQL_DEPTH_EXCEEDED', 'GraphQL query depth exceeds the limit')
    if field_count > _bounded_graphql_limit('GRAPHQL_MAX_FIELDS', 100, 1000):
        return _graphql_error(
            'GRAPHQL_COMPLEXITY_EXCEEDED',
            'GraphQL query complexity exceeds the limit',
        )
    return None

def graphql_view():
    """Custom GraphQL view to handle requests without flask-graphql."""
    if request.method == 'GET':
        # Return simple message for browser access
        return "GraphQL API is running. Use POST to query.", 200
    
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'errors': [{'message': 'No query provided'}]}), 400
    
    query = data.get('query')
    variables = data.get('variables')
    validation_error = _validate_graphql_query(query)
    if validation_error:
        return validation_error
    
    result = schema.execute(query, variable_values=variables)
    
    response_data = {}
    if result.data:
        response_data['data'] = result.data
    if result.errors:
        for error in result.errors:
            logger.warning("GraphQL execution error", exc_info=error)
        response_data['errors'] = [{
            'code': 'GRAPHQL_EXECUTION_FAILED',
            'message': 'GraphQL execution failed',
        }]
        
    return jsonify(response_data)


# ============ Blueprint Registration ============

graphql_bp = Blueprint('graphql', __name__)


@graphql_bp.before_request
@api_login_required
def require_graphql_authentication():
    """Require a server-authenticated principal for GraphQL operations."""
    return None

@graphql_bp.route('/graphql', methods=['GET', 'POST'])
def handle_graphql():
    return graphql_view()


def register_graphql(app):
    """Register GraphQL endpoint with Flask app."""
    app.register_blueprint(graphql_bp)
    logger.info("GraphQL API registered at /graphql")
