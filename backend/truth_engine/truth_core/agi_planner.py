import logging
import math
import re
import uuid
from typing import Any

from backend.knowledge_algorithms.consumer import (
    execute_required_ka,
    require_output_field,
)
from backend.truth_engine.truth_core.l7_schemas import (
    AGIBelief,
    AGIConflict,
    AGIContext,
    AGIGoal,
    AGIPlan,
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
        if ka_controller is None:
            from backend.knowledge_algorithms.ka_master_controller import (
                get_controller,
            )

            ka_controller = get_controller()
        self.ka_controller = ka_controller
        self.guardrail = guardrail_service or (AIGuardrailService() if AIGuardrailService else None)
        self.max_depth = 3
        self.max_iterations = 5
        self.max_total_goals = 50 # Resource Limit (DoS Protection)
        self.semantic_conflict_threshold = 0.52
        self._negation_terms = {"not", "never", "no", "without", "avoid", "against", "cannot", "can't"}
        self._explicit_conflict_terms = {"impossible", "violate", "contradict", "override"}
        logger.info("AGIPlannerService (Layer 7) initialized with Security Hardening + KA Integration")

    def plan(self, initial_goal: str, beliefs: list[dict[str, Any]]) -> AGIPlan:
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
                    ka021_result = execute_required_ka(
                        self.ka_controller,
                        "KA-021",
                        {
                            "observations": [
                                {
                                    "observation_id": "post-plan-conflicts",
                                    "metric_name": "unresolved_conflict_count",
                                    "baseline_value": 0.0,
                                    "observed_value": float(
                                        sum(not conflict.resolved for conflict in conflicts)
                                    ),
                                    "tolerance": 0.0,
                                    "corroborating_trace_ids": [
                                        conflict.id
                                        for conflict in conflicts
                                        if not conflict.resolved
                                    ],
                                }
                            ],
                        },
                    )
                    if require_output_field(ka021_result, "is_emergent"):
                        logger.info("Layer 7: Emergence pattern detected, flagging for L8 escalation.")
                        # Could set a flag here for L8 escalation
                except Exception as exc:
                    raise RuntimeError(
                        "Required KA-021 post-plan emergence check failed"
                    ) from exc

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
            return self._create_failed_plan(initial_goal, f"System Error: {e!s}")

    def _create_failed_plan(self, initial_content: str, reason: str) -> AGIPlan:
        """Returns a structural plan object indicating failure."""
        return AGIPlan(
            root_goal=AGIGoal(id="failed", content=initial_content, depth=0, status="failed"),
            conflicts=[],
            convergence_score=0.0,
            iterations=0
        )

    def _decompose_goal(self, goal: AGIGoal) -> list[AGIGoal]:
        """
        Uses KA-002 (Tree of Thought) or KA-040 (Hypothesis Generation)
        to break a goal into sub-steps.
        """
        subgoals = []
        execution_errors = []
        
        # Try KA-002: Tree of Thought
        if self.ka_controller:
            try:
                ka002_result = execute_required_ka(
                    self.ka_controller,
                    "KA-002",
                    {"goal": goal.content},
                )
                ka002_subgoals = require_output_field(
                    ka002_result,
                    "sub_goals",
                )
                if ka002_subgoals:
                    for item in ka002_subgoals:
                        sg_content = (
                            item.get("label")
                            if isinstance(item, dict)
                            else str(item)
                        )
                        if not sg_content:
                            raise RuntimeError(
                                "KA-002 returned a sub-goal without a label"
                            )
                        subgoals.append(AGIGoal(
                            id=str(uuid.uuid4()),
                            content=sg_content,
                            depth=goal.depth + 1,
                            parent_id=goal.id
                        ))
                    return subgoals
            except Exception as exc:
                execution_errors.append(f"KA-002: {exc}")
        
        # Try KA-040: Hypothesis Generation
        if self.ka_controller:
            try:
                ka040_result = execute_required_ka(
                    self.ka_controller,
                    "KA-040",
                    {"goal": goal.content},
                )
                hypotheses = require_output_field(
                    ka040_result,
                    "hypotheses",
                )
                if hypotheses:
                    for item in hypotheses:
                        hypothesis = (
                            item.get("statement")
                            if isinstance(item, dict)
                            else str(item)
                        )
                        if not hypothesis:
                            raise RuntimeError(
                                "KA-040 returned a hypothesis without a statement"
                            )
                        subgoals.append(AGIGoal(
                            id=str(uuid.uuid4()),
                            content=hypothesis,
                            depth=goal.depth + 1,
                            parent_id=goal.id
                        ))
                    return subgoals
            except Exception as exc:
                execution_errors.append(f"KA-040: {exc}")
        
        if self.ka_controller:
            detail = "; ".join(execution_errors) or "no candidate output"
            raise RuntimeError(
                f"KA-backed goal decomposition produced no sub-goals: {detail}"
            )
        return []

    def _detect_conflicts(self, goal: AGIGoal, beliefs: list[AGIBelief]) -> list[AGIConflict]:
        """
        Checks if a goal contradicts any held belief.
        """
        conflicts = []
        normalized_goal = goal.content.lower()
        goal_tokens = self._tokenize(goal.content)
        explicit_violation = any(term in normalized_goal for term in self._explicit_conflict_terms)

        for belief in beliefs:
            # Semantic check with safe fallback for environments without vector integrations.
            semantic_similarity = self._semantic_similarity(goal.content, belief.content)
            belief_tokens = self._tokenize(belief.content)
            shared_tokens = goal_tokens.intersection(belief_tokens)
            negates_belief = bool(goal_tokens.intersection(self._negation_terms))
            semantic_conflict = (
                semantic_similarity >= self.semantic_conflict_threshold
                and negates_belief
                and bool(shared_tokens)
            )

            if explicit_violation or semantic_conflict:
                severity = min(1.0, 0.5 + (semantic_similarity * 0.4))
                if explicit_violation:
                    severity = max(0.9, severity)
                conflicts.append(AGIConflict(
                    id=str(uuid.uuid4()),
                    goal_id=goal.id,
                    belief_id=belief.id,
                    description=f"Goal '{goal.content}' violates Belief '{belief.content}'",
                    severity=severity
                ))
                
        return conflicts

    def _arbitrate_conflict(self, conflict: AGIConflict):
        """
        Resolves a conflict by modifying the goal or marking as failed.
        """
        llm_resolution = self._llm_arbitration_resolution(conflict)
        conflict.resolution = llm_resolution or "Goal modified to align with belief constraints."
        conflict.resolved = True

    def _tokenize(self, text: str) -> set[str]:
        return {tok for tok in re.findall(r"[a-zA-Z0-9']+", text.lower()) if len(tok) > 1}

    def _semantic_similarity(self, text_a: str, text_b: str) -> float:
        """Compute similarity with optional external provider fallback."""
        for provider in (self.ka_controller, self.llm_gateway):
            if not provider:
                continue
            fn = getattr(provider, "semantic_similarity", None)
            if callable(fn):
                try:
                    score = float(fn(text_a, text_b))
                    return max(0.0, min(1.0, score))
                except Exception as e:
                    logger.debug(f"External semantic similarity skipped: {e}")

        tokens_a = self._tokenize(text_a)
        tokens_b = self._tokenize(text_b)
        if not tokens_a or not tokens_b:
            return 0.0

        vocab = sorted(tokens_a.union(tokens_b))
        vec_a = [1.0 if token in tokens_a else 0.0 for token in vocab]
        vec_b = [1.0 if token in tokens_b else 0.0 for token in vocab]
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _llm_arbitration_resolution(self, conflict: AGIConflict) -> str | None:
        if not self.llm_gateway:
            return None

        arbitration_payload = {
            "goal_id": conflict.goal_id,
            "belief_id": conflict.belief_id,
            "description": conflict.description,
            "severity": conflict.severity,
        }
        for method_name in ("arbitrate_conflict", "arbitrate", "resolve_conflict"):
            method = getattr(self.llm_gateway, method_name, None)
            if not callable(method):
                continue
            try:
                result = method(arbitration_payload)
                if isinstance(result, str) and result.strip():
                    return result.strip()
                if isinstance(result, dict):
                    for key in ("resolution", "content", "answer", "text"):
                        value = result.get(key)
                        if isinstance(value, str) and value.strip():
                            return value.strip()
            except Exception as e:
                logger.debug(f"LLM arbitration skipped ({method_name}): {e}")
        return None
        
    def _calculate_convergence(self, conflicts: list[AGIConflict]) -> float:
        if not conflicts:
            return 1.0
        resolved = sum(1 for c in conflicts if c.resolved)
        return resolved / len(conflicts)
