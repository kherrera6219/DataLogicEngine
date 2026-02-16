"""
Natural Language to 17-Axis Coordinate Mapper

This module provides AI-powered mapping from natural language queries
to the 17-axis coordinate system used by UKG/USKD.

Uses OpenAI integration to analyze queries and extract coordinate values
for each of the 17 axes.
"""

import logging
import json
import os
from datetime import datetime, UTC
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class NLCoordinateMapper:
    """
    Natural Language to 17-Axis Coordinate Mapper
    
    Converts natural language queries into 17-dimensional coordinate
    representations using AI-powered analysis.
    """
    
    AXIS_DEFINITIONS = {
        1: {
            'name': 'Temporal',
            'description': 'Time context (when events occur; dates, times, sequences)',
            'extraction_prompt': 'Extract any temporal information: dates, times, periods, deadlines, schedules'
        },
        2: {
            'name': 'Spatial',
            'description': 'Geographic/Location context (where events occur)',
            'extraction_prompt': 'Extract location information: countries, cities, regions, facilities'
        },
        3: {
            'name': 'Semantic',
            'description': 'Conceptual/Ontological context (definitions, concepts)',
            'extraction_prompt': 'Identify key concepts, definitions, and semantic relationships'
        },
        4: {
            'name': 'Procedural',
            'description': 'Process & Methods context (how things are done)',
            'extraction_prompt': 'Identify processes, procedures, workflows, methods mentioned'
        },
        5: {
            'name': 'Analytical',
            'description': 'Quantitative analysis & models',
            'extraction_prompt': 'Extract analytical requirements: statistics, predictions, data analysis'
        },
        6: {
            'name': 'Normative',
            'description': 'Policies, rules & standards',
            'extraction_prompt': 'Identify policies, standards, guidelines, best practices referenced'
        },
        7: {
            'name': 'Risk/Impact',
            'description': 'Risks, threats & consequences',
            'extraction_prompt': 'Identify risks, threats, impacts, consequences mentioned'
        },
        8: {
            'name': 'Performance',
            'description': 'Performance & efficiency metrics',
            'extraction_prompt': 'Extract performance requirements: KPIs, metrics, efficiency goals'
        },
        9: {
            'name': 'Expertise',
            'description': 'Expert knowledge & authority',
            'extraction_prompt': 'Identify expertise areas, credentials, specialist knowledge needed'
        },
        10: {
            'name': 'Ethical',
            'description': 'Ethical considerations',
            'extraction_prompt': 'Identify ethical considerations, values, moral principles'
        },
        11: {
            'name': 'Regulatory',
            'description': 'External laws & regulations',
            'extraction_prompt': 'Identify regulations, laws, legal requirements (FAR, HIPAA, GDPR, etc.)'
        },
        12: {
            'name': 'Compliance',
            'description': 'Internal policy adherence',
            'extraction_prompt': 'Identify internal compliance requirements, policies, controls'
        },
        13: {
            'name': 'Simulation',
            'description': 'Hypothetical scenarios & modeling',
            'extraction_prompt': 'Identify what-if scenarios, simulations, hypotheticals'
        },
        14: {
            'name': 'AI-Generated',
            'description': 'AI/Synthetic knowledge',
            'extraction_prompt': 'Identify AI/ML components, synthetic data, automated analysis needs'
        },
        15: {
            'name': 'Cultural/Social',
            'description': 'Cultural and social context',
            'extraction_prompt': 'Identify cultural factors, social context, stakeholder considerations'
        },
        16: {
            'name': 'Innovation',
            'description': 'Innovation & emerging trends',
            'extraction_prompt': 'Identify innovation aspects, emerging technologies, research frontiers'
        },
        17: {
            'name': 'Learning',
            'description': 'Meta-learning & self-improvement',
            'extraction_prompt': 'Identify learning requirements, improvement goals, adaptation needs'
        }
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the NL Coordinate Mapper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.openai_client = None
        
        self._initialize_openai()
        
        self.cache = {}
        
        self.stats = {
            'queries_mapped': 0,
            'ai_calls': 0,
            'cache_hits': 0
        }
        
        logger.info(f"[{datetime.now()}] NLCoordinateMapper initialized")
    
    def _initialize_openai(self) -> None:
        """Initialize OpenAI client if available."""
        try:
            from openai import OpenAI
            api_key = os.environ.get('OPENAI_API_KEY')
            
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OPENAI_API_KEY not found. AI mapping will use fallback method.")
        except ImportError:
            logger.warning("OpenAI package not available. Using fallback mapping.")
    
    def map_query(self, query: str, use_ai: bool = True) -> Dict[str, Any]:
        """
        Map a natural language query to 17-axis coordinates.
        
        Args:
            query: Natural language query
            use_ai: Whether to use AI for mapping (if available)
            
        Returns:
            Mapping result with coordinates for each axis
        """
        start_time = datetime.now(UTC)
        
        logger.info(f"[{start_time}] Mapping query to 17-axis coordinates")
        
        cache_key = hash(query)
        if cache_key in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[cache_key]
        
        result = {
            'query': query,
            'mapping_method': 'keyword',
            'coordinates': {},
            'axis_values': {},
            'confidence': 0.0,
            'mapped_at': start_time.isoformat()
        }
        
        if use_ai and self.openai_client:
            try:
                ai_result = self._map_with_ai(query)
                result['coordinates'] = ai_result['coordinates']
                result['axis_values'] = ai_result['axis_values']
                result['confidence'] = ai_result['confidence']
                result['mapping_method'] = 'ai'
                self.stats['ai_calls'] += 1
            except Exception as e:
                logger.warning(f"AI mapping failed, using fallback: {e}")
                fallback = self._map_with_keywords(query)
                result['coordinates'] = fallback['coordinates']
                result['axis_values'] = fallback['axis_values']
                result['confidence'] = fallback['confidence']
        else:
            fallback = self._map_with_keywords(query)
            result['coordinates'] = fallback['coordinates']
            result['axis_values'] = fallback['axis_values']
            result['confidence'] = fallback['confidence']
        
        result['processing_duration_ms'] = (datetime.now(UTC) - start_time).total_seconds() * 1000
        
        self.cache[cache_key] = result
        self.stats['queries_mapped'] += 1
        
        logger.info(f"[{datetime.now()}] Query mapped with confidence {result['confidence']:.2f}")
        
        return result
    
    def _map_with_ai(self, query: str) -> Dict[str, Any]:
        """
        Map query using OpenAI.
        
        Args:
            query: The query to map
            
        Returns:
            AI-generated mapping
        """
        system_prompt = """You are a knowledge coordinate mapper for a 17-axis knowledge system.
        
Given a query, extract relevant information for each of the 17 axes:
1. Temporal - time/dates
2. Spatial - locations
3. Semantic - concepts/definitions
4. Procedural - processes/methods
5. Analytical - data/analysis
6. Normative - policies/standards
7. Risk/Impact - risks/consequences
8. Performance - metrics/KPIs
9. Expertise - expert domains
10. Ethical - ethical concerns
11. Regulatory - laws/regulations
12. Compliance - internal policies
13. Simulation - scenarios/what-ifs
14. AI-Generated - AI/ML aspects
15. Cultural/Social - social factors
16. Innovation - new technologies
17. Learning - improvement needs

For each axis, provide:
- relevance: float 0-1 (how relevant this axis is to the query)
- value: extracted information or null if not applicable
- confidence: float 0-1 (confidence in extraction)

Respond in JSON format with structure:
{
    "axes": {
        "1": {"relevance": 0.8, "value": "2025 deadline", "confidence": 0.9},
        ...
    },
    "overall_confidence": 0.85
}"""

        user_prompt = f"Map this query to the 17-axis coordinate system:\n\n{query}"
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        parsed = json.loads(content)
        
        coordinates = {}
        axis_values = {}
        
        axes_data = parsed.get('axes', {})
        for axis_num in range(1, 18):
            axis_key = str(axis_num)
            if axis_key in axes_data:
                axis_info = axes_data[axis_key]
                coordinates[axis_num] = axis_info.get('relevance', 0.0)
                if axis_info.get('value'):
                    axis_values[axis_num] = {
                        'value': axis_info['value'],
                        'confidence': axis_info.get('confidence', 0.7)
                    }
            else:
                coordinates[axis_num] = 0.0
        
        return {
            'coordinates': coordinates,
            'axis_values': axis_values,
            'confidence': parsed.get('overall_confidence', 0.7)
        }
    
    def _map_with_keywords(self, query: str) -> Dict[str, Any]:
        """
        Map query using keyword matching (fallback method).
        
        Args:
            query: The query to map
            
        Returns:
            Keyword-based mapping
        """
        axis_keywords = {
            1: ['when', 'date', 'time', 'deadline', 'schedule', 'year', 'month', 'day', '2024', '2025'],
            2: ['where', 'location', 'city', 'country', 'region', 'site', 'facility', 'address'],
            3: ['what', 'define', 'meaning', 'concept', 'is', 'are', 'explain', 'describe'],
            4: ['how', 'process', 'procedure', 'method', 'steps', 'workflow', 'guide', 'implement'],
            5: ['analyze', 'data', 'statistics', 'measure', 'quantify', 'predict', 'model', 'calculate'],
            6: ['policy', 'standard', 'guideline', 'best practice', 'should', 'recommended', 'principle'],
            7: ['risk', 'threat', 'impact', 'danger', 'vulnerability', 'consequence', 'mitigation'],
            8: ['performance', 'kpi', 'metric', 'efficiency', 'effectiveness', 'outcome', 'result'],
            9: ['expert', 'specialist', 'professional', 'credential', 'certification', 'qualified'],
            10: ['ethical', 'moral', 'fair', 'bias', 'integrity', 'responsible', 'values'],
            11: ['regulation', 'law', 'legal', 'far', 'dfars', 'hipaa', 'gdpr', 'sox', 'compliance'],
            12: ['internal', 'policy', 'control', 'audit', 'governance', 'procedure', 'requirement'],
            13: ['scenario', 'what-if', 'simulate', 'hypothetical', 'projection', 'forecast'],
            14: ['ai', 'machine learning', 'artificial intelligence', 'automated', 'ml', 'algorithm'],
            15: ['culture', 'social', 'community', 'stakeholder', 'public', 'society', 'people'],
            16: ['innovation', 'emerging', 'new', 'novel', 'research', 'frontier', 'cutting-edge'],
            17: ['learn', 'improve', 'adapt', 'optimize', 'feedback', 'continuous', 'evolve']
        }
        
        query_lower = query.lower()
        coordinates = {}
        axis_values = {}
        
        for axis_num, keywords in axis_keywords.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            relevance = min(1.0, matches / max(1, len(keywords) * 0.3))
            coordinates[axis_num] = relevance
            
            if relevance > 0.3:
                matched_keywords = [kw for kw in keywords if kw in query_lower]
                if matched_keywords:
                    axis_values[axis_num] = {
                        'value': ', '.join(matched_keywords[:3]),
                        'confidence': min(0.8, relevance)
                    }
        
        max_relevance = max(coordinates.values()) if coordinates else 0
        overall_confidence = min(0.7, max_relevance * 0.8)
        
        return {
            'coordinates': coordinates,
            'axis_values': axis_values,
            'confidence': overall_confidence
        }
    
    def get_axis_definitions(self) -> Dict[int, Dict[str, str]]:
        """Get the axis definitions."""
        return self.AXIS_DEFINITIONS.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mapping statistics."""
        return self.stats.copy()


class QueryToCoordinatePipeline:
    """
    End-to-end pipeline for processing queries through coordinate mapping
    and into the simulation system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the pipeline.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.mapper = NLCoordinateMapper(config)
        self.orchestrator = None
        
        self._initialize_orchestrator()
        
        logger.info("QueryToCoordinatePipeline initialized")
    
    def _initialize_orchestrator(self) -> None:
        """Initialize the master workflow orchestrator."""
        try:
            from core.orchestration.master_workflow import MasterWorkflowOrchestrator
            self.orchestrator = MasterWorkflowOrchestrator(self.config)
        except ImportError as e:
            logger.warning(f"Could not initialize orchestrator: {e}")
    
    def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a query through the complete pipeline.
        
        Args:
            query: Natural language query
            context: Optional additional context
            
        Returns:
            Complete processing result
        """
        start_time = datetime.now(UTC)
        
        logger.info(f"[{start_time}] Processing query through pipeline")
        
        mapping_result = self.mapper.map_query(query)
        
        pipeline_context = {
            'query': query,
            'coordinates': mapping_result['coordinates'],
            'axis_values': mapping_result['axis_values'],
            'mapping_confidence': mapping_result['confidence']
        }
        
        if context:
            pipeline_context.update(context)
        
        if self.orchestrator:
            result = self.orchestrator.execute(query, pipeline_context)
        else:
            result = {
                'status': 'partial',
                'message': 'Orchestrator not available, returning mapping only',
                'mapping': mapping_result
            }
        
        result['pipeline_processing_time_ms'] = (datetime.now(UTC) - start_time).total_seconds() * 1000
        
        return result


def create_coordinate_mapper(config: Optional[Dict] = None) -> NLCoordinateMapper:
    """Factory function to create a coordinate mapper."""
    return NLCoordinateMapper(config)


def create_query_pipeline(config: Optional[Dict] = None) -> QueryToCoordinatePipeline:
    """Factory function to create a query pipeline."""
    return QueryToCoordinatePipeline(config)
