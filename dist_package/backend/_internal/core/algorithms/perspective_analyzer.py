"""
Perspective Analyzer Algorithm

This knowledge algorithm analyzes content to identify different perspectives
and viewpoints, supporting Axis 6 (Perspective) of the UKG system.
"""

from core.algorithms.base_algorithm import BaseKnowledgeAlgorithm
import re
import json

class PerspectiveAnalyzerAlgorithm(BaseKnowledgeAlgorithm):
    """
    Perspective Analyzer Algorithm
    
    This algorithm identifies and analyzes different perspectives and viewpoints
    within content. It supports Axis 6 (Perspective) of the UKG system and helps
    in understanding the different ways knowledge can be viewed and interpreted.
    """
    
    # Knowledge Algorithm metadata
    KA_ID = "PERSPECTIVE_ANALYZER_KA"
    NAME = "Perspective Analyzer"
    VERSION = "1.0.0"
    DESCRIPTION = "Analyzes content to identify different perspectives and viewpoints"
    
    # Schema definitions
    INPUT_SCHEMA = {
        "type": "object",
        "properties": {
            "query_text": {"type": "string"},
            "session_id": {"type": "string"},
            "pass_num": {"type": "integer"},
            "layer_num": {"type": "integer"},
            "content": {"type": "string"},
            "prev_layer_results": {"type": "object"}
        },
        "required": ["query_text", "session_id"]
    }
    
    OUTPUT_SCHEMA = {
        "type": "object",
        "properties": {
            "perspectives": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "perspective_type": {"type": "string"},
                        "stance": {"type": "string"},
                        "confidence": {"type": "number"},
                        "key_points": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            },
            "content_analysis": {"type": "object"},
            "confidence": {"type": "number"},
            "status": {"type": "string"}
        }
    }
    
    # Metadata for the algorithm management system
    METADATA = {
        "applicable_layers": [3, 4],  # This algorithm runs in layer 3 and 4
        "applicable_axes": [6],  # Primarily for Axis 6 (Perspective)
        "execution_mode": "synchronous",
        "complexity": "high"
    }
    
    def __init__(self):
        """
        Initialize the Perspective Analyzer algorithm.
        """
        super().__init__()
        
        # Initialize perspective identification patterns
        self.perspective_patterns = {
            'economic': {
                'capitalist': [
                    r'free market', r'economic freedom', r'private property',
                    r'laissez-faire', r'capitalism', r'investor', r'profit motive',
                    r'entrepreneurship', r'deregulation', r'market-driven'
                ],
                'socialist': [
                    r'wealth redistribution', r'economic equality', r'public ownership',
                    r'workers rights', r'class struggle', r'labor union', r'social welfare',
                    r'centralized planning', r'socialism', r'collectivism'
                ],
                'mixed_economy': [
                    r'regulatory framework', r'public-private partnership',
                    r'social safety net', r'managed economy', r'keynesian',
                    r'stakeholder capitalism', r'economic regulation', r'market intervention'
                ]
            },
            'political': {
                'conservative': [
                    r'traditional values', r'national security', r'limited government',
                    r'fiscal responsibility', r'patriotism', r'constitutional',
                    r'heritage', r'family values', r'stable society', r'authority'
                ],
                'liberal': [
                    r'progressive', r'social justice', r'civil liberties',
                    r'equality', r'reform', r'human rights', r'diversity',
                    r'inclusion', r'environmental protection', r'social progress'
                ],
                'libertarian': [
                    r'individual liberty', r'voluntarism', r'non-aggression',
                    r'minimal state', r'self-determination', r'freedom of choice',
                    r'personal responsibility', r'civil liberties', r'decentralization'
                ]
            },
            'ethical': {
                'utilitarian': [
                    r'greatest good', r'maximum happiness', r'utility',
                    r'consequences', r'outcome-based', r'cost-benefit',
                    r'aggregate welfare', r'net benefit', r'social utility'
                ],
                'deontological': [
                    r'moral duty', r'categorical imperative', r'universal law',
                    r'human dignity', r'rights-based', r'moral worth',
                    r'obligation', r'moral principles', r'moral rules'
                ],
                'virtue_ethics': [
                    r'character', r'virtue', r'flourishing', r'eudaimonia',
                    r'moral excellence', r'human nature', r'moral character',
                    r'wisdom', r'temperance', r'practical wisdom'
                ],
                'relativistic': [
                    r'cultural context', r'moral relativism', r'subjective ethics',
                    r'cultural norms', r'moral pluralism', r'descriptive ethics',
                    r'ethical pluralism', r'normative relativism', r'cultural values'
                ]
            },
            'scientific': {
                'empirical': [
                    r'evidence-based', r'experimental', r'observational',
                    r'data-driven', r'reproducible', r'statistical',
                    r'empirical observation', r'measurement', r'quantifiable'
                ],
                'theoretical': [
                    r'conceptual framework', r'theoretical model', r'hypothesis',
                    r'abstract reasoning', r'logical deduction', r'paradigm',
                    r'scientific theory', r'thought experiment', r'prediction'
                ],
                'pragmatic': [
                    r'application', r'problem-solving', r'practical utility',
                    r'real-world impact', r'technological implementation', r'verification',
                    r'practical consequences', r'usefulness', r'effectiveness'
                ]
            }
        }
        
        # Initialize stance detection patterns
        self.stance_patterns = {
            'supportive': [
                r'support', r'agree', r'advocate', r'favor', r'endorse',
                r'approve', r'champion', r'back', r'promote', r'defend'
            ],
            'critical': [
                r'criticize', r'oppose', r'reject', r'disagree', r'condemn',
                r'disapprove', r'denounce', r'refute', r'dispute', r'challenge'
            ],
            'neutral': [
                r'observe', r'analyze', r'consider', r'examine', r'study',
                r'evaluate', r'assess', r'review', r'investigate', r'explore'
            ],
            'balanced': [
                r'on one hand.*on the other hand', r'pros and cons',
                r'advantages and disadvantages', r'strengths and weaknesses',
                r'both sides', r'multiple viewpoints', r'balanced view',
                r'different perspectives', r'nuanced approach'
            ]
        }
    
    def execute(self, input_data: dict) -> dict:
        """
        Execute the Perspective Analyzer algorithm.
        
        Args:
            input_data: Input data containing the text to analyze
            
        Returns:
            dict: Analysis results with identified perspectives
        """
        # Validate input
        if not self.validate_input(input_data):
            return {
                'status': 'error',
                'message': 'Invalid input data',
                'confidence': 0.0
            }
        
        # Get query text and content to analyze
        query_text = input_data.get('query_text', '')
        
        # Get content from input or previous layer results
        content = input_data.get('content', '')
        if not content and 'prev_layer_results' in input_data and input_data['prev_layer_results']:
            prev_results = input_data['prev_layer_results']
            if 'result' in prev_results and 'query_text' in prev_results['result']:
                content = prev_results['result']['query_text']
        
        # If no content, use query text
        if not content:
            content = query_text
        
        # Perform analysis
        try:
            # Analyze content for perspectives
            identified_perspectives = self._identify_perspectives(content)
            
            # Analyze stances
            for perspective in identified_perspectives:
                perspective['stance'] = self._determine_stance(content, perspective)
                
                # Add key points (simplified implementation)
                perspective['key_points'] = self._extract_key_points(content, perspective)
            
            # Perform overall content analysis
            content_analysis = self._analyze_content(content, identified_perspectives)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(identified_perspectives, content)
            
            # Prepare result
            result = {
                'status': 'success',
                'perspectives': identified_perspectives,
                'content_analysis': content_analysis,
                'confidence': confidence,
                'analyzed_text': content[:200] + '...' if len(content) > 200 else content  # Truncate for readability
            }
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error analyzing perspectives: {str(e)}",
                'confidence': 0.0
            }
    
    def _identify_perspectives(self, text: str) -> list:
        """
        Identify perspectives in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            list: Identified perspectives
        """
        perspectives = []
        text_lower = text.lower()
        
        # Check each perspective type and subtype
        for perspective_type, subtypes in self.perspective_patterns.items():
            for subtype, patterns in subtypes.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        matches += 1
                
                # If we found enough matches, add this perspective
                if matches > 0:
                    confidence = min(0.5 + (matches / len(patterns)) * 0.5, 1.0)
                    perspectives.append({
                        'perspective_type': perspective_type,
                        'subtype': subtype,
                        'confidence': confidence,
                        'matches': matches
                    })
        
        # Sort by confidence
        perspectives.sort(key=lambda p: p['confidence'], reverse=True)
        
        return perspectives
    
    def _determine_stance(self, text: str, perspective: dict) -> str:
        """
        Determine the stance toward a particular perspective.
        
        Args:
            text: The text to analyze
            perspective: The perspective to analyze stance for
            
        Returns:
            str: Determined stance
        """
        text_lower = text.lower()
        stance_scores = {}
        
        # Check each stance
        for stance, patterns in self.stance_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                score += len(matches)
            
            if score > 0:
                stance_scores[stance] = score
        
        # If no stances detected, return 'unknown'
        if not stance_scores:
            return 'unknown'
        
        # Return the stance with the highest score
        return max(stance_scores.items(), key=lambda x: x[1])[0]
    
    def _extract_key_points(self, text: str, perspective: dict) -> list:
        """
        Extract key points related to a perspective.
        
        Args:
            text: The text to analyze
            perspective: The perspective to extract key points for
            
        Returns:
            list: Key points
        """
        # This is a simplified implementation
        # In a real system, this would use more sophisticated NLP techniques
        
        perspective_type = perspective['perspective_type']
        subtype = perspective['subtype']
        
        # Get patterns related to this perspective
        patterns = self.perspective_patterns.get(perspective_type, {}).get(subtype, [])
        
        # Find sentences containing these patterns
        key_points = []
        
        # Split text into sentences (simplified)
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            for pattern in patterns:
                if re.search(pattern, sentence.lower()):
                    # Avoid duplicates
                    if sentence not in key_points:
                        key_points.append(sentence)
                    break
        
        # Limit to max 5 key points
        return key_points[:5]
    
    def _analyze_content(self, text: str, perspectives: list) -> dict:
        """
        Perform overall analysis of the content.
        
        Args:
            text: The text to analyze
            perspectives: Identified perspectives
            
        Returns:
            dict: Content analysis
        """
        # Calculate perspective diversity
        perspective_types = set(p['perspective_type'] for p in perspectives)
        diversity_score = min(len(perspective_types) / 4, 1.0)  # Normalize to 0-1
        
        # Determine dominant perspective (if any)
        dominant_perspective = None
        if perspectives:
            # Get perspective with highest confidence
            dominant_perspective = perspectives[0]['perspective_type'] + '/' + perspectives[0]['subtype']
        
        # Simplified sentiment analysis
        sentiment = self._analyze_sentiment(text)
        
        return {
            'perspective_diversity': diversity_score,
            'dominant_perspective': dominant_perspective,
            'sentiment': sentiment,
            'perspective_count': len(perspectives),
            'unique_perspective_types': list(perspective_types)
        }
    
    def _analyze_sentiment(self, text: str) -> str:
        """
        Perform very basic sentiment analysis.
        
        Args:
            text: The text to analyze
            
        Returns:
            str: Sentiment classification
        """
        text_lower = text.lower()
        
        # Define basic sentiment patterns
        positive_patterns = [
            r'good', r'great', r'excellent', r'positive', r'beneficial',
            r'advantage', r'helpful', r'effective', r'useful', r'success'
        ]
        
        negative_patterns = [
            r'bad', r'poor', r'negative', r'harmful', r'disadvantage',
            r'ineffective', r'useless', r'failure', r'problem', r'issue'
        ]
        
        # Count matches
        positive_count = sum(1 for pattern in positive_patterns if re.search(pattern, text_lower))
        negative_count = sum(1 for pattern in negative_patterns if re.search(pattern, text_lower))
        
        # Determine sentiment
        if positive_count > negative_count * 2:
            return 'very positive'
        elif positive_count > negative_count:
            return 'somewhat positive'
        elif negative_count > positive_count * 2:
            return 'very negative'
        elif negative_count > positive_count:
            return 'somewhat negative'
        else:
            return 'neutral'
    
    def _calculate_confidence(self, perspectives: list, text: str) -> float:
        """
        Calculate overall confidence in the analysis.
        
        Args:
            perspectives: Identified perspectives
            text: The analyzed text
            
        Returns:
            float: Confidence score (0.0-1.0)
        """
        # Base confidence
        confidence = 0.5
        
        # Adjust based on identified perspectives
        if perspectives:
            # Average perspective confidence
            avg_perspective_confidence = sum(p['confidence'] for p in perspectives) / len(perspectives)
            confidence = (confidence + avg_perspective_confidence) / 2
            
            # Adjust based on number of perspectives
            perspective_count_factor = min(len(perspectives) / 5, 1.0) * 0.2
            confidence += perspective_count_factor
        else:
            # Reduce confidence if no perspectives found
            confidence -= 0.2
        
        # Adjust based on text length (longer text generally allows for better analysis)
        text_length_factor = min(len(text) / 1000, 1.0) * 0.1
        confidence += text_length_factor
        
        # Ensure confidence is within bounds
        return min(1.0, max(0.0, confidence))