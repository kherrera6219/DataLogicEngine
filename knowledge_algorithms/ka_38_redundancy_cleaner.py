"""
KA-38: Redundancy and Bias Cleaner

This algorithm detects and removes redundancies, duplications, and potential biases
from simulation outputs, ensuring concise and balanced results.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
import time
import re
from collections import Counter

logger = logging.getLogger(__name__)

class RedundancyBiasCleaner:
    """
    KA-38: Detects and removes redundancies and biases from outputs.
    
    This algorithm analyzes simulation outputs to identify and eliminate
    duplications, redundancies, and potential biases, improving clarity and balance.
    """
    
    def __init__(self):
        """Initialize the Redundancy and Bias Cleaner."""
        self.redundancy_patterns = self._initialize_redundancy_patterns()
        self.bias_indicators = self._initialize_bias_indicators()
        logger.info("KA-38: Redundancy and Bias Cleaner initialized")
    
    def _initialize_redundancy_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for detecting redundancies."""
        return {
            "exact_duplication": {
                "description": "Exactly identical content appearing multiple times",
                "detection_method": "string_equality",
                "severity": "high"
            },
            "semantic_repetition": {
                "description": "Similar meaning expressed in different words",
                "detection_method": "semantic_similarity",
                "severity": "medium"
            },
            "circular_explanation": {
                "description": "Content that repeats core concepts without adding information",
                "detection_method": "keyword_frequency",
                "severity": "medium"
            },
            "nested_duplication": {
                "description": "Content where a smaller chunk is contained within larger chunks",
                "detection_method": "substring_analysis",
                "severity": "low"
            },
            "overspecification": {
                "description": "Excessive detail that doesn't add value",
                "detection_method": "complexity_ratio",
                "severity": "low"
            }
        }
    
    def _initialize_bias_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Initialize indicators for detecting potential bias."""
        return {
            "perspective_bias": {
                "description": "Presenting only one viewpoint on a topic",
                "detection_patterns": [
                    r"(?:always|never|everyone|nobody)\b",
                    r"(?:clearly|obviously|undoubtedly)\b",
                    r"(?:only|just|simply)\s+(?:one|a single)\s+(?:way|approach|option)"
                ],
                "severity": "high"
            },
            "authority_bias": {
                "description": "Over-reliance on authority or credentials",
                "detection_patterns": [
                    r"(?:experts|authorities|professionals)\s+(?:all|universally)\s+(?:agree|believe|recommend)",
                    r"(?:according to|as stated by)\s+(?:leading|prominent|respected)",
                    r"(?:science|research|studies)\s+(?:proves|confirms|establishes)"
                ],
                "severity": "medium"
            },
            "recency_bias": {
                "description": "Overemphasizing recent information",
                "detection_patterns": [
                    r"(?:recent|latest|newest|current)\s+(?:research|studies|findings|data)\s+(?:shows|indicates|suggests)",
                    r"(?:no longer|outdated|obsolete)\s+(?:approach|thinking|methodology)",
                    r"(?:traditional|conventional|historical)\s+(?:approaches|methods|thinking)\s+(?:are not|aren't)"
                ],
                "severity": "medium"
            },
            "confirmation_bias": {
                "description": "Emphasizing evidence that supports predetermined conclusions",
                "detection_patterns": [
                    r"(?:this|that|these|those)\s+(?:confirms|supports|aligns with|validates)",
                    r"(?:as expected|as anticipated|unsurprisingly)",
                    r"(?:clearly|obviously)\s+(?:demonstrates|shows|proves)"
                ],
                "severity": "high"
            },
            "emotional_bias": {
                "description": "Using emotional language that could influence interpretation",
                "detection_patterns": [
                    r"(?:unfortunately|sadly|regrettably|disappointingly)",
                    r"(?:exciting|promising|encouraging|remarkable)",
                    r"(?:shocking|alarming|concerning|troubling)"
                ],
                "severity": "medium"
            }
        }
    
    def clean_outputs(self, outputs: List[str], clean_redundancy: bool = True,
                    detect_bias: bool = True, similarity_threshold: float = 0.6) -> Dict[str, Any]:
        """
        Clean outputs by removing redundancies and detecting biases.
        
        Args:
            outputs: List of output strings to clean
            clean_redundancy: Whether to clean redundancies
            detect_bias: Whether to detect bias
            similarity_threshold: Threshold for detecting similar outputs
            
        Returns:
            Dictionary with cleaning results
        """
        # Skip empty outputs
        if not outputs:
            return {
                "cleaned_outputs": [],
                "original_count": 0,
                "final_count": 0,
                "redundancies_removed": 0,
                "biases_detected": []
            }
        
        # Initialize tracking structures
        original_count = len(outputs)
        removed_indices = set()
        redundancy_instances = []
        bias_instances = []
        
        # Clean redundancies if requested
        if clean_redundancy:
            removed_indices, redundancy_instances = self._clean_redundancies(
                outputs, similarity_threshold
            )
        
        # Detect biases if requested
        if detect_bias:
            bias_instances = self._detect_biases(outputs)
        
        # Create cleaned output list
        cleaned_outputs = [
            output for i, output in enumerate(outputs)
            if i not in removed_indices
        ]
        
        # Final counts
        final_count = len(cleaned_outputs)
        redundancies_removed = original_count - final_count
        
        return {
            "cleaned_outputs": cleaned_outputs,
            "original_count": original_count,
            "final_count": final_count,
            "redundancies_removed": redundancies_removed,
            "redundancy_instances": redundancy_instances,
            "bias_instances": bias_instances
        }
    
    def _clean_redundancies(self, outputs: List[str], 
                         similarity_threshold: float) -> Tuple[Set[int], List[Dict[str, Any]]]:
        """
        Clean redundancies from outputs.
        
        Args:
            outputs: List of output strings
            similarity_threshold: Threshold for semantic similarity
            
        Returns:
            Tuple of (removed_indices, redundancy_instances)
        """
        removed_indices = set()
        redundancy_instances = []
        
        # Check for exact duplications (simplest case)
        seen_outputs = {}
        for i, output in enumerate(outputs):
            # Normalize output for comparison
            normalized = self._normalize_text(output)
            
            # Check if already seen
            if normalized in seen_outputs:
                # Record redundancy
                redundancy_instances.append({
                    "type": "exact_duplication",
                    "first_index": seen_outputs[normalized],
                    "duplicate_index": i,
                    "content": output,
                    "severity": "high"
                })
                
                # Mark for removal
                removed_indices.add(i)
            else:
                seen_outputs[normalized] = i
        
        # Check for nested duplications
        for i, output_i in enumerate(outputs):
            if i in removed_indices:
                continue  # Skip already removed
            
            for j, output_j in enumerate(outputs):
                if j in removed_indices or i == j:
                    continue  # Skip already removed or same index
                
                # Check if one is contained within the other
                if len(output_i) < len(output_j) and output_i in output_j:
                    # output_i is a subset of output_j
                    redundancy_instances.append({
                        "type": "nested_duplication",
                        "container_index": j,
                        "nested_index": i,
                        "nested_content": output_i,
                        "severity": "low"
                    })
                    
                    # Mark smaller one for removal
                    removed_indices.add(i)
                    break
                elif len(output_j) < len(output_i) and output_j in output_i:
                    # output_j is a subset of output_i
                    redundancy_instances.append({
                        "type": "nested_duplication",
                        "container_index": i,
                        "nested_index": j,
                        "nested_content": output_j,
                        "severity": "low"
                    })
                    
                    # Mark smaller one for removal
                    removed_indices.add(j)
        
        # Check for semantic repetition
        for i, output_i in enumerate(outputs):
            if i in removed_indices:
                continue  # Skip already removed
            
            for j in range(i + 1, len(outputs)):
                if j in removed_indices:
                    continue  # Skip already removed
                
                output_j = outputs[j]
                
                # Calculate semantic similarity
                similarity = self._calculate_semantic_similarity(output_i, output_j)
                
                if similarity >= similarity_threshold:
                    # Record redundancy
                    redundancy_instances.append({
                        "type": "semantic_repetition",
                        "first_index": i,
                        "similar_index": j,
                        "similarity_score": similarity,
                        "severity": "medium"
                    })
                    
                    # Mark second one for removal
                    removed_indices.add(j)
        
        # Check for circular explanations (repetitive keywords)
        for i, output in enumerate(outputs):
            if i in removed_indices:
                continue  # Skip already removed
            
            # Check keyword frequency
            keyword_ratio = self._calculate_keyword_ratio(output)
            
            if keyword_ratio > 0.2:  # Over 20% repetition
                redundancy_instances.append({
                    "type": "circular_explanation",
                    "index": i,
                    "keyword_ratio": keyword_ratio,
                    "severity": "medium"
                })
                
                # Don't mark for removal, just flag for review
        
        return removed_indices, redundancy_instances
    
    def _detect_biases(self, outputs: List[str]) -> List[Dict[str, Any]]:
        """
        Detect potential biases in outputs.
        
        Args:
            outputs: List of output strings
            
        Returns:
            List of detected bias instances
        """
        bias_instances = []
        
        # Check each output for bias indicators
        for i, output in enumerate(outputs):
            output_lower = output.lower()
            
            # Check each bias type
            for bias_type, bias_info in self.bias_indicators.items():
                detection_patterns = bias_info["detection_patterns"]
                matches = []
                
                # Check each pattern for this bias type
                for pattern in detection_patterns:
                    pattern_matches = re.findall(pattern, output_lower)
                    matches.extend(pattern_matches)
                
                # If matches found, record bias instance
                if matches:
                    bias_instances.append({
                        "type": bias_type,
                        "index": i,
                        "matches": matches,
                        "severity": bias_info["severity"],
                        "description": bias_info["description"]
                    })
        
        return bias_instances
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        Args:
            text: The text to normalize
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.
        
        In a real implementation, this would use embedding-based similarity.
        For this demonstration, we'll use a simple approximation based on word overlap.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        # Normalize texts
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        # Split into words
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _calculate_keyword_ratio(self, text: str) -> float:
        """
        Calculate ratio of repeated keywords to total words.
        
        Args:
            text: The text to analyze
            
        Returns:
            Ratio of repetition
        """
        # Normalize text
        normalized = self._normalize_text(text)
        
        # Split into words
        words = normalized.split()
        
        if not words:
            return 0.0
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Calculate repeated keywords (appearing more than once)
        repeated_keywords = sum(count - 1 for count in word_counts.values() if count > 1)
        
        # Calculate ratio
        return repeated_keywords / len(words)
    
    def analyze_output_balance(self, outputs: List[str]) -> Dict[str, Any]:
        """
        Analyze output balance and representation.
        
        Args:
            outputs: List of output strings to analyze
            
        Returns:
            Dictionary with balance analysis
        """
        if not outputs:
            return {
                "balance_score": 0.0,
                "perspective_count": 0,
                "analysis": "Empty output set"
            }
        
        # Initialize analysis
        perspective_markers = {
            "advantages": ["benefit", "advantage", "pro", "positive", "strength", "opportunity"],
            "disadvantages": ["drawback", "disadvantage", "con", "negative", "weakness", "threat", "risk"],
            "neutral": ["however", "nevertheless", "alternatively", "whereas", "while", "on the other hand"]
        }
        
        # Count perspective markers
        perspective_counts = {category: 0 for category in perspective_markers}
        
        for output in outputs:
            output_lower = output.lower()
            
            for category, markers in perspective_markers.items():
                for marker in markers:
                    perspective_counts[category] += output_lower.count(marker)
        
        # Calculate balance metrics
        total_markers = sum(perspective_counts.values())
        
        if total_markers == 0:
            balance_score = 0.5  # Neutral if no markers
        else:
            # Calculate how evenly distributed markers are across perspectives
            expected_per_category = total_markers / len(perspective_markers)
            deviations = sum(abs(count - expected_per_category) for count in perspective_counts.values())
            max_deviation = 2 * expected_per_category * (len(perspective_markers) - 1)
            
            if max_deviation == 0:
                balance_score = 1.0
            else:
                # 1.0 = perfectly balanced, 0.0 = completely imbalanced
                balance_score = 1.0 - (deviations / max_deviation)
        
        # Generate analysis
        if balance_score >= 0.8:
            analysis = "Well-balanced output with multiple perspectives"
        elif balance_score >= 0.5:
            analysis = "Moderately balanced output with some perspective diversity"
        else:
            # Determine dominant perspective
            dominant = max(perspective_counts.items(), key=lambda x: x[1])[0]
            analysis = f"Potentially imbalanced output with '{dominant}' perspective dominant"
        
        return {
            "balance_score": balance_score,
            "perspective_counts": perspective_counts,
            "total_perspective_markers": total_markers,
            "analysis": analysis
        }


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Redundancy and Bias Cleaner (KA-38) on the provided data.
    
    Args:
        data: A dictionary containing outputs to clean
        
    Returns:
        Dictionary with cleaned outputs
    """
    outputs = data.get("outputs", [])
    clean_redundancy = data.get("clean_redundancy", True)
    detect_bias = data.get("detect_bias", True)
    similarity_threshold = data.get("similarity_threshold", 0.6)
    analyze_balance = data.get("analyze_balance", False)
    
    cleaner = RedundancyBiasCleaner()
    
    # Clean outputs
    result = cleaner.clean_outputs(outputs, clean_redundancy, detect_bias, similarity_threshold)
    
    # Add balance analysis if requested
    if analyze_balance:
        balance_analysis = cleaner.analyze_output_balance(outputs)
        result["balance_analysis"] = balance_analysis
    
    return {
        "algorithm": "KA-38",
        "cleaned_outputs": result["cleaned_outputs"],
        "original_count": result["original_count"],
        "success": True,
        "timestamp": time.time(),
        **{k: v for k, v in result.items() if k not in ["cleaned_outputs", "original_count"]}
    }