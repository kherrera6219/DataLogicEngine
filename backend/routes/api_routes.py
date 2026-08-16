"""
API Routes Blueprint

Handles all API endpoints defined in routes.py (not backend blueprint APIs).
"""

import datetime
from datetime import UTC
import logging
import uuid
import asyncio
import concurrent.futures

from flask import Blueprint, request, jsonify, g
from flask_login import current_user
from sqlalchemy import text, select

from extensions import db
from models import SimulationSession
from models import (
    Domain,
    Edge,
    IngestionChunk,
    IngestionFile,
    IngestionJob,
    Node,
    PillarLevel,
    Sector,
)
from backend.auth.api_decorators import api_login_required
from backend.product_version import PRODUCT_VERSION
from backend.utils.error_normalization import normalize_public_error_message
from backend.utils.responses import error_response, internal_error
from backend.schemas.api_request_schemas import QueryRequest, SimulationRunRequest
from backend.utils.flask_request_validation import get_validated_payload, validate_json_payload

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


def _get_authenticated_user():
    auth_user = getattr(g, "auth_user", None)
    if auth_user is not None:
        return auth_user
    if getattr(current_user, "is_authenticated", False):
        return current_user
    return None


def _run_async(coro):
    try:
        asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        return asyncio.run(coro)


@api_bp.route('/health')
def api_health():
    """API health check endpoint."""
    try:
        db.session.execute(select(text('1')))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    return jsonify({
        "status": "ok" if db_status == "healthy" else "degraded",
        "version": PRODUCT_VERSION,
        "timestamp": datetime.datetime.now(UTC).isoformat(),
        "components": {
            "api": "healthy",
            "database": db_status
        }
    })


