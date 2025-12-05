"""
KA-52: Attention Layer Mapper

This algorithm maps attention mechanisms across neural layers, analyzing
focus points, attention weights, and cross-connections between information streams.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import time
import math
import random
import numpy as np

logger = logging.getLogger(__name__)

class AttentionLayerMapper:
    """
    KA-52: Maps and analyzes attention mechanisms across neural simulations.
    
    This algorithm focuses on identifying attention patterns, head configurations,
    and focus distributions across simulated neural pathways. It enables mapping
    of where information concentrates during processing and how attention shifts
    through processing steps.
    """
    
    def __init__(self):
        """Initialize the Attention Layer Mapper."""
        self.attention_patterns = self._initialize_attention_patterns()
        self.head_configurations = self._initialize_head_configurations()
        self.attention_metrics = self._initialize_attention_metrics()
        logger.info("KA-52: Attention Layer Mapper initialized")
    
    def _initialize_attention_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize common attention patterns."""
        return {
            "uniform": {
                "description": "Equal attention distribution across all inputs",
                "characteristics": ["stable", "general-purpose"],
                "use_case": "Initial information gathering",
                "entropy": "high"
            },
            "focused": {
                "description": "Concentrated attention on specific inputs",
                "characteristics": ["selective", "detail-oriented"],
                "use_case": "Critical information extraction",
                "entropy": "low"
            },
            "sequential": {
                "description": "Attention shifts sequentially through inputs",
                "characteristics": ["ordered", "temporal"],
                "use_case": "Processing ordered information",
                "entropy": "medium"
            },
            "contextual": {
                "description": "Attention based on context relevance",
                "characteristics": ["adaptive", "relevance-based"],
                "use_case": "Contextual understanding",
                "entropy": "medium-high"
            },
            "multi-focus": {
                "description": "Multiple attention peaks distributed across inputs",
                "characteristics": ["parallel", "multi-channel"],
                "use_case": "Multi-aspect analysis",
                "entropy": "medium-high"
            },
            "decaying": {
                "description": "Attention diminishes with distance or time",
                "characteristics": ["proximity-based", "temporal"],
                "use_case": "Proximity-based processing",
                "entropy": "medium-low"
            }
        }
    
    def _initialize_head_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Initialize head configurations for multi-head attention."""
        return {
            "single": {
                "description": "One attention mechanism processing all inputs",
                "optimal_inputs": 8,
                "specialization": "none",
                "complexity": "low"
            },
            "dual": {
                "description": "Two parallel attention mechanisms",
                "optimal_inputs": 16,
                "specialization": "basic",
                "complexity": "low-medium"
            },
            "quad": {
                "description": "Four specialized attention mechanisms",
                "optimal_inputs": 32,
                "specialization": "moderate",
                "complexity": "medium"
            },
            "octo": {
                "description": "Eight highly specialized attention mechanisms",
                "optimal_inputs": 64,
                "specialization": "high",
                "complexity": "high"
            },
            "adaptive": {
                "description": "Dynamic number of attention mechanisms based on input",
                "optimal_inputs": "variable",
                "specialization": "adaptive",
                "complexity": "very-high"
            }
        }
    
    def _initialize_attention_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize metrics for evaluating attention quality."""
        return {
            "coverage": {
                "description": "Percentage of input space covered by attention",
                "optimal_range": [0.8, 1.0],
                "critical_threshold": 0.5
            },
            "specificity": {
                "description": "How precisely attention targets relevant information",
                "optimal_range": [0.7, 0.9],
                "critical_threshold": 0.4
            },
            "entropy": {
                "description": "Randomness in attention distribution",
                "optimal_range": [0.3, 0.7],
                "critical_threshold": 0.9
            },
            "consistency": {
                "description": "Stability of attention patterns over time",
                "optimal_range": [0.6, 0.8],
                "critical_threshold": 0.3
            },
            "responsiveness": {
                "description": "How quickly attention shifts to relevant inputs",
                "optimal_range": [0.7, 0.95],
                "critical_threshold": 0.5
            }
        }
    
    def map_attention_layer(self, 
                         inputs: List[Dict[str, Any]], 
                         config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Map attention across inputs and identify patterns.
        
        Args:
            inputs: List of input tokens or neurons to analyze
            config: Optional configuration parameters
            
        Returns:
            Dictionary with attention mapping results
        """
        # Set default configuration if not provided
        if config is None:
            config = {
                "head_count": 4,
                "attention_type": "auto",
                "max_sequence_length": 100,
                "sensitivity": 0.7,
                "depth": 3,
                "include_cross_attention": True
            }
        
        # Validate inputs
        if not inputs:
            return {
                "success": False,
                "error": "No inputs provided for attention mapping",
                "attention_map": None
            }
        
        # Extract input sequence if too long
        if len(inputs) > config["max_sequence_length"]:
            inputs = inputs[:config["max_sequence_length"]]
        
        # Determine appropriate head configuration
        head_config = self._determine_head_configuration(len(inputs), config["head_count"])
        
        # Determine attention pattern type if auto
        if config["attention_type"] == "auto":
            attention_type = self._infer_attention_type(inputs)
        else:
            attention_type = config["attention_type"]
            # Fallback if the specified type is invalid
            if attention_type not in self.attention_patterns:
                attention_type = "contextual"
        
        # Generate attention weights
        attention_weights = self._generate_attention_weights(
            inputs, 
            attention_type, 
            head_config, 
            config["sensitivity"]
        )
        
        # Map attention across layers if depth > 1
        layered_attention = self._map_multilayer_attention(
            inputs,
            attention_weights,
            config["depth"]
        )
        
        # Generate cross-attention if requested
        cross_attention = None
        if config["include_cross_attention"]:
            cross_attention = self._generate_cross_attention(inputs, attention_weights)
        
        # Calculate attention metrics
        metrics = self._calculate_attention_metrics(attention_weights, attention_type)
        
        # Prepare result
        result = {
            "success": True,
            "attention_type": attention_type,
            "head_configuration": head_config,
            "input_count": len(inputs),
            "attention_weights": attention_weights,
            "layered_attention": layered_attention,
            "cross_attention": cross_attention,
            "metrics": metrics,
            "config": config
        }
        
        return result
    
    def _determine_head_configuration(self, input_length: int, requested_heads: int) -> Dict[str, Any]:
        """
        Determine the optimal head configuration based on input length.
        
        Args:
            input_length: Number of inputs to process
            requested_heads: Requested number of attention heads
            
        Returns:
            Selected head configuration
        """
        # Find the most appropriate configuration based on input size
        if input_length <= 8:
            config_name = "single"
        elif input_length <= 16:
            config_name = "dual"
        elif input_length <= 32:
            config_name = "quad"
        elif input_length <= 64:
            config_name = "octo"
        else:
            config_name = "adaptive"
        
        # Get the base configuration
        config = dict(self.head_configurations[config_name])
        
        # Override head count if explicitly requested and within reasonable bounds
        if 1 <= requested_heads <= 12:
            # Adjust the configuration to use the requested number of heads
            config["actual_heads"] = requested_heads
            config["description"] = f"{requested_heads}-head attention mechanism"
        else:
            # Default head count based on configuration
            if config_name == "single":
                config["actual_heads"] = 1
            elif config_name == "dual":
                config["actual_heads"] = 2
            elif config_name == "quad":
                config["actual_heads"] = 4
            elif config_name == "octo":
                config["actual_heads"] = 8
            else:
                # For adaptive, scale with input size
                config["actual_heads"] = max(1, min(12, input_length // 8))
        
        config["name"] = config_name
        return config
    
    def _infer_attention_type(self, inputs: List[Dict[str, Any]]) -> str:
        """
        Infer the most appropriate attention type from input characteristics.
        
        Args:
            inputs: List of input tokens or neurons
            
        Returns:
            Inferred attention type
        """
        # Check for sequential markers in inputs
        has_sequential_markers = False
        has_position_field = False
        
        for input_item in inputs:
            if "position" in input_item or "index" in input_item or "sequence" in input_item:
                has_position_field = True
                break
        
        if has_position_field:
            # If positions are mostly sequential, likely sequential attention
            positions = []
            for input_item in inputs:
                pos = input_item.get("position", input_item.get("index", input_item.get("sequence")))
                if pos is not None:
                    positions.append(pos)
            
            if positions:
                positions.sort()
                sequence_breaks = sum(1 for i in range(1, len(positions)) if positions[i] - positions[i-1] > 1)
                if sequence_breaks / len(positions) < 0.2:
                    has_sequential_markers = True
        
        # Check for importance or weight markers
        has_importance_markers = False
        for input_item in inputs:
            if "importance" in input_item or "weight" in input_item or "relevance" in input_item:
                has_importance_markers = True
                break
        
        # Check for contextual markers
        has_contextual_markers = False
        for input_item in inputs:
            if "context" in input_item or "topic" in input_item or "subject" in input_item:
                has_contextual_markers = True
                break
        
        # Determine type based on markers
        if has_sequential_markers:
            return "sequential"
        elif has_importance_markers:
            # Check distribution of importance values
            importance_values = []
            for input_item in inputs:
                imp = input_item.get("importance", input_item.get("weight", input_item.get("relevance")))
                if imp is not None:
                    importance_values.append(float(imp))
            
            if importance_values:
                if max(importance_values) - min(importance_values) < 0.3:
                    return "uniform"
                
                # Count how many importance values are significantly higher than the mean
                mean_imp = sum(importance_values) / len(importance_values)
                focus_count = sum(1 for imp in importance_values if imp > mean_imp * 1.5)
                
                if focus_count == 0:
                    return "uniform"
                elif focus_count == 1:
                    return "focused"
                else:
                    return "multi-focus"
            
            return "focused"
        elif has_contextual_markers:
            return "contextual"
        
        # Default to contextual if no clear indicators
        return "contextual"
    
    def _generate_attention_weights(self, inputs: List[Dict[str, Any]], 
                                 attention_type: str,
                                 head_config: Dict[str, Any],
                                 sensitivity: float) -> Dict[str, Any]:
        """
        Generate attention weights based on type and head configuration.
        
        Args:
            inputs: List of input tokens or neurons
            attention_type: Type of attention pattern to generate
            head_config: Head configuration to use
            sensitivity: Sensitivity parameter for attention calculation
            
        Returns:
            Dictionary with attention weights for each head
        """
        num_inputs = len(inputs)
        num_heads = head_config["actual_heads"]
        
        # Initialize attention matrix for each head
        attention_matrices = {}
        
        for head_idx in range(num_heads):
            # Different distribution for each head
            attention_matrices[f"head_{head_idx+1}"] = self._create_attention_matrix(
                num_inputs, 
                attention_type, 
                head_idx, 
                num_heads,
                sensitivity,
                inputs
            )
        
        # Create combined attention (average of all heads)
        combined_matrix = np.zeros((num_inputs, num_inputs))
        for head_matrix in attention_matrices.values():
            combined_matrix += head_matrix
        
        if num_heads > 0:
            combined_matrix /= num_heads
        
        attention_matrices["combined"] = combined_matrix.tolist()
        
        # Calculate attention focus indices (max attention for each token)
        token_focus = []
        for i in range(num_inputs):
            # Get indices of top 3 attention values for this token
            attention_row = combined_matrix[i]
            top_indices = np.argsort(attention_row)[-3:][::-1].tolist()
            top_values = [attention_row[idx] for idx in top_indices]
            
            token_focus.append({
                "token_idx": i,
                "top_attention_indices": top_indices,
                "top_attention_values": top_values
            })
        
        return {
            "matrices": attention_matrices,
            "token_focus": token_focus,
            "head_count": num_heads
        }
    
    def _create_attention_matrix(self, num_inputs: int, attention_type: str, 
                              head_idx: int, num_heads: int, sensitivity: float,
                              inputs: List[Dict[str, Any]]) -> np.ndarray:
        """
        Create an attention matrix based on the specified pattern.
        
        Args:
            num_inputs: Number of input tokens
            attention_type: Type of attention pattern
            head_idx: Index of the current head
            num_heads: Total number of heads
            sensitivity: Sensitivity parameter
            inputs: Original input data
            
        Returns:
            Numpy array with attention weights
        """
        matrix = np.zeros((num_inputs, num_inputs))
        
        # Create different attention patterns based on type
        if attention_type == "uniform":
            # Uniform attention with slight variation
            base_value = 1.0 / num_inputs
            for i in range(num_inputs):
                for j in range(num_inputs):
                    variation = random.uniform(-0.05, 0.05) * sensitivity
                    matrix[i, j] = max(0, min(1, base_value + variation))
        
        elif attention_type == "focused":
            # Each head focuses on a different segment
            segment_size = max(1, num_inputs // num_heads)
            start_idx = (head_idx * segment_size) % num_inputs
            end_idx = min(start_idx + segment_size, num_inputs)
            
            for i in range(num_inputs):
                # Main focus in assigned segment
                for j in range(start_idx, end_idx):
                    # Gaussian distribution around center of segment
                    center = (start_idx + end_idx) / 2
                    distance = abs(j - center)
                    attention = math.exp(-distance * sensitivity / segment_size)
                    matrix[i, j] = attention
                
                # Normalize to sum to 1
                if sum(matrix[i]) > 0:
                    matrix[i] = matrix[i] / sum(matrix[i])
        
        elif attention_type == "sequential":
            # Attention to current and next few tokens
            look_ahead = int(3 * sensitivity)
            
            for i in range(num_inputs):
                window_start = max(0, i - 1)
                window_end = min(num_inputs, i + look_ahead + 1)
                _window_size = window_end - window_start  # noqa: F841 - For future use
                
                for j in range(window_start, window_end):
                    # Decreasing attention with distance
                    distance = abs(j - i)
                    if distance == 0:
                        matrix[i, j] = 1.0  # Self-attention
                    else:
                        matrix[i, j] = max(0, 1.0 - (distance / (look_ahead + 1)))
                
                # Normalize to sum to 1
                if sum(matrix[i]) > 0:
                    matrix[i] = matrix[i] / sum(matrix[i])
        
        elif attention_type == "contextual":
            # Look for context indicators in inputs
            for i in range(num_inputs):
                # Get context of current token if available
                current_context = None
                if i < len(inputs):
                    current_context = inputs[i].get("context", inputs[i].get("topic", None))
                
                # If context is available, focus on tokens with similar context
                if current_context:
                    for j in range(num_inputs):
                        if j < len(inputs):
                            other_context = inputs[j].get("context", inputs[j].get("topic", None))
                            if other_context and other_context == current_context:
                                matrix[i, j] = 0.8 + (0.2 * random.random())
                            else:
                                matrix[i, j] = 0.2 * random.random()
                else:
                    # Fallback to distance-based attention
                    for j in range(num_inputs):
                        distance = abs(j - i)
                        matrix[i, j] = max(0, 1.0 - (distance / num_inputs))
                
                # Normalize to sum to 1
                if sum(matrix[i]) > 0:
                    matrix[i] = matrix[i] / sum(matrix[i])
        
        elif attention_type == "multi-focus":
            # Multiple focus points for each head
            num_focus_points = 2 + head_idx % 3  # 2-4 focus points per head
            
            for i in range(num_inputs):
                # Select focus points with preference for different regions
                focus_points = []
                for f in range(num_focus_points):
                    region_size = num_inputs // num_focus_points
                    region_start = (f * region_size + head_idx * 7) % num_inputs
                    point = min(num_inputs - 1, region_start + random.randint(0, region_size - 1))
                    focus_points.append(point)
                
                # Create distribution with peaks at focus points
                for j in range(num_inputs):
                    attention_value = 0
                    for focus in focus_points:
                        distance = min(abs(j - focus), num_inputs - abs(j - focus))
                        attention_value = max(attention_value, math.exp(-distance * sensitivity / 5))
                    matrix[i, j] = attention_value
                
                # Normalize to sum to 1
                if sum(matrix[i]) > 0:
                    matrix[i] = matrix[i] / sum(matrix[i])
        
        elif attention_type == "decaying":
            # Exponentially decaying attention with distance
            for i in range(num_inputs):
                for j in range(num_inputs):
                    distance = abs(j - i)
                    decay_rate = 0.2 + (0.1 * head_idx % 3)  # Different decay rates per head
                    matrix[i, j] = math.exp(-distance * decay_rate * sensitivity)
                
                # Normalize to sum to 1
                if sum(matrix[i]) > 0:
                    matrix[i] = matrix[i] / sum(matrix[i])
        
        else:
            # Default to uniform if unknown type
            base_value = 1.0 / num_inputs
            for i in range(num_inputs):
                for j in range(num_inputs):
                    matrix[i, j] = base_value
        
        return matrix
    
    def _map_multilayer_attention(self, inputs: List[Dict[str, Any]], 
                                attention_weights: Dict[str, Any],
                                depth: int) -> List[Dict[str, Any]]:
        """
        Map attention across multiple layers.
        
        Args:
            inputs: Original input tokens or neurons
            attention_weights: Generated attention weights
            depth: Number of layers to map
            
        Returns:
            List of layer attention maps
        """
        num_inputs = len(inputs)
        combined_matrix = np.array(attention_weights["matrices"]["combined"])
        
        # Initialize layers list with first layer (original attention)
        layers = [{
            "layer": 1,
            "description": "Input attention layer",
            "attention_key_points": self._extract_key_attention_points(combined_matrix, inputs),
            "token_focus": attention_weights["token_focus"][:],
            "attention_matrix": combined_matrix.tolist()
        }]
        
        # Generate subsequent layers
        prev_matrix = combined_matrix
        for layer_idx in range(2, depth + 1):
            # Each subsequent layer is influenced by the previous layer's attention
            # We calculate this by matrix multiplication (composition of attention)
            layer_matrix = np.matmul(prev_matrix, prev_matrix)
            
            # Normalize to maintain probabilities
            for i in range(num_inputs):
                if sum(layer_matrix[i]) > 0:
                    layer_matrix[i] = layer_matrix[i] / sum(layer_matrix[i])
            
            # Extract key points for this layer
            key_points = self._extract_key_attention_points(layer_matrix, inputs)
            
            # Calculate token focus for this layer
            token_focus = []
            for i in range(num_inputs):
                attention_row = layer_matrix[i]
                top_indices = np.argsort(attention_row)[-3:][::-1].tolist()
                top_values = [attention_row[idx] for idx in top_indices]
                
                token_focus.append({
                    "token_idx": i,
                    "top_attention_indices": top_indices,
                    "top_attention_values": top_values
                })
            
            # Add layer to results
            layers.append({
                "layer": layer_idx,
                "description": f"Depth {layer_idx} attention composition",
                "attention_key_points": key_points,
                "token_focus": token_focus,
                "attention_matrix": layer_matrix.tolist()
            })
            
            # Update previous matrix for next iteration
            prev_matrix = layer_matrix
        
        return layers
    
    def _extract_key_attention_points(self, attention_matrix: np.ndarray, 
                                    inputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract key attention points from an attention matrix.
        
        Args:
            attention_matrix: The attention matrix to analyze
            inputs: Original input tokens or neurons
            
        Returns:
            List of key attention points
        """
        num_inputs = len(inputs)
        key_points = []
        
        # Find global maximum
        max_value = np.max(attention_matrix)
        max_indices = np.where(attention_matrix == max_value)
        max_i, max_j = max_indices[0][0], max_indices[1][0]
        
        key_points.append({
            "type": "global_maximum",
            "source_idx": int(max_i),
            "target_idx": int(max_j),
            "value": float(max_value),
            "description": "Global maximum attention"
        })
        
        # Find attention sinks (columns with high total attention)
        col_sums = np.sum(attention_matrix, axis=0)
        top_sink_indices = np.argsort(col_sums)[-3:][::-1].tolist()
        
        for idx in top_sink_indices:
            key_points.append({
                "type": "attention_sink",
                "target_idx": idx,
                "value": float(col_sums[idx]),
                "description": "Token receiving high collective attention"
            })
        
        # Find attention sources (rows with focused attention)
        row_maxes = np.max(attention_matrix, axis=1)
        top_source_indices = np.argsort(row_maxes)[-3:][::-1].tolist()
        
        for idx in top_source_indices:
            target_idx = np.argmax(attention_matrix[idx])
            key_points.append({
                "type": "focused_source",
                "source_idx": idx,
                "target_idx": int(target_idx),
                "value": float(row_maxes[idx]),
                "description": "Token with highly focused attention"
            })
        
        # Find self-attention points
        self_attention = np.diagonal(attention_matrix)
        high_self_indices = [i for i in range(num_inputs) if self_attention[i] > 0.7]
        
        for idx in high_self_indices[:3]:  # Limit to top 3
            key_points.append({
                "type": "self_attention",
                "source_idx": idx,
                "target_idx": idx,
                "value": float(self_attention[idx]),
                "description": "Token with high self-attention"
            })
        
        return key_points
    
    def _generate_cross_attention(self, inputs: List[Dict[str, Any]], 
                               attention_weights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate cross-attention analysis across attention heads.
        
        Args:
            inputs: Original input tokens or neurons
            attention_weights: Generated attention weights
            
        Returns:
            Dictionary with cross-attention analysis
        """
        num_heads = attention_weights["head_count"]
        if num_heads <= 1:
            return {
                "head_count": num_heads,
                "cross_attention_analysis": None,
                "specialization_score": 0
            }
        
        # Get attention matrices for each head
        head_matrices = {}
        for head_idx in range(num_heads):
            head_key = f"head_{head_idx+1}"
            if head_key in attention_weights["matrices"]:
                head_matrices[head_key] = np.array(attention_weights["matrices"][head_key])
        
        if not head_matrices:
            return {
                "head_count": 0,
                "cross_attention_analysis": None,
                "specialization_score": 0
            }
        
        # Calculate head similarity matrix
        head_names = list(head_matrices.keys())
        num_heads = len(head_names)
        similarity_matrix = np.zeros((num_heads, num_heads))
        
        for i in range(num_heads):
            for j in range(num_heads):
                if i == j:
                    similarity_matrix[i, j] = 1.0
                else:
                    # Flatten matrices for comparison
                    matrix1_flat = head_matrices[head_names[i]].flatten()
                    matrix2_flat = head_matrices[head_names[j]].flatten()
                    
                    # Cosine similarity
                    dot_product = np.dot(matrix1_flat, matrix2_flat)
                    norm1 = np.linalg.norm(matrix1_flat)
                    norm2 = np.linalg.norm(matrix2_flat)
                    
                    if norm1 > 0 and norm2 > 0:
                        similarity_matrix[i, j] = dot_product / (norm1 * norm2)
                    else:
                        similarity_matrix[i, j] = 0
        
        # Analyze head specialization
        specialization_scores = []
        for i in range(num_heads):
            # Average similarity to other heads (excluding self)
            other_similarities = [similarity_matrix[i, j] for j in range(num_heads) if j != i]
            avg_similarity = sum(other_similarities) / len(other_similarities) if other_similarities else 0
            
            # Specialization is the inverse of similarity (1 - avg_similarity)
            specialization = 1.0 - avg_similarity
            specialization_scores.append(specialization)
        
        # Find token pairs with significantly different attention across heads
        token_pair_variation = []
        num_inputs = len(inputs)
        
        for i in range(num_inputs):
            for j in range(num_inputs):
                # Extract attention values for this token pair across all heads
                attention_values = [head_matrices[head][i, j] for head in head_names]
                
                # Calculate variation (max - min)
                if attention_values:
                    variation = max(attention_values) - min(attention_values)
                    
                    # Only include pairs with significant variation
                    if variation > 0.3:
                        max_head_idx = attention_values.index(max(attention_values))
                        min_head_idx = attention_values.index(min(attention_values))
                        
                        token_pair_variation.append({
                            "source_idx": i,
                            "target_idx": j,
                            "variation": variation,
                            "max_attention": max(attention_values),
                            "min_attention": min(attention_values),
                            "max_head": head_names[max_head_idx],
                            "min_head": head_names[min_head_idx]
                        })
        
        # Sort by variation
        token_pair_variation.sort(key=lambda x: x["variation"], reverse=True)
        
        # Limit to top 10 pairs
        token_pair_variation = token_pair_variation[:10]
        
        # Create cross-attention result
        cross_attention = {
            "head_count": num_heads,
            "head_similarity_matrix": similarity_matrix.tolist(),
            "head_specialization_scores": [float(score) for score in specialization_scores],
            "average_specialization": float(sum(specialization_scores) / len(specialization_scores)) if specialization_scores else 0,
            "token_pair_variations": token_pair_variation
        }
        
        return cross_attention
    
    def _calculate_attention_metrics(self, attention_weights: Dict[str, Any], 
                                  attention_type: str) -> Dict[str, Any]:
        """
        Calculate metrics to evaluate attention quality.
        
        Args:
            attention_weights: Generated attention weights
            attention_type: Type of attention pattern used
            
        Returns:
            Dictionary with calculated metrics
        """
        combined_matrix = np.array(attention_weights["matrices"]["combined"])
        num_inputs = combined_matrix.shape[0]
        
        # Coverage: How much of the input space receives significant attention
        # (percentage of attention values above 0.1)
        significant_attention = np.sum(combined_matrix > 0.1) / (num_inputs * num_inputs)
        coverage = float(significant_attention)
        
        # Specificity: How concentrated attention is on key inputs
        # (ratio of max attention to mean attention for each input)
        row_max = np.max(combined_matrix, axis=1)
        row_mean = np.mean(combined_matrix, axis=1)
        
        specificity_values = []
        for i in range(num_inputs):
            if row_mean[i] > 0:
                specificity_values.append(row_max[i] / row_mean[i])
        
        specificity = float(np.mean(specificity_values)) if specificity_values else 0
        
        # Normalize to 0-1 range
        specificity = min(1.0, specificity / 10)
        
        # Entropy: Randomness in attention distribution
        # (normalized Shannon entropy)
        entropy_values = []
        for i in range(num_inputs):
            row = combined_matrix[i]
            if np.sum(row) > 0:
                # Add small epsilon to avoid log(0)
                row = row + 1e-10
                row = row / np.sum(row)
                row_entropy = -np.sum(row * np.log2(row)) / np.log2(num_inputs)
                entropy_values.append(row_entropy)
        
        entropy = float(np.mean(entropy_values)) if entropy_values else 0
        
        # Consistency: How similar attention is across rows
        # (average pairwise cosine similarity of rows)
        similarity_sum = 0
        comparison_count = 0
        
        for i in range(num_inputs):
            for j in range(i+1, num_inputs):
                row_i = combined_matrix[i]
                row_j = combined_matrix[j]
                
                norm_i = np.linalg.norm(row_i)
                norm_j = np.linalg.norm(row_j)
                
                if norm_i > 0 and norm_j > 0:
                    similarity = np.dot(row_i, row_j) / (norm_i * norm_j)
                    similarity_sum += similarity
                    comparison_count += 1
        
        consistency = float(similarity_sum / comparison_count) if comparison_count > 0 else 0
        
        # Responsiveness: Metric depends on attention type
        if attention_type == "sequential":
            # For sequential: check if attention peaks at i+1 for each position i
            responsiveness_values = []
            for i in range(num_inputs - 1):
                next_pos_attention = combined_matrix[i, i+1]
                responsiveness_values.append(next_pos_attention)
            
            responsiveness = float(np.mean(responsiveness_values)) if responsiveness_values else 0
        
        elif attention_type == "focused":
            # For focused: check concentration of attention (Gini coefficient)
            gini_values = []
            for i in range(num_inputs):
                row = np.sort(combined_matrix[i])
                index = np.arange(1, num_inputs + 1)
                gini = np.sum((2 * index - num_inputs - 1) * row) / (num_inputs * np.sum(row))
                gini_values.append(gini)
            
            responsiveness = float(np.mean(gini_values)) if gini_values else 0
        
        else:
            # Default: use attention to highest value inputs
            responsiveness_values = []
            for i in range(num_inputs):
                sorted_row = np.sort(combined_matrix[i])[::-1]
                if len(sorted_row) >= 2:
                    # Ratio of top 2 attention values
                    responsiveness_values.append(sorted_row[0] / (sorted_row[1] + 1e-10))
            
            responsiveness = float(np.mean(responsiveness_values)) if responsiveness_values else 0
            
            # Normalize to 0-1 range
            responsiveness = min(1.0, responsiveness / 5)
        
        # Compile metrics with assessments
        metrics = {
            "coverage": {
                "value": round(coverage, 3),
                "assessment": self._assess_metric("coverage", coverage)
            },
            "specificity": {
                "value": round(specificity, 3),
                "assessment": self._assess_metric("specificity", specificity)
            },
            "entropy": {
                "value": round(entropy, 3),
                "assessment": self._assess_metric("entropy", entropy)
            },
            "consistency": {
                "value": round(consistency, 3),
                "assessment": self._assess_metric("consistency", consistency)
            },
            "responsiveness": {
                "value": round(responsiveness, 3),
                "assessment": self._assess_metric("responsiveness", responsiveness)
            }
        }
        
        # Overall quality score (weighted average)
        weights = {"coverage": 0.2, "specificity": 0.25, "entropy": 0.15, "consistency": 0.15, "responsiveness": 0.25}
        quality_score = sum(weights[metric] * metrics[metric]["value"] for metric in weights)
        
        metrics["overall_quality"] = {
            "value": round(quality_score, 3),
            "assessment": "Excellent" if quality_score > 0.8 else 
                          "Good" if quality_score > 0.6 else
                          "Average" if quality_score > 0.4 else
                          "Poor"
        }
        
        return metrics
    
    def _assess_metric(self, metric_name: str, value: float) -> str:
        """
        Assess a metric value based on optimal ranges.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            
        Returns:
            Assessment string
        """
        if metric_name in self.attention_metrics:
            metric_info = self.attention_metrics[metric_name]
            optimal_range = metric_info["optimal_range"]
            critical = metric_info["critical_threshold"]
            
            if optimal_range[0] <= value <= optimal_range[1]:
                return "Optimal"
            elif value < optimal_range[0]:
                if metric_name == "entropy" and value < critical:
                    return "Too Low (Critical)"
                elif metric_name in ["coverage", "specificity", "consistency", "responsiveness"] and value < critical:
                    return "Too Low (Critical)"
                else:
                    return "Below Optimal"
            else:  # value > optimal_range[1]
                if metric_name == "entropy" and value > critical:
                    return "Too High (Critical)"
                elif metric_name in ["coverage", "specificity", "consistency", "responsiveness"] and value > 0.95:
                    return "Excellent"
                else:
                    return "Above Optimal"
        
        return "Unknown Metric"


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Attention Layer Mapper (KA-52) on the provided data.
    
    Args:
        data: A dictionary containing inputs to analyze and optional configuration
        
    Returns:
        Dictionary with attention mapping results
    """
    inputs = data.get("inputs", [])
    config = data.get("config", None)
    
    # Create sample inputs if none provided but tokens specified
    if not inputs and "num_tokens" in data:
        num_tokens = data["num_tokens"]
        
        # Generate sample inputs
        inputs = []
        
        # Pattern specified for sample generation
        pattern = data.get("pattern", "uniform")
        
        for i in range(num_tokens):
            token = {
                "id": f"token_{i}",
                "position": i
            }
            
            # Add pattern-specific attributes
            if pattern == "sequential":
                token["sequence"] = i
            elif pattern == "focused" and i == num_tokens // 2:
                token["importance"] = 0.9
            elif pattern == "focused":
                token["importance"] = 0.3 + (random.random() * 0.2)
            elif pattern == "contextual":
                # Assign random contexts
                contexts = ["topic_A", "topic_B", "topic_C"]
                token["context"] = contexts[i % len(contexts)]
            elif pattern == "multi-focus":
                # Create multiple importance peaks
                if i % (num_tokens // 3) == 0:
                    token["importance"] = 0.8 + (random.random() * 0.15)
                else:
                    token["importance"] = 0.3 + (random.random() * 0.2)
            
            inputs.append(token)
    
    mapper = AttentionLayerMapper()
    
    try:
        result = mapper.map_attention_layer(inputs, config)
        
        if not result.get("success", False):
            return {
                "algorithm": "KA-52",
                "success": False,
                "error": result.get("error", "Unknown error"),
                "timestamp": time.time()
            }
        
        # Limit the size of returned data for very large inputs
        if result.get("input_count", 0) > 50:
            # For large inputs, reduce the amount of detailed data returned
            for matrix_name in result.get("attention_weights", {}).get("matrices", {}):
                matrix = result["attention_weights"]["matrices"][matrix_name]
                if isinstance(matrix, list) and len(matrix) > 50:
                    # Replace with summary statistics
                    result["attention_weights"]["matrices"][matrix_name] = {
                        "size": [len(matrix), len(matrix[0]) if matrix and isinstance(matrix[0], list) else 0],
                        "summary": "Matrix too large to return in full, access specific elements if needed"
                    }
        
        return {
            "algorithm": "KA-52",
            "attention_type": result.get("attention_type"),
            "head_configuration": result.get("head_configuration"),
            "attention_weights": result.get("attention_weights"),
            "layered_attention": result.get("layered_attention"),
            "cross_attention": result.get("cross_attention"),
            "metrics": result.get("metrics"),
            "input_count": result.get("input_count"),
            "timestamp": time.time(),
            "success": True
        }
    
    except Exception as e:
        logger.error(f"Error in KA-52 Attention Layer Mapper: {str(e)}")
        return {
            "algorithm": "KA-52",
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }