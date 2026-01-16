"""
Query Analyzer Algorithm

This knowledge algorithm analyzes user queries to extract key concepts,
entities, and intents for further processing in the UKG system.
"""

from core.algorithms.base_algorithm import BaseKnowledgeAlgorithm
import re
import json

class QueryAnalyzerAlgorithm(BaseKnowledgeAlgorithm):
    """
    Query Analyzer Algorithm
    
    This algorithm analyzes user queries to extract key information such as:
    - Primary entities
    - Secondary entities
    - Intents
    - Relationships
    - Query type classification
    
    It forms part of the first layer of processing in the UKG system.
    """
    
    # Knowledge Algorithm metadata
    KA_ID = "QUERY_ANALYZER_KA"
    NAME = "Query Analyzer"
    VERSION = "1.0.0"
    DESCRIPTION = "Analyzes user queries to extract key concepts, entities, and intents"
    
    # Schema definitions (extending the base schema)
    INPUT_SCHEMA = {
        "type": "object",
        "properties": {
            "query_text": {"type": "string"},
            "session_id": {"type": "string"},
            "pass_num": {"type": "integer"},
            "layer_num": {"type": "integer"},
            "prev_layer_results": {"type": "object"}
        },
        "required": ["query_text", "session_id"]
    }
    
    OUTPUT_SCHEMA = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {"type": "object"}
            },
            "intents": {
                "type": "array",
                "items": {"type": "string"}
            },
            "query_type": {"type": "string"},
            "confidence": {"type": "number"},
            "status": {"type": "string"}
        }
    }
    
    # Metadata for the algorithm management system
    METADATA = {
        "applicable_layers": [1],  # This algorithm runs in the first layer
        "applicable_axes": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],  # Relevant to all axes
        "execution_mode": "synchronous",
        "complexity": "high"
    }
    
    def __init__(self):
        """
        Initialize the Query Analyzer algorithm.
        """
        super().__init__()
        
        # Initialize entity patterns (simple regex-based for demonstration)
        self.entity_patterns = {
            'person': r'(?:Dr\.|Mr\.|Mrs\.|Ms\.|Prof\.)?\s?[A-Z][a-z]+ [A-Z][a-z]+',
            'location': r'(?:in|at|from|to)\s([A-Z][a-z]+ ?(?:[A-Z][a-z]+)?)',
            'organization': r'(?:the\s)?([A-Z][a-z]* (?:Company|Corporation|Inc\.|Ltd\.|LLC|Group|Organization))',
            'date': r'\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{2,4}',
            'time': r'\d{1,2}:\d{2} ?(?:AM|PM|am|pm)?'
        }
        
        # Initialize intent patterns
        self.intent_patterns = {
            'search': r'(?:find|search for|look for|locate|discover|show|tell me about)',
            'compare': r'(?:compare|versus|vs\.|difference between|similarities between)',
            'explain': r'(?:explain|describe|what is|define|elaborate on|tell me about)',
            'calculate': r'(?:calculate|compute|determine|find the value of)',
            'locate': r'(?:where is|locate|find the location of)'
        }
        
        # Query type classification
        self.query_types = {
            'factual': r'(?:what|who|where|when|why|how many|how much)',
            'analytical': r'(?:analyze|assess|evaluate|examine|review)',
            'procedural': r'(?:how to|steps to|process for|procedure for)',
            'causal': r'(?:why|what causes|reason for|effect of|impact of)',
            'comparative': r'(?:compare|contrast|difference|better|worse|best|worst)'
        }
    
    def execute(self, input_data: dict) -> dict:
        """
        Execute the Query Analyzer algorithm.
        
        Args:
            input_data: Input data containing the query_text
            
        Returns:
            dict: Analysis results
        """
        # Validate input
        if not self.validate_input(input_data):
            return {
                'status': 'error',
                'message': 'Invalid input data',
                'confidence': 0.0
            }
        
        query_text = input_data.get('query_text', '')
        
        # Perform analysis
        try:
            # Extract entities
            entities = self._extract_entities(query_text)
            
            # Extract intents
            intents = self._extract_intents(query_text)
            
            # Classify query type
            query_type = self._classify_query_type(query_text)
            
            # Calculate confidence based on the richness of extracted information
            confidence = self._calculate_confidence(entities, intents, query_type)
            
            # Prepare result
            result = {
                'status': 'success',
                'entities': entities,
                'intents': intents,
                'query_type': query_type,
                'confidence': confidence,
                'query_text': query_text
            }
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error analyzing query: {str(e)}",
                'confidence': 0.0
            }
    
    def _extract_entities(self, query_text: str) -> list:
        """
        Extract entities from the query text.
        
        Args:
            query_text: User query text
            
        Returns:
            list: Extracted entities with types
        """
        entities = []
        
        # Apply each entity pattern
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query_text)
            for match in matches:
                entities.append({
                    'type': entity_type,
                    'value': match.strip(),
                    'confidence': 0.8  # Fixed confidence for demonstration
                })
        
        return entities
    
    def _extract_intents(self, query_text: str) -> list:
        """
        Extract intents from the query text.
        
        Args:
            query_text: User query text
            
        Returns:
            list: Extracted intents
        """
        intents = []
        
        # Apply each intent pattern
        for intent, pattern in self.intent_patterns.items():
            if re.search(pattern, query_text, re.IGNORECASE):
                intents.append(intent)
        
        return intents
    
    def _classify_query_type(self, query_text: str) -> str:
        """
        Classify the query type.
        
        Args:
            query_text: User query text
            
        Returns:
            str: Query type classification
        """
        for q_type, pattern in self.query_types.items():
            if re.search(pattern, query_text, re.IGNORECASE):
                return q_type
        
        # Default type if no match
        return 'unclassified'
    
    def _calculate_confidence(self, entities: list, intents: list, query_type: str) -> float:
        """
        Calculate confidence score based on extracted information.
        
        Args:
            entities: Extracted entities
            intents: Extracted intents
            query_type: Query type classification
            
        Returns:
            float: Confidence score (0.0-1.0)
        """
        # Base confidence
        confidence = 0.5
        
        # Adjust based on extracted information
        if entities:
            confidence += min(0.2, len(entities) * 0.05)
            
        if intents:
            confidence += min(0.2, len(intents) * 0.1)
            
        if query_type != 'unclassified':
            confidence += 0.1
        
        # Ensure confidence is within bounds
        return min(1.0, max(0.0, confidence))