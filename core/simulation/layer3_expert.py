"""
Layer 3: Expert Simulation Layer

This layer simulates domain experts and regulatory systems.
It activates primary personas (Knowledge & Sector experts) and integrates
regulatory and compliance checks.

Algorithms:
- KA-07: Regulatory Expert Simulation
- KA-08: Compliance Expert Simulation
- KA-09: Conflict Resolution
- KA-10: Contractual Logic Validator
- KA-20: Quad Persona
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class Layer3ExpertEngine:
    """
    Layer 3: Expert Simulation Layer
    
    Purpose: Simulate domain experts and regulatory systems.
    
    Actions:
    - Activate primary personas (Knowledge & Sector experts) to analyze the query
    - Activate Regulatory persona (external laws/regulations) and Compliance persona (internal policies)
    - Inject regulatory/legal context and internal policy constraints into analysis
    """
    
    def __init__(self, config: Optional[Dict] = None, persona_engine=None):
        """
        Initialize Layer 3 Expert Engine.
        
        Args:
            config: Optional configuration dictionary
            persona_engine: Optional QuadPersonaEngine instance
        """
        self.config = config or {}
        self.persona_engine = persona_engine
        
        self.expert_profiles = self._initialize_expert_profiles()
        
        self.regulatory_frameworks = self._initialize_regulatory_frameworks()
        
        self.compliance_standards = self._initialize_compliance_standards()
        
        self.stats = {
            'simulations_run': 0,
            'experts_activated': 0,
            'conflicts_detected': 0,
            'regulatory_checks': 0
        }
        
        logger.info(f"[{datetime.now()}] Layer3ExpertEngine initialized")
    
    def _initialize_expert_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Initialize expert profile templates."""
        return {
            'knowledge_expert': {
                'role': 'Domain Knowledge Specialist',
                'focus': ['concepts', 'definitions', 'technical accuracy'],
                'weight': 0.25,
                'components': ['job_role', 'education', 'certifications', 'skills']
            },
            'sector_expert': {
                'role': 'Industry Sector Specialist',
                'focus': ['market context', 'industry practices', 'stakeholder needs'],
                'weight': 0.25,
                'components': ['job_role', 'training', 'career_path', 'related_jobs']
            },
            'regulatory_expert': {
                'role': 'Regulatory Compliance Advisor',
                'focus': ['legal requirements', 'regulations', 'mandates'],
                'weight': 0.25,
                'components': ['job_role', 'certifications', 'skills']
            },
            'compliance_expert': {
                'role': 'Internal Compliance Officer',
                'focus': ['policies', 'controls', 'audit requirements'],
                'weight': 0.25,
                'components': ['job_role', 'training', 'skills']
            }
        }
    
    def _initialize_regulatory_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Initialize regulatory framework references."""
        return {
            'FAR': {
                'name': 'Federal Acquisition Regulation',
                'scope': 'federal procurement',
                'keywords': ['acquisition', 'procurement', 'contract', 'federal']
            },
            'DFARS': {
                'name': 'Defense Federal Acquisition Regulation Supplement',
                'scope': 'defense procurement',
                'keywords': ['defense', 'dod', 'military', 'dfars']
            },
            'HIPAA': {
                'name': 'Health Insurance Portability and Accountability Act',
                'scope': 'healthcare data',
                'keywords': ['health', 'medical', 'patient', 'hipaa', 'phi']
            },
            'GDPR': {
                'name': 'General Data Protection Regulation',
                'scope': 'data privacy',
                'keywords': ['data', 'privacy', 'personal', 'gdpr', 'eu']
            },
            'SOX': {
                'name': 'Sarbanes-Oxley Act',
                'scope': 'financial reporting',
                'keywords': ['financial', 'audit', 'sox', 'accounting']
            },
            'NIST': {
                'name': 'NIST Cybersecurity Framework',
                'scope': 'cybersecurity',
                'keywords': ['security', 'cyber', 'nist', 'framework']
            }
        }
    
    def _initialize_compliance_standards(self) -> Dict[str, Dict[str, Any]]:
        """Initialize internal compliance standard references."""
        return {
            'internal_audit': {
                'name': 'Internal Audit Requirements',
                'checks': ['documentation', 'approval chain', 'record keeping']
            },
            'quality_management': {
                'name': 'Quality Management System',
                'checks': ['iso_9001', 'process compliance', 'continuous improvement']
            },
            'data_governance': {
                'name': 'Data Governance Policies',
                'checks': ['data classification', 'access control', 'retention']
            },
            'ethics_code': {
                'name': 'Code of Ethics',
                'checks': ['conflict of interest', 'fair dealing', 'confidentiality']
            }
        }
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context through Layer 3 expert simulation.
        
        Args:
            context: Input context from Layer 2
            
        Returns:
            Enhanced context with expert analysis and compliance checks
        """
        start_time = datetime.now(UTC)
        
        logger.info(f"[{start_time}] Layer 3: Processing context for expert simulation")
        
        enhanced_context = context.copy()
        
        layer3_metadata = {
            'layer': 3,
            'layer_name': 'Expert Simulation Layer',
            'processing_start': start_time.isoformat(),
            'experts_activated': [],
            'regulatory_analysis': {},
            'compliance_analysis': {},
            'conflicts': []
        }
        
        query = context.get('query', '')
        pillar_context = context.get('pillar_context', {})
        expert_roles = context.get('expert_roles', [])
        
        primary_analysis = self._activate_primary_personas(query, pillar_context, expert_roles)
        layer3_metadata['primary_analysis'] = primary_analysis
        layer3_metadata['experts_activated'].extend(primary_analysis.get('activated', []))
        
        regulatory_analysis = self._perform_regulatory_analysis(query, pillar_context)
        layer3_metadata['regulatory_analysis'] = regulatory_analysis
        
        compliance_analysis = self._perform_compliance_analysis(query, pillar_context)
        layer3_metadata['compliance_analysis'] = compliance_analysis
        
        integrated_analysis = self._integrate_analyses(
            primary_analysis, regulatory_analysis, compliance_analysis
        )
        layer3_metadata['integrated_analysis'] = integrated_analysis
        
        conflicts = self._detect_conflicts(integrated_analysis)
        layer3_metadata['conflicts'] = conflicts
        
        layer3_metadata['processing_end'] = datetime.now(UTC).isoformat()
        layer3_metadata['processing_duration_ms'] = (datetime.now(UTC) - start_time).total_seconds() * 1000
        
        layer_confidence = self._calculate_layer_confidence(
            primary_analysis, regulatory_analysis, compliance_analysis, conflicts
        )
        layer3_metadata['layer_confidence'] = layer_confidence
        
        enhanced_context['layer3_expert'] = layer3_metadata
        enhanced_context['expert_analysis'] = integrated_analysis
        enhanced_context['regulatory_constraints'] = regulatory_analysis.get('applicable_frameworks', [])
        enhanced_context['compliance_requirements'] = compliance_analysis.get('requirements', [])
        enhanced_context['analysis_conflicts'] = conflicts
        
        self.stats['simulations_run'] += 1
        self.stats['experts_activated'] += len(layer3_metadata['experts_activated'])
        self.stats['conflicts_detected'] += len(conflicts)
        self.stats['regulatory_checks'] += 1
        
        logger.info(f"[{datetime.now()}] Layer 3 complete. Confidence: {layer_confidence:.3f}")
        
        return enhanced_context
    
    def _activate_primary_personas(self, query: str, pillar_context: Dict[str, Any],
                                    expert_roles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Activate primary personas (Knowledge & Sector experts).
        
        Args:
            query: The user query
            pillar_context: Pillar context from Layer 1
            expert_roles: Expert roles assigned from Layer 1
            
        Returns:
            Primary persona analysis results
        """
        analysis_result = {
            'activated': [],
            'responses': {},
            'confidence_scores': {}
        }
        
        if self.persona_engine:
            try:
                persona_result = self.persona_engine.process_query(query)
                analysis_result['responses'] = persona_result.get('persona_responses', {})
                for persona_type, response in analysis_result['responses'].items():
                    analysis_result['activated'].append(persona_type)
                    analysis_result['confidence_scores'][persona_type] = response.get('confidence', 0.7)
                return analysis_result
            except Exception as e:
                logger.warning(f"Persona engine error: {e}")
        
        for expert_type, profile in self.expert_profiles.items():
            if expert_type in ['knowledge_expert', 'sector_expert']:
                analysis_result['activated'].append(expert_type)
                
                analysis_result['responses'][expert_type] = {
                    'role': profile['role'],
                    'focus_areas': profile['focus'],
                    'analysis': f"Expert analysis from {profile['role']} perspective",
                    'recommendations': [],
                    'confidence': 0.75
                }
                
                analysis_result['confidence_scores'][expert_type] = 0.75
        
        return analysis_result
    
    def _perform_regulatory_analysis(self, query: str,
                                      pillar_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform regulatory analysis using regulatory expert persona.
        
        Args:
            query: The user query
            pillar_context: Pillar context
            
        Returns:
            Regulatory analysis results
        """
        query_lower = query.lower()
        
        applicable_frameworks = []
        
        for framework_id, framework_info in self.regulatory_frameworks.items():
            keywords = framework_info['keywords']
            matches = sum(1 for kw in keywords if kw in query_lower)
            
            if matches > 0:
                relevance = min(1.0, matches / len(keywords) * 2)
                applicable_frameworks.append({
                    'framework_id': framework_id,
                    'name': framework_info['name'],
                    'scope': framework_info['scope'],
                    'relevance': relevance,
                    'keyword_matches': matches
                })
        
        applicable_frameworks.sort(key=lambda x: x['relevance'], reverse=True)
        
        regulatory_constraints = []
        for fw in applicable_frameworks[:3]:
            regulatory_constraints.append({
                'source': fw['framework_id'],
                'constraint_type': 'regulatory_requirement',
                'description': f"Must comply with {fw['name']}",
                'severity': 'mandatory' if fw['relevance'] > 0.5 else 'advisory'
            })
        
        return {
            'applicable_frameworks': applicable_frameworks,
            'constraints': regulatory_constraints,
            'expert_type': 'regulatory_expert',
            'confidence': 0.8 if applicable_frameworks else 0.5
        }
    
    def _perform_compliance_analysis(self, query: str,
                                      pillar_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform compliance analysis using compliance expert persona.
        
        Args:
            query: The user query
            pillar_context: Pillar context
            
        Returns:
            Compliance analysis results
        """
        query_lower = query.lower()
        
        applicable_standards = []
        
        for standard_id, standard_info in self.compliance_standards.items():
            checks = standard_info['checks']
            has_relevant = any(check.replace('_', ' ') in query_lower for check in checks)
            
            if has_relevant:
                applicable_standards.append({
                    'standard_id': standard_id,
                    'name': standard_info['name'],
                    'relevant_checks': checks
                })
        
        if not applicable_standards:
            applicable_standards.append({
                'standard_id': 'general_compliance',
                'name': 'General Compliance Requirements',
                'relevant_checks': ['documentation', 'approval']
            })
        
        requirements = []
        for std in applicable_standards:
            for check in std['relevant_checks'][:2]:
                requirements.append({
                    'source': std['standard_id'],
                    'requirement': check,
                    'description': f"Ensure {check.replace('_', ' ')} compliance"
                })
        
        return {
            'applicable_standards': applicable_standards,
            'requirements': requirements,
            'expert_type': 'compliance_expert',
            'confidence': 0.75
        }
    
    def _integrate_analyses(self, primary: Dict[str, Any], regulatory: Dict[str, Any],
                            compliance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate all expert analyses into unified result.
        
        Args:
            primary: Primary persona analysis
            regulatory: Regulatory analysis
            compliance: Compliance analysis
            
        Returns:
            Integrated analysis
        """
        all_recommendations = []
        
        for expert_type, response in primary.get('responses', {}).items():
            recommendations = response.get('recommendations', [])
            for rec in recommendations:
                all_recommendations.append({
                    'source': expert_type,
                    'recommendation': rec
                })
        
        for constraint in regulatory.get('constraints', []):
            all_recommendations.append({
                'source': 'regulatory',
                'recommendation': constraint['description']
            })
        
        for req in compliance.get('requirements', []):
            all_recommendations.append({
                'source': 'compliance',
                'recommendation': req['description']
            })
        
        confidence_scores = primary.get('confidence_scores', {})
        confidence_scores['regulatory'] = regulatory.get('confidence', 0.7)
        confidence_scores['compliance'] = compliance.get('confidence', 0.7)
        
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.5
        
        return {
            'recommendations': all_recommendations,
            'confidence_scores': confidence_scores,
            'average_confidence': avg_confidence,
            'experts_consulted': list(confidence_scores.keys()),
            'integration_timestamp': datetime.now(UTC).isoformat()
        }
    
    def _detect_conflicts(self, integrated_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect conflicts between expert analyses.
        
        Args:
            integrated_analysis: Integrated analysis results
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        confidence_scores = integrated_analysis.get('confidence_scores', {})
        
        if confidence_scores:
            scores = list(confidence_scores.values())
            if max(scores) - min(scores) > 0.3:
                low_confidence_experts = [
                    k for k, v in confidence_scores.items() if v < 0.6
                ]
                high_confidence_experts = [
                    k for k, v in confidence_scores.items() if v > 0.8
                ]
                
                if low_confidence_experts and high_confidence_experts:
                    conflicts.append({
                        'conflict_type': 'confidence_divergence',
                        'description': 'Significant confidence gap between experts',
                        'low_confidence': low_confidence_experts,
                        'high_confidence': high_confidence_experts,
                        'severity': 'medium'
                    })
        
        recommendations = integrated_analysis.get('recommendations', [])
        regulatory_recs = [r for r in recommendations if r['source'] == 'regulatory']
        other_recs = [r for r in recommendations if r['source'] != 'regulatory']
        
        if regulatory_recs and other_recs:
            pass
        
        return conflicts
    
    def _calculate_layer_confidence(self, primary: Dict[str, Any], regulatory: Dict[str, Any],
                                     compliance: Dict[str, Any], conflicts: List) -> float:
        """
        Calculate Layer 3 processing confidence.
        
        Args:
            primary: Primary analysis
            regulatory: Regulatory analysis
            compliance: Compliance analysis
            conflicts: Detected conflicts
            
        Returns:
            Confidence score (0.0-1.0)
        """
        primary_confidence = sum(primary.get('confidence_scores', {}).values())
        if primary.get('confidence_scores'):
            primary_confidence /= len(primary['confidence_scores'])
        else:
            primary_confidence = 0.5
        
        regulatory_confidence = regulatory.get('confidence', 0.5)
        compliance_confidence = compliance.get('confidence', 0.5)
        
        base_confidence = (primary_confidence * 0.4 + 
                          regulatory_confidence * 0.3 + 
                          compliance_confidence * 0.3)
        
        conflict_penalty = len(conflicts) * 0.05
        
        final_confidence = max(0.3, base_confidence - conflict_penalty)
        
        return min(0.95, final_confidence)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.copy()
