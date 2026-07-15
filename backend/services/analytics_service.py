import logging
from datetime import datetime, timedelta, UTC
from extensions import db
from models import Node, Edge, KAExecution, UkgSession, MCPServer, MCPTool, TraceRun
from backend.mcp_server.connector_metrics import connector_metrics_snapshot, infer_connector_id

class AnalyticsService:
    @staticmethod
    def get_dashboard_overview(tenant_id=None):
        """
        Get high-level metrics for the dashboard.
        """
        try:
            # 1. API Requests (Last 24 hours)
            yesterday = datetime.now(UTC) - timedelta(days=1)
            request_count = db.session.query(KAExecution).filter(
                KAExecution.created_at >= yesterday
            )
            if tenant_id:
                request_count = request_count.filter(KAExecution.tenant_id == tenant_id)
            request_count = request_count.count()

            # 2. Knowledge Graph Size. Prefer the active USKD graph used by the
            # reasoning engine, then fall back to the legacy SQL visualization tables.
            from backend.storage import get_uskd_memory_graph

            graph_stats = get_uskd_memory_graph().stats()
            if graph_stats.node_count:
                node_count = graph_stats.node_count
                edge_count = graph_stats.edge_count
            else:
                node_query = db.session.query(Node)
                edge_query = db.session.query(Edge)
                if tenant_id:
                    node_query = node_query.filter(Node.tenant_id == tenant_id)
                    edge_query = edge_query.filter(Edge.tenant_id == tenant_id)
                node_count = node_query.count()
                edge_count = edge_query.count()
            
            # Simple heuristic for "size" in MB/GB for display
            # Assume 1KB per node+edge entry
            size_kb = (node_count + edge_count) * 1.0 
            size_display = f"{size_kb / 1024:.2f} MB" if size_kb < 1024*1024 else f"{size_kb / (1024*1024):.2f} GB"

            # 3. Trace-derived validation score. Do not report a passing score
            # when no validation runs exist.
            trace_query = db.session.query(TraceRun).order_by(TraceRun.created_at.desc()).limit(100)
            traces = trace_query.all()
            confidence_values = [float(run.confidence) for run in traces if run.confidence is not None]
            failed_runs = sum(1 for run in traces if str(run.status or "").lower() in {"fail", "failed"})
            average_confidence = (
                sum(confidence_values) / len(confidence_values)
                if confidence_values else None
            )
            average_validation_confidence = (
                f"{average_confidence * 100:.1f}%"
                if average_confidence is not None
                else "Not measured"
            )
            if not traces:
                validation_status = "No validation data"
            elif failed_runs:
                validation_status = "Review required"
            elif average_confidence is not None and average_confidence >= 0.8:
                validation_status = "Validation checks passed"
            else:
                validation_status = "Needs review"

            return {
                "api_requests_24h": request_count,
                "kg_nodes": node_count,
                "kg_edges": edge_count,
                "kg_size_display": size_display,
                "validation_status": validation_status,
                "average_validation_confidence": average_validation_confidence,
                "validation_run_count": len(traces),
                "failed_validation_runs": failed_runs,
                "timestamp": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logging.error(f"Analytics: Error getting dashboard overview: {str(e)}")
            return None

    @staticmethod
    def get_trends(metric="sessions", days=7, tenant_id=None):
        """Return real daily activity counts for the requested metric."""
        days = min(max(int(days or 7), 1), 90)
        start = datetime.now(UTC) - timedelta(days=days - 1)
        metric_key = str(metric or "sessions").lower()
        model = KAExecution if metric_key in {"ka", "kas", "algorithms", "executions"} else UkgSession
        query = db.session.query(model).filter(model.created_at >= start)
        if tenant_id and hasattr(model, "tenant_id"):
            query = query.filter(model.tenant_id == tenant_id)

        counts = {}
        for row in query.all():
            created_at = row.created_at
            if created_at is not None:
                counts[created_at.date().isoformat()] = counts.get(created_at.date().isoformat(), 0) + 1

        return {
            "metric": metric_key,
            "days": days,
            "data_points": [
                {
                    "date": (start + timedelta(days=offset)).date().isoformat(),
                    "value": counts.get((start + timedelta(days=offset)).date().isoformat(), 0),
                }
                for offset in range(days)
            ],
        }

    @staticmethod
    def get_recent_activity(limit=10, tenant_id=None):
        """
        Get recent system activity (Chat, Upload, Security events).
        """
        try:
            # Aggregate from Sessions and KAExecutions
            activities = []
            
            # Recent Sessions (Chat)
            sessions = db.session.query(UkgSession).order_by(UkgSession.created_at.desc())
            if tenant_id:
                sessions = sessions.filter(UkgSession.tenant_id == tenant_id)
            
            for s in sessions.limit(limit).all():
                activities.append({
                    "type": "chat",
                    "title": s.user_query or "New Session",
                    "time": s.created_at.isoformat(),
                    "id": s.session_id
                })

            # Sort and return
            activities.sort(key=lambda x: x["time"], reverse=True)
            return activities[:limit]
        except Exception as e:
            logging.error(f"Analytics: Error getting recent activity: {str(e)}")
            return None

    @staticmethod
    def get_mcp_stats():
        """
        Get stats for MCP servers and tool usage.
        """
        try:
            servers = db.session.query(MCPServer).all()
            tools = db.session.query(MCPTool).all()

            total_requests = sum(int(s.total_requests or 0) for s in servers)
            total_success = sum(int(s.successful_requests or 0) for s in servers)
            total_failed = sum(int(s.failed_requests or 0) for s in servers)
            pending_requests = max(total_requests - total_success - total_failed, 0)

            total_tool_calls = sum(int(t.execution_count or 0) for t in tools)
            connector_metrics = connector_metrics_snapshot()
            top_tools_raw = sorted(
                tools,
                key=lambda t: int(t.execution_count or 0),
                reverse=True
            )[:5]
            top_tools = []
            for tool in top_tools_raw:
                calls = int(tool.execution_count or 0)
                percent = (calls / total_tool_calls * 100.0) if total_tool_calls > 0 else 0.0
                top_tools.append({
                    "name": tool.name,
                    "calls": calls,
                    "percent": round(percent, 1)
                })

            server_health = []
            for server in servers:
                status = str(server.status or 'inactive').lower()
                connector_id = infer_connector_id(server.name)
                connector_latency = connector_metrics.get(connector_id or "", {}).get("avg_latency_ms", 0.0)
                server_health.append({
                    "name": server.name,
                    "status": "Healthy" if status == 'active' else status.title(),
                    "latency": round(float(connector_latency), 2),
                })

            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "time_series": [
                    {
                        "time": "Now",
                        "requests": total_requests,
                        "responses": total_success,
                        "errors": total_failed
                    }
                ],
                "top_tools": top_tools,
                "server_health": server_health,
                "error_stats": [
                    {"name": "Failed", "value": total_failed, "colorCode": "#ef4444"},
                    {"name": "Successful", "value": total_success, "colorCode": "#10b981"},
                    {"name": "Pending", "value": pending_requests, "colorCode": "#f59e0b"},
                ]
            }
        except Exception as e:
            logging.error(f"Analytics: Error getting MCP stats: {str(e)}")
            return None
