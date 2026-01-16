"""
TruthMemory Metrics Tracker

MLflow-style metrics tracking for performance monitoring.
"""

import logging
import uuid
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricsTracker:
    """
    Track and aggregate performance metrics.
    
    Metrics tracked:
    - hallucination_rate
    - simulation_accuracy
    - latency_ms
    - token_spend
    - confidence_score
    - cache_hit_ratio
    """
    
    METRIC_DEFINITIONS = {
        'hallucination_rate': {'unit': 'ratio', 'type': 'gauge', 'lower_is_better': True},
        'simulation_accuracy': {'unit': 'ratio', 'type': 'gauge', 'lower_is_better': False},
        'latency_ms': {'unit': 'ms', 'type': 'histogram', 'lower_is_better': True},
        'token_spend': {'unit': 'tokens', 'type': 'counter', 'lower_is_better': True},
        'confidence_score': {'unit': 'ratio', 'type': 'gauge', 'lower_is_better': False},
        'cache_hit_ratio': {'unit': 'ratio', 'type': 'gauge', 'lower_is_better': False},
        'request_count': {'unit': 'count', 'type': 'counter', 'lower_is_better': False},
        'error_count': {'unit': 'count', 'type': 'counter', 'lower_is_better': True}
    }

    def __init__(self, db_session=None):
        """Initialize metrics tracker."""
        self.db_session = db_session
        self.in_memory_metrics = defaultdict(list)
        self.aggregates = defaultdict(lambda: {'sum': 0, 'count': 0, 'min': float('inf'), 'max': float('-inf')})
        logger.info("MetricsTracker initialized")

    def record(self, metric_name: str, value: float, session_id: str = None,
               tier: str = None, llm_model: str = None, 
               labels: Dict[str, str] = None) -> Dict[str, Any]:
        """Record a metric value."""
        metric_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)
        
        definition = self.METRIC_DEFINITIONS.get(metric_name, {})
        
        metric_record = {
            'metric_id': metric_id,
            'session_id': session_id,
            'metric_name': metric_name,
            'metric_value': value,
            'metric_unit': definition.get('unit', ''),
            'metric_type': definition.get('type', 'gauge'),
            'tier': tier,
            'llm_model': llm_model,
            'labels': labels or {},
            'timestamp': timestamp.isoformat()
        }
        
        agg = self.aggregates[metric_name]
        agg['sum'] += value
        agg['count'] += 1
        agg['min'] = min(agg['min'], value)
        agg['max'] = max(agg['max'], value)
        
        self.in_memory_metrics[metric_name].append(metric_record)
        
        if len(self.in_memory_metrics[metric_name]) > 1000:
            self.in_memory_metrics[metric_name] = self.in_memory_metrics[metric_name][-500:]
        
        if self.db_session:
            try:
                from models import TruthMetric
                
                db_metric = TruthMetric(
                    metric_id=metric_id,
                    session_id=session_id,
                    metric_name=metric_name,
                    metric_value=value,
                    metric_unit=definition.get('unit', ''),
                    metric_type=definition.get('type', 'gauge'),
                    tier=tier,
                    llm_model=llm_model,
                    labels=labels,
                    timestamp=timestamp
                )
                self.db_session.add(db_metric)
                self.db_session.commit()
            except Exception as e:
                logger.error(f"Failed to persist metric: {e}")
        
        return metric_record

    def get_metric(self, metric_name: str, 
                   time_range: timedelta = None,
                   tier: str = None) -> List[Dict[str, Any]]:
        """Get metric values with optional filters."""
        if not self.db_session:
            metrics = self.in_memory_metrics.get(metric_name, [])
            if tier:
                metrics = [m for m in metrics if m.get('tier') == tier]
            return metrics
        
        try:
            from models import TruthMetric
            query = self.db_session.query(TruthMetric).filter_by(metric_name=metric_name)
            
            if tier:
                query = query.filter_by(tier=tier)
            
            if time_range:
                cutoff = datetime.now(UTC) - time_range
                query = query.filter(TruthMetric.timestamp >= cutoff)
            
            return [m.to_dict() for m in query.order_by(TruthMetric.timestamp.desc()).limit(1000).all()]
        except Exception as e:
            logger.error(f"Failed to get metrics from DB: {e}")
            return []

    def get_aggregate(self, metric_name: str) -> Dict[str, Any]:
        """Get aggregate statistics for a metric."""
        agg = self.aggregates.get(metric_name)
        
        if not agg or agg['count'] == 0:
            return {
                'metric_name': metric_name,
                'count': 0,
                'avg': 0,
                'min': 0,
                'max': 0,
                'sum': 0
            }
        
        return {
            'metric_name': metric_name,
            'count': agg['count'],
            'avg': agg['sum'] / agg['count'],
            'min': agg['min'] if agg['min'] != float('inf') else 0,
            'max': agg['max'] if agg['max'] != float('-inf') else 0,
            'sum': agg['sum']
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked metrics."""
        summary = {
            'metrics_tracked': list(self.METRIC_DEFINITIONS.keys()),
            'aggregates': {}
        }
        
        for metric_name in self.aggregates:
            summary['aggregates'][metric_name] = self.get_aggregate(metric_name)
        
        return summary

    def get_tier_breakdown(self, metric_name: str) -> Dict[str, Dict[str, float]]:
        """Get metric breakdown by tier."""
        tier_data = defaultdict(lambda: {'sum': 0, 'count': 0})
        
        for record in self.in_memory_metrics.get(metric_name, []):
            tier = record.get('tier', 'unknown')
            tier_data[tier]['sum'] += record['metric_value']
            tier_data[tier]['count'] += 1
        
        return {
            tier: {
                'avg': data['sum'] / data['count'] if data['count'] > 0 else 0,
                'count': data['count']
            }
            for tier, data in tier_data.items()
        }

    def record_request(self, session_id: str, tier: str, 
                       latency_ms: float, tokens: int = 0,
                       confidence: float = 0, success: bool = True) -> None:
        """Convenience method to record common request metrics."""
        self.record('request_count', 1, session_id, tier)
        self.record('latency_ms', latency_ms, session_id, tier)
        
        if tokens > 0:
            self.record('token_spend', tokens, session_id, tier)
        
        if confidence > 0:
            self.record('confidence_score', confidence, session_id, tier)
        
        if not success:
            self.record('error_count', 1, session_id, tier)