@api_bp.route('/graph')
@api_login_required
def api_graph():
    """API endpoint to get graph data for visualization."""
    try:
        axis = request.args.get('axis', type=int)
        node_type = request.args.get('nodeType')
        root_uid = str(request.args.get('root') or '').strip()
        depth = min(max(request.args.get('depth', 1, type=int) or 1, 0), 3)
        limit = min(max(request.args.get('limit', 100, type=int) or 100, 1), 500)

        from backend.storage import get_uskd_memory_graph

        memory_graph = get_uskd_memory_graph()
        if memory_graph.graph.number_of_nodes() > 0:
            scoped_node_ids = None
            if root_uid:
                neighborhood = memory_graph.neighborhood(root_uid, depth=depth)
                scoped_node_ids = {
                    str(node.get("uid"))
                    for node in neighborhood.get("nodes", [])
                    if node.get("uid") is not None
                }
            pillar_by_node = {}
            for source, target, edge_attrs in memory_graph.graph.edges(data=True):
                source_attrs = memory_graph.graph.nodes[source]
                source_data = source_attrs.get("data") if isinstance(source_attrs.get("data"), dict) else {}
                edge_data = edge_attrs.get("data") if isinstance(edge_attrs.get("data"), dict) else {}
                source_kind = str(source_attrs.get("kind") or source_data.get("node_type") or "")
                relationship = str(
                    edge_attrs.get("relationship_type")
                    or edge_data.get("edge_type")
                    or ""
                )
                if source_kind == "pillar" and relationship == "HAS_KNOWLEDGE_NODE":
                    pillar_by_node[str(target)] = (
                        source_attrs.get("name")
                        or source_attrs.get("title")
                        or source_data.get("name")
                        or str(source)
                    )

            selected_nodes = []
            selected_ids = set()
            for uid, attrs in memory_graph.graph.nodes(data=True):
                data = attrs.get("data") if isinstance(attrs.get("data"), dict) else {}
                axis_number = attrs.get("axis_number") or data.get("axis_number")
                kind = str(attrs.get("kind") or data.get("node_type") or "knowledge_node")
                if axis and axis_number not in (None, axis):
                    continue
                if node_type and kind.lower() != node_type.lower():
                    continue
                node_id = str(uid)
                if scoped_node_ids is not None and node_id not in scoped_node_ids:
                    continue
                label = attrs.get("name") or attrs.get("title") or data.get("name") or data.get("title") or node_id
                selected_ids.add(node_id)
                selected_nodes.append({
                    "id": node_id,
                    "label": label,
                    "axis_number": axis_number,
                    "node_type": kind,
                    "pillar": pillar_by_node.get(node_id) or (label if kind == "pillar" else None),
                    "description": data.get("description") or data.get("content"),
                    "size": data.get("size", 8),
                    "value": data.get("value", 1),
                    "attributes": data,
                })
                if len(selected_nodes) >= limit:
                    break

            ingestion_node_ids = [
                node["id"] for node in selected_nodes if str(node["id"]).startswith("ki_")
            ]
            if ingestion_node_ids:
                latest_chunks: dict[str, IngestionChunk] = {}
                for chunk in IngestionChunk.query.filter(
                    IngestionChunk.node_uid.in_(ingestion_node_ids)
                ).order_by(IngestionChunk.created_at.desc()):
                    latest_chunks.setdefault(chunk.node_uid, chunk)
                for node in selected_nodes:
                    chunk = latest_chunks.get(node["id"])
                    if chunk is None:
                        continue
                    source_file = db.session.get(IngestionFile, chunk.file_id)
                    job = db.session.get(IngestionJob, chunk.job_id)
                    if source_file is None or job is None:
                        continue
                    node["attributes"] = {
                        **dict(node.get("attributes") or {}),
                        "ingestion_id": str(job.id),
                        "source_path": source_file.relative_path,
                        "document_uid": source_file.document_uid,
                        "source_revision": chunk.source_revision,
                        "source_state": source_file.status,
                        "parser_state": (source_file.parser_result or {}).get("status"),
                        "defense_state": (source_file.defense_result or {}).get("disposition"),
                        "defense_policy": (source_file.defense_result or {}).get("policy_version"),
                        "object_state": source_file.object_status,
                        "normalized_object_state": source_file.normalized_object_status,
                        "vector_state": chunk.materialization_state,
                        "graph_state": chunk.materialization_state,
                        "embedding_revision": source_file.embedding_revision,
                        "last_retrieved_at": (
                            source_file.last_retrieved_at.isoformat()
                            if source_file.last_retrieved_at
                            else None
                        ),
                        "last_retrieval_trace_id": source_file.last_retrieval_trace_id,
                    }

            selected_edges = []
            for source, target, attrs in memory_graph.graph.edges(data=True):
                source_id = str(source)
                target_id = str(target)
                if source_id not in selected_ids or target_id not in selected_ids:
                    continue
                data = attrs.get("data") if isinstance(attrs.get("data"), dict) else {}
                selected_edges.append({
                    "source": source_id,
                    "target": target_id,
                    "label": attrs.get("relationship_type") or data.get("edge_type") or "RELATED_TO",
                    "value": attrs.get("weight") or data.get("weight") or 1.0,
                    "directed": True,
                })

            return jsonify({
                "nodes": selected_nodes,
                "links": selected_edges,
                "pillars": [],
                "sectors": [],
                "domains": [],
                "source": "uskd_memory_graph",
                "stats": memory_graph.stats().to_dict(),
                "scope": {
                    "root": root_uid or None,
                    "depth": depth if root_uid else None,
                },
            })
        
        node_query = Node.query
        
        if axis:
            node_query = node_query.filter_by(axis_number=axis)
        
        if node_type:
            node_query = node_query.filter_by(node_type=node_type)
        
        nodes = node_query.limit(limit).all()
        
        node_data = []
        node_ids = []
        
        for node in nodes:
            node_ids.append(node.id)
            node_data.append({
                "id": node.id,
                "label": node.label,
                "axis_number": node.axis_number,
                "node_type": node.node_type,
                "description": node.description,
                "size": 8,
                "value": 1
            })
        
        edges = Edge.query.filter(
            Edge.source_node_id.in_(node_ids),
            Edge.target_node_id.in_(node_ids)
        ).all()
        
        edge_data = []
        
        for edge in edges:
            edge_data.append({
                "source": edge.source_node_id,
                "target": edge.target_node_id,
                "label": edge.edge_type,
                "value": edge.weight,
                "directed": True
            })
        
        pillars = PillarLevel.query.order_by(PillarLevel.pillar_id).all()
        sectors = Sector.query.order_by(Sector.sector_code).all()
        domains = Domain.query.order_by(Domain.domain_code).all()
        
        pillar_data = [{"id": p.id, "pillar_id": p.pillar_id, "name": p.name, "description": p.description} for p in pillars]
        sector_data = [{"id": s.id, "sector_code": s.sector_code, "name": s.name, "naics_mapping": s.naics_mapping} for s in sectors]
        domain_data = [{"id": d.id, "domain_code": d.domain_code, "name": d.name, "description": d.description} for d in domains]
        
        graph_data = {
            "nodes": node_data,
            "links": edge_data,
            "pillars": pillar_data,
            "sectors": sector_data,
            "domains": domain_data,
            "source": "sql_fallback",
        }
        
        return jsonify(graph_data)
    
    except Exception as e:
        logger.error(f"Error getting graph data: {str(e)}")
        return internal_error()


