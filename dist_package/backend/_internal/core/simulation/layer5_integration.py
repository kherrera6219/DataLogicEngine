"""
Layer 5: Memory & Analysis Integration Engine

This layer integrates multiple memory sources and analysis results,
performs cross-reference analysis, resolves conflicts between different
memory sources, and provides weighted memory synthesis.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional


class Layer5IntegrationEngine:
    """
    Layer 5: Memory & Analysis Integration Engine

    Integrates outputs from Layers 1-4 (Memory simulation layers and reasoning)
    to create a unified, coherent knowledge base for the simulation.
    """

    def __init__(self, config: Optional[Dict] = None, system_manager=None):
        """
        Initialize the Layer 5 Integration Engine.

        Args:
            config: Optional configuration dictionary
            system_manager: Reference to system manager for accessing memory
        """
        self.config = config or {}
        self.system_manager = system_manager

        # Integration configuration
        self.memory_weight_pillar = self.config.get('memory_weight_pillar', 0.35)
        self.memory_weight_sector = self.config.get('memory_weight_sector', 0.30)
        self.memory_weight_honeycomb = self.config.get('memory_weight_honeycomb', 0.35)

        # Conflict resolution strategy
        self.conflict_strategy = self.config.get(
            'conflict_resolution',
            'weighted_merge'  # Options: weighted_merge, highest_confidence, temporal_priority
        )

        # Integration thresholds
        self.min_confidence_threshold = self.config.get('min_confidence_threshold', 0.3)
        self.cross_reference_threshold = self.config.get('cross_reference_threshold', 0.7)

        # Statistics
        self.stats = {
            'total_integrations': 0,
            'conflicts_resolved': 0,
            'cross_references_found': 0,
            'sources_integrated': 0
        }

        logging.info(f"[{datetime.now()}] Layer5IntegrationEngine initialized")

    def process(self, context: Dict, params: Optional[Dict] = None) -> Dict:
        """
        Process context through Layer 5 integration engine.

        Args:
            context: Simulation context from previous layers
            params: Optional processing parameters

        Returns:
            Enhanced context with integrated memory and analysis
        """
        start_time = datetime.now()

        logging.info(f"[{start_time}] Layer 5: Processing context through integration engine")

        try:
            # Create enhanced context
            enhanced_context = context.copy()

            # Initialize integration metadata
            integration_metadata = {
                'layer': 5,
                'layer_name': 'Memory & Analysis Integration',
                'processing_start': start_time.isoformat(),
                'memory_sources': [],
                'cross_references': [],
                'conflicts': [],
                'integration_confidence': 0.0
            }

            # Step 1: Collect memory from all layers
            memory_collection = self._collect_memory_sources(enhanced_context)
            integration_metadata['memory_sources'] = memory_collection['sources']

            # Step 2: Cross-reference analysis
            cross_references = self._perform_cross_reference_analysis(memory_collection)
            integration_metadata['cross_references'] = cross_references
            self.stats['cross_references_found'] += len(cross_references)

            # Step 3: Detect conflicts between memory sources
            conflicts = self._detect_memory_conflicts(memory_collection)
            integration_metadata['conflicts'] = conflicts

            # Step 4: Resolve conflicts
            if conflicts:
                resolution = self._resolve_memory_conflicts(conflicts, memory_collection)
                integration_metadata['conflict_resolution'] = resolution
                self.stats['conflicts_resolved'] += len(conflicts)
                memory_collection = resolution['unified_memory']

            # Step 5: Integrate reasoning from Layer 4
            if 'layer4_reasoning' in enhanced_context:
                reasoning_integration = self._integrate_reasoning_layer(
                    memory_collection,
                    enhanced_context['layer4_reasoning']
                )
                integration_metadata['reasoning_integration'] = reasoning_integration

            # Step 6: Create unified memory synthesis
            unified_synthesis = self._create_unified_synthesis(
                memory_collection,
                cross_references,
                enhanced_context
            )

            # Step 7: Calculate integration confidence
            integration_confidence = self._calculate_integration_confidence(
                memory_collection,
                cross_references,
                conflicts
            )
            integration_metadata['integration_confidence'] = integration_confidence

            # Step 8: Enhance content if confidence improved
            if integration_confidence > enhanced_context.get('confidence_score', 0):
                enhanced_context['confidence_score'] = integration_confidence
                enhanced_context['content'] = unified_synthesis.get('content', enhanced_context.get('content', ''))

            # Finalize metadata
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            integration_metadata['processing_end'] = end_time.isoformat()
            integration_metadata['processing_time_seconds'] = processing_time

            # Add to context
            enhanced_context['layer5_integration'] = integration_metadata
            enhanced_context['unified_memory'] = unified_synthesis

            # Update stats
            self.stats['total_integrations'] += 1
            self.stats['sources_integrated'] += len(integration_metadata['memory_sources'])

            logging.info(
                f"[{end_time}] Layer 5: Completed in {processing_time:.2f}s. "
                f"Sources: {len(integration_metadata['memory_sources'])}, "
                f"Cross-refs: {len(cross_references)}, "
                f"Conflicts: {len(conflicts)}, "
                f"Confidence: {integration_confidence:.3f}"
            )

            return enhanced_context

        except Exception as e:
            logging.error(f"[{datetime.now()}] Layer 5: Error in integration engine: {str(e)}")
            # Return original context with error flag
            context['layer5_error'] = str(e)
            return context

    def _collect_memory_sources(self, context: Dict) -> Dict:
        """
        Collect memory from all available sources (Layers 1-3).

        Args:
            context: Current context

        Returns:
            Dict containing all memory sources
        """
        sources = []

        # Collect from Layer 1: Pillar memory
        if 'layer1_memory' in context:
            sources.append({
                'layer': 1,
                'type': 'pillar_memory',
                'weight': self.memory_weight_pillar,
                'data': context['layer1_memory'],
                'confidence': context['layer1_memory'].get('confidence', 0.5)
            })

        # Collect from Layer 2: Sector memory
        if 'layer2_memory' in context:
            sources.append({
                'layer': 2,
                'type': 'sector_memory',
                'weight': self.memory_weight_sector,
                'data': context['layer2_memory'],
                'confidence': context['layer2_memory'].get('confidence', 0.5)
            })

        # Collect from Layer 3: Honeycomb memory
        if 'layer3_memory' in context:
            sources.append({
                'layer': 3,
                'type': 'honeycomb_memory',
                'weight': self.memory_weight_honeycomb,
                'data': context['layer3_memory'],
                'confidence': context['layer3_memory'].get('confidence', 0.5)
            })

        return {'sources': sources, 'total_sources': len(sources)}

    def _perform_cross_reference_analysis(self, memory_collection: Dict) -> List[Dict]:
        """
        Perform cross-reference analysis between memory sources.

        Args:
            memory_collection: Collection of memory sources

        Returns:
            List of cross-references found
        """
        cross_references = []
        sources = memory_collection['sources']

        # Compare each pair of sources
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                source_a = sources[i]
                source_b = sources[j]

                # Find overlapping information
                overlap = self._find_overlap(source_a, source_b)

                if overlap['similarity'] > self.cross_reference_threshold:
                    cross_references.append({
                        'source_a': source_a['type'],
                        'source_b': source_b['type'],
                        'similarity': overlap['similarity'],
                        'common_elements': overlap['common_elements'],
                        'reinforces': True
                    })

        return cross_references

    def _find_overlap(self, source_a: Dict, source_b: Dict) -> Dict:
        """
        Find overlap between two memory sources.

        Args:
            source_a: First memory source
            source_b: Second memory source

        Returns:
            Dict with overlap information
        """
        # Simplified overlap detection based on confidence similarity
        conf_a = source_a.get('confidence', 0.5)
        conf_b = source_b.get('confidence', 0.5)

        # Calculate similarity
        similarity = 1.0 - abs(conf_a - conf_b)

        return {
            'similarity': similarity,
            'common_elements': ['confidence_alignment'] if similarity > 0.7 else []
        }

    def _detect_memory_conflicts(self, memory_collection: Dict) -> List[Dict]:
        """
        Detect conflicts between memory sources.

        Args:
            memory_collection: Collection of memory sources

        Returns:
            List of conflicts detected
        """
        conflicts = []
        sources = memory_collection['sources']

        # Check for confidence divergence
        if len(sources) >= 2:
            confidences = [s['confidence'] for s in sources]
            std_dev = self._calculate_std_dev(confidences)

            if std_dev > 0.3:
                conflicts.append({
                    'type': 'confidence_divergence',
                    'sources': [s['type'] for s in sources],
                    'confidences': confidences,
                    'divergence': std_dev,
                    'severity': 'medium' if std_dev < 0.5 else 'high'
                })

        return conflicts

    def _resolve_memory_conflicts(self, conflicts: List[Dict], memory_collection: Dict) -> Dict:
        """
        Resolve conflicts between memory sources.

        Args:
            conflicts: List of detected conflicts
            memory_collection: Memory collection with conflicts

        Returns:
            Dict with resolved conflicts and unified memory
        """
        resolution = {
            'strategy': self.conflict_strategy,
            'conflicts_resolved': len(conflicts),
            'resolutions': []
        }

        sources = memory_collection['sources']

        if self.conflict_strategy == 'weighted_merge':
            # Use weighted average based on source weights
            total_weight = sum(s['weight'] for s in sources)
            weighted_confidence = sum(
                s['confidence'] * s['weight'] for s in sources
            ) / total_weight

            resolution['resolutions'].append({
                'method': 'weighted_average',
                'result_confidence': weighted_confidence,
                'weights_used': {s['type']: s['weight'] for s in sources}
            })

            # Update source confidences
            for source in sources:
                source['unified_confidence'] = weighted_confidence

        elif self.conflict_strategy == 'highest_confidence':
            # Choose source with highest confidence
            best_source = max(sources, key=lambda s: s['confidence'])
            resolution['resolutions'].append({
                'method': 'highest_confidence',
                'chosen_source': best_source['type'],
                'confidence': best_source['confidence']
            })

        resolution['unified_memory'] = memory_collection

        return resolution

    def _integrate_reasoning_layer(self, memory_collection: Dict, reasoning_data: Dict) -> Dict:
        """
        Integrate reasoning from Layer 4 with memory sources.

        Args:
            memory_collection: Memory collection
            reasoning_data: Data from Layer 4 reasoning

        Returns:
            Dict with integration results
        """
        integration = {
            'inferences_applied': reasoning_data.get('total_inferences', 0),
            'rules_applied': len(reasoning_data.get('rules_applied', [])),
            'reasoning_confidence_adjustment': 0.0
        }

        # Check if reasoning supports memory
        deductive_inferences = reasoning_data.get('deductive_inferences', [])
        if deductive_inferences:
            # Boost confidence if reasoning supports memory
            integration['reasoning_confidence_adjustment'] = 0.05 * len(deductive_inferences)

        return integration

    def _create_unified_synthesis(
        self,
        memory_collection: Dict,
        cross_references: List[Dict],
        context: Dict
    ) -> Dict:
        """
        Create unified synthesis from all integrated sources.

        Args:
            memory_collection: Memory collection
            cross_references: Cross-references found
            context: Current context

        Returns:
            Dict with unified synthesis
        """
        synthesis = {
            'timestamp': datetime.now().isoformat(),
            'sources': [s['type'] for s in memory_collection['sources']],
            'cross_reference_count': len(cross_references),
            'content': '',
            'confidence': 0.0
        }

        # Build content from sources
        content_parts = []

        for source in memory_collection['sources']:
            source_content = source['data'].get('content', '')
            if source_content:
                content_parts.append(f"[{source['type'].replace('_', ' ').title()}]\n{source_content}")

        # Add synthesis from context if available
        if 'synthesis' in context:
            context_synthesis = context['synthesis'].get('content', '')
            if context_synthesis:
                content_parts.append(f"\n[Integrated Analysis]\n{context_synthesis}")

        synthesis['content'] = '\n\n'.join(content_parts)

        # Calculate unified confidence
        sources = memory_collection['sources']
        if sources:
            total_weight = sum(s['weight'] for s in sources)
            synthesis['confidence'] = sum(
                s['confidence'] * s['weight'] for s in sources
            ) / total_weight

            # Boost for cross-references
            if cross_references:
                boost = min(0.1, 0.02 * len(cross_references))
                synthesis['confidence'] = min(1.0, synthesis['confidence'] + boost)

        return synthesis

    def _calculate_integration_confidence(
        self,
        memory_collection: Dict,
        cross_references: List[Dict],
        conflicts: List[Dict]
    ) -> float:
        """
        Calculate overall integration confidence.

        Args:
            memory_collection: Memory collection
            cross_references: Cross-references found
            conflicts: Conflicts detected

        Returns:
            Integration confidence score
        """
        sources = memory_collection['sources']

        if not sources:
            return 0.0

        # Base confidence from weighted sources
        total_weight = sum(s['weight'] for s in sources)
        base_confidence = sum(
            s['confidence'] * s['weight'] for s in sources
        ) / total_weight

        # Boost for cross-references (they reinforce confidence)
        cross_ref_boost = min(0.15, 0.03 * len(cross_references))

        # Penalty for unresolved conflicts
        conflict_penalty = 0.05 * len(conflicts)

        # Calculate final confidence
        final_confidence = base_confidence + cross_ref_boost - conflict_penalty

        return max(0.0, min(1.0, final_confidence))

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
