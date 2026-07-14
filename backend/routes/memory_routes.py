"""Owner-only review and lifecycle controls for bounded working memory."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.auth.api_decorators import api_admin_required
from backend.memory import get_unified_memory_service


memory_api = Blueprint("memory_api", __name__, url_prefix="/api/v1/memory")


@memory_api.route("/review", methods=["GET"])
@api_admin_required
def review_memory():
    include_working = request.args.get("include_working", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    service = get_unified_memory_service()
    return jsonify(
        {
            "success": True,
            "data": {
                "items": service.review(include_working=include_working),
                "stats": service.stats(),
            },
        }
    )


@memory_api.route("/export", methods=["GET"])
@api_admin_required
def export_memory():
    return jsonify(
        {"success": True, "data": get_unified_memory_service().export_graph()}
    )


@memory_api.route("/compact", methods=["POST"])
@api_admin_required
def compact_memory():
    data = request.get_json(silent=True) or {}
    try:
        limit = int(data.get("max_working_vertices", 500))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid working-memory limit"}), 400
    if limit < 0 or limit > 10_000:
        return jsonify({"success": False, "error": "Invalid working-memory limit"}), 400
    return jsonify(
        {
            "success": True,
            "data": get_unified_memory_service().compact(
                max_working_vertices=limit
            ),
        }
    )


@memory_api.route("/<vertex_id>", methods=["DELETE"])
@api_admin_required
def delete_memory(vertex_id: str):
    deleted = get_unified_memory_service().delete(vertex_id)
    if not deleted:
        return jsonify({"success": False, "error": "Memory record not found"}), 404
    return jsonify({"success": True, "data": {"deleted": True}})


@memory_api.route("/recover", methods=["POST"])
@api_admin_required
def recover_memory():
    try:
        stats = get_unified_memory_service().recover_from_backup()
    except Exception:
        return jsonify({"success": False, "error": "Verified memory backup unavailable"}), 409
    return jsonify({"success": True, "data": stats})
