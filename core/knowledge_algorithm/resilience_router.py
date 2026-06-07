"""
Resilience Router (Self-Healing Module)

Provides a robust wrapper for Knowledge Algorithm execution.
Implements the 'Graceful Degradation' pattern:
1. Attempt primary (complex) execution.
2. Catch failures (exceptions, timeouts).
3. Fallback to secondary (simple) execution.
4. Annotate result with 'degraded' status.

Pure domain logic; no Flask/DB dependencies.
"""
from typing import Any, Callable, Dict
import logging

logger = logging.getLogger(__name__)


class ResilienceRouter:
    """Manages execution reliability and fallback logic for KA invocations."""

    def __init__(self, audit_logger=None):
        self.audit_logger = audit_logger

    def execute_with_fallback(
        self,
        primary_func: Callable,
        fallback_func: Callable,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a function with automatic fallback on failure.

        Args:
            primary_func: High-complexity function to try first
            fallback_func: Low-complexity function to try if primary fails
            context: Input parameters for the functions

        Returns:
            Result dict with 'meta' detailing execution path
        """
        try:
            logger.info(f"Attempting primary execution for context: {context.get('request_id', 'unknown')}")
            result = primary_func(context)

            if isinstance(result, dict):
                result.setdefault('meta', {})
                result['meta']['execution_mode'] = 'OPTIMAL'

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Primary execution failed: {error_msg}. Triggering Self-Healing.")

            if self.audit_logger:
                self.audit_logger.log_security_event(
                    event_type="system_self_healing_execution",
                    details={"error": error_msg, "context": str(context)[:100]},
                    severity="WARNING",
                )

            try:
                fallback_result = fallback_func(context)

                if isinstance(fallback_result, dict):
                    fallback_result.setdefault('meta', {})
                    fallback_result['meta']['execution_mode'] = 'DEGRADED'
                    fallback_result['meta']['fallback_reason'] = error_msg
                    fallback_result['meta']['warning'] = "Result generated via fallback logic. Precision may be reduced."

                return fallback_result

            except Exception as fallback_error:
                logger.critical(f"Fallback also failed: {str(fallback_error)}")
                return {
                    "status": "error",
                    "error": "System Failure: Primary and Fallback execution failed.",
                    "details": str(fallback_error),
                }


_resilience_router: ResilienceRouter | None = None


def get_resilience_router(audit_logger=None) -> ResilienceRouter:
    global _resilience_router
    if not _resilience_router:
        _resilience_router = ResilienceRouter(audit_logger)
    return _resilience_router
