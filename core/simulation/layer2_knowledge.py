"""
Layer 2: Knowledge Integration Layer (Knowledge Expansion)

This layer expands and enriches context by traversing knowledge graph links.
It retrieves related knowledge nodes along each relevant axis and broadens
context with relevant information branches.

Algorithms:
- KA-04: Honeycomb Expansion
- KA-05: Contextual Relevance
- KA-06: Coordinate Mapper
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class Layer2KnowledgeEngine:
    """
    Layer 2: Knowledge Integration Layer - Knowledge Expansion
    
    Purpose: Expand and enrich context by traversing knowledge graph links.
    
    Actions:
    - Retrieve related knowledge nodes along each relevant axis (temporal, spatial, etc.)
    - Broaden context with relevant information branches
    """
    
    def __init__(self, config: Optional[Dict] = None, graph_manager=None):
        """
        Initialize Layer 2 Knowledge Engine.
        
        Args:
            config: Optional configuration dictionary
            graph_manager: Optional graph manager for knowledge traversal
        """
        self.config = config or {}
        self.graph_manager = graph_manager
        
        self.expansion_depth = self.config.get('expansion_depth', 3)
        self.max_nodes_per_axis = self.config.get('max_nodes_per_axis', 10)
        self.relevance_threshold = self.config.get('relevance_threshold', 0.3)
        
        self.honeycomb_mappings = self._initialize_honeycomb_mappings()
        
        self.stats = {
            'expansions_performed': 0,
            'nodes_retrieved': 0,
            'cross_domain_links': 0
        }
        
        logger.info(f"[{datetime.now()}] Layer2KnowledgeEngine initialized")
    
    def _initialize_honeycomb_mappings(self) -> Dict[str, List[str]]:
        """Initialize honeycomb cross-domain mappings."""
        return {
            'acquisition_technology': ['software procurement', 'it services', 'cloud computing'],
            'acquisition_finance': ['contract pricing', 'cost analysis', 'budget allocation'],
            'technology_security': ['cybersecurity', 'data protection', 'access control'],
            'healthcare_technology': ['health IT', 'medical devices', 'telemedicine'],
            'defense_acquisition': ['defense contracts', 'weapon systems', 'military procurement'],
            'finance_compliance': ['financial regulations', 'audit requirements', 'reporting standards'],
            'legal_regulatory': ['statutory requirements', 'case law', 'regulatory interpretation']
        }
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context through Layer 2 knowledge expansion.
        
        Args:
            context: Input context from Layer 1
            
        Returns:
            Enhanced context with expanded knowledge
        """
        start_time = datetime.now(UTC)
        
        logger.info(f"[{start_time}] Layer 2: Processing context for knowledge expansion")
        
        enhanced_context = context.copy()
        
        layer2_metadata = {
            'layer': 2,
            'layer_name': 'Knowledge Integration Layer (Knowledge Expansion)',
            'processing_start': start_time.isoformat(),
            'expanded_nodes': [],
            'cross_domain_links': []
        }
        
        axis_scores = context.get('axis_scores', {})
        pillar_context = context.get('pillar_context', {})
        expansion_params = context.get('layer1_entry', {}).get('knowledge_expansion', {})
        
        expanded_axes = self._expand_along_axes(axis_scores, expansion_params)
        layer2_metadata['expanded_axes'] = expanded_axes
        
        cross_domain = self._find_cross_domain_links(pillar_context, axis_scores)
        layer2_metadata['cross_domain_links'] = cross_domain
        
        information_branches = self._broaden_context(expanded_axes, cross_domain, pillar_context)
        layer2_metadata['information_branches'] = information_branches
        
        enriched_knowledge = self._aggregate_knowledge(expanded_axes, cross_domain, information_branches)
        layer2_metadata['enriched_knowledge'] = enriched_knowledge
        
        layer2_metadata['processing_end'] = datetime.now(UTC).isoformat()
        layer2_metadata['processing_duration_ms'] = (datetime.now(UTC) - start_time).total_seconds() * 1000
        
        layer_confidence = self._calculate_layer_confidence(expanded_axes, cross_domain)
        layer2_metadata['layer_confidence'] = layer_confidence
        
        enhanced_context['layer2_knowledge'] = layer2_metadata
        enhanced_context['enriched_knowledge'] = enriched_knowledge
        enhanced_context['cross_domain_links'] = cross_domain
        
        self.stats['expansions_performed'] += 1
        self.stats['nodes_retrieved'] += len(enriched_knowledge.get('nodes', []))
        self.stats['cross_domain_links'] += len(cross_domain)
        
        logger.info(f"[{datetime.now()}] Layer 2 complete. Confidence: {layer_confidence:.3f}")
        
        return enhanced_context
    
    def _expand_along_axes(self, axis_scores: Dict[int, float],
                           expansion_params: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
        """
        Expand knowledge along each relevant axis.
        
        Args:
            axis_scores: Relevance scores for each axis
            expansion_params: Parameters from Layer 1
            
        Returns:
            Expanded nodes for each axis
        """
        expanded_axes = {}
        target_axes = expansion_params.get('target_axes', [])
        
        for axis_num, score in axis_scores.items():
            if score < self.relevance_threshold and axis_num not in target_axes:
                continue
            
            axis_expansion = {
                'axis_number': axis_num,
                'relevance_score': score,
                'nodes': [],
                'relationships': []
            }
            
            if self.graph_manager:
                nodes = self._retrieve_axis_nodes(axis_num, score)
                axis_expansion['nodes'] = nodes
            else:
                axis_expansion['nodes'] = self._generate_mock_nodes(axis_num, score)
            
            expanded_axes[axis_num] = axis_expansion
        
        return expanded_axes
    
    def _retrieve_axis_nodes(self, axis_num: int, relevance: float) -> List[Dict[str, Any]]:
        """
        Retrieve knowledge nodes for a specific axis from the graph.
        
        Args:
            axis_num: The axis number
            relevance: Relevance score for prioritization
            
        Returns:
            List of retrieved nodes
        """
        if self.graph_manager:
            try:
                return self.graph_manager.get_nodes_by_axis(axis_num, limit=self.max_nodes_per_axis)
            except Exception as e:
                logger.warning(f"Error retrieving nodes for axis {axis_num}: {e}")
        
        return []
    
    def _generate_mock_nodes(self, axis_num: int, relevance: float) -> List[Dict[str, Any]]:
        """
        Generate placeholder nodes when graph is unavailable.
        
        Args:
            axis_num: The axis number
            relevance: Relevance score
            
        Returns:
            List of mock nodes
        """
        axis_names = {
            1: 'Temporal', 2: 'Spatial', 3: 'Semantic', 4: 'Procedural',
            5: 'Analytical', 6: 'Normative', 7: 'Risk/Impact', 8: 'Performance',
            9: 'Expertise', 10: 'Ethical', 11: 'Regulatory', 12: 'Compliance',
            13: 'Simulation', 14: 'AI-Generated', 15: 'Cultural/Social',
            16: 'Innovation', 17: 'Learning'
        }
        
        num_nodes = max(1, int(relevance * 5))
        
        return [
            {
                'node_id': f'axis_{axis_num}_node_{i}',
                'axis': axis_num,
                'axis_name': axis_names.get(axis_num, f'Axis {axis_num}'),
                'relevance': relevance * (1 - i * 0.1),
                'type': 'knowledge_node',
                'generated': True
            }
            for i in range(num_nodes)
        ]
    
    def _find_cross_domain_links(self, pillar_context: Dict[str, Any],
                                  axis_scores: Dict[int, float]) -> List[Dict[str, Any]]:
        """
        Find cross-domain links using honeycomb expansion.
        
        Args:
            pillar_context: Pillar context from Layer 1
            axis_scores: Axis relevance scores
            
        Returns:
            List of cross-domain link opportunities
        """
        cross_domain_links = []
        
        primary_pillar = pillar_context.get('primary_pillar', '')
        matched_pillars = [p['pillar'] for p in pillar_context.get('matched_pillars', [])]

        live_links = self._find_live_graph_links(primary_pillar, matched_pillars)
        if live_links:
            return live_links
        
        for mapping_key, concepts in self.honeycomb_mappings.items():
            pillars_in_mapping = mapping_key.split('_')
            
            relevance = 0
            for pillar in pillars_in_mapping:
                if pillar == primary_pillar:
                    relevance += 0.6
                elif pillar in matched_pillars:
                    relevance += 0.3
            
            if relevance > 0.3:
                cross_domain_links.append({
                    'mapping_key': mapping_key,
                    'concepts': concepts,
                    'relevance': min(1.0, relevance),
                    'source_pillars': pillars_in_mapping
                })
        
        return sorted(cross_domain_links, key=lambda x: x['relevance'], reverse=True)

    def _find_live_graph_links(self, primary_pillar: str, matched_pillars: List[str]) -> List[Dict[str, Any]]:
        """Prefer the live USKD memory graph when it has relevant anchors."""
        try:
            from backend.storage import get_uskd_memory_graph

            graph = get_uskd_memory_graph()
            anchors = []
            for value in [primary_pillar, *matched_pillars]:
                if value:
                    anchors.extend(graph.search(value, limit=3))
            links = []
            seen = set()
            for anchor in anchors:
                uid = str(anchor.get("uid"))
                if uid in seen:
                    continue
                seen.add(uid)
                neighborhood = graph.neighborhood(uid, depth=1)
                related = [
                    node
                    for node in neighborhood.get("nodes", [])
                    if str(node.get("uid")) != uid
                ]
                if related:
                    links.append({
                        'mapping_key': f"uskd:{uid}",
                        'concepts': [
                            str(node.get("title") or node.get("name") or node.get("uid"))
                            for node in related[:5]
                        ],
                        'relevance': 1.0,
                        'source_pillars': [primary_pillar] if primary_pillar else [],
                        'subgraph_nodes': related,
                    })
            return links
        except Exception as exc:
            logger.debug("Live USKD graph links unavailable: %s", exc)
            return []
    
    def _broaden_context(self, expanded_axes: Dict[int, Dict[str, Any]],
                         cross_domain: List[Dict[str, Any]],
                         pillar_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Broaden context with relevant information branches.
        
        Args:
            expanded_axes: Expanded axis information
            cross_domain: Cross-domain links
            pillar_context: Pillar context
            
        Returns:
            List of information branches
        """
        branches = []
        
        for axis_num, axis_data in expanded_axes.items():
            if axis_data['relevance_score'] > 0.5:
                branches.append({
                    'branch_type': 'axis_expansion',
                    'axis': axis_num,
                    'depth': 1,
                    'node_count': len(axis_data.get('nodes', [])),
                    'relevance': axis_data['relevance_score']
                })
        
        for link in cross_domain[:3]:
            branches.append({
                'branch_type': 'cross_domain',
                'mapping': link['mapping_key'],
                'concepts': link['concepts'],
                'relevance': link['relevance']
            })
        
        primary_pillar = pillar_context.get('primary_pillar', '')
        if primary_pillar:
            branches.append({
                'branch_type': 'pillar_hierarchy',
                'pillar': primary_pillar,
                'depth': 2,
                'relevance': pillar_context.get('confidence', 0.5)
            })
        
        return branches
    
    def _aggregate_knowledge(self, expanded_axes: Dict[int, Dict[str, Any]],
                             cross_domain: List[Dict[str, Any]],
                             branches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate all expanded knowledge into a unified structure.
        
        Args:
            expanded_axes: Expanded axis data
            cross_domain: Cross-domain links
            branches: Information branches
            
        Returns:
            Aggregated knowledge structure
        """
        all_nodes = []
        for axis_data in expanded_axes.values():
            all_nodes.extend(axis_data.get('nodes', []))
        
        return {
            'nodes': all_nodes,
            'node_count': len(all_nodes),
            'axes_covered': list(expanded_axes.keys()),
            'cross_domain_count': len(cross_domain),
            'branch_count': len(branches),
            'aggregation_timestamp': datetime.now(UTC).isoformat()
        }
    
    def _calculate_layer_confidence(self, expanded_axes: Dict[int, Dict[str, Any]],
                                     cross_domain: List[Dict[str, Any]]) -> float:
        """
        Calculate Layer 2 processing confidence.
        
        Args:
            expanded_axes: Expanded axis data
            cross_domain: Cross-domain links
            
        Returns:
            Confidence score (0.0-1.0)
        """
        axis_coverage = len(expanded_axes) / 17
        
        avg_axis_relevance = 0
        if expanded_axes:
            avg_axis_relevance = sum(
                a['relevance_score'] for a in expanded_axes.values()
            ) / len(expanded_axes)
        
        cross_domain_score = min(1.0, len(cross_domain) / 3) * 0.3
        
        confidence = (axis_coverage * 0.3 + avg_axis_relevance * 0.4 + cross_domain_score)
        
        return min(0.95, confidence)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.copy()
