import logging
from datetime import datetime
from typing import Dict, Any, List
import re

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA02(KnowledgeAlgorithm):
    """
    KA02: Axis Scorer
    
    This KA scores the relevance of each axis in the UKG for a given query,
    helping to determine which axes are most important for answering the query.
    """
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Axis Scorer KA.
        
        Args:
            input_data (dict): Contains 'query_text', 'ka01_output' (optional)
            
        Returns:
            dict: Scores for each of the 13 axes
        """
        # Validate input
        if not self.validate_input(input_data, ['query_text']):
            return {
                "status": "error",
                "error_message": "Missing required input: query_text",
                "ka_confidence": 0.0,
                "findings": {}
            }
        
        query_text = input_data['query_text']
        ka01_output = input_data.get('ka01_output', None)
        
        self.log_execution_step("Scoring axes for query", {"query_text": query_text[:50] + "..." if len(query_text) > 50 else query_text})
        
        try:
            # Get all axes from the UKG
            axes = self._get_all_axes()
            
            # Score each axis
            axis_scores = {}
            for axis in axes:
                score = self._score_axis_relevance(axis, query_text, ka01_output)
                axis_scores[axis['original_id']] = {
                    'score': score,
                    'axis_number': axis['number'],
                    'axis_label': axis['label']
                }
            
            # Determine top axes
            top_axes = sorted(
                axis_scores.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )[:5]  # Top 5 axes
            
            # Calculate confidence based on score distribution
            score_values = [item[1]['score'] for item in axis_scores.items()]
            score_range = max(score_values) - min(score_values) if score_values else 0
            avg_score = sum(score_values) / len(score_values) if score_values else 0
            
            confidence_factors = {
                'score_distribution': min(1.0, score_range * 2),  # Higher range means more confident scoring
                'top_axis_score': max(score_values) if score_values else 0,
                'average_score': avg_score
            }
            
            ka_confidence = self.calculate_confidence(confidence_factors)
            
            # Prepare findings
            findings = {
                'axis_scores': axis_scores,
                'top_axes': [{'axis_id': axis_id, **info} for axis_id, info in top_axes],
                'confidence_factors': confidence_factors
            }
            
            self.log_execution_step("Completed axis scoring", {"ka_confidence": ka_confidence})
            
            return {
                "status": "success",
                "ka_confidence": ka_confidence,
                "findings": findings
            }
        
        except Exception as e:
            error_msg = f"Error scoring axes: {str(e)}"
            logging.error(f"[{datetime.now()}] KA02: {error_msg}", exc_info=True)
            return {
                "status": "error",
                "error_message": error_msg,
                "ka_confidence": 0.0,
                "findings": {}
            }
    
    def _get_all_axes(self) -> List[Dict[str, Any]]:
        """Get all axes from the UKG."""
        axes = []
        
        # In a real implementation, this would query the GraphManager
        # For simplicity, hardcode the 13 axes
        axes = [
            {'number': 1, 'label': 'Pillar Levels', 'original_id': 'Axis1'},
            {'number': 2, 'label': 'Sectors', 'original_id': 'Axis2'},
            {'number': 3, 'label': 'Topics', 'original_id': 'Axis3'},
            {'number': 4, 'label': 'Methods', 'original_id': 'Axis4'},
            {'number': 5, 'label': 'Tools', 'original_id': 'Axis5'},
            {'number': 6, 'label': 'Regulatory Frameworks', 'original_id': 'Axis6'},
            {'number': 7, 'label': 'Compliance Standards', 'original_id': 'Axis7'},
            {'number': 8, 'label': 'Knowledge Experts', 'original_id': 'Axis8'},
            {'number': 9, 'label': 'Skill Experts', 'original_id': 'Axis9'},
            {'number': 10, 'label': 'Role Experts', 'original_id': 'Axis10'},
            {'number': 11, 'label': 'Context Experts', 'original_id': 'Axis11'},
            {'number': 12, 'label': 'Locations', 'original_id': 'Axis12'},
            {'number': 13, 'label': 'Time', 'original_id': 'Axis13'},
        ]
        
        return axes
    
    def _score_axis_relevance(self, axis: Dict[str, Any], query_text: str, ka01_output: Dict[str, Any] = None) -> float:
        """
        Score the relevance of an axis for the query.
        
        Args:
            axis (dict): Axis information
            query_text (str): The query text
            ka01_output (dict, optional): Output from KA01
            
        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        query_lower = query_text.lower()
        axis_number = axis['number']
        
        # Base score
        score = 0.1  # Starting point
        
        # Check axis-specific keywords in query
        if axis_number == 1:  # Pillar Levels
            if any(kw in query_lower for kw in ['domain', 'field', 'pillar', 'discipline', 'area']):
                score += 0.3
        
        elif axis_number == 2:  # Sectors
            if any(kw in query_lower for kw in ['sector', 'industry', 'market', 'business']):
                score += 0.3
            
            # Check for specific sectors if KA01 output is available
            if ka01_output and 'findings' in ka01_output:
                sectors = ka01_output['findings'].get('identified_sectors', [])
                if sectors:
                    score += 0.4
        
        elif axis_number == 3:  # Topics
            if any(kw in query_lower for kw in ['topic', 'subject', 'theme', 'about']):
                score += 0.3
            
            # Check for specific topics if KA01 output is available
            if ka01_output and 'findings' in ka01_output:
                topics = ka01_output['findings'].get('identified_topics', [])
                if topics:
                    score += 0.4
        
        elif axis_number == 4:  # Methods
            if any(kw in query_lower for kw in ['method', 'approach', 'methodology', 'process', 'procedure']):
                score += 0.4
        
        elif axis_number == 5:  # Tools
            if any(kw in query_lower for kw in ['tool', 'software', 'application', 'system', 'platform']):
                score += 0.4
        
        elif axis_number == 6:  # Regulatory Frameworks
            if any(kw in query_lower for kw in ['regulation', 'regulatory', 'law', 'legal', 'rule', 'policy']):
                score += 0.4
            
            # Check for specific regulations if KA01 output is available
            if ka01_output and 'findings' in ka01_output:
                regulations = ka01_output['findings'].get('identified_regulations', [])
                if regulations:
                    score += 0.5
        
        elif axis_number == 7:  # Compliance Standards
            if any(kw in query_lower for kw in ['compliance', 'standard', 'requirement', 'conform', 'adhere']):
                score += 0.4
        
        elif axis_number == 8:  # Knowledge Experts
            if any(kw in query_lower for kw in ['expert', 'knowledge', 'specialist', 'authority', 'expertise']):
                score += 0.3
        
        elif axis_number == 9:  # Skill Experts
            if any(kw in query_lower for kw in ['skill', 'ability', 'capability', 'proficiency', 'competence']):
                score += 0.3
        
        elif axis_number == 10:  # Role Experts
            if any(kw in query_lower for kw in ['role', 'job', 'position', 'responsibility', 'duty']):
                score += 0.3
        
        elif axis_number == 11:  # Context Experts
            if any(kw in query_lower for kw in ['context', 'situation', 'circumstance', 'scenario', 'setting']):
                score += 0.3
        
        elif axis_number == 12:  # Locations
            if any(kw in query_lower for kw in ['location', 'place', 'country', 'region', 'city', 'geographic']):
                score += 0.3
            
            # Check for specific locations if KA01 output is available
            if ka01_output and 'findings' in ka01_output:
                locations = ka01_output['findings'].get('identified_locations', [])
                if locations:
                    score += 0.4
        
        elif axis_number == 13:  # Time
            if any(kw in query_lower for kw in ['time', 'date', 'period', 'duration', 'when', 'history', 'future']):
                score += 0.4
            
            # Check for date patterns
            if re.search(r'\b(19|20)\d{2}\b', query_text):  # Years like 1999, 2023
                score += 0.3
            if re.search(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', query_text):  # Date patterns like 01/01/2023
                score += 0.3
        
        # Apply query type modifier if KA01 output is available
        if ka01_output and 'findings' in ka01_output:
            query_type = ka01_output['findings'].get('query_type', '')
            
            if query_type == 'factual_question':
                if axis_number in [1, 3]:  # Boost Pillar Levels and Topics
                    score += 0.1
            elif query_type == 'explanation_question':
                if axis_number in [4, 8]:  # Boost Methods and Knowledge Experts
                    score += 0.1
            elif query_type == 'comparison_request':
                if axis_number in [2, 6, 7]:  # Boost Sectors, Regulatory Frameworks, and Compliance Standards
                    score += 0.1
        
        # Cap score at 1.0
        return min(1.0, score)