@api_bp.route('/query', methods=['POST'])
@api_login_required
@validate_json_payload(QueryRequest)
def api_query():
    """API endpoint to process a knowledge query."""
    try:
        payload = get_validated_payload(QueryRequest)
        if payload is None:
            return internal_error()

        user = _get_authenticated_user()
        if user is None:
            return error_response("Authentication required", 401)

        query = payload.query
        confidence_threshold = payload.confidenceThreshold
        max_layer = payload.maxLayer
        
        simulation = SimulationSession()
        simulation.session_id = str(uuid.uuid4())
        simulation.user_id = user.id
        simulation.parameters = {
            "query": query,
            "confidenceThreshold": confidence_threshold,
            "maxLayer": max_layer
        }
        simulation.status = "running"
        simulation.current_step = 0
        simulation.total_steps = max_layer
        simulation.started_at = datetime.datetime.now(UTC)
        db.session.add(simulation)
        db.session.commit()

        from backend.governed_execution import GovernedRequest
        from backend.llm_gateway.gateway import get_gateway

        gateway_request = GovernedRequest(
            messages=[{"role": "user", "content": query}],
            mode="standard",
            user_id=user.id,
            session_id=simulation.session_id,
            metadata={
                "source": "api_v1_query",
                "confidence_threshold": confidence_threshold,
                "max_layer": max_layer,
            },
            source="compatible_query_facade",
            principal_kind="desktop",
            principal_id=str(user.id),
        )
        response = _run_async(get_gateway().process(gateway_request))
        if not response or not getattr(response, "ok", True):
            simulation.status = "failed"
            simulation.completed_at = datetime.datetime.now(UTC)
            simulation.results = {
                "error": getattr(response, "error", "Gateway failed to generate a response") if response else "No gateway response",
                "run_id": getattr(response, "run_id", None) if response else None,
                "provider_used": getattr(response, "provider_used", None) if response else None,
                "model_used": getattr(response, "model_used", None) if response else None,
            }
            db.session.commit()
            return error_response(
                normalize_public_error_message(
                    getattr(response, "error", None) if response else None,
                    "Query service unavailable",
                ),
                503,
                error_code="QUERY_UNAVAILABLE",
            )

        confidence = response.confidence if isinstance(response.confidence, (int, float)) else None
        active_layer = len(response.layers) if response.layers else 1
        simulation.status = "completed"
        simulation.current_step = active_layer
        simulation.completed_at = datetime.datetime.now(UTC)
        simulation.results = {
            "response": response.content,
            "confidenceScore": confidence,
            "activeLayer": active_layer,
            "providerUsed": response.provider_used,
            "modelUsed": response.model_used,
            "runId": response.run_id,
            "warnings": response.warnings,
        }
        db.session.commit()
        
        return jsonify({
            "query": query,
            "response": response.content,
            "confidenceScore": confidence,
            "activeLayer": active_layer,
            "simulationId": simulation.session_id
        })
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return internal_error()


@api_bp.route('/simulation/run', methods=['POST'])
@api_login_required
@validate_json_payload(SimulationRunRequest)
def api_run_simulation():
    """API endpoint to run a simulation."""
    try:
        payload = get_validated_payload(SimulationRunRequest)
        if payload is None:
            return internal_error()

        user = _get_authenticated_user()
        if user is None:
            return error_response("Authentication required", 401)

        query = payload.query
        confidence_threshold = payload.confidenceThreshold
        max_layer = payload.maxLayer
        refinement_steps = payload.refinementSteps
        
        simulation = SimulationSession()
        simulation.session_id = str(uuid.uuid4())
        simulation.name = payload.name or f"Simulation {datetime.datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"
        simulation.user_id = user.id
        simulation.parameters = {
            "query": query,
            "confidenceThreshold": confidence_threshold,
            "maxLayer": max_layer,
            "refinementSteps": refinement_steps
        }
        simulation.status = "running"
        simulation.current_step = 0
        simulation.total_steps = refinement_steps
        simulation.started_at = datetime.datetime.now(UTC)
        
        db.session.add(simulation)
        db.session.commit()
        
        return jsonify({
            "simulationId": simulation.session_id,
            "status": "running",
            "message": "Simulation started successfully"
        })
    
    except Exception as e:
        logger.error(f"Error starting simulation: {str(e)}", exc_info=True)
        return internal_error()
