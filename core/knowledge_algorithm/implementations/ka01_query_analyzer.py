import logging
from datetime import datetime
from typing import Dict, Any, List
import re

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA01(KnowledgeAlgorithm):
    """
    KA01: Query Analyzer
    
    This KA analyzes a query to extract key information and determine its context.
    It performs basic NLP to identify entities, actions, and intentions in the query.
    """
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Query Analyzer KA.
        
        Args:
            input_data (dict): Contains 'query_text' and other optional parameters
            
        Returns:
            dict: Analysis results including entities, actions, and query classification
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
        self.log_execution_step("Processing query", {"query_text": query_text[:50] + "..." if len(query_text) > 50 else query_text})
        
        # Process the query
        try:
            # Extract key elements from the query
            entities = self._extract_entities(query_text)
            actions = self._extract_actions(query_text)
            query_type = self._classify_query_type(query_text)
            topics = self._identify_topics(query_text)
            sectors = self._identify_sectors(query_text)
            regulations = self._identify_regulations(query_text)
            locations = self._identify_locations(query_text)
            
            # Calculate confidence based on various factors
            confidence_factors = {
                'entity_extraction': min(1.0, len(entities) * 0.2),
                'action_clarity': min(1.0, len(actions) * 0.25),
                'query_type_confidence': 0.7 if query_type else 0.3,
                'topic_relevance': min(1.0, len(topics) * 0.2),
                'query_length_adequacy': min(1.0, len(query_text.split()) / 20)
            }
            
            ka_confidence = self.calculate_confidence(confidence_factors)
            
            # Prepare findings
            findings = {
                'extracted_entities': entities,
                'extracted_actions': actions,
                'query_type': query_type,
                'identified_topics': topics,
                'identified_sectors': sectors,
                'identified_regulations': regulations,
                'identified_locations': locations,
                'confidence_factors': confidence_factors
            }
            
            self.log_execution_step("Completed analysis", {"ka_confidence": ka_confidence})
            
            return {
                "status": "success",
                "ka_confidence": ka_confidence,
                "findings": findings
            }
        
        except Exception as e:
            error_msg = f"Error analyzing query: {str(e)}"
            logging.error(f"[{datetime.now()}] KA01: {error_msg}", exc_info=True)
            return {
                "status": "error",
                "error_message": error_msg,
                "ka_confidence": 0.0,
                "findings": {}
            }
    
    def _extract_entities(self, query_text: str) -> List[Dict[str, Any]]:
        """Extract entities from the query text."""
        entities = []
        
        # In a real implementation, this would use NLP techniques
        # For this implementation, use simple pattern matching
        
        # Look for potential entities (capitalized words, except at the beginning of sentences)
        words = query_text.split()
        for i, word in enumerate(words):
            # Skip first word of sentences
            if i == 0 or (i > 0 and words[i-1][-1] in '.!?'):
                continue
            
            # Check for capitalized words that might be entities
            if word[0].isupper() and len(word) > 1:
                entities.append({
                    'text': word,
                    'type': 'potential_entity',
                    'confidence': 0.6
                })
        
        # Look for terms in quotes
        quoted_terms = re.findall(r'"([^"]*)"', query_text)
        for term in quoted_terms:
            entities.append({
                'text': term,
                'type': 'quoted_term',
                'confidence': 0.8
            })
        
        # Look for numeric values
        numeric_values = re.findall(r'\b\d+(?:\.\d+)?\b', query_text)
        for value in numeric_values:
            entities.append({
                'text': value,
                'type': 'numeric_value',
                'confidence': 0.9
            })
        
        return entities
    
    def _extract_actions(self, query_text: str) -> List[str]:
        """Extract action verbs from the query text."""
        # Common action verbs in queries
        action_verbs = [
            'analyze', 'explain', 'describe', 'compare', 'summarize',
            'list', 'find', 'identify', 'evaluate', 'recommend',
            'tell', 'show', 'calculate', 'compute', 'determine'
        ]
        
        # Extract actions that appear in the query
        words = re.findall(r'\b\w+\b', query_text.lower())
        actions_found = [verb for verb in action_verbs if verb in words]
        
        return actions_found
    
    def _classify_query_type(self, query_text: str) -> str:
        """Classify the query type."""
        query_lower = query_text.lower()
        
        # Check if it's a question
        if '?' in query_text:
            if any(word in query_lower for word in ['what', 'which', 'who']):
                return 'factual_question'
            elif any(word in query_lower for word in ['how', 'why']):
                return 'explanation_question'
            elif any(word in query_lower for word in ['can', 'could', 'would', 'will']):
                return 'possibility_question'
            else:
                return 'general_question'
        
        # Check if it's a command/request
        if any(word in query_lower for word in ['list', 'find', 'show', 'tell', 'give']):
            return 'command_request'
        
        # Check if it's a comparison
        if any(word in query_lower for word in ['compare', 'difference', 'versus', 'vs']):
            return 'comparison_request'
        
        # Default to general query
        return 'general_query'
    
    def _identify_topics(self, query_text: str) -> List[Dict[str, Any]]:
        """Identify topics in the query that match known topics in the UKG."""
        topics = []
        
        # In a real implementation, this would query the UKG for matching topics
        # For this implementation, use simple checks for common topics
        
        query_lower = query_text.lower()
        
        # Check for topic-related keywords
        topic_keywords = {
            'cybersecurity': ['cybersecurity', 'cyber security', 'hacking', 'encryption', 'firewall'],
            'finance': ['finance', 'financial', 'budget', 'investment', 'funding'],
            'environment': ['environment', 'environmental', 'ecology', 'sustainability'],
            'healthcare': ['healthcare', 'health care', 'medical', 'clinical', 'patient'],
            'legal': ['legal', 'law', 'regulation', 'compliance', 'policy']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                topics.append({
                    'topic': topic,
                    'confidence': 0.7
                })
        
        return topics
    
    def _identify_sectors(self, query_text: str) -> List[Dict[str, Any]]:
        """Identify sectors in the query that match known sectors in the UKG."""
        sectors = []
        
        # In a real implementation, this would query the UKG for matching sectors
        # For this implementation, use simple checks for common sectors
        
        query_lower = query_text.lower()
        
        # Check for sector-related keywords
        sector_keywords = {
            'government': ['government', 'federal', 'state', 'municipal', 'public sector'],
            'healthcare': ['healthcare', 'hospital', 'medical', 'clinical'],
            'finance': ['banking', 'finance', 'financial', 'investment', 'insurance'],
            'education': ['education', 'school', 'university', 'academic', 'college'],
            'technology': ['technology', 'tech', 'IT', 'software', 'hardware']
        }
        
        for sector, keywords in sector_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                sectors.append({
                    'sector': sector,
                    'confidence': 0.7
                })
        
        return sectors
    
    def _identify_regulations(self, query_text: str) -> List[Dict[str, Any]]:
        """Identify regulations in the query that match known regulatory frameworks in the UKG."""
        regulations = []
        
        # In a real implementation, this would query the UKG for matching regulations
        # For this implementation, use simple checks for common regulations
        
        query_lower = query_text.lower()
        
        # Check for regulation-related keywords
        regulation_keywords = {
            'GDPR': ['gdpr', 'general data protection regulation'],
            'HIPAA': ['hipaa', 'health insurance portability'],
            'SOX': ['sox', 'sarbanes-oxley', 'sarbanes oxley'],
            'CCPA': ['ccpa', 'california consumer privacy'],
            'FAR': ['far', 'federal acquisition regulation']
        }
        
        for regulation, keywords in regulation_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                regulations.append({
                    'regulation': regulation,
                    'confidence': 0.8
                })
        
        return regulations
    
    def _identify_locations(self, query_text: str) -> List[Dict[str, Any]]:
        """Identify locations in the query that match known locations in the UKG."""
        locations = []
        
        # In a real implementation, this would query the UKG for matching locations
        # For this implementation, use simple checks for common locations
        
        query_lower = query_text.lower()
        
        # Check for location-related keywords
        location_keywords = {
            'USA': ['usa', 'united states', 'america', 'u.s.'],
            'EU': ['eu', 'european union', 'europe'],
            'UK': ['uk', 'united kingdom', 'britain'],
            'California': ['california', 'ca'],
            'Texas': ['texas', 'tx'],
            'Germany': ['germany', 'german'],
            'Canada': ['canada', 'canadian']
        }
        
        for location, keywords in location_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                locations.append({
                    'location': location,
                    'confidence': 0.7
                })
        
        return locations
