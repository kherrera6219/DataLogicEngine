"""
MCP API Endpoints

Provides REST API endpoints for managing MCP servers, clients,
resources, tools, and prompts.
"""

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import UTC, datetime

from flask import Blueprint, current_app, g, has_app_context, jsonify, request

from backend.auth.api_decorators import (
    api_admin_required,
    api_login_required,
    api_session_login_required,
    get_authenticated_principal,
)
from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
    ExtendedSubsystemError,
)
from backend.governed_execution.knowledge_lifecycle import KnowledgeLifecycleError
from backend.mcp_server.connector_metrics import (
    infer_connector_id,
    record_connector_execution,
)
from backend.mcp_server.credential_store import (
    protect_connector_credentials,
    resolve_connector_credentials,
)
from backend.mcp_server.live_state import MCPLiveStateUnavailable, RedisMCPLiveState
from backend.mcp_server.policy import (
    MCPPolicyError,
    govern_connector_result,
    validate_stdio_definition,
)
from backend.mcp_server.router import MCPRouter
from backend.mcp_server.scope_enforcement import (
    ScopeEnforcementError,
    enforce_scopes,
    normalize_scopes,
    parse_execution_context,
)
from core.mcp import MCPManager
from extensions import db
from models import (
    AuditLog,
    MCPConsentGrant,
    MCPExecutionRecord,
    MCPLifecycleEvent,
    MCPPrompt,
    MCPResource,
    MCPTool,
)
from models import (
    MCPServer as MCPServerModel,
)

logger = logging.getLogger(__name__)

def get_async_loop():
    """Create an operation-local event loop; callers must close it."""
    return asyncio.new_event_loop()


def run_async(coro):
    """Run an async coroutine safely without blocking Flask routes."""
    loop = get_async_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def get_mcp_router() -> MCPRouter:
    """Return the JSON-RPC router owned by the active application."""
    router = current_app.extensions.get("dle_mcp_router")
    if router is None:
        router = MCPRouter()
        current_app.extensions["dle_mcp_router"] = router
    return router


# Create blueprint
mcp_bp = Blueprint('mcp', __name__)

# Global MCP manager instance
mcp_manager = None


def init_mcp_manager(app_orchestrator=None):
    """Initialize the MCP manager"""
    if has_app_context():
        manager = MCPManager(app_orchestrator=app_orchestrator)
        current_app.extensions["dle_mcp_manager"] = manager
        logger.info("MCP Manager initialized")
        return manager
    global mcp_manager
    mcp_manager = MCPManager(app_orchestrator=app_orchestrator)
    logger.info("MCP Manager initialized")
    return mcp_manager


def get_mcp_manager():
    """Return the MCP manager owned by the active application."""
    if has_app_context():
        manager = current_app.extensions.get("dle_mcp_manager")
        if manager is None:
            manager = MCPManager()
            current_app.extensions["dle_mcp_manager"] = manager
        return manager
    return get_fallback_mcp_manager()


def get_fallback_mcp_manager():
    """Compatibility accessor for explicit non-Flask tooling."""
    global mcp_manager
    if mcp_manager is None:
        mcp_manager = MCPManager()
    return mcp_manager


def _mcp_error(message, status=500):
    return jsonify({'success': False, 'error': message}), status


def _principal_id() -> str:
    principal = get_authenticated_principal()
    value = str(getattr(principal, "id", "") or "").strip()
    if not value:
        raise MCPPolicyError("MCP_PRINCIPAL_REQUIRED", "Authenticated principal is required")
    return value


def _live_state() -> RedisMCPLiveState | None:
    """Return the content-free Redis mirror when the data plane requires it."""
    required = bool(
        current_app.config.get("DLE_USE_REDIS")
        or current_app.config.get("DLE_PRODUCTION_MODE")
    )
    if not required:
        return None
    coordinator = current_app.extensions.get("dle_mcp_live_state")
    if coordinator is None:
        redis_url = str(
            current_app.config.get("REDIS_URL")
            or os.environ.get("REDIS_URL")
            or ""
        ).strip()
        if not redis_url:
            raise MCPPolicyError(
                "MCP_REDIS_LIVE_STATE_UNAVAILABLE",
                "Required MCP live state is unavailable",
            )
        try:
            coordinator = RedisMCPLiveState.from_url(redis_url)
        except MCPLiveStateUnavailable as exc:
            raise MCPPolicyError(
                "MCP_REDIS_LIVE_STATE_UNAVAILABLE",
                "Required MCP live state is unavailable",
            ) from exc
        current_app.extensions["dle_mcp_live_state"] = coordinator
    return coordinator


def _publish_execution_state(server: MCPServerModel, execution: MCPExecutionRecord) -> None:
    try:
        coordinator = _live_state()
        if coordinator is not None:
            coordinator.record_execution(server.server_id, execution.execution_id, execution.status)
    except (MCPPolicyError, MCPLiveStateUnavailable):
        logger.warning(
            "MCP execution live-state publication failed after the authoritative commit: %s",
            execution.execution_id,
        )


def _publish_lifecycle_state(server: MCPServerModel, event: MCPLifecycleEvent) -> None:
    try:
        coordinator = _live_state()
        if coordinator is not None:
            coordinator.record_lifecycle(server.server_id, event.event_type, event.status)
    except (MCPPolicyError, MCPLiveStateUnavailable):
        logger.warning(
            "MCP lifecycle live-state publication failed after the authoritative commit: %s",
            event.event_type,
        )


def _lifecycle(
    server: MCPServerModel,
    event_type: str,
    status: str,
    *,
    details: dict | None = None,
) -> MCPLifecycleEvent:
    event = MCPLifecycleEvent(
        server_id=server.id,
        principal_id=_principal_id(),
        event_type=event_type,
        status=status,
        details=details or {},
    )
    db.session.add(event)
    return event


def _active_consent(server: MCPServerModel) -> MCPConsentGrant | None:
    return MCPConsentGrant.query.filter_by(
        server_id=server.id,
        command_fingerprint=server.command_fingerprint,
        status="approved",
    ).order_by(MCPConsentGrant.approved_at.desc()).first()


