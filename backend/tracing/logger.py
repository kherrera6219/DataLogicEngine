import uuid
import json
import logging
from datetime import datetime, UTC
from typing import Dict, Any, Optional

from extensions import db
from models import TraceKAInvocation, TraceRun, TraceStage

logger = logging.getLogger(__name__)

class TraceLogger:
    """Helper to log trace events to the database."""
    
    @staticmethod
    def log_ka_invocation(ka_id: str, 
                          inputs: Dict[str, Any], 
                          outputs: Dict[str, Any], 
                          run_id: Optional[str] = None,
                          stage_id: Optional[str] = None,
                          duration_ms: Optional[float] = None,
                          success: bool = True,
                          error: Optional[str] = None) -> Optional[str]:
        """Record a Knowledge Algorithm invocation."""
        try:
            # Check for active run if not provided
            if not run_id:
                # In a real system, we might pull this from a thread-local or context
                return None
            
            invocation = TraceKAInvocation(
                invocation_id=uuid.uuid4(),
                run_id=uuid.UUID(run_id),
                stage_id=uuid.UUID(stage_id) if stage_id else None,
                ka_id=ka_id,
                status='success' if success else 'fail',
                inputs=inputs,
                outputs=outputs,
                duration_ms=duration_ms,
                error_message=error,
                invoked_at=datetime.now(UTC)
            )
            
            db.session.add(invocation)
            db.session.commit()
            return str(invocation.invocation_id)
        except Exception as e:
            logger.error(f"Failed to log KA invocation to trace: {e}")
            db.session.rollback()
            return None

    @staticmethod
    def create_run(user_id: int, query: str, tier: str = 'moderate') -> str:
        """Create a new trace run."""
        try:
            run = TraceRun(
                run_id=uuid.uuid4(),
                user_id=user_id,
                query=query,
                tier=tier,
                status='processing',
                created_at=datetime.now(UTC)
            )
            db.session.add(run)
            db.session.commit()
            return str(run.run_id)
        except Exception as e:
            logger.error(f"Failed to create trace run: {e}")
            db.session.rollback()
            return str(uuid.uuid4()) # Fallback ID

    @staticmethod
    def update_run_status(run_id: str, status: str, confidence: float = 0.0):
        """Update trace run status and confidence."""
        try:
            run = TraceRun.query.filter_by(run_id=uuid.UUID(run_id)).first()
            if run:
                run.status = status
                run.confidence = confidence
                run.completed_at = datetime.now(UTC) if status in ['completed', 'failed'] else None
                db.session.commit()
        except Exception as e:
            logger.error(f"Failed to update trace run: {e}")
            db.session.rollback()
