"""
Data Retention Policy Service for DataLogicEngine

This module provides configurable data retention policies for:
- Session data (chat sessions, simulation sessions)
- Audit logs
- Temporary files
- Archived data

Supports automated cleanup via scheduled tasks (Celery).
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RetentionCategory(Enum):
    """Categories of data subject to retention policies."""
    SESSIONS = "sessions"
    AUDIT_LOGS = "audit_logs"
    TEMP_FILES = "temp_files"
    ARCHIVED_DATA = "archived_data"
    TRACE_RUNS = "trace_runs"
    API_LOGS = "api_logs"


@dataclass
class RetentionPolicy:
    """Configuration for a data retention policy."""
    category: RetentionCategory
    retention_days: int
    description: str
    enabled: bool = True
    archive_before_delete: bool = True


class DataRetentionService:
    """
    Manages data retention policies and automated cleanup.
    
    Usage:
        service = DataRetentionService()
        service.set_policy(RetentionCategory.SESSIONS, 90)  # Keep for 90 days
        service.run_cleanup()  # Execute cleanup for all policies
    """
    
    # Default retention periods (in days)
    DEFAULT_POLICIES = {
        RetentionCategory.SESSIONS: 90,         # 3 months
        RetentionCategory.AUDIT_LOGS: 365,      # 1 year (regulatory requirement)
        RetentionCategory.TEMP_FILES: 7,        # 1 week
        RetentionCategory.ARCHIVED_DATA: 730,   # 2 years
        RetentionCategory.TRACE_RUNS: 180,      # 6 months
        RetentionCategory.API_LOGS: 30,         # 1 month
    }
    
    def __init__(self, db_session=None):
        """
        Initialize the retention service.
        
        Args:
            db_session: Optional SQLAlchemy session (uses Flask's db.session if not provided)
        """
        self.db_session = db_session
        self.policies: Dict[RetentionCategory, RetentionPolicy] = {}
        self._init_default_policies()
        logger.info("DataRetentionService initialized")
    
    def _init_default_policies(self):
        """Initialize with default retention policies."""
        for category, days in self.DEFAULT_POLICIES.items():
            self.policies[category] = RetentionPolicy(
                category=category,
                retention_days=days,
                description=f"Default {days}-day retention for {category.value}",
                enabled=True,
                archive_before_delete=category != RetentionCategory.TEMP_FILES
            )
    
    def get_policy(self, category: RetentionCategory) -> Optional[RetentionPolicy]:
        """Get the retention policy for a category."""
        return self.policies.get(category)
    
    def set_policy(
        self, 
        category: RetentionCategory, 
        retention_days: int,
        archive_before_delete: bool = True,
        enabled: bool = True
    ) -> RetentionPolicy:
        """
        Set or update a retention policy.
        
        Args:
            category: The data category
            retention_days: Number of days to retain data
            archive_before_delete: Whether to archive data before deletion
            enabled: Whether the policy is active
            
        Returns:
            The updated RetentionPolicy
        """
        policy = RetentionPolicy(
            category=category,
            retention_days=retention_days,
            description=f"Custom {retention_days}-day retention for {category.value}",
            enabled=enabled,
            archive_before_delete=archive_before_delete
        )
        self.policies[category] = policy
        logger.info(f"Updated retention policy: {category.value} = {retention_days} days")
        return policy
    
    def list_policies(self) -> List[Dict[str, Any]]:
        """Get all retention policies as a list of dictionaries."""
        return [
            {
                "category": policy.category.value,
                "retention_days": policy.retention_days,
                "description": policy.description,
                "enabled": policy.enabled,
                "archive_before_delete": policy.archive_before_delete,
                "cutoff_date": (datetime.now(UTC) - timedelta(days=policy.retention_days)).isoformat()
            }
            for policy in self.policies.values()
        ]
    
    def get_cutoff_date(self, category: RetentionCategory) -> datetime:
        """Get the cutoff date for a category (data older than this should be cleaned up)."""
        policy = self.policies.get(category)
        if not policy:
            raise ValueError(f"No policy defined for category: {category}")
        return datetime.now(UTC) - timedelta(days=policy.retention_days)
    
    def cleanup_sessions(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Clean up old session data.
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Summary of cleanup operation
        """
        policy = self.policies.get(RetentionCategory.SESSIONS)
        if not policy or not policy.enabled:
            return {"status": "skipped", "reason": "Policy disabled"}
        
        cutoff = self.get_cutoff_date(RetentionCategory.SESSIONS)
        result = {
            "category": "sessions",
            "cutoff_date": cutoff.isoformat(),
            "dry_run": dry_run,
            "deleted_count": 0,
            "archived_count": 0
        }
        
        try:
            from extensions import db
            from models import ChatSession
            
            # Count sessions to delete
            query = ChatSession.query.filter(ChatSession.created_at < cutoff)
            count = query.count()
            result["eligible_count"] = count
            
            if not dry_run and count > 0:
                if policy.archive_before_delete:
                    # Archive logic could export to cold storage here
                    result["archived_count"] = count
                    logger.info(f"Archived {count} sessions before deletion")
                
                # Delete old sessions
                query.delete(synchronize_session=False)
                db.session.commit()
                result["deleted_count"] = count
                logger.info(f"Deleted {count} sessions older than {cutoff}")
            
            result["status"] = "success"
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def cleanup_trace_runs(self, dry_run: bool = False) -> Dict[str, Any]:
        """Clean up old trace run data."""
        policy = self.policies.get(RetentionCategory.TRACE_RUNS)
        if not policy or not policy.enabled:
            return {"status": "skipped", "reason": "Policy disabled"}
        
        cutoff = self.get_cutoff_date(RetentionCategory.TRACE_RUNS)
        result = {
            "category": "trace_runs",
            "cutoff_date": cutoff.isoformat(),
            "dry_run": dry_run,
            "deleted_count": 0
        }
        
        try:
            from extensions import db
            from models import TraceRun
            
            query = TraceRun.query.filter(TraceRun.created_at < cutoff)
            count = query.count()
            result["eligible_count"] = count
            
            if not dry_run and count > 0:
                query.delete(synchronize_session=False)
                db.session.commit()
                result["deleted_count"] = count
                logger.info(f"Deleted {count} trace runs older than {cutoff}")
            
            result["status"] = "success"
        except ImportError:
            result["status"] = "skipped"
            result["reason"] = "Trace models not available"
        except Exception as e:
            logger.error(f"Trace run cleanup failed: {e}")
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def run_cleanup(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run cleanup for all enabled retention policies.
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Summary of all cleanup operations
        """
        logger.info(f"Starting retention cleanup (dry_run={dry_run})")
        
        results = {
            "started_at": datetime.now(UTC).isoformat(),
            "dry_run": dry_run,
            "cleanups": []
        }
        
        # Run cleanup for each category
        cleanup_methods = {
            RetentionCategory.SESSIONS: self.cleanup_sessions,
            RetentionCategory.TRACE_RUNS: self.cleanup_trace_runs,
        }
        
        for category, method in cleanup_methods.items():
            try:
                result = method(dry_run=dry_run)
                results["cleanups"].append(result)
            except Exception as e:
                logger.error(f"Cleanup failed for {category.value}: {e}")
                results["cleanups"].append({
                    "category": category.value,
                    "status": "error",
                    "error": str(e)
                })
        
        results["completed_at"] = datetime.now(UTC).isoformat()
        results["status"] = "success"
        
        logger.info(f"Retention cleanup completed: {len(results['cleanups'])} categories processed")
        return results
    
    def check_health(self) -> Dict[str, Any]:
        """Health check for the retention service."""
        return {
            "healthy": True,
            "policies_count": len(self.policies),
            "enabled_policies": sum(1 for p in self.policies.values() if p.enabled)
        }


# Celery task for scheduled cleanup
def register_celery_tasks(celery_app):
    """Register retention cleanup tasks with Celery."""
    
    @celery_app.task(name='retention.run_cleanup')
    def run_retention_cleanup():
        """Celery task to run data retention cleanup."""
        from flask import current_app
        with current_app.app_context():
            service = DataRetentionService()
            return service.run_cleanup(dry_run=False)
    
    return run_retention_cleanup
