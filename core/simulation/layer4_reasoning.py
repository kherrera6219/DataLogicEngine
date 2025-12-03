"""
Layer 4: Reasoning & Logic Engine

This layer applies logical reasoning and inference to simulation context,
including deductive reasoning, inductive reasoning, rule-based logic,
and conflict resolution.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set


class Layer4ReasoningEngine:
    """
    Layer 4: Reasoning & Logic Engine

    Applies logical reasoning, inference, and rule-based processing
    to enhance simulation context with logical conclusions.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the Layer 4 Reasoning Engine.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

        # Reasoning configuration
        self.enable_deductive = self.config.get('enable_deductive_reasoning', True)
        self.enable_inductive = self.config.get('enable_inductive_reasoning', True)
        self.enable_abductive = self.config.get('enable_abductive_reasoning', True)
        self.enable_rule_based = self.config.get('enable_rule_based_reasoning', True)

        # Confidence thresholds
        self.deductive_confidence = self.config.get('deductive_confidence', 0.95)
        self.inductive_confidence = self.config.get('inductive_confidence', 0.75)
        self.abductive_confidence = self.config.get('abductive_confidence', 0.65)

        # Conflict resolution
        self.conflict_resolution_strategy = self.config.get(
            'conflict_resolution_strategy',
            'weighted_vote'  # Options: weighted_vote, highest_confidence, consensus
        )

        # Rule base
        self.rules = self._initialize_rules()

        # Statistics
        self.stats = {
            'total_inferences': 0,
            'deductive_inferences': 0,
            'inductive_inferences': 0,
            'abductive_inferences': 0,
            'conflicts_resolved': 0,
            'rules_applied': 0
        }

        logging.info(f"[{datetime.now()}] Layer4ReasoningEngine initialized")

    def _initialize_rules(self) -> List[Dict]:
        """Initialize rule base for rule-based reasoning."""
        return [
            {
                'id': 'R001',
                'name': 'High Confidence Propagation',
                'condition': lambda ctx: ctx.get('confidence_score', 0) > 0.9,
                'action': lambda ctx: self._propagate_high_confidence(ctx),
                'priority': 1
            },
            {
                'id': 'R002',
                'name': 'Low Confidence Enhancement',
                'condition': lambda ctx: ctx.get('confidence_score', 0) < 0.5,
                'action': lambda ctx: self._enhance_low_confidence(ctx),
                'priority': 2
            },
            {
                'id': 'R003',
                'name': 'Conflicting Information Detection',
                'condition': lambda ctx: self._has_conflicts(ctx),
                'action': lambda ctx: self._resolve_conflicts(ctx),
                'priority': 1
            },
            {
                'id': 'R004',
                'name': 'Missing Context Detection',
                'condition': lambda ctx: self._has_missing_context(ctx),
                'action': lambda ctx: self._flag_missing_context(ctx),
                'priority': 3
            }
        ]

    def process(self, context: Dict) -> Dict:
        """
        Process context through Layer 4 reasoning engine.

        Args:
            context: Simulation context from previous layers

        Returns:
            Enhanced context with logical reasoning applied
        """
        start_time = datetime.now()

        logging.info(f"[{start_time}] Layer 4: Processing context through reasoning engine")

        try:
            # Create enhanced context
            enhanced_context = context.copy()

            # Initialize reasoning metadata
            reasoning_metadata = {
                'layer': 4,
                'layer_name': 'Reasoning & Logic Engine',
                'processing_start': start_time.isoformat(),
                'inferences': [],
                'rules_applied': [],
                'conflicts_resolved': [],
                'confidence_adjustments': []
            }

            # Step 1: Apply deductive reasoning
            if self.enable_deductive:
                deductive_results = self._apply_deductive_reasoning(enhanced_context)
                enhanced_context = deductive_results['context']
                reasoning_metadata['deductive_inferences'] = deductive_results['inferences']
                self.stats['deductive_inferences'] += len(deductive_results['inferences'])

            # Step 2: Apply inductive reasoning
            if self.enable_inductive:
                inductive_results = self._apply_inductive_reasoning(enhanced_context)
                enhanced_context = inductive_results['context']
                reasoning_metadata['inductive_inferences'] = inductive_results['inferences']
                self.stats['inductive_inferences'] += len(inductive_results['inferences'])

            # Step 3: Apply abductive reasoning (inference to best explanation)
            if self.enable_abductive:
                abductive_results = self._apply_abductive_reasoning(enhanced_context)
                enhanced_context = abductive_results['context']
                reasoning_metadata['abductive_inferences'] = abductive_results['inferences']
                self.stats['abductive_inferences'] += len(abductive_results['inferences'])

            # Step 4: Apply rule-based reasoning
            if self.enable_rule_based:
                rule_results = self._apply_rule_based_reasoning(enhanced_context)
                enhanced_context = rule_results['context']
                reasoning_metadata['rules_applied'] = rule_results['rules_applied']
                self.stats['rules_applied'] += len(rule_results['rules_applied'])

            # Step 5: Detect and resolve conflicts
            conflict_results = self._detect_and_resolve_conflicts(enhanced_context)
            enhanced_context = conflict_results['context']
            reasoning_metadata['conflicts_resolved'] = conflict_results['conflicts']
            self.stats['conflicts_resolved'] += len(conflict_results['conflicts'])

            # Step 6: Adjust confidence based on logical consistency
            confidence_adjustment = self._adjust_confidence_for_consistency(enhanced_context)
            enhanced_context['confidence_score'] = confidence_adjustment['new_confidence']
            reasoning_metadata['confidence_adjustments'].append(confidence_adjustment)

            # Finalize metadata
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            reasoning_metadata['processing_end'] = end_time.isoformat()
            reasoning_metadata['processing_time_seconds'] = processing_time
            reasoning_metadata['total_inferences'] = (
                len(reasoning_metadata.get('deductive_inferences', [])) +
                len(reasoning_metadata.get('inductive_inferences', [])) +
                len(reasoning_metadata.get('abductive_inferences', []))
            )

            # Add to context
            enhanced_context['layer4_reasoning'] = reasoning_metadata

            # Update stats
            self.stats['total_inferences'] += reasoning_metadata['total_inferences']

            logging.info(
                f"[{end_time}] Layer 4: Completed in {processing_time:.2f}s. "
                f"Inferences: {reasoning_metadata['total_inferences']}, "
                f"Rules: {len(reasoning_metadata['rules_applied'])}, "
                f"Conflicts: {len(reasoning_metadata['conflicts_resolved'])}"
            )

            return enhanced_context

        except Exception as e:
            logging.error(f"[{datetime.now()}] Layer 4: Error in reasoning engine: {str(e)}")
            # Return original context with error flag
            context['layer4_error'] = str(e)
            return context

    def _apply_deductive_reasoning(self, context: Dict) -> Dict:
        """
        Apply deductive reasoning (general principles to specific conclusions).

        Args:
            context: Current context

        Returns:
            Dict with context and inferences
        """
        inferences = []

        # Get synthesis from previous layers
        synthesis = context.get('synthesis', {})
        perspectives = synthesis.get('perspectives', [])

        # Deductive rule: If all perspectives agree, conclusion is highly confident
        if len(perspectives) >= 2:
            # Check for agreement
            agreement_score = self._calculate_agreement(perspectives)

            if agreement_score > 0.8:
                inference = {
                    'type': 'deductive',
                    'premise': 'All expert perspectives are in agreement',
                    'conclusion': 'High confidence in synthesized response',
                    'confidence': self.deductive_confidence,
                    'evidence': [p['persona_id'] for p in perspectives]
                }
                inferences.append(inference)

                # Boost overall confidence
                current_confidence = context.get('confidence_score', 0.5)
                context['confidence_score'] = min(1.0, current_confidence * 1.1)

        # Deductive rule: If high confidence in memory layers, propagate forward
        memory_confidence = context.get('memory_confidence', 0.5)
        if memory_confidence > 0.85:
            inference = {
                'type': 'deductive',
                'premise': 'Memory layers show high confidence',
                'conclusion': 'Historical knowledge strongly supports response',
                'confidence': self.deductive_confidence,
                'evidence': {'memory_confidence': memory_confidence}
            }
            inferences.append(inference)

        return {'context': context, 'inferences': inferences}

    def _apply_inductive_reasoning(self, context: Dict) -> Dict:
        """
        Apply inductive reasoning (specific observations to general patterns).

        Args:
            context: Current context

        Returns:
            Dict with context and inferences
        """
        inferences = []

        # Get persona results
        persona_results = context.get('persona_results', {})

        # Inductive rule: If multiple personas show similar patterns, infer general trend
        if len(persona_results) >= 3:
            # Look for common themes
            common_themes = self._identify_common_themes(persona_results)

            for theme in common_themes:
                inference = {
                    'type': 'inductive',
                    'observations': theme['occurrences'],
                    'pattern': theme['pattern'],
                    'generalization': theme['generalization'],
                    'confidence': self.inductive_confidence * theme['support'],
                    'evidence': theme['sources']
                }
                inferences.append(inference)

        # Inductive rule: Past performance predicts future results
        simulation_pass = context.get('simulation_pass', 1)
        if simulation_pass > 1:
            # Look at historical confidence
            historical_confidence = context.get('historical_confidence', [])
            if historical_confidence:
                trend = self._calculate_trend(historical_confidence)

                if trend != 'stable':
                    inference = {
                        'type': 'inductive',
                        'observations': f"Confidence trend across {len(historical_confidence)} passes",
                        'pattern': trend,
                        'generalization': f"Confidence is {trend}",
                        'confidence': self.inductive_confidence,
                        'evidence': {'historical_confidence': historical_confidence}
                    }
                    inferences.append(inference)

        return {'context': context, 'inferences': inferences}

    def _apply_abductive_reasoning(self, context: Dict) -> Dict:
        """
        Apply abductive reasoning (inference to best explanation).

        Args:
            context: Current context

        Returns:
            Dict with context and inferences
        """
        inferences = []

        # Get uncertainty level
        uncertainty = context.get('uncertainty_level', 0.0)

        # Abductive rule: If high uncertainty, infer need for more information
        if uncertainty > 0.5:
            inference = {
                'type': 'abductive',
                'observation': f"High uncertainty level: {uncertainty:.2f}",
                'best_explanation': 'Insufficient information or conflicting evidence',
                'recommendation': 'Consider additional knowledge sources or expert consultation',
                'confidence': self.abductive_confidence,
                'evidence': {'uncertainty_level': uncertainty}
            }
            inferences.append(inference)

        # Abductive rule: If low confidence in specific personas, explain why
        persona_results = context.get('persona_results', {})
        for persona_id, result in persona_results.items():
            persona_confidence = result.get('confidence', 0.5)

            if persona_confidence < 0.4:
                inference = {
                    'type': 'abductive',
                    'observation': f"Low confidence for {persona_id} persona: {persona_confidence:.2f}",
                    'best_explanation': f"{persona_id.capitalize()} expertise may be limited for this query",
                    'recommendation': f"Seek additional {persona_id} expert input",
                    'confidence': self.abductive_confidence,
                    'evidence': {'persona': persona_id, 'confidence': persona_confidence}
                }
                inferences.append(inference)

        return {'context': context, 'inferences': inferences}

    def _apply_rule_based_reasoning(self, context: Dict) -> Dict:
        """
        Apply rule-based reasoning using predefined rules.

        Args:
            context: Current context

        Returns:
            Dict with context and rules applied
        """
        rules_applied = []

        # Sort rules by priority
        sorted_rules = sorted(self.rules, key=lambda r: r['priority'])

        # Apply each rule
        for rule in sorted_rules:
            try:
                # Check condition
                if rule['condition'](context):
                    # Apply action
                    context = rule['action'](context)

                    # Record rule application
                    rules_applied.append({
                        'rule_id': rule['id'],
                        'rule_name': rule['name'],
                        'priority': rule['priority'],
                        'applied_at': datetime.now().isoformat()
                    })

                    logging.debug(f"[{datetime.now()}] Layer 4: Applied rule {rule['id']}: {rule['name']}")
            except Exception as e:
                logging.warning(f"[{datetime.now()}] Layer 4: Error applying rule {rule['id']}: {str(e)}")

        return {'context': context, 'rules_applied': rules_applied}

    def _detect_and_resolve_conflicts(self, context: Dict) -> Dict:
        """
        Detect and resolve conflicts in context.

        Args:
            context: Current context

        Returns:
            Dict with context and resolved conflicts
        """
        conflicts = []

        # Check for conflicting persona results
        persona_results = context.get('persona_results', {})

        if len(persona_results) >= 2:
            # Compare perspectives for conflicts
            perspectives = []
            for persona_id, result in persona_results.items():
                if result.get('status') == 'completed':
                    perspectives.append({
                        'persona_id': persona_id,
                        'confidence': result.get('confidence', 0.5),
                        'response': result.get('response', {})
                    })

            # Detect conflicts
            detected_conflicts = self._find_conflicts(perspectives)

            # Resolve each conflict
            for conflict in detected_conflicts:
                resolution = self._resolve_conflict(conflict, self.conflict_resolution_strategy)
                conflicts.append(resolution)

                logging.info(
                    f"[{datetime.now()}] Layer 4: Resolved conflict between "
                    f"{conflict['personas']} using {self.conflict_resolution_strategy}"
                )

        return {'context': context, 'conflicts': conflicts}

    def _find_conflicts(self, perspectives: List[Dict]) -> List[Dict]:
        """Find conflicts between perspectives."""
        conflicts = []

        # Simple conflict detection based on confidence divergence
        if len(perspectives) >= 2:
            confidences = [p['confidence'] for p in perspectives]
            confidence_std = self._calculate_std_dev(confidences)

            # If high variance in confidence, flag as potential conflict
            if confidence_std > 0.3:
                conflicts.append({
                    'type': 'confidence_divergence',
                    'personas': [p['persona_id'] for p in perspectives],
                    'confidences': confidences,
                    'divergence': confidence_std,
                    'perspectives': perspectives
                })

        return conflicts

    def _resolve_conflict(self, conflict: Dict, strategy: str) -> Dict:
        """
        Resolve a conflict using specified strategy.

        Args:
            conflict: Conflict data
            strategy: Resolution strategy

        Returns:
            Resolution result
        """
        resolution = {
            'conflict_type': conflict['type'],
            'strategy': strategy,
            'resolved_at': datetime.now().isoformat()
        }

        perspectives = conflict['perspectives']

        if strategy == 'highest_confidence':
            # Choose perspective with highest confidence
            winner = max(perspectives, key=lambda p: p['confidence'])
            resolution['chosen_perspective'] = winner['persona_id']
            resolution['confidence'] = winner['confidence']

        elif strategy == 'weighted_vote':
            # Weight by confidence and average
            total_weight = sum(p['confidence'] for p in perspectives)
            if total_weight > 0:
                weighted_confidence = sum(
                    p['confidence'] * p['confidence'] for p in perspectives
                ) / total_weight
                resolution['weighted_confidence'] = weighted_confidence
                resolution['participating_personas'] = [p['persona_id'] for p in perspectives]

        elif strategy == 'consensus':
            # Require minimum threshold agreement
            avg_confidence = sum(p['confidence'] for p in perspectives) / len(perspectives)
            resolution['consensus_confidence'] = avg_confidence
            resolution['consensus_reached'] = avg_confidence > 0.6

        return resolution

    def _adjust_confidence_for_consistency(self, context: Dict) -> Dict:
        """
        Adjust overall confidence based on logical consistency.

        Args:
            context: Current context

        Returns:
            Dict with adjustment info
        """
        current_confidence = context.get('confidence_score', 0.5)

        # Factors that affect confidence
        factors = []

        # Factor 1: Agreement between personas
        persona_results = context.get('persona_results', {})
        if persona_results:
            confidences = [r.get('confidence', 0.5) for r in persona_results.values()]
            agreement = 1.0 - self._calculate_std_dev(confidences)
            factors.append(('persona_agreement', agreement))

        # Factor 2: Logical consistency (number of conflicts)
        conflicts = context.get('layer4_reasoning', {}).get('conflicts_resolved', [])
        conflict_penalty = 0.05 * len(conflicts)
        factors.append(('conflict_penalty', -conflict_penalty))

        # Factor 3: Number of successful inferences
        total_inferences = context.get('layer4_reasoning', {}).get('total_inferences', 0)
        inference_boost = min(0.1, 0.02 * total_inferences)
        factors.append(('inference_boost', inference_boost))

        # Calculate adjustment
        total_adjustment = sum(f[1] for f in factors)
        new_confidence = max(0.0, min(1.0, current_confidence + total_adjustment))

        return {
            'old_confidence': current_confidence,
            'new_confidence': new_confidence,
            'adjustment': total_adjustment,
            'factors': factors
        }

    # Helper methods

    def _propagate_high_confidence(self, context: Dict) -> Dict:
        """Propagate high confidence through context."""
        context['high_confidence_flag'] = True
        return context

    def _enhance_low_confidence(self, context: Dict) -> Dict:
        """Flag low confidence for enhancement."""
        context['needs_enhancement'] = True
        context['enhancement_reason'] = 'Low confidence score'
        return context

    def _has_conflicts(self, context: Dict) -> bool:
        """Check if context has conflicts."""
        persona_results = context.get('persona_results', {})
        if len(persona_results) < 2:
            return False

        confidences = [r.get('confidence', 0.5) for r in persona_results.values()]
        return self._calculate_std_dev(confidences) > 0.3

    def _has_missing_context(self, context: Dict) -> bool:
        """Check if context is missing important information."""
        # Check for high uncertainty
        return context.get('uncertainty_level', 0.0) > 0.7

    def _flag_missing_context(self, context: Dict) -> Dict:
        """Flag missing context."""
        context['missing_context_flag'] = True
        return context

    def _calculate_agreement(self, perspectives: List[Dict]) -> float:
        """Calculate agreement score between perspectives."""
        if not perspectives:
            return 0.0

        confidences = [p.get('confidence', 0.5) for p in perspectives]
        # High agreement = low standard deviation
        return 1.0 - self._calculate_std_dev(confidences)

    def _identify_common_themes(self, persona_results: Dict) -> List[Dict]:
        """Identify common themes across persona results."""
        # Simplified theme detection
        themes = []

        # Count personas with high confidence
        high_confidence_count = sum(
            1 for r in persona_results.values()
            if r.get('confidence', 0) > 0.7
        )

        if high_confidence_count >= 2:
            themes.append({
                'pattern': 'high_confidence_consensus',
                'occurrences': high_confidence_count,
                'generalization': 'Multiple experts show high confidence',
                'support': min(1.0, high_confidence_count / len(persona_results)),
                'sources': [
                    k for k, v in persona_results.items()
                    if v.get('confidence', 0) > 0.7
                ]
            })

        return themes

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from list of values."""
        if len(values) < 2:
            return 'stable'

        # Simple trend detection
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

        diff = second_half - first_half

        if diff > 0.1:
            return 'increasing'
        elif diff < -0.1:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if not values:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def get_stats(self) -> Dict:
        """Get engine statistics."""
        return self.stats.copy()
