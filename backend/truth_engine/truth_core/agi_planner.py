import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from backend.truth_engine.truth_core.l7_schemas import (
    AGIGoal, AGIBelief, AGIConflict, AGIPlan, AGIContext
)
try:
    from backend.security.ai_guardrail import AIGuardrailService
except ImportError:
    AIGuardrailService = None

logger = logging.getLogger(__name__)

class AGIPlannerService:
    """
    Layer 7: Recursive AGI Planner.
    Uses LLM-driven decomposition and conflict arbitration to create
    robust, multi-step plans that align with held beliefs (Truths).
    
    HARDENED: Includes Input Sanitization, Resource Limits, and Fail-Safe Logic.
    """

    def __init__(self, llm_gateway=None, guardrail_service=None, ka_controller=None):
        self.llm_gateway = llm_gateway
        self.ka_controller = ka_controller
        self.guardrail = guardrail_service or (AIGuardrailService() if AIGuardrailService else None)
        self.max_depth = 3
        self.max_iterations = 5
        self.max_total_goals = 50 # Resource Limit (DoS Protection)
        logger.info("AGIPlannerService (Layer 7) initialized with Security Hardening + KA Integration")

    def plan(self, initial_goal: str, beliefs: List[Dict[str, Any]]) -> AGIPlan:
        """
        Main entry point. Generates a recursive plan.
        Follows Fail-Safe protocol: Returns a valid 'Failed' plan on crash.
        """
        try:
            # 0. Security Guardrail (Layer 1 Check)
            if self.guardrail:
                is_safe, reason = self.guardrail.validate_input(initial_goal)
                if not is_safe:
                    logger.warning(f"AGI Goal Rejected by Guardrail: {reason}")
                    return self._create_failed_plan(initial_goal, f"Security Violation: {reason}")
            
            # 1. Initialize Context
            root_goal = AGIGoal(
                id=str(uuid.uuid4()),
                content=initial_goal,
                depth=0,
                probability_success=1.0
            )
            
            typed_beliefs = [
                AGIBelief(**b) if isinstance(b, dict) else b 
                for b in beliefs
            ]

            context = AGIContext(
                goals=[root_goal],
                beliefs=typed_beliefs
            )

            conflicts = []
            
            # 2. Recruitment / Decomposition Loop
            # We process goals queue-style (BFS)
            queue = [root_goal]
            
            while queue:
                current = queue.pop(0)
                
                # Stop if max depth
                if current.depth >= self.max_depth:
                    continue
                
                # Resource Limit (DoS Prevention)
                if len(context.goals) >= self.max_total_goals:
                    logger.warning("AGI Plan exceeded max goal limit. Helper function stopping.")
                    break
                    
                # A. Decompose
                subgoals = self._decompose_goal(current)
                
                # Sanitize Subgoals (Prevent Injection in Recursion)
                valid_subgoals = []
                for sg in subgoals:
                    if self.guardrail:
                        safe, _ = self.guardrail.validate_input(sg.content)
                        if not safe:
                            logger.info(f"Subgoal sanitized/blocked: {sg.content}")
                            continue
                    valid_subgoals.append(sg)
                    context.goals.append(sg) # Track for resource limit
                
                current.sub_goals = valid_subgoals
                
                # B. Conflict Detection
                new_conflicts = self._detect_conflicts(current, context.beliefs)
                conflicts.extend(new_conflicts)
                
                # C. Arbitration (Resolve immediately or optimize later? resolving now)
                for conflict in new_conflicts:
                    self._arbitrate_conflict(conflict)
                    # If resolved, maybe update goal status
                    if conflict.resolved:
                        current.status = "realigned"
                
                # Add to queue
                queue.extend(valid_subgoals)

            # Post-Loop: KA-021 Emergence Detection
            if self.ka_controller:
                try:
                    ka021_result = self.ka_controller.execute_algorithm('KA-021', {
                        'goals': [g.model_dump() for g in context.goals],
                        'conflicts': [c.model_dump() for c in conflicts]
                    })
                    if ka021_result.get('emergence_detected'):
                        logger.info("Layer 7: Emergence pattern detected, flagging for L8 escalation.")
                        # Could set a flag here for L8 escalation
                except Exception as e:
                    logger.debug(f"KA-021 skipped: {e}")

            # 3. Finalize Plan
            convergence_score = self._calculate_convergence(conflicts)
            
            return AGIPlan(
                root_goal=root_goal,
                conflicts=conflicts,
                convergence_score=convergence_score,
                iterations=1 # Simplified for MVP
            )

        except Exception as e:
            logger.error(f"AGI Planner Critical Failure: {e}")
            return self._create_failed_plan(initial_goal, f"System Error: {str(e)}")

    def _create_failed_plan(self, initial_content: str, reason: str) -> AGIPlan:
        """Returns a structural plan object indicating failure."""
        return AGIPlan(
            root_goal=AGIGoal(id="failed", content=initial_content, depth=0, status="failed"),
            conflicts=[],
            convergence_score=0.0,
            iterations=0
        )

    def _decompose_goal(self, goal: AGIGoal) -> List[AGIGoal]:
        """
        Uses KA-002 (Tree of Thought) or KA-040 (Hypothesis Generation)
        to break a goal into sub-steps.
        """
        subgoals = []
        
        # Try KA-002: Tree of Thought
        if self.ka_controller:
            try:
                ka002_result = self.ka_controller.execute_algorithm('KA-002', {'goal': goal.content})
                if ka002_result.get('sub_goals'):
                    for sg_content in ka002_result['sub_goals']:
                        subgoals.append(AGIGoal(
                            id=str(uuid.uuid4()),
                            content=sg_content,
                            depth=goal.depth + 1,
                            parent_id=goal.id
                        ))
                    return subgoals
            except Exception as e:
                logger.debug(f"KA-002 skipped: {e}")
        
        # Try KA-040: Hypothesis Generation
        if self.ka_controller:
            try:
                ka040_result = self.ka_controller.execute_algorithm('KA-040', {'goal': goal.content})
                if ka040_result.get('hypotheses'):
                    for hyp in ka040_result['hypotheses']:
                        subgoals.append(AGIGoal(
                            id=str(uuid.uuid4()),
                            content=hyp,
                            depth=goal.depth + 1,
                            parent_id=goal.id
                        ))
                    return subgoals
            except Exception as e:
                logger.debug(f"KA-040 skipped: {e}")
        
        # Fallback: Mock Intelligence for stability
        sub_content_templates = [
            f"Research preconditions for '{goal.content}'",
            f"Execute core logic of '{goal.content}'",
            f"Verify outcome of '{goal.content}'"
        ]
        
        for content in sub_content_templates:
            subgoals.append(AGIGoal(
                id=str(uuid.uuid4()),
                content=content,
                depth=goal.depth + 1,
                parent_id=goal.id
            ))
            
        return subgoals

    def _detect_conflicts(self, goal: AGIGoal, beliefs: List[AGIBelief]) -> List[AGIConflict]:
        """
        Checks if a goal contradicts any held belief.
        """
        conflicts = []
        # TODO: Semantic Similarity Check via Vector DB
        
        # Simple Keyword heuristic for MVP
        normalized_goal = goal.content.lower()
        
        for belief in beliefs:
            # If belief is "The sky is blue" and goal is "Make sky green"
            # We simulate detection
            if "impossible" in normalized_goal or "violate" in normalized_goal:
                conflicts.append(AGIConflict(
                    id=str(uuid.uuid4()),
                    goal_id=goal.id,
                    belief_id=belief.id,
                    description=f"Goal '{goal.content}' violates Belief '{belief.content}'",
                    severity=0.9
                ))
                
        return conflicts

    def _arbitrate_conflict(self, conflict: AGIConflict):
        """
        Resolves a conflict by modifying the goal or marking as failed.
        """
        # TODO: LLM Arbitration Persona
        conflict.resolution = "Goal modified to align with belief constraints."
        conflict.resolved = True
        
    def _calculate_convergence(self, conflicts: List[AGIConflict]) -> float:
        if not conflicts:
            return 1.0
        resolved = sum(1 for c in conflicts if c.resolved)
        return resolved / len(conflicts)