def _canonical_sha256(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _apply_mcp_result_records(
    *,
    execution: MCPExecutionRecord,
    tool_name: str,
    governed_result: dict,
    result_validation,
    result_governance: dict,
    coordinator: ExtendedSubsystemCoordinator,
) -> dict:
    """Apply content-free log/audit records and bind owning-service receipts."""
    existing = dict(execution.ka_lifecycle or {}).get("result_records")
    if isinstance(existing, dict) and existing.get("status") == "applied":
        return existing

    outputs = coordinator.execution_outputs(result_validation)
    logging_result = outputs.get("KA-096", {})
    audit_result = outputs.get("KA-097", {})
    audit_proposal = audit_result.get("effect_proposal")
    if logging_result.get("logs_processed") != 1:
        raise ExtendedSubsystemError(
            "MCP result logging record was not validated"
        )
    if not isinstance(audit_proposal, dict):
        raise ExtendedSubsystemError("MCP result audit proposal is missing")
    if audit_proposal.get("kind") != "append_audit_record":
        raise ExtendedSubsystemError("MCP result audit proposal is invalid")
    if audit_proposal.get("status") != "proposed":
        raise ExtendedSubsystemError("MCP result audit proposal is not proposed")

    record_payload = {
        "schema_version": "dle.mcp-result-record.v1",
        "event": "mcp_tool_result",
        "execution_id": execution.execution_id,
        "principal_id": execution.principal_id,
        "tool": tool_name,
        "result_sha256": governed_result.get("sha256"),
        "result_trust": governed_result.get("trust"),
        "prompt_injection_risk": bool(
            governed_result.get("prompt_injection_risk")
        ),
        "release_allowed": bool(result_governance.get("release_allowed")),
        "audit_id": audit_result.get("audit_id"),
        "audit_content_sha256": audit_result.get("content_sha256"),
    }
    logger.info(
        "MCP result governance record applied",
        extra={
            "event": record_payload["event"],
            "mcp_execution_id": execution.execution_id,
            "mcp_tool": tool_name,
            "result_sha256": record_payload["result_sha256"],
            "result_trust": record_payload["result_trust"],
            "prompt_injection_risk": record_payload[
                "prompt_injection_risk"
            ],
            "release_allowed": record_payload["release_allowed"],
            "audit_id": record_payload["audit_id"],
        },
    )
    logging_receipt = coordinator.bind_effect_receipt(
        service="StructuredLoggingService",
        operation="append_mcp_result_log",
        resource_id=execution.execution_id,
        request_payload={
            "ka_id": "KA-096",
            "logs_processed": logging_result.get("logs_processed"),
            "backend": logging_result.get("backend"),
        },
        result_payload=record_payload,
        idempotency_key=f"mcp-result-log:{execution.execution_id}",
        ka_execution=result_validation,
        proposal_ids=["KA-096"],
    )

    principal_text = str(execution.principal_id or "")
    audit_row = AuditLog(
        user_id=(int(principal_text) if principal_text.isdecimal() else None),
        windows_sid=(
            principal_text if principal_text.startswith("S-") else None
        ),
        action="mcp_tool_result",
        details=json.dumps(record_payload, sort_keys=True, separators=(",", ":")),
    )
    db.session.add(audit_row)
    db.session.flush()
    audit_receipt = coordinator.bind_effect_receipt(
        service="AppAuditService",
        operation="append_audit_record",
        resource_id=str(audit_row.id),
        request_payload=audit_proposal,
        result_payload={
            "audit_log_id": audit_row.id,
            "audit_id": audit_result.get("audit_id"),
            "content_sha256": audit_result.get("content_sha256"),
            "action": audit_row.action,
        },
        idempotency_key=str(audit_result.get("audit_id") or ""),
        ka_execution=result_validation,
        proposal_ids=["KA-097"],
    )
    return {
        "schema_version": "dle.mcp-result-record-application.v1",
        "status": "applied",
        "logging_receipt": logging_receipt.to_dict(),
        "audit_receipt": audit_receipt.to_dict(),
        "audit_log_id": audit_row.id,
    }


def _apply_mcp_recovery_record(
    *,
    execution: MCPExecutionRecord,
    recovery_execution,
    recovery_plan: dict,
    coordinator: ExtendedSubsystemCoordinator,
) -> dict:
    """Bind the durable recovery-plan record without applying proposed steps."""
    if recovery_plan.get("status") != "planned":
        raise ExtendedSubsystemError("MCP recovery record requires a plan")
    if int(recovery_plan.get("actions_applied") or 0) != 0:
        raise ExtendedSubsystemError(
            "MCP recovery KAs cannot claim operational actions"
        )
    receipt = coordinator.bind_effect_receipt(
        service="MCPRecoveryLedger",
        operation="record_recovery_plan",
        resource_id=execution.execution_id,
        request_payload=recovery_plan,
        result_payload={
            "execution_id": execution.execution_id,
            "record_status": "persisted_with_execution",
            "incident_id": recovery_plan.get("incident_id"),
            "actions_applied": 0,
        },
        idempotency_key=f"mcp-recovery:{execution.execution_id}",
        ka_execution=recovery_execution,
        proposal_ids=["KA-184"],
    )
    return {
        **recovery_plan,
        "record_status": "persisted_with_execution",
        "record_receipt": receipt.to_dict(),
    }


def _policy_error(exc: MCPPolicyError, *, status: int = 400):
    return jsonify({
        "success": False,
        "error": exc.public_message,
        "code": exc.code,
    }), status


def _required_scope_for_operation(server: MCPServerModel, operation_name: str) -> list[str]:
    action = "write" if _tool_uses_write_scope(operation_name) else "read"
    return ["mcp:execute", f"connector:{server.name.lower()}:{action}"]


def _sync_discovery(server: MCPServerModel, discovery: dict) -> None:
    """Replace materialized discovery rows from one live handshake."""
    MCPResource.query.filter_by(server_id=server.id).delete(synchronize_session=False)
    MCPTool.query.filter_by(server_id=server.id).delete(synchronize_session=False)
    MCPPrompt.query.filter_by(server_id=server.id).delete(synchronize_session=False)

    for raw in discovery.get("resources", []):
        if not isinstance(raw, dict) or not raw.get("uri") or not raw.get("name"):
            continue
        db.session.add(MCPResource(
            server_id=server.id,
            uri=str(raw["uri"])[:256],
            name=str(raw["name"])[:128],
            description=str(raw.get("description") or "")[:2_000],
            mime_type=str(raw.get("mimeType") or "application/octet-stream")[:64],
            resource_metadata={
                "required_scopes": _required_scope_for_operation(server, "read_resource"),
                "source": "live_discovery",
            },
        ))
    for raw in discovery.get("tools", []):
        if not isinstance(raw, dict) or not raw.get("name"):
            continue
        name = str(raw["name"])[:128]
        db.session.add(MCPTool(
            server_id=server.id,
            name=name,
            description=str(raw.get("description") or "MCP tool")[:2_000],
            input_schema=raw.get("inputSchema") if isinstance(raw.get("inputSchema"), dict) else {"type": "object"},
            tool_metadata={
                "required_scopes": _required_scope_for_operation(server, name),
                "source": "live_discovery",
            },
        ))
    for raw in discovery.get("prompts", []):
        if not isinstance(raw, dict) or not raw.get("name"):
            continue
        db.session.add(MCPPrompt(
            server_id=server.id,
            name=str(raw["name"])[:128],
            description=str(raw.get("description") or "MCP prompt")[:2_000],
            arguments=raw.get("arguments") if isinstance(raw.get("arguments"), list) else [],
            prompt_metadata={
                "required_scopes": _required_scope_for_operation(server, "read_prompt"),
                "source": "live_discovery",
            },
        ))


def _tool_uses_write_scope(tool_name: str) -> bool:
    lowered = (tool_name or "").strip().lower()
    write_markers = ("create", "update", "delete", "write", "import", "sync", "patch")
    return any(marker in lowered for marker in write_markers)


def _required_tool_scopes(tool: MCPTool) -> list[str]:
    metadata = tool.tool_metadata if isinstance(tool.tool_metadata, dict) else {}
    explicit_scopes = normalize_scopes(metadata.get("required_scopes"))
    if explicit_scopes:
        return sorted(explicit_scopes)

    connector = infer_connector_id(tool.name)
    if connector is None:
        return []
    action = "write" if _tool_uses_write_scope(tool.name) else "read"
    return ["mcp:execute", f"connector:{connector}:{action}"]


def _build_tool_execution_context() -> dict:
    user = get_authenticated_principal()
    tenant_id = getattr(user, "tenant_id", None)

    api_key = getattr(g, "external_api_key", None)
    if api_key is not None:
        permissions = api_key.permissions if isinstance(api_key.permissions, dict) else {}
        scopes = normalize_scopes(permissions.get("connector_scopes"))
        if permissions.get("mcp_execute"):
            scopes.add("mcp:execute")
        is_admin = bool(permissions.get("admin"))
        roles = {"external-client"}
        if is_admin:
            scopes.add("*")
            roles.add("admin")
    else:
        # The authenticated Windows owner receives the local desktop authority.
        roles = {"owner"}
        scopes = {"mcp:execute", "connector:*:read", "connector:*:write", "*"}
        is_admin = True

    return {
        "user_id": str(getattr(user, "id", "")),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "roles": sorted(roles),
        "scopes": sorted(scopes),
        "is_admin": is_admin,
    }


_CALLER_IDENTITY_CONTEXT_FIELDS = {
    "user_id", "tenant_id", "role", "roles", "scope", "scopes", "is_admin"
}


def _caller_supplied_identity_context(payload: dict) -> bool:
    params = payload.get("params") if isinstance(payload, dict) else None
    context = params.get("context") if isinstance(params, dict) else None
    return isinstance(context, dict) and bool(_CALLER_IDENTITY_CONTEXT_FIELDS & context.keys())


def _without_caller_context(payload: dict) -> dict:
    sanitized = dict(payload)
    params = payload.get("params")
    if isinstance(params, dict):
        sanitized_params = dict(params)
        sanitized_params.pop("context", None)
        sanitized["params"] = sanitized_params
    return sanitized


@mcp_bp.route('/rpc', methods=['POST'])
@api_session_login_required
def mcp_rpc():
    """Handle active MCP JSON-RPC requests, including sampling and subscriptions."""
    try:
        payload = request.get_json() or {}
        if _caller_supplied_identity_context(payload):
            return jsonify({
                "jsonrpc": "2.0",
                "id": payload.get("id"),
                "error": {
                    "code": "MCP_CALLER_CONTEXT_REJECTED",
                    "message": "Caller-supplied identity context is not allowed",
                },
            }), 400
        response = run_async(get_mcp_router().handle_message(
            _without_caller_context(payload),
            execution_context=_build_tool_execution_context(),
        ))
        return jsonify(response), 200
    except Exception as exc:
        logger.error("MCP RPC failed: %s", exc)
        return jsonify({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": "MCP RPC failed"}}), 500


@mcp_bp.route('/subscriptions/stream/<client_id>', methods=['GET'])
@api_session_login_required
def mcp_subscription_stream(client_id):
    """Reject the retired caller-selected subscription stream."""
    del client_id
    return jsonify({
        'success': False,
        'error': 'MCP subscriptions are not supported by the production transport set',
        'code': 'MCP_SUBSCRIPTIONS_UNSUPPORTED',
    }), 410


# Server Management Endpoints

@mcp_bp.route('/servers', methods=['GET'])
@api_session_login_required
def list_servers():
    """List all MCP servers"""
    try:
        # Get from database
        db_servers = MCPServerModel.query.all()
        servers_data = [server.to_dict() for server in db_servers]

        # Get runtime servers
        manager = get_mcp_manager()
        runtime_servers = manager.list_servers()

        return jsonify({
            'success': True,
            'servers': servers_data,
            'runtime_servers': runtime_servers,
            'count': len(servers_data)
        }), 200

    except Exception:
        logger.exception("Error listing servers")
        return _mcp_error('MCP servers are unavailable', 500)


@mcp_bp.route('/servers', methods=['POST'])
@api_admin_required
def create_server():
    """Register a validated stdio connector without executing it."""
    try:
        data = request.get_json(silent=True) or {}

        name = str(data.get('name') or '').strip()
        version = data.get('version', '1.0.0')
        description = data.get('description', '')

        if not name:
            return jsonify({
                'success': False,
                'error': 'Server name is required'
            }), 400

        if MCPServerModel.query.filter_by(name=name).first():
            return jsonify({
                'success': False,
                'error': 'A connector with this name already exists',
                'code': 'MCP_NAME_CONFLICT',
            }), 409

        raw_definition = data.get('config') if isinstance(data.get('config'), dict) else data
        validated = validate_stdio_definition(name, raw_definition)
        definition = validated['definition']
        credential_blobs = protect_connector_credentials(
            definition.get('credential_env', {}),
            data.get('credentials'),
        )

        db_server = MCPServerModel(
            server_id=str(uuid.uuid4()),
            name=name,
            version=version,
            description=description,
            status='inactive',
            protocol_version=definition['protocol_version'],
            transport=definition['transport'],
            enabled=False,
            consent_state='pending',
            requested_scopes=definition['requested_scopes'],
            approved_scopes=[],
            command_fingerprint=validated['fingerprint'],
            containment_status='windows_job_object_pending_installed_qualification',
            health_status='not_started',
            supports_resources=False,
            supports_tools=False,
            supports_prompts=False,
            supports_logging=False,
            config=definition,
            credential_blobs=credential_blobs,
            server_metadata=data.get('metadata', {}),
        )
        db.session.add(db_server)
        db.session.flush()
        event = _lifecycle(
            db_server,
            'registered',
            'pending_consent',
            details={
                'command_fingerprint': validated['fingerprint'],
                'requested_scopes': definition['requested_scopes'],
            },
        )
        db.session.commit()
        _publish_lifecycle_state(db_server, event)

        logger.info("Registered MCP connector pending consent: %s", name)

        return jsonify({
            'success': True,
            'server': db_server.to_dict()
        }), 201

    except MCPPolicyError as exc:
        db.session.rollback()
        return _policy_error(exc)
    except Exception:
        logger.exception("Error creating server")
        db.session.rollback()
        return _mcp_error('MCP server could not be created', 500)


@mcp_bp.route('/servers/<server_id>', methods=['GET'])
@api_session_login_required
def get_server(server_id):
    """Get a specific MCP server"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()

        if not db_server:
            return jsonify({
                'success': False,
                'error': 'Server not found'
            }), 404

        # Get runtime server info
        manager = get_mcp_manager()
        runtime_server = manager.get_server(server_id)

        response_data = db_server.to_dict()
        if runtime_server:
            response_data['runtime_info'] = runtime_server.get_server_info()

        return jsonify({
            'success': True,
            'server': response_data
        }), 200

    except Exception:
        logger.exception("Error getting server")
        return _mcp_error('MCP server details are unavailable', 500)


@mcp_bp.route('/servers/<server_id>/consent', methods=['POST'])
@api_admin_required
def approve_server_consent(server_id):
    """Approve the exact visible command fingerprint and granular scopes."""
    try:
        server = MCPServerModel.query.filter_by(server_id=server_id).first()
        if not server:
            return _mcp_error('Server not found', 404)
        data = request.get_json(silent=True) or {}
        fingerprint = str(data.get('command_fingerprint') or '')
        if not fingerprint or fingerprint != server.command_fingerprint:
            return jsonify({
                'success': False,
                'error': 'The connector command changed; review the current command before approval',
                'code': 'MCP_CONSENT_FINGERPRINT_MISMATCH',
            }), 409
        approved_scopes = sorted(set(str(scope).strip().lower() for scope in data.get('approved_scopes', [])))
        requested_scopes = set(str(scope).lower() for scope in (server.requested_scopes or []))
        if not approved_scopes or not set(approved_scopes) <= requested_scopes:
            return jsonify({
                'success': False,
                'error': 'Approved scopes must be a non-empty subset of requested scopes',
                'code': 'MCP_CONSENT_SCOPE_INVALID',
            }), 400

        now = datetime.now(UTC)
        for grant in MCPConsentGrant.query.filter_by(server_id=server.id, status='approved').all():
            grant.status = 'superseded'
            grant.revoked_at = now
        grant = MCPConsentGrant(
            server_id=server.id,
            principal_id=_principal_id(),
            command_fingerprint=fingerprint,
            requested_scopes=sorted(requested_scopes),
            approved_scopes=approved_scopes,
            status='approved',
            approved_at=now,
        )
        db.session.add(grant)
        server.consent_state = 'approved'
        server.approved_scopes = approved_scopes
        event = _lifecycle(
            server,
            'consent_approved',
            'approved',
            details={
                'command_fingerprint': fingerprint,
                'approved_scopes': approved_scopes,
            },
        )
        db.session.commit()
        _publish_lifecycle_state(server, event)
        return jsonify({'success': True, 'server': server.to_dict(), 'consent': grant.to_dict()}), 200
    except Exception:
        db.session.rollback()
        logger.exception('MCP consent approval failed')
        return _mcp_error('MCP consent could not be recorded', 500)


@mcp_bp.route('/servers/<server_id>/consent', methods=['DELETE'])
@api_admin_required
def revoke_server_consent(server_id):
    """Revoke connector authority and stop any active process."""
    try:
        server = MCPServerModel.query.filter_by(server_id=server_id).first()
        if not server:
            return _mcp_error('Server not found', 404)
        try:
            get_mcp_manager().stop_external_server_sync(server.server_id)
        except Exception:
            logger.exception('MCP connector stop during consent revoke failed')
        now = datetime.now(UTC)
        for grant in MCPConsentGrant.query.filter_by(server_id=server.id, status='approved').all():
            grant.status = 'revoked'
            grant.revoked_at = now
        server.consent_state = 'revoked'
        server.approved_scopes = []
        server.enabled = False
        server.status = 'inactive'
        server.health_status = 'stopped'
        event = _lifecycle(server, 'consent_revoked', 'revoked')
        db.session.commit()
        _publish_lifecycle_state(server, event)
        return jsonify({'success': True, 'server': server.to_dict()}), 200
    except Exception:
        db.session.rollback()
        logger.exception('MCP consent revocation failed')
        return _mcp_error('MCP consent could not be revoked', 500)


@mcp_bp.route('/servers/<server_id>/lifecycle', methods=['GET'])
@api_session_login_required
def list_server_lifecycle(server_id):
    server = MCPServerModel.query.filter_by(server_id=server_id).first()
    if not server:
        return _mcp_error('Server not found', 404)
    events = MCPLifecycleEvent.query.filter_by(server_id=server.id).order_by(
        MCPLifecycleEvent.created_at.desc()
    ).limit(200).all()
    return jsonify({'success': True, 'events': [event.to_dict() for event in events]}), 200


@mcp_bp.route('/servers/<server_id>/executions', methods=['GET'])
@api_session_login_required
def list_server_executions(server_id):
    server = MCPServerModel.query.filter_by(server_id=server_id).first()
    if not server:
        return _mcp_error('Server not found', 404)
    records = MCPExecutionRecord.query.filter_by(server_id=server.id).order_by(
        MCPExecutionRecord.started_at.desc()
    ).limit(200).all()
    return jsonify({'success': True, 'executions': [record.to_dict() for record in records]}), 200


@mcp_bp.route('/servers/<server_id>/executions/<execution_id>/cancel', methods=['POST'])
@api_login_required
def cancel_server_execution(server_id, execution_id):
    """Cancel one owned in-flight external connector operation."""
    server = MCPServerModel.query.filter_by(server_id=server_id).first()
    if not server:
        return _mcp_error('Server not found', 404)
    execution = MCPExecutionRecord.query.filter_by(
        execution_id=execution_id,
        server_id=server.id,
    ).first()
    if not execution or execution.principal_id != _principal_id():
        return _mcp_error('Execution not found', 404)
    if execution.status != 'running':
        return jsonify({
            'success': False,
            'error': 'Only a running execution can be cancelled',
            'code': 'MCP_EXECUTION_NOT_RUNNING',
        }), 409
    if not get_mcp_manager().cancel_external_operation(execution.execution_id):
        return jsonify({
            'success': False,
            'error': 'The execution already finished or cannot be cancelled',
            'code': 'MCP_EXECUTION_CANCEL_RACE',
        }), 409

    execution.status = 'cancelled'
    execution.error_code = 'MCP_EXECUTION_CANCELLED'
    execution.error_message = 'MCP execution was cancelled by the owner'
    execution.completed_at = datetime.now(UTC)
    server.total_requests += 1
    server.failed_requests += 1
    if execution.tool_id:
        tool = MCPTool.query.filter_by(id=execution.tool_id, server_id=server.id).first()
        if tool:
            tool.execution_count += 1
            tool.failure_count += 1
            tool.last_executed = datetime.now(UTC)
    db.session.commit()
    _publish_execution_state(server, execution)
    return jsonify({'success': True, 'execution': execution.to_dict()}), 200


@mcp_bp.route('/servers/<server_id>', methods=['DELETE'])
@api_admin_required
def delete_server(server_id):
    """Delete an MCP server"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()

        if not db_server:
            return jsonify({
                'success': False,
                'error': 'Server not found'
            }), 404

        # Remove from runtime
        manager = get_mcp_manager()
        manager.remove_server(server_id)
        if server_id in manager.external_clients:
            manager.stop_external_server_sync(server_id)

        # Delete from database
        db.session.delete(db_server)
        db.session.commit()

        logger.info(f"Deleted MCP server: {server_id}")

        return jsonify({
            'success': True,
            'message': 'Server deleted successfully'
        }), 200

    except Exception:
        logger.exception("Error deleting server")
        db.session.rollback()
        return _mcp_error('MCP server could not be deleted', 500)


# Resource Endpoints

@mcp_bp.route('/servers/<server_id>/resources', methods=['GET'])
@api_session_login_required
def list_resources(server_id):
    """List resources for a server"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()

        if not db_server:
            return jsonify({
                'success': False,
                'error': 'Server not found'
            }), 404

        resources = MCPResource.query.filter_by(server_id=db_server.id).all()
        resources_data = [resource.to_dict() for resource in resources]

        return jsonify({
            'success': True,
            'resources': resources_data,
            'count': len(resources_data)
        }), 200

    except Exception:
        logger.exception("Error listing resources")
        return _mcp_error('MCP resources are unavailable', 500)


@mcp_bp.route('/servers/<server_id>/resources/<int:resource_id>', methods=['GET'])
@api_session_login_required
def read_resource(server_id, resource_id):
    """Read a specific resource"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()
        if not db_server:
            return jsonify({'success': False, 'error': 'Server not found'}), 404
        resource = MCPResource.query.filter_by(id=resource_id, server_id=db_server.id).first()

        if not resource:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404
        consent = _active_consent(db_server)
        required_scopes = (resource.resource_metadata or {}).get('required_scopes') or _required_scope_for_operation(
            db_server, 'read_resource'
        )
        approved = set(str(scope).lower() for scope in ((consent.approved_scopes if consent else []) or []))
        connector_requirements = {
            str(scope).lower() for scope in required_scopes if str(scope).lower() != 'mcp:execute'
        }
        if consent is None or not connector_requirements <= approved:
            return jsonify({
                'success': False,
                'error': 'Connector consent does not authorize this resource',
                'code': 'MCP_CONSENT_SCOPE_DENIED',
            }), 403
        if db_server.status != 'active':
            return jsonify({
                'success': False,
                'error': 'Server is not running',
                'code': 'MCP_SERVER_NOT_RUNNING',
            }), 409

        manager = get_mcp_manager()
        server = manager.get_server(server_id)
        started = time.perf_counter()
        execution = MCPExecutionRecord(
            server_id=db_server.id,
            principal_id=_principal_id(),
            operation=f'resources/read:{resource.uri}',
            status='running',
            required_scopes=sorted(required_scopes),
            request_sha256=_canonical_sha256({'uri': resource.uri}),
        )
        db.session.add(execution)
        db.session.flush()
        db.session.commit()
        _publish_execution_state(db_server, execution)
        try:
            if server is not None:
                content = run_async(server._handle_resources_read({'uri': resource.uri}))
            elif server_id in manager.external_clients:
                timeout = float((db_server.config or {}).get('limits', {}).get('request_timeout_seconds', 30))
                content = manager.read_external_resource_sync(
                    server_id,
                    resource.uri,
                    timeout=timeout + 2,
                    operation_id=execution.execution_id,
                )
            else:
                raise MCPPolicyError('MCP_SERVER_NOT_RUNNING', 'Server is not running')
            max_bytes = int((db_server.config or {}).get('limits', {}).get('max_message_bytes', 65_536))
            governed = govern_connector_result(content, max_bytes=max_bytes)
            duration_ms = round((time.perf_counter() - started) * 1000.0)
            execution.status = 'completed'
            execution.result_sha256 = governed['sha256']
            execution.result_size_bytes = governed['size_bytes']
            execution.result_content = governed['content'] if governed['size_bytes'] <= 65_536 else None
            execution.result_trust = governed['trust']
            execution.prompt_injection_risk = governed['prompt_injection_risk']
            execution.duration_ms = duration_ms
            execution.completed_at = datetime.now(UTC)
            resource.access_count += 1
            resource.last_accessed = datetime.now(UTC)
            db_server.total_requests += 1
            db_server.successful_requests += 1
            db.session.commit()
            _publish_execution_state(db_server, execution)
            return jsonify({
                'success': True,
                'resource': resource.to_dict(),
                'execution': execution.to_dict(),
                'result': governed,
            }), 200
        except Exception as exc:
            db.session.refresh(execution)
            if execution.status == 'cancelled':
                return jsonify({
                    'success': False,
                    'error': 'MCP resource read was cancelled',
                    'code': 'MCP_EXECUTION_CANCELLED',
                    'execution_id': execution.execution_id,
                }), 409
            execution.status = 'failed'
            execution.error_code = str(getattr(exc, 'code', None) or 'MCP_RESOURCE_READ_FAILED')[:100]
            execution.error_message = 'MCP resource read failed'
            execution.duration_ms = round((time.perf_counter() - started) * 1000.0)
            execution.completed_at = datetime.now(UTC)
            db_server.failed_requests += 1
            db.session.commit()
            _publish_execution_state(db_server, execution)
            logger.error('MCP resource read failed: %s', type(exc).__name__)
            return jsonify({
                'success': False,
                'error': 'MCP resource read failed',
                'code': str(execution.error_code),
                'execution_id': execution.execution_id,
            }), 500

    except Exception:
        logger.exception("Error reading resource")
        return _mcp_error('MCP resource is unavailable', 500)


# Tool Endpoints

@mcp_bp.route('/servers/<server_id>/tools', methods=['GET'])
@api_session_login_required
def list_tools(server_id):
    """List tools for a server"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()

        if not db_server:
            return jsonify({
                'success': False,
                'error': 'Server not found'
            }), 404

        tools = MCPTool.query.filter_by(server_id=db_server.id).all()
        tools_data = [tool.to_dict() for tool in tools]

        return jsonify({
            'success': True,
            'tools': tools_data,
            'count': len(tools_data)
        }), 200

    except Exception:
        logger.exception("Error listing tools")
        return _mcp_error('MCP tools are unavailable', 500)


@mcp_bp.route('/servers/<server_id>/tools/<int:tool_id>/call', methods=['POST'])
@api_login_required
def call_tool(server_id, tool_id):
    """Call a tool"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()
        if not db_server:
            return jsonify({'success': False, 'error': 'Server not found'}), 404
        tool = MCPTool.query.filter_by(id=tool_id, server_id=db_server.id).first()

        if not tool:
            return jsonify({
                'success': False,
                'error': 'Tool not found'
            }), 404

        data = request.get_json(silent=True) or {}
        if isinstance(data.get('context'), dict) and (
            _CALLER_IDENTITY_CONTEXT_FIELDS & data['context'].keys()
        ):
            return jsonify({
                'success': False,
                'error': 'Caller-supplied identity context is not allowed',
                'code': 'MCP_CALLER_CONTEXT_REJECTED',
            }), 400
        arguments = data.get('arguments', {})
        if not isinstance(arguments, dict):
            return jsonify({
                'success': False,
                'error': 'Tool arguments must be an object',
                'code': 'MCP_ARGUMENTS_INVALID',
            }), 400
        connector_id = db_server.name.lower()

        consent = _active_consent(db_server)
        if consent is None or db_server.consent_state != 'approved':
            return jsonify({
                'success': False,
                'error': 'Connector consent is required',
                'code': 'MCP_EXPLICIT_CONSENT_REQUIRED',
            }), 409
        if db_server.status != 'active':
            return jsonify({
                'success': False,
                'error': 'Server is not running',
                'code': 'MCP_SERVER_NOT_RUNNING',
            }), 409

        execution_context_raw = _build_tool_execution_context()
        execution_context = parse_execution_context(execution_context_raw)
        required_scopes = _required_tool_scopes(tool)
        approved = set(str(scope).lower() for scope in (consent.approved_scopes or []))
        connector_requirements = {
            str(scope).lower() for scope in required_scopes if str(scope).lower() != 'mcp:execute'
        }
        if not connector_requirements <= approved:
            return jsonify({
                'success': False,
                'error': 'The tool requires scopes that were not approved',
                'code': 'MCP_CONSENT_SCOPE_DENIED',
                'required_scopes': sorted(required_scopes),
            }), 403
        try:
            enforce_scopes(
                tool_name=tool.name,
                required_scopes=required_scopes,
                context=execution_context,
                permissive_on_missing_context=False,
            )
        except ScopeEnforcementError as scope_error:
            logger.warning("MCP scope enforcement denied tool call for %s: %s", tool.name, scope_error)
            return jsonify({
                'success': False,
                'error': 'MCP scope denied',
                'code': 'MCP_SCOPE_DENIED',
                'required_scopes': sorted(required_scopes),
            }), 403

        manager = get_mcp_manager()
        server = manager.get_server(server_id)
        started = time.perf_counter()
        execution = MCPExecutionRecord(
            server_id=db_server.id,
            tool_id=tool.id,
            principal_id=_principal_id(),
            operation=f'tools/call:{tool.name}',
            status='running',
            required_scopes=sorted(required_scopes),
            request_sha256=_canonical_sha256({'name': tool.name, 'arguments': arguments}),
            trace_id=str(getattr(g, 'correlation_id', '') or '')[:36] or None,
        )
        db.session.add(execution)
        db.session.flush()
        db.session.commit()
        _publish_execution_state(db_server, execution)
        ka_phase = 'admission'
        extended = None
        try:
            extended = ExtendedSubsystemCoordinator()
            admission = extended.admit_mcp_tool(
                execution_id=execution.execution_id,
                principal_id=execution.principal_id,
                server_id=server_id,
                tool_name=tool.name,
                arguments=arguments,
                required_scopes=set(required_scopes),
                consent_approved=True,
            )
            execution.ka_lifecycle = {
                "admission": extended.lifecycle_evidence(admission)
            }
            db.session.commit()
            if server is not None:
                result = run_async(server._handle_tools_call({
                    'name': tool.name,
                    'arguments': arguments,
                    'context': execution_context_raw,
                }))
            elif server_id in manager.external_clients:
                timeout = float((db_server.config or {}).get('limits', {}).get('request_timeout_seconds', 30))
                result = manager.call_external_tool_sync(
                    server_id,
                    tool.name,
                    arguments,
                    timeout=timeout + 2,
                    operation_id=execution.execution_id,
                )
            else:
                raise MCPPolicyError('MCP_SERVER_NOT_RUNNING', 'Server is not running')

            duration_ms = (time.perf_counter() - started) * 1000.0
            max_bytes = int((db_server.config or {}).get('limits', {}).get('max_message_bytes', 65_536))
            governed = govern_connector_result(result, max_bytes=max_bytes)
            effect_receipt = extended.bind_effect_receipt(
                service="MCPConnectorService",
                operation=f"tools/call:{tool.name}",
                resource_id=execution.execution_id,
                request_payload={
                    "name": tool.name,
                    "arguments": arguments,
                },
                result_payload={
                    "sha256": governed["sha256"],
                    "size_bytes": governed["size_bytes"],
                    "trust": governed["trust"],
                },
                idempotency_key=execution.execution_id,
                ka_execution=admission,
                proposal_ids=["KA-177", "KA-179"],
            )
            execution.effect_receipt = effect_receipt.to_dict()
            ka_phase = 'result_validation'
            result_validation = extended.validate_mcp_result(
                execution_id=execution.execution_id,
                principal_id=execution.principal_id,
                tool_name=tool.name,
                governed_result=governed,
            )
            result_governance = extended.mcp_result_governance_decision(
                result_validation
            )
            result_records = _apply_mcp_result_records(
                execution=execution,
                tool_name=tool.name,
                governed_result=governed,
                result_validation=result_validation,
                result_governance=result_governance,
                coordinator=extended,
            )
            execution.ka_lifecycle = {
                **dict(execution.ka_lifecycle or {}),
                "result_validation": extended.lifecycle_evidence(
                    result_validation
                ),
                "result_governance": result_governance,
                "result_records": result_records,
            }
            db.session.commit()
            if not result_governance["release_allowed"]:
                raise ExtendedSubsystemError(
                    "MCP result release blocked: "
                    + ",".join(result_governance["blockers"])
                )
            governed["governance"] = result_governance

            execution.status = 'completed'
            execution.result_sha256 = governed['sha256']
            execution.result_size_bytes = governed['size_bytes']
            execution.result_trust = governed['trust']
            execution.prompt_injection_risk = governed['prompt_injection_risk']
            execution.duration_ms = round(duration_ms)
            execution.completed_at = datetime.now(UTC)
            if governed['size_bytes'] <= 65_536:
                execution.result_content = governed['content']
            else:
                from backend.storage.object_store import get_object_store

                object_key = f"executions/{execution.execution_id}/result.txt"
                get_object_store().put(
                    'mcp-results',
                    object_key,
                    governed['content'].encode('utf-8'),
                    content_type='text/plain; charset=utf-8',
                    metadata={
                        'sha256': governed['sha256'],
                        'schema_version': governed['schema_version'],
                        'trust': governed['trust'],
                    },
                )
                execution.artifact_object_key = object_key

            tool.execution_count += 1
            tool.success_count += 1
            tool.last_executed = datetime.now(UTC)
            db_server.total_requests += 1
            db_server.successful_requests += 1
            db_server.last_active = datetime.now(UTC)
            db.session.commit()
            _publish_execution_state(db_server, execution)
            record_connector_execution(
                tool_name=tool.name,
                connector_id=connector_id,
                duration_ms=duration_ms,
                success=True,
            )

            return jsonify({
                'success': True,
                'execution': execution.to_dict(),
                'result': governed,
                'metrics': {
                    'connector_id': connector_id,
                    'latency_ms': round(duration_ms, 2),
                },
            }), 200

        except Exception as exc:
            db.session.refresh(execution)
            if execution.status == 'cancelled':
                record_connector_execution(
                    tool_name=tool.name,
                    connector_id=connector_id,
                    duration_ms=(time.perf_counter() - started) * 1000.0,
                    success=False,
                )
                return jsonify({
                    'success': False,
                    'error': 'MCP tool execution was cancelled',
                    'code': 'MCP_EXECUTION_CANCELLED',
                    'execution_id': execution.execution_id,
                }), 409
            duration_ms = (time.perf_counter() - started) * 1000.0
            error_data = getattr(exc, 'data', None)
            error_code = getattr(exc, 'code', None)
            if isinstance(exc, MCPPolicyError):
                error_code = exc.code
            elif isinstance(exc, (ExtendedSubsystemError, KnowledgeLifecycleError)):
                error_code = (
                    'MCP_KA_ADMISSION_BLOCKED'
                    if ka_phase == 'admission'
                    else 'MCP_KA_RESULT_VALIDATION_FAILED'
                )
            elif isinstance(error_data, dict) and error_data.get('reason'):
                error_code = error_data['reason']
            execution.status = 'failed'
            execution.error_code = str(error_code or 'MCP_TOOL_EXECUTION_FAILED')[:100]
            execution.error_message = 'MCP tool execution failed'
            execution.duration_ms = round(duration_ms)
            execution.completed_at = datetime.now(UTC)
            tool.execution_count += 1
            tool.failure_count += 1
            tool.last_executed = datetime.now(UTC)
            db_server.total_requests += 1
            db_server.failed_requests += 1
            db_server.last_error_code = execution.error_code
            db_server.last_error_message = execution.error_message
            try:
                recovery_coordinator = extended or ExtendedSubsystemCoordinator()
                recovery = recovery_coordinator.plan_mcp_recovery(
                    execution_id=execution.execution_id,
                    principal_id=execution.principal_id,
                    server_id=server_id,
                    operation=execution.operation,
                    error_code=execution.error_code,
                    failures=db_server.failed_requests,
                    successes=db_server.successful_requests,
                    effect_already_applied=bool(execution.effect_receipt),
                )
                recovery_plan = recovery_coordinator.mcp_recovery_decision(
                    recovery
                )
                recovery_plan = _apply_mcp_recovery_record(
                    execution=execution,
                    recovery_execution=recovery,
                    recovery_plan=recovery_plan,
                    coordinator=recovery_coordinator,
                )
                execution.ka_lifecycle = {
                    **dict(execution.ka_lifecycle or {}),
                    "recovery": recovery_coordinator.lifecycle_evidence(
                        recovery
                    ),
                    "recovery_plan": recovery_plan,
                }
            except (ExtendedSubsystemError, KnowledgeLifecycleError):
                execution.ka_lifecycle = {
                    **dict(execution.ka_lifecycle or {}),
                    "recovery_plan": {
                        "schema_version": "dle.mcp-recovery-plan.v1",
                        "status": "unavailable",
                        "automatic_retry_allowed": False,
                        "error_code": "MCP_RECOVERY_PLAN_UNAVAILABLE",
                        "actions_applied": 0,
                    },
                }
            db.session.commit()
            _publish_execution_state(db_server, execution)
            record_connector_execution(
                tool_name=tool.name,
                connector_id=connector_id,
                duration_ms=duration_ms,
                success=False,
            )

            logger.error("Error calling MCP tool: %s", type(exc).__name__)
            status = (
                403
                if execution.error_code == 'MCP_KA_ADMISSION_BLOCKED'
                else 502
                if execution.error_code == 'MCP_KA_RESULT_VALIDATION_FAILED'
                else 409
                if execution.error_code == 'MCP_SERVER_NOT_RUNNING'
                else 500
            )
            return jsonify({
                'success': False,
                'error': 'MCP tool execution failed',
                'code': execution.error_code,
                'execution_id': execution.execution_id,
            }), status

    except Exception:
        logger.exception("Error in tool call endpoint")
        return _mcp_error('MCP tool execution failed', 500)


# Prompt Endpoints

@mcp_bp.route('/servers/<server_id>/prompts', methods=['GET'])
@api_session_login_required
def list_prompts(server_id):
    """List prompts for a server"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()

        if not db_server:
            return jsonify({
                'success': False,
                'error': 'Server not found'
            }), 404

        prompts = MCPPrompt.query.filter_by(server_id=db_server.id).all()
        prompts_data = [prompt.to_dict() for prompt in prompts]

        return jsonify({
            'success': True,
            'prompts': prompts_data,
            'count': len(prompts_data)
        }), 200

    except Exception:
        logger.exception("Error listing prompts")
        return _mcp_error('MCP prompts are unavailable', 500)


@mcp_bp.route('/servers/<server_id>/prompts/<int:prompt_id>/get', methods=['POST'])
@api_session_login_required
def get_prompt(server_id, prompt_id):
    """Get a prompt template"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()
        if not db_server:
            return jsonify({'success': False, 'error': 'Server not found'}), 404
        prompt = MCPPrompt.query.filter_by(id=prompt_id, server_id=db_server.id).first()

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404

        data = request.get_json(silent=True) or {}
        arguments = data.get('arguments', {})
        if not isinstance(arguments, dict):
            return jsonify({'success': False, 'error': 'Prompt arguments must be an object'}), 400

        consent = _active_consent(db_server)
        required_scopes = (prompt.prompt_metadata or {}).get('required_scopes') or _required_scope_for_operation(
            db_server, 'read_prompt'
        )
        approved = set(str(scope).lower() for scope in ((consent.approved_scopes if consent else []) or []))
        connector_requirements = {
            str(scope).lower() for scope in required_scopes if str(scope).lower() != 'mcp:execute'
        }
        if consent is None or not connector_requirements <= approved:
            return jsonify({
                'success': False,
                'error': 'Connector consent does not authorize this prompt',
                'code': 'MCP_CONSENT_SCOPE_DENIED',
            }), 403
        if db_server.status != 'active':
            return jsonify({
                'success': False,
                'error': 'Server is not running',
                'code': 'MCP_SERVER_NOT_RUNNING',
            }), 409

        manager = get_mcp_manager()
        server = manager.get_server(server_id)
        started = time.perf_counter()
        execution = MCPExecutionRecord(
            server_id=db_server.id,
            principal_id=_principal_id(),
            operation=f'prompts/get:{prompt.name}',
            status='running',
            required_scopes=sorted(required_scopes),
            request_sha256=_canonical_sha256({'name': prompt.name, 'arguments': arguments}),
        )
        db.session.add(execution)
        db.session.flush()
        db.session.commit()
        _publish_execution_state(db_server, execution)
        try:
            if server is not None:
                result = run_async(server._handle_prompts_get({
                    'name': prompt.name,
                    'arguments': arguments,
                }))
            elif server_id in manager.external_clients:
                timeout = float((db_server.config or {}).get('limits', {}).get('request_timeout_seconds', 30))
                result = manager.get_external_prompt_sync(
                    server_id,
                    prompt.name,
                    arguments,
                    timeout=timeout + 2,
                    operation_id=execution.execution_id,
                )
            else:
                raise MCPPolicyError('MCP_SERVER_NOT_RUNNING', 'Server is not running')
            max_bytes = int((db_server.config or {}).get('limits', {}).get('max_message_bytes', 65_536))
            governed = govern_connector_result(result, max_bytes=max_bytes)
            execution.status = 'completed'
            execution.result_sha256 = governed['sha256']
            execution.result_size_bytes = governed['size_bytes']
            execution.result_content = governed['content'] if governed['size_bytes'] <= 65_536 else None
            execution.result_trust = governed['trust']
            execution.prompt_injection_risk = governed['prompt_injection_risk']
            execution.duration_ms = round((time.perf_counter() - started) * 1000.0)
            execution.completed_at = datetime.now(UTC)
            prompt.usage_count += 1
            prompt.last_used = datetime.now(UTC)
            db_server.total_requests += 1
            db_server.successful_requests += 1
            db.session.commit()
            _publish_execution_state(db_server, execution)

            return jsonify({
                'success': True,
                'prompt': prompt.to_dict(),
                'execution': execution.to_dict(),
                'result': governed,
            }), 200

        except Exception as exc:
            db.session.refresh(execution)
            if execution.status == 'cancelled':
                return jsonify({
                    'success': False,
                    'error': 'MCP prompt request was cancelled',
                    'code': 'MCP_EXECUTION_CANCELLED',
                    'execution_id': execution.execution_id,
                }), 409
            execution.status = 'failed'
            execution.error_code = str(getattr(exc, 'code', None) or 'MCP_PROMPT_GET_FAILED')[:100]
            execution.error_message = 'MCP prompt is unavailable'
            execution.duration_ms = round((time.perf_counter() - started) * 1000.0)
            execution.completed_at = datetime.now(UTC)
            db_server.failed_requests += 1
            db.session.commit()
            _publish_execution_state(db_server, execution)
            logger.error("Error getting prompt: %s", type(exc).__name__)
            return jsonify({
                'success': False,
                'error': 'MCP prompt is unavailable',
                'code': execution.error_code,
                'execution_id': execution.execution_id,
            }), 500

    except Exception:
        logger.exception("Error in get prompt endpoint")
        return _mcp_error('MCP prompt is unavailable', 500)


# Client Management Endpoints

@mcp_bp.route('/clients', methods=['GET'])
@api_session_login_required
def list_clients():
    """List all MCP clients"""
    try:
        manager = get_mcp_manager()
        clients = manager.list_clients()

        return jsonify({
            'success': True,
            'clients': clients,
            'count': len(clients)
        }), 200

    except Exception:
        logger.exception("Error listing clients")
        return _mcp_error('MCP clients are unavailable', 500)


@mcp_bp.route('/clients', methods=['POST'])
@api_admin_required
def create_client():
    """Create a new MCP client"""
    try:
        data = request.get_json()

        name = data.get('name', 'DataLogicEngine')
        version = data.get('version', '1.0.0')

        manager = get_mcp_manager()
        client = manager.create_client(name=name, version=version)

        return jsonify({
            'success': True,
            'client': client.get_client_info()
        }), 201

    except Exception:
        logger.exception("Error creating client")
        return _mcp_error('MCP client could not be created', 500)


@mcp_bp.route('/clients/<client_id>/connect/<server_id>', methods=['POST'])
@api_admin_required
def connect_client(client_id, server_id):
    """Connect a client to a server"""
    try:
        manager = get_mcp_manager()
        result = run_async(manager.connect_client_to_server(client_id, server_id))

        return jsonify({
            'success': True,
            'connection': result
        }), 200

    except Exception:
        logger.exception("Error connecting client")
        return _mcp_error('MCP client connection failed', 500)


# Statistics Endpoint

@mcp_bp.route('/stats', methods=['GET'])
@api_session_login_required
def get_stats():
    """Get MCP system statistics"""
    try:
        manager = get_mcp_manager()
        stats = manager.get_stats()

        # Database stats
        db_stats = {
            'total_servers': MCPServerModel.query.count(),
            'active_servers': MCPServerModel.query.filter_by(status='active').count(),
            'total_resources': MCPResource.query.count(),
            'total_tools': MCPTool.query.count(),
            'total_prompts': MCPPrompt.query.count()
        }

        return jsonify({
            'success': True,
            'stats': {
                **stats,
                **db_stats
            }
        }), 200

    except Exception:
        logger.exception("Error getting stats")
        return _mcp_error('MCP statistics are unavailable', 500)


# Setup default servers endpoint

@mcp_bp.route('/setup-default', methods=['POST'])
@api_admin_required
def setup_default_servers():
    """Retired placeholder registration path."""
    return jsonify({
        'success': False,
        'error': 'Placeholder default MCP servers were removed; register a real connector for explicit review',
        'code': 'MCP_DEFAULT_PLACEHOLDERS_REMOVED',
    }), 410


@mcp_bp.route('/console', methods=['POST'])
@api_admin_required
def mcp_console():
    """Execute a raw MCP console command (admin only)."""
    try:
        data = request.get_json() or {}
        command = str(data.get('command', '')).strip()
        if not command:
            return jsonify({'success': False, 'error': 'command is required'}), 400

        manager = get_mcp_manager()
        # Interpret simple commands: list-servers, stats, help
        if command in ('list-servers', 'servers'):
            servers = MCPServerModel.query.all()
            result = [s.to_dict() for s in servers]
        elif command in ('stats', 'status'):
            stats = manager.get_stats()
            result = stats
        elif command == 'help':
            result = {
                'commands': ['list-servers', 'servers', 'stats', 'status', 'help'],
                'description': 'MCP Console — type a command to inspect the MCP system.'
            }
        else:
            result = {'error': 'Unknown command. Type "help" for available commands.'}

        return jsonify({'success': True, 'result': result})
    except Exception:
        logger.exception("MCP console error")
        return jsonify({'success': False, 'error': 'MCP console is unavailable'}), 500


@mcp_bp.route('/config', methods=['GET'])
@api_admin_required
def get_external_config():
    """Return PostgreSQL-owned, renderer-safe connector configuration."""
    try:
        manager = get_mcp_manager()
        servers = MCPServerModel.query.order_by(MCPServerModel.name.asc()).all()
        return jsonify({
            'success': True,
            'servers': [server.to_dict() for server in servers],
            'active_servers': list(manager.external_clients.keys()),
            'authority': 'postgresql',
            'repository_config_enabled': False,
        }), 200
    except Exception:
        logger.exception("Error getting external config")
        return jsonify({'success': False, 'error': 'MCP external configuration is unavailable'}), 500


@mcp_bp.route('/config', methods=['POST'])
@api_admin_required
def update_external_config():
    """Reject the retired repository JSON/hot-reload authority."""
    return jsonify({
        'success': False,
        'error': 'Repository MCP configuration and automatic hot-reload are retired; register one connector for review',
        'code': 'MCP_CONFIG_FILE_RETIRED',
    }), 410


@mcp_bp.route('/servers/<server_id>/start', methods=['POST'])
@api_admin_required
def start_dynamic_server(server_id):
    """Start one exact approved connector on the durable runtime loop."""
    try:
        server = MCPServerModel.query.filter_by(server_id=server_id).first()
        if not server:
            return _mcp_error('Server configuration not found', 404)
        consent = _active_consent(server)
        if consent is None or server.consent_state != 'approved':
            return jsonify({
                'success': False,
                'error': 'Explicit consent for the current command is required',
                'code': 'MCP_EXPLICIT_CONSENT_REQUIRED',
            }), 409

        validated = validate_stdio_definition(server.name, server.config or {})
        if (
            current_app.config.get('DLE_PRODUCTION_MODE')
            and not current_app.config.get('TESTING')
            and not current_app.config.get('DLE_MCP_CONNECTORS_QUALIFIED')
        ):
            return jsonify({
                'success': False,
                'error': 'Installed Windows connector qualification is required before production start',
                'code': 'MCP_INSTALLED_QUALIFICATION_REQUIRED',
            }), 503
        if validated['fingerprint'] != server.command_fingerprint:
            server.consent_state = 'stale'
            server.approved_scopes = []
            event = _lifecycle(server, 'start_denied', 'fingerprint_mismatch')
            db.session.commit()
            _publish_lifecycle_state(server, event)
            return jsonify({
                'success': False,
                'error': 'The connector definition changed and must be approved again',
                'code': 'MCP_CONSENT_FINGERPRINT_MISMATCH',
            }), 409
        resolved_env = resolve_connector_credentials(
            validated['definition'].get('credential_env', {}),
            server.credential_blobs,
        )
        manager = get_mcp_manager()
        if server_id in manager.external_clients:
            return jsonify({'success': True, 'message': f"Server '{server.name}' is already running", 'server': server.to_dict()}), 200
        runtime = manager.start_external_server_sync(
            server_id,
            validated['definition'],
            resolved_env,
        )
        discovery = runtime.get('discovery', {})
        _sync_discovery(server, discovery)
        capabilities = (runtime.get('initialized') or {}).get('capabilities') or {}
        server.supports_tools = 'tools' in capabilities
        server.supports_resources = 'resources' in capabilities
        server.supports_prompts = 'prompts' in capabilities
        server.supports_logging = False
        server.status = 'active'
        server.enabled = True
        server.health_status = 'degraded' if discovery.get('errors') else 'healthy'
        server.containment_status = runtime.get('client', {}).get('containment_status', 'unknown')
        server.last_error_code = 'MCP_PARTIAL_DISCOVERY' if discovery.get('errors') else None
        server.last_error_message = 'One or more capabilities could not be discovered' if discovery.get('errors') else None
        server.last_active = datetime.now(UTC)
        event = _lifecycle(
            server,
            'started',
            server.health_status,
            details={
                'containment_status': server.containment_status,
                'discovered_tools': len(discovery.get('tools', [])),
                'discovered_resources': len(discovery.get('resources', [])),
                'discovered_prompts': len(discovery.get('prompts', [])),
                'partial_discovery_errors': discovery.get('errors', []),
            },
        )
        db.session.commit()
        _publish_lifecycle_state(server, event)
        return jsonify({
            'success': True,
            'message': f"Dynamic server '{server.name}' started successfully",
            'server': server.to_dict(),
            'discovery': discovery,
        }), 200
    except MCPPolicyError as exc:
        db.session.rollback()
        return _policy_error(exc, status=409)
    except Exception:
        logger.exception("Error starting dynamic server")
        db.session.rollback()
        return _mcp_error('MCP dynamic server could not be started', 500)


@mcp_bp.route('/servers/<server_id>/stop', methods=['POST'])
@api_admin_required
def stop_dynamic_server(server_id):
    """Stop a specific active dynamic MCP server"""
    try:
        server = MCPServerModel.query.filter_by(server_id=server_id).first()
        if not server:
            return _mcp_error('Server configuration not found', 404)
        manager = get_mcp_manager()
        if server_id not in manager.external_clients:
            return _mcp_error('Dynamic server is not running', 404)
        manager.stop_external_server_sync(server_id)
        server.status = 'inactive'
        server.enabled = False
        server.health_status = 'stopped'
        server.containment_status = 'stopped'
        event = _lifecycle(server, 'stopped', 'stopped')
        db.session.commit()
        _publish_lifecycle_state(server, event)
        return jsonify({
            'success': True,
            'message': f"Dynamic server '{server.name}' stopped successfully",
            'server': server.to_dict(),
        }), 200
    except Exception:
        logger.exception("Error stopping dynamic server")
        db.session.rollback()
        return _mcp_error('MCP dynamic server could not be stopped', 500)


@mcp_bp.route('/servers/<server_id>/restart', methods=['POST'])
@api_admin_required
def restart_dynamic_server(server_id):
    """Restart through the same consent and fingerprint checks as start."""
    manager = get_mcp_manager()
    if server_id in manager.external_clients:
        try:
            manager.stop_external_server_sync(server_id)
        except Exception:
            logger.exception('MCP connector restart stop failed')
            return _mcp_error('MCP dynamic server could not be restarted', 500)
    return start_dynamic_server(server_id)
