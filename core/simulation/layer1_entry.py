"""
Layer 1: Entry Layer (Context Initialization)

This layer handles the initial processing of queries and user interactions.
It maps the user query into fundamental axes and determines initial domain/pillar context.

Algorithms:
- KA-01: Semantic Mapping
- KA-02: Knowledge Graph Integration  
- KA-03: Decision Support
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class Layer1EntryEngine:
    """
    Layer 1: Entry Layer - Context Initialization
    
    Purpose: Map the user query into fundamental axes and determine initial 
    domain/pillar context.
    
    Actions:
    - Identify relevant axes from query (time, location, domain keywords)
    - Assign initial expert roles or pillars based on query classification
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Layer 1 Entry Engine.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        self.axis_keywords = {
            1: {
                'name': 'Temporal',
                'keywords': ['when', 'date', 'time', 'schedule', 'deadline', 'period', 'year', 'month', 'day'],
                'weight': 1.0
            },
            2: {
                'name': 'Spatial',
                'keywords': ['where', 'location', 'place', 'country', 'city', 'region', 'geography', 'site'],
                'weight': 1.0
            },
            3: {
                'name': 'Semantic',
                'keywords': ['what', 'meaning', 'definition', 'concept', 'term', 'ontology', 'category'],
                'weight': 1.0
            },
            4: {
                'name': 'Procedural',
                'keywords': ['how', 'process', 'method', 'procedure', 'workflow', 'steps', 'guide'],
                'weight': 1.0
            },
            5: {
                'name': 'Analytical',
                'keywords': ['analyze', 'data', 'statistics', 'predict', 'model', 'quantify', 'measure'],
                'weight': 1.0
            },
            6: {
                'name': 'Normative',
                'keywords': ['should', 'policy', 'standard', 'guideline', 'best practice', 'rule', 'principle'],
                'weight': 1.0
            },
            7: {
                'name': 'Risk/Impact',
                'keywords': ['risk', 'threat', 'impact', 'consequence', 'danger', 'vulnerability', 'mitigation'],
                'weight': 1.0
            },
            8: {
                'name': 'Performance',
                'keywords': ['performance', 'efficiency', 'kpi', 'metric', 'outcome', 'result', 'benchmark'],
                'weight': 1.0
            },
            9: {
                'name': 'Expertise',
                'keywords': ['expert', 'specialist', 'authority', 'professional', 'credential', 'qualification'],
                'weight': 1.0
            },
            10: {
                'name': 'Ethical',
                'keywords': ['ethical', 'moral', 'values', 'bias', 'fairness', 'integrity', 'responsibility'],
                'weight': 1.0
            },
            11: {
                'name': 'Regulatory',
                'keywords': ['regulation', 'law', 'legal', 'compliance', 'requirement', 'mandate', 'statute'],
                'weight': 1.0
            },
            12: {
                'name': 'Compliance',
                'keywords': ['comply', 'adherence', 'conform', 'internal', 'control', 'audit', 'policy'],
                'weight': 1.0
            },
            13: {
                'name': 'Simulation',
                'keywords': ['simulate', 'hypothetical', 'what-if', 'scenario', 'model', 'projection'],
                'weight': 1.0
            },
            14: {
                'name': 'AI-Generated',
                'keywords': ['ai', 'machine learning', 'inference', 'synthetic', 'generated', 'automated'],
                'weight': 1.0
            },
            15: {
                'name': 'Cultural/Social',
                'keywords': ['culture', 'social', 'public', 'sentiment', 'community', 'society', 'human'],
                'weight': 1.0
            },
            16: {
                'name': 'Innovation',
                'keywords': ['innovation', 'emerging', 'frontier', 'novel', 'research', 'breakthrough', 'new'],
                'weight': 1.0
            },
            17: {
                'name': 'Learning',
                'keywords': ['learn', 'improve', 'adapt', 'evolve', 'optimize', 'feedback', 'meta'],
                'weight': 1.0
            }
        }
        
        self.pillar_mappings = {
            'acquisition': {
                'keywords': ['acquisition', 'procurement', 'contract', 'purchase', 'buy', 'vendor'],
                'primary_axes': [4, 6, 11, 12],
                'expert_roles': ['contracting_officer', 'procurement_specialist']
            },
            'technology': {
                'keywords': ['technology', 'software', 'hardware', 'system', 'digital', 'cyber'],
                'primary_axes': [5, 14, 16, 17],
                'expert_roles': ['it_specialist', 'software_engineer', 'data_scientist']
            },
            'finance': {
                'keywords': ['finance', 'budget', 'cost', 'funding', 'investment', 'fiscal'],
                'primary_axes': [5, 8, 11, 12],
                'expert_roles': ['financial_analyst', 'budget_officer', 'accountant']
            },
            'healthcare': {
                'keywords': ['health', 'medical', 'clinical', 'patient', 'hospital', 'treatment'],
                'primary_axes': [7, 9, 10, 11],
                'expert_roles': ['healthcare_provider', 'medical_expert', 'compliance_officer']
            },
            'defense': {
                'keywords': ['defense', 'military', 'security', 'dod', 'armed forces', 'weapon'],
                'primary_axes': [7, 11, 12, 13],
                'expert_roles': ['defense_analyst', 'security_specialist', 'military_expert']
            },
            'legal': {
                'keywords': ['legal', 'law', 'attorney', 'litigation', 'court', 'statute'],
                'primary_axes': [6, 10, 11, 12],
                'expert_roles': ['attorney', 'legal_counsel', 'paralegal']
            }
        }
        
        self.stats = {
            'queries_processed': 0,
            'axes_identified': 0,
            'pillars_matched': 0
        }
        
        logger.info(f"[{datetime.now()}] Layer1EntryEngine initialized")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the query through Layer 1 entry processing.
        
        Args:
            context: Input context containing query and optional metadata
            
        Returns:
            Enhanced context with axis scores and pillar assignments
        """
        start_time = datetime.now(UTC)
        
        query = context.get('query', '')
        
        logger.info(f"[{start_time}] Layer 1: Processing query for context initialization")
        
        enhanced_context = context.copy()
        
        layer1_metadata = {
            'layer': 1,
            'layer_name': 'Entry Layer (Context Initialization)',
            'processing_start': start_time.isoformat(),
            'query_length': len(query),
            'query_word_count': len(query.split())
        }
        
        axis_scores = self._identify_relevant_axes(query)
        layer1_metadata['axis_scores'] = axis_scores
        
        pillar_context = self._assign_pillar_context(query, axis_scores)
        layer1_metadata['pillar_context'] = pillar_context
        
        expert_roles = self._assign_expert_roles(pillar_context)
        layer1_metadata['expert_roles'] = expert_roles
        
        knowledge_expansion = self._prepare_knowledge_expansion(query, axis_scores, pillar_context)
        layer1_metadata['knowledge_expansion'] = knowledge_expansion
        
        layer1_metadata['processing_end'] = datetime.now(UTC).isoformat()
        layer1_metadata['processing_duration_ms'] = (datetime.now(UTC) - start_time).total_seconds() * 1000
        
        layer_confidence = self._calculate_layer_confidence(axis_scores, pillar_context)
        layer1_metadata['layer_confidence'] = layer_confidence
        
        enhanced_context['layer1_entry'] = layer1_metadata
        enhanced_context['axis_scores'] = axis_scores
        enhanced_context['pillar_context'] = pillar_context
        enhanced_context['expert_roles'] = expert_roles
        
        self.stats['queries_processed'] += 1
        self.stats['axes_identified'] += len([s for s in axis_scores.values() if s > 0.3])
        self.stats['pillars_matched'] += len(pillar_context.get('matched_pillars', []))
        
        logger.info(f"[{datetime.now()}] Layer 1 complete. Confidence: {layer_confidence:.3f}")
        
        return enhanced_context
    
    def _identify_relevant_axes(self, query: str) -> Dict[int, float]:
        """
        Identify relevant axes from the query based on keyword matching.
        
        Args:
            query: The user query string
            
        Returns:
            Dictionary mapping axis number to relevance score (0.0-1.0)
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        axis_scores = {}
        
        for axis_num, axis_info in self.axis_keywords.items():
            keywords = axis_info['keywords']
            weight = axis_info['weight']
            
            keyword_matches = sum(1 for kw in keywords if kw in query_lower)
            word_matches = sum(1 for kw in keywords if kw in query_words)
            
            phrase_score = keyword_matches / len(keywords) if keywords else 0
            word_score = word_matches / len(keywords) if keywords else 0
            
            combined_score = (phrase_score * 0.6 + word_score * 0.4) * weight
            
            axis_scores[axis_num] = min(1.0, combined_score * 2.5)
        
        max_score = max(axis_scores.values()) if axis_scores else 0
        if max_score < 0.2:
            axis_scores[3] = max(axis_scores.get(3, 0), 0.4)
            axis_scores[4] = max(axis_scores.get(4, 0), 0.3)
        
        return axis_scores
    
    def _assign_pillar_context(self, query: str, axis_scores: Dict[int, float]) -> Dict[str, Any]:
        """
        Assign pillar context based on query and axis scores.
        
        Args:
            query: The user query string
            axis_scores: Calculated axis relevance scores
            
        Returns:
            Pillar context assignment
        """
        query_lower = query.lower()
        
        matched_pillars = []
        pillar_scores = {}
        
        for pillar_name, pillar_info in self.pillar_mappings.items():
            keywords = pillar_info['keywords']
            
            keyword_matches = sum(1 for kw in keywords if kw in query_lower)
            keyword_score = keyword_matches / len(keywords) if keywords else 0
            
            primary_axes = pillar_info['primary_axes']
            axis_alignment = sum(axis_scores.get(axis, 0) for axis in primary_axes)
            axis_score = axis_alignment / len(primary_axes) if primary_axes else 0
            
            combined_score = (keyword_score * 0.6 + axis_score * 0.4)
            pillar_scores[pillar_name] = combined_score
            
            if combined_score > 0.2:
                matched_pillars.append({
                    'pillar': pillar_name,
                    'score': combined_score,
                    'keyword_score': keyword_score,
                    'axis_score': axis_score
                })
        
        matched_pillars.sort(key=lambda x: x['score'], reverse=True)
        
        primary_pillar = matched_pillars[0]['pillar'] if matched_pillars else 'general'
        
        return {
            'primary_pillar': primary_pillar,
            'matched_pillars': matched_pillars[:3],
            'pillar_scores': pillar_scores,
            'confidence': matched_pillars[0]['score'] if matched_pillars else 0.3
        }
    
    def _assign_expert_roles(self, pillar_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Assign expert roles based on pillar context.
        
        Args:
            pillar_context: The pillar context assignment
            
        Returns:
            List of assigned expert roles
        """
        expert_roles = []
        
        primary_pillar = pillar_context.get('primary_pillar', 'general')
        
        if primary_pillar in self.pillar_mappings:
            roles = self.pillar_mappings[primary_pillar].get('expert_roles', [])
            for role in roles:
                expert_roles.append({
                    'role_id': role,
                    'source_pillar': primary_pillar,
                    'priority': 'primary'
                })
        
        matched_pillars = pillar_context.get('matched_pillars', [])
        for pillar_match in matched_pillars[1:3]:
            pillar_name = pillar_match['pillar']
            if pillar_name in self.pillar_mappings:
                roles = self.pillar_mappings[pillar_name].get('expert_roles', [])
                for role in roles[:1]:
                    if role not in [r['role_id'] for r in expert_roles]:
                        expert_roles.append({
                            'role_id': role,
                            'source_pillar': pillar_name,
                            'priority': 'secondary'
                        })
        
        return expert_roles
    
    def _prepare_knowledge_expansion(self, query: str, axis_scores: Dict[int, float],
                                      pillar_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare parameters for Layer 2 knowledge expansion.
        
        Args:
            query: The user query
            axis_scores: Axis relevance scores
            pillar_context: Pillar context assignment
            
        Returns:
            Knowledge expansion parameters for Layer 2
        """
        high_relevance_axes = [axis for axis, score in axis_scores.items() if score > 0.4]
        
        expansion_params = {
            'target_axes': high_relevance_axes,
            'primary_pillar': pillar_context.get('primary_pillar'),
            'expansion_depth': 2 if len(high_relevance_axes) > 3 else 3,
            'include_cross_domain': pillar_context.get('confidence', 0) < 0.5,
            'query_tokens': query.lower().split()[:20]
        }
        
        return expansion_params
    
    def _calculate_layer_confidence(self, axis_scores: Dict[int, float],
                                     pillar_context: Dict[str, Any]) -> float:
        """
        Calculate overall Layer 1 processing confidence.
        
        Args:
            axis_scores: Axis relevance scores
            pillar_context: Pillar context assignment
            
        Returns:
            Confidence score (0.0-1.0)
        """
        axis_clarity = len([s for s in axis_scores.values() if s > 0.4])
        axis_confidence = min(1.0, axis_clarity / 4)
        
        pillar_confidence = pillar_context.get('confidence', 0.3)
        
        overall_confidence = (axis_confidence * 0.5 + pillar_confidence * 0.5)
        
        return min(0.95, overall_confidence)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.copy()
