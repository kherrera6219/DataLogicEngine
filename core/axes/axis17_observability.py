"""
Universal Knowledge Graph (UKG) System - Axis 17: Observability & Analytics

This module implements the Observability & Analytics axis for the 17-Axis UKG system,
providing metrics collection, audit trails, performance dashboards, and SLA management.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(Enum):
    """Log severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SLAStatus(Enum):
    """SLA compliance status"""
    COMPLIANT = "compliant"
    AT_RISK = "at_risk"
    BREACHED = "breached"
    UNKNOWN = "unknown"


class ObservabilityAxis:
    """Handler for Axis 17: Observability & Analytics - Metrics, Logging, and Monitoring"""
    
    def __init__(self):
        """Initialize the Observability & Analytics axis handler."""
        self.axis_number = 17
        self.axis_name = "Observability & Analytics"
        self.description = "Metrics collection, audit trails, performance dashboards, and SLA management"
        
        self.metric_types = [m.value for m in MetricType]
        self.log_levels = [l.value for l in LogLevel]
        self.alert_severities = [a.value for a in AlertSeverity]
        self.sla_statuses = [s.value for s in SLAStatus]
        
        self.metrics = defaultdict(list)
        self.audit_trail = []
        self.alerts = []
        self.sla_definitions = {}
        self.traces = {}
    
    def navigate(self, **kwargs) -> Dict[str, Any]:
        """
        Navigate the Observability & Analytics axis based on provided parameters.
        
        Parameters:
        - metric_name (str): Specific metric to retrieve
        - time_range (tuple): Start and end datetime for filtering
        - log_level (str): Filter audit logs by level
        - alert_severity (str): Filter alerts by severity
        - include_traces (bool): Include distributed traces
        
        Returns:
        - Dict containing the navigation results
        """
        metric_name = kwargs.get('metric_name')
        time_range = kwargs.get('time_range')
        log_level = kwargs.get('log_level')
        alert_severity = kwargs.get('alert_severity')
        include_traces = kwargs.get('include_traces', False)
        
        try:
            result_data = {
                "axis": self.axis_number,
                "name": self.axis_name,
                "filters_applied": {
                    "metric_name": metric_name,
                    "time_range": time_range,
                    "log_level": log_level,
                    "alert_severity": alert_severity
                },
                "metric_types_available": self.metric_types,
                "log_levels_available": self.log_levels,
                "alert_severities_available": self.alert_severities,
                "sla_statuses": self.sla_statuses
            }
            
            if metric_name:
                result_data["metrics"] = self._get_metrics(metric_name, time_range)
            
            if log_level:
                result_data["audit_logs"] = self._get_audit_logs(log_level, time_range)
            
            if alert_severity:
                result_data["alerts"] = self._get_alerts(alert_severity)
            
            if include_traces:
                result_data["traces"] = self._get_recent_traces()
            
            result_data["system_health"] = self._get_system_health()
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error navigating Observability & Analytics axis: {str(e)}")
            return {
                "axis": self.axis_number,
                "name": self.axis_name,
                "error": str(e)
            }
    
    def record_metric(self, name: str, value: float, metric_type: str,
                      labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Record a metric value.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric (counter, gauge, histogram, summary)
            labels: Additional labels for the metric
            
        Returns:
            Recorded metric entry
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "name": name,
            "value": value,
            "type": metric_type,
            "labels": labels or {}
        }
        
        self.metrics[name].append(entry)
        
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-500:]
        
        return entry
    
    def log_audit_event(self, event_type: str, actor: str, action: str,
                         resource: str, details: Optional[Dict] = None,
                         level: str = "info") -> Dict[str, Any]:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            actor: Who performed the action
            action: What action was performed
            resource: What resource was affected
            details: Additional details
            level: Log level
            
        Returns:
            Audit log entry
        """
        entry = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "actor": actor,
            "action": action,
            "resource": resource,
            "details": details or {},
            "level": level
        }
        
        self.audit_trail.append(entry)
        
        if len(self.audit_trail) > 10000:
            self.audit_trail = self.audit_trail[-5000:]
        
        logger.log(
            getattr(logging, level.upper(), logging.INFO),
            f"AUDIT: {actor} {action} on {resource}"
        )
        
        return entry
    
    def create_alert(self, name: str, message: str, severity: str,
                      source: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create an alert.
        
        Args:
            name: Alert name
            message: Alert message
            severity: Alert severity
            source: Source of the alert
            metadata: Additional metadata
            
        Returns:
            Created alert
        """
        alert = {
            "alert_id": str(uuid.uuid4()),
            "name": name,
            "message": message,
            "severity": severity,
            "source": source,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "acknowledged": False,
            "resolved": False,
            "resolved_at": None
        }
        
        self.alerts.append(alert)
        
        logger.warning(f"ALERT [{severity.upper()}]: {name} - {message}")
        
        return alert
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Dict[str, Any]:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_by"] = acknowledged_by
                alert["acknowledged_at"] = datetime.utcnow().isoformat()
                return {"success": True, "alert": alert}
        
        return {"success": False, "error": "Alert not found"}
    
    def resolve_alert(self, alert_id: str, resolution_notes: str) -> Dict[str, Any]:
        """Resolve an alert."""
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                alert["resolved"] = True
                alert["resolution_notes"] = resolution_notes
                alert["resolved_at"] = datetime.utcnow().isoformat()
                return {"success": True, "alert": alert}
        
        return {"success": False, "error": "Alert not found"}
    
    def define_sla(self, sla_id: str, name: str, target_metric: str,
                    threshold: float, evaluation_window: int,
                    metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Define an SLA.
        
        Args:
            sla_id: SLA identifier
            name: SLA name
            target_metric: Metric to evaluate
            threshold: Threshold value for compliance
            evaluation_window: Window in minutes
            metadata: Additional metadata
            
        Returns:
            SLA definition
        """
        sla = {
            "sla_id": sla_id,
            "name": name,
            "target_metric": target_metric,
            "threshold": threshold,
            "evaluation_window_minutes": evaluation_window,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "current_status": SLAStatus.UNKNOWN.value
        }
        
        self.sla_definitions[sla_id] = sla
        
        return sla
    
    def evaluate_sla(self, sla_id: str) -> Dict[str, Any]:
        """
        Evaluate SLA compliance.
        
        Args:
            sla_id: SLA to evaluate
            
        Returns:
            SLA evaluation results
        """
        sla = self.sla_definitions.get(sla_id)
        if not sla:
            return {"success": False, "error": "SLA not found"}
        
        metric_name = sla["target_metric"]
        threshold = sla["threshold"]
        window = sla["evaluation_window_minutes"]
        
        recent_metrics = self._get_metrics(metric_name, (
            datetime.utcnow() - timedelta(minutes=window),
            datetime.utcnow()
        ))
        
        if not recent_metrics:
            status = SLAStatus.UNKNOWN.value
            compliance_rate = None
        else:
            values = [m["value"] for m in recent_metrics]
            avg_value = sum(values) / len(values)
            
            if avg_value >= threshold:
                status = SLAStatus.COMPLIANT.value
            elif avg_value >= threshold * 0.9:
                status = SLAStatus.AT_RISK.value
            else:
                status = SLAStatus.BREACHED.value
            
            compliance_rate = avg_value / threshold if threshold > 0 else 1.0
        
        self.sla_definitions[sla_id]["current_status"] = status
        self.sla_definitions[sla_id]["last_evaluated"] = datetime.utcnow().isoformat()
        
        return {
            "sla_id": sla_id,
            "status": status,
            "compliance_rate": compliance_rate,
            "metrics_evaluated": len(recent_metrics) if recent_metrics else 0,
            "evaluated_at": datetime.utcnow().isoformat()
        }
    
    def start_trace(self, trace_name: str, metadata: Optional[Dict] = None) -> str:
        """Start a distributed trace."""
        trace_id = str(uuid.uuid4())
        
        self.traces[trace_id] = {
            "trace_id": trace_id,
            "name": trace_name,
            "started_at": datetime.utcnow().isoformat(),
            "ended_at": None,
            "duration_ms": None,
            "spans": [],
            "metadata": metadata or {},
            "status": "in_progress"
        }
        
        return trace_id
    
    def add_span(self, trace_id: str, span_name: str, 
                  duration_ms: float, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add a span to a trace."""
        if trace_id not in self.traces:
            return {"success": False, "error": "Trace not found"}
        
        span = {
            "span_id": str(uuid.uuid4()),
            "name": span_name,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": duration_ms,
            "metadata": metadata or {}
        }
        
        self.traces[trace_id]["spans"].append(span)
        
        return {"success": True, "span": span}
    
    def end_trace(self, trace_id: str, status: str = "completed") -> Dict[str, Any]:
        """End a trace."""
        if trace_id not in self.traces:
            return {"success": False, "error": "Trace not found"}
        
        trace = self.traces[trace_id]
        trace["ended_at"] = datetime.utcnow().isoformat()
        trace["status"] = status
        
        start = datetime.fromisoformat(trace["started_at"])
        end = datetime.fromisoformat(trace["ended_at"])
        trace["duration_ms"] = (end - start).total_seconds() * 1000
        
        return {"success": True, "trace": trace}
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get aggregated dashboard data."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_summary": {
                "total_metrics": len(self.metrics),
                "total_data_points": sum(len(v) for v in self.metrics.values())
            },
            "audit_summary": {
                "total_events": len(self.audit_trail),
                "by_level": self._count_by_field(self.audit_trail, "level")
            },
            "alerts_summary": {
                "total_alerts": len(self.alerts),
                "active": len([a for a in self.alerts if not a["resolved"]]),
                "by_severity": self._count_by_field(self.alerts, "severity")
            },
            "sla_summary": {
                "total_slas": len(self.sla_definitions),
                "by_status": self._count_by_field(list(self.sla_definitions.values()), "current_status")
            },
            "traces_summary": {
                "total_traces": len(self.traces),
                "active": len([t for t in self.traces.values() if t["status"] == "in_progress"])
            }
        }
    
    def _get_metrics(self, name: str, time_range: Optional[tuple] = None) -> List[Dict]:
        """Get metrics by name and optional time range."""
        metrics = self.metrics.get(name, [])
        
        if time_range and len(time_range) == 2:
            start, end = time_range
            if isinstance(start, datetime) and isinstance(end, datetime):
                metrics = [m for m in metrics 
                          if start <= datetime.fromisoformat(m["timestamp"]) <= end]
        
        return metrics
    
    def _get_audit_logs(self, level: str, time_range: Optional[tuple] = None) -> List[Dict]:
        """Get audit logs by level."""
        logs = [l for l in self.audit_trail if l["level"] == level]
        return logs[-100:]
    
    def _get_alerts(self, severity: str) -> List[Dict]:
        """Get alerts by severity."""
        return [a for a in self.alerts if a["severity"] == severity]
    
    def _get_recent_traces(self) -> List[Dict]:
        """Get recent traces."""
        return list(self.traces.values())[-50:]
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        active_alerts = [a for a in self.alerts if not a["resolved"]]
        critical_alerts = [a for a in active_alerts if a["severity"] == "critical"]
        
        if critical_alerts:
            health_status = "critical"
        elif len(active_alerts) > 10:
            health_status = "degraded"
        elif active_alerts:
            health_status = "warning"
        else:
            health_status = "healthy"
        
        return {
            "status": health_status,
            "active_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "checked_at": datetime.utcnow().isoformat()
        }
    
    def _count_by_field(self, items: List[Dict], field: str) -> Dict[str, int]:
        """Count items by a field value."""
        counts = defaultdict(int)
        for item in items:
            counts[item.get(field, "unknown")] += 1
        return dict(counts)
    
    def get_axis_metadata(self) -> Dict[str, Any]:
        """Get metadata about this axis."""
        return {
            "axis_number": self.axis_number,
            "axis_name": self.axis_name,
            "description": self.description,
            "metric_types": self.metric_types,
            "log_levels": self.log_levels,
            "alert_severities": self.alert_severities,
            "sla_statuses": self.sla_statuses,
            "total_metrics": len(self.metrics),
            "total_audit_entries": len(self.audit_trail),
            "total_alerts": len(self.alerts),
            "total_slas": len(self.sla_definitions)
        }
