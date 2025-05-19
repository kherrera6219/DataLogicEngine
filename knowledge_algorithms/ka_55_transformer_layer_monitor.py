"""
KA-55: Transformer Layer Monitor

This algorithm monitors and analyzes transformer neural network layers,
tracking attention patterns, information flow, and feature interactions
across layers.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import time
import math
import random
import copy
import uuid

logger = logging.getLogger(__name__)

class TransformerLayerMonitor:
    """
    KA-55: Monitors and analyzes transformer neural network layers.
    
    This algorithm specializes in tracking attention patterns, information flow,
    and feature interactions across transformer layers, providing insights into
    how different components process and transform information.
    """
    
    def __init__(self):
        """Initialize the Transformer Layer Monitor."""
        self.layer_types = self._initialize_layer_types()
        self.attention_patterns = self._initialize_attention_patterns()
        self.monitoring_metrics = self._initialize_monitoring_metrics()
        self.abnormality_signatures = self._initialize_abnormality_signatures()
        logger.info("KA-55: Transformer Layer Monitor initialized")
    
    def _initialize_layer_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize types of transformer layers to monitor."""
        return {
            "self_attention": {
                "description": "Layer processing token relationships within the same sequence",
                "key_components": ["query", "key", "value", "attention_weights"],
                "typical_patterns": ["local_focus", "global_context", "position_biased"],
                "critical_metrics": ["attention_entropy", "token_influence"]
            },
            "cross_attention": {
                "description": "Layer processing relationships between different sequences",
                "key_components": ["encoder_key", "encoder_value", "decoder_query", "attention_weights"],
                "typical_patterns": ["alignment", "selective_focus", "context_tracking"],
                "critical_metrics": ["alignment_score", "context_utilization"]
            },
            "feed_forward": {
                "description": "Layer applying non-linear transformations to token representations",
                "key_components": ["linear1_weights", "linear2_weights", "activations"],
                "typical_patterns": ["feature_specialization", "information_compression", "knowledge_encoding"],
                "critical_metrics": ["activation_sparsity", "feature_diversity"]
            },
            "layer_norm": {
                "description": "Layer normalizing features across tokens",
                "key_components": ["scale", "bias", "normalized_features"],
                "typical_patterns": ["variance_stabilization", "feature_rebalancing"],
                "critical_metrics": ["normalization_magnitude", "feature_distribution"]
            },
            "embedding": {
                "description": "Layer converting tokens to vector representations",
                "key_components": ["token_embeddings", "position_embeddings", "type_embeddings"],
                "typical_patterns": ["semantic_clustering", "position_encoding"],
                "critical_metrics": ["embedding_utilization", "semantic_separation"]
            },
            "pooling": {
                "description": "Layer aggregating information across tokens",
                "key_components": ["attention_pooling", "cls_token", "pooled_representation"],
                "typical_patterns": ["information_distillation", "sequence_summarization"],
                "critical_metrics": ["information_retention", "representation_compactness"]
            }
        }
    
    def _initialize_attention_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize attention patterns to recognize."""
        return {
            "diagonal": {
                "description": "Attention primarily focused on the token itself and nearby tokens",
                "indication": "Local processing of token context",
                "typical_layers": ["early_encoder_self_attention"],
                "detection_threshold": 0.7
            },
            "vertical": {
                "description": "Attention focused on specific tokens across all queries",
                "indication": "Key information tokens (e.g., punctuation, keywords)",
                "typical_layers": ["middle_encoder_self_attention"],
                "detection_threshold": 0.6
            },
            "horizontal": {
                "description": "Attention from specific tokens spread across all keys",
                "indication": "Information gathering tokens (e.g., question words)",
                "typical_layers": ["late_encoder_self_attention", "early_decoder_self_attention"],
                "detection_threshold": 0.6
            },
            "global": {
                "description": "Broad attention distributed across many tokens",
                "indication": "Global context integration",
                "typical_layers": ["deep_encoder_self_attention"],
                "detection_threshold": 0.5
            },
            "local_chunks": {
                "description": "Attention focused within semantic chunks of tokens",
                "indication": "Phrase or entity processing",
                "typical_layers": ["early_encoder_self_attention", "middle_encoder_self_attention"],
                "detection_threshold": 0.65
            },
            "block_diagonal": {
                "description": "Attention in blocks along the diagonal",
                "indication": "Processing of multiple segments independently",
                "typical_layers": ["early_encoder_self_attention", "early_decoder_self_attention"],
                "detection_threshold": 0.6
            },
            "triangular": {
                "description": "Attention to previous tokens only (causal mask)",
                "indication": "Autoregressive generation",
                "typical_layers": ["decoder_self_attention"],
                "detection_threshold": 0.8
            },
            "alternating": {
                "description": "Alternating strong and weak attention bands",
                "indication": "Processing of paired elements or structured data",
                "typical_layers": ["middle_encoder_self_attention", "cross_attention"],
                "detection_threshold": 0.55
            }
        }
    
    def _initialize_monitoring_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize metrics for monitoring transformer layers."""
        return {
            "attention_entropy": {
                "description": "Measure of attention distribution randomness",
                "calculation": "Shannon entropy of attention weights",
                "typical_range": [0.3, 0.8],
                "interpretation": {
                    "low": "Highly focused attention (possibly overspecialized)",
                    "high": "Diffuse attention (possibly unfocused)",
                    "optimal": "Balance of focused and context-aware attention"
                }
            },
            "activation_sparsity": {
                "description": "Percentage of near-zero activations in a layer",
                "calculation": "Fraction of activations below threshold",
                "typical_range": [0.4, 0.8],
                "interpretation": {
                    "low": "Dense activations (possibly inefficient)",
                    "high": "Very sparse activations (possibly undertrained)",
                    "optimal": "Efficient feature encoding with appropriate sparsity"
                }
            },
            "token_influence": {
                "description": "Measure of how much each token influences the output",
                "calculation": "Gradient of output with respect to token",
                "typical_range": [0.05, 0.3],
                "interpretation": {
                    "low": "Token has little impact on prediction",
                    "high": "Token strongly determines output (possible overreliance)",
                    "optimal": "Balanced influence appropriate to token importance"
                }
            },
            "feature_diversity": {
                "description": "Variety in activated features across inputs",
                "calculation": "Variance across feature activation patterns",
                "typical_range": [0.3, 0.7],
                "interpretation": {
                    "low": "Limited feature utilization (possible undertrained)",
                    "high": "Highly diverse features (good generalization)",
                    "optimal": "Rich feature representation with good coverage"
                }
            },
            "layer_gradient_norm": {
                "description": "Magnitude of gradients flowing through the layer",
                "calculation": "L2 norm of layer gradients",
                "typical_range": [0.01, 0.5],
                "interpretation": {
                    "low": "Layer learning slowly or converged",
                    "high": "Layer updating rapidly (possibly unstable)",
                    "optimal": "Steady learning appropriate to layer position"
                }
            },
            "cross_layer_alignment": {
                "description": "Similarity between representations across layers",
                "calculation": "CKA or CCA between layer representations",
                "typical_range": [0.3, 0.8],
                "interpretation": {
                    "low": "Layers transforming information substantially",
                    "high": "Layers preserving information (possible redundancy)",
                    "optimal": "Progressive refinement without information loss"
                }
            },
            "normalization_magnitude": {
                "description": "Degree of feature normalization",
                "calculation": "Average scale of normalization operations",
                "typical_range": [0.5, 2.0],
                "interpretation": {
                    "low": "Minimal normalization (possible instability)",
                    "high": "Heavy normalization (possible information loss)",
                    "optimal": "Balanced normalization for stable processing"
                }
            },
            "attention_alignment": {
                "description": "Alignment between attention and token relationships",
                "calculation": "Correlation between attention and token relevance",
                "typical_range": [0.4, 0.9],
                "interpretation": {
                    "low": "Attention unaligned with token relationships",
                    "high": "Attention strongly following expected patterns",
                    "optimal": "Attention captures both expected and novel patterns"
                }
            }
        }
    
    def _initialize_abnormality_signatures(self) -> Dict[str, Dict[str, Any]]:
        """Initialize signatures of abnormal layer behavior."""
        return {
            "attention_collapse": {
                "description": "Attention focusing too narrowly on a few tokens",
                "indicators": {
                    "attention_entropy": "<0.2",
                    "token_influence": ">0.5 for <3 tokens"
                },
                "potential_causes": [
                    "Overfitting to specific patterns",
                    "Insufficient training data diversity",
                    "Attention head specialization"
                ],
                "severity": "high"
            },
            "gradient_saturation": {
                "description": "Gradients consistently near zero",
                "indicators": {
                    "layer_gradient_norm": "<0.001",
                    "activation_sparsity": ">0.9"
                },
                "potential_causes": [
                    "Dead neurons or vanishing gradients",
                    "Learning rate too low",
                    "Layer converged to local minimum"
                ],
                "severity": "high"
            },
            "feature_redundancy": {
                "description": "Multiple layers encoding the same information",
                "indicators": {
                    "cross_layer_alignment": ">0.9",
                    "feature_diversity": "<0.2"
                },
                "potential_causes": [
                    "Network over-parameterization",
                    "Insufficient regularization",
                    "Task too simple for model capacity"
                ],
                "severity": "medium"
            },
            "attention_diffusion": {
                "description": "Attention spread too broadly with no focus",
                "indicators": {
                    "attention_entropy": ">0.9",
                    "attention_alignment": "<0.3"
                },
                "potential_causes": [
                    "Noise in input data",
                    "Poor initialization",
                    "Layer underfitting"
                ],
                "severity": "medium"
            },
            "normalization_instability": {
                "description": "Extreme values in normalization layers",
                "indicators": {
                    "normalization_magnitude": ">3.0 or <0.2",
                    "feature_diversity": "<0.3"
                },
                "potential_causes": [
                    "Learning rate too high",
                    "Gradient explosion",
                    "Batch size too small"
                ],
                "severity": "high"
            },
            "representation_drift": {
                "description": "Representation distribution changing significantly",
                "indicators": {
                    "cross_layer_alignment": "rapid change over time",
                    "feature_diversity": "inconsistent across batches"
                },
                "potential_causes": [
                    "Distribution shift in data",
                    "Unstable training dynamics",
                    "Catastrophic forgetting"
                ],
                "severity": "medium"
            },
            "token_neglect": {
                "description": "Some tokens consistently ignored across layers",
                "indicators": {
                    "token_influence": "<0.01 for multiple tokens",
                    "attention_alignment": "<0.3"
                },
                "potential_causes": [
                    "Irrelevant tokens in input",
                    "Attention bias toward certain positions",
                    "Imbalanced feature importance"
                ],
                "severity": "low"
            },
            "attention_fragmentation": {
                "description": "Attention scattered in inconsistent patterns",
                "indicators": {
                    "attention_entropy": "oscillating between batches",
                    "attention_pattern": "no clear recognizable pattern"
                },
                "potential_causes": [
                    "Conflicting optimization objectives",
                    "High-variance in training examples",
                    "Unstable attention mechanism"
                ],
                "severity": "medium"
            }
        }
    
    def monitor_transformer_layers(self, 
                                model_state: Dict[str, Any],
                                layer_activations: Dict[str, Any],
                                inputs: Dict[str, Any],
                                config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Monitor and analyze transformer layer behavior.
        
        Args:
            model_state: Dictionary with model parameters and state
            layer_activations: Activations from each layer for current inputs
            inputs: Input data being processed
            config: Optional configuration for monitoring
            
        Returns:
            Dictionary with monitoring results
        """
        # Set default configuration if not provided
        if config is None:
            config = {
                "monitoring_level": "comprehensive",  # Options: basic, comprehensive, detailed
                "focus_layers": [],  # Empty list means all layers
                "track_abnormalities": True,
                "measure_efficiency": True,
                "analyze_patterns": True,
                "max_tokens_to_analyze": 50,  # Limit for detailed token analysis
                "include_historical_comparison": False
            }
        
        # Validate inputs
        if not model_state or not layer_activations:
            return {
                "success": False,
                "error": "Missing model state or layer activations",
                "results": {}
            }
        
        # Extract model information
        model_info = self._extract_model_info(model_state)
        
        # Filter layers to analyze based on config
        focus_layers = config.get("focus_layers", [])
        layers_to_analyze = self._select_layers_to_analyze(layer_activations, focus_layers)
        
        # Analyze each selected layer
        layer_analyses = {}
        abnormalities = []
        
        for layer_id, layer_data in layers_to_analyze.items():
            # Determine layer type
            layer_type = self._determine_layer_type(layer_id, layer_data, model_info)
            
            # Analyze layer based on its type
            layer_analysis = self._analyze_layer(
                layer_id, layer_type, layer_data, 
                inputs, model_info, config
            )
            
            # Check for abnormalities if requested
            if config.get("track_abnormalities", True):
                layer_abnormalities = self._detect_abnormalities(layer_id, layer_type, layer_analysis)
                if layer_abnormalities:
                    abnormalities.extend(layer_abnormalities)
            
            # Add to results
            layer_analyses[layer_id] = layer_analysis
        
        # Generate cross-layer analyses
        cross_layer_analysis = self._analyze_cross_layer_patterns(
            layers_to_analyze, layer_analyses, model_info, config
        )
        
        # Measure overall efficiency if requested
        efficiency_metrics = {}
        if config.get("measure_efficiency", True):
            efficiency_metrics = self._measure_efficiency(
                layer_activations, layer_analyses, model_info
            )
        
        # Prepare result
        results = {
            "model_info": {
                "name": model_info.get("name", "unknown"),
                "num_layers": model_info.get("num_layers", 0),
                "hidden_size": model_info.get("hidden_size", 0),
                "num_attention_heads": model_info.get("num_attention_heads", 0)
            },
            "layers_analyzed": list(layer_analyses.keys()),
            "layer_analyses": layer_analyses,
            "cross_layer_analysis": cross_layer_analysis,
            "efficiency_metrics": efficiency_metrics,
            "abnormalities_detected": len(abnormalities),
            "abnormalities": abnormalities,
            "monitoring_level": config.get("monitoring_level", "comprehensive")
        }
        
        return {
            "success": True,
            "results": results
        }
    
    def _extract_model_info(self, model_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract basic information about the transformer model.
        
        Args:
            model_state: Dictionary with model parameters and state
            
        Returns:
            Dictionary with model information
        """
        info = {
            "name": model_state.get("name", "unknown"),
            "num_layers": 0,
            "hidden_size": 0,
            "num_attention_heads": 0,
            "layer_structure": {},
            "vocabulary_size": 0
        }
        
        # Try to extract information from model_state
        config = model_state.get("config", {})
        if config:
            info["num_layers"] = config.get("num_hidden_layers", 
                                         config.get("n_layer", 
                                                 config.get("num_layers", 0)))
            
            info["hidden_size"] = config.get("hidden_size", 
                                          config.get("d_model", 
                                                  config.get("n_embd", 0)))
            
            info["num_attention_heads"] = config.get("num_attention_heads", 
                                                  config.get("n_head", 
                                                          config.get("nhead", 0)))
            
            info["vocabulary_size"] = config.get("vocab_size", 
                                              config.get("n_vocab", 0))
        
        # Try to infer from parameter shapes if not in config
        parameters = model_state.get("parameters", {})
        if parameters and info["hidden_size"] == 0:
            # Look for embeddings to infer hidden size
            for param_name, param in parameters.items():
                if "embed" in param_name.lower() and isinstance(param, dict) and "shape" in param:
                    if len(param["shape"]) == 2:
                        info["hidden_size"] = param["shape"][1]  # Second dimension is typically embedding size
                        break
        
        # Identify layer structure
        if parameters:
            layer_counts = {}
            for param_name in parameters:
                # Extract layer numbers from parameter names
                parts = param_name.split(".")
                for part in parts:
                    if part.startswith("layer"):
                        layer_num = part.replace("layer", "")
                        if layer_num.isdigit():
                            layer_num = int(layer_num)
                            layer_counts[layer_num] = layer_counts.get(layer_num, 0) + 1
                    elif len(parts) > 1 and parts[0].isdigit():
                        # Handle formats like "0.attention.query"
                        layer_num = int(parts[0])
                        layer_counts[layer_num] = layer_counts.get(layer_num, 0) + 1
            
            if layer_counts and info["num_layers"] == 0:
                info["num_layers"] = max(layer_counts.keys()) + 1
        
        return info
    
    def _select_layers_to_analyze(self, layer_activations: Dict[str, Any], 
                               focus_layers: List[str]) -> Dict[str, Any]:
        """
        Select which layers to analyze based on configuration.
        
        Args:
            layer_activations: Activations from each layer
            focus_layers: List of layer IDs to focus on
            
        Returns:
            Dictionary with selected layers
        """
        selected_layers = {}
        
        # If focus_layers is empty, select all layers
        if not focus_layers:
            return layer_activations
        
        # Select only specified layers
        for layer_id, activations in layer_activations.items():
            if self._layer_matches_focus(layer_id, focus_layers):
                selected_layers[layer_id] = activations
        
        return selected_layers
    
    def _layer_matches_focus(self, layer_id: str, focus_layers: List[str]) -> bool:
        """
        Check if a layer matches one of the focus layer patterns.
        
        Args:
            layer_id: ID of the layer to check
            focus_layers: List of layer patterns to focus on
            
        Returns:
            True if the layer should be analyzed
        """
        for pattern in focus_layers:
            # Exact match
            if pattern == layer_id:
                return True
            
            # Wildcard patterns (e.g., "encoder.*", "*.attention", "encoder.*.attention")
            if pattern.endswith(".*") and layer_id.startswith(pattern[:-2]):
                return True
            
            if pattern.startswith("*.") and layer_id.endswith(pattern[1:]):
                return True
            
            if "*" in pattern:
                parts = pattern.split("*")
                if len(parts) == 2 and layer_id.startswith(parts[0]) and layer_id.endswith(parts[1]):
                    return True
        
        return False
    
    def _determine_layer_type(self, layer_id: str, layer_data: Dict[str, Any], 
                           model_info: Dict[str, Any]) -> str:
        """
        Determine the type of transformer layer.
        
        Args:
            layer_id: ID of the layer
            layer_data: Layer activations and data
            model_info: Model information
            
        Returns:
            Layer type string
        """
        layer_id_lower = layer_id.lower()
        
        # Check for attention layers
        if "attention" in layer_id_lower:
            if "self" in layer_id_lower or "encoder" in layer_id_lower:
                return "self_attention"
            elif "cross" in layer_id_lower or "encoder_decoder" in layer_id_lower:
                return "cross_attention"
        
        # Check for feed forward layers
        if "ffn" in layer_id_lower or "feed_forward" in layer_id_lower or "mlp" in layer_id_lower:
            return "feed_forward"
        
        # Check for normalization layers
        if "norm" in layer_id_lower or "ln" in layer_id_lower:
            return "layer_norm"
        
        # Check for embedding layers
        if "embed" in layer_id_lower or "token_type" in layer_id_lower or "position" in layer_id_lower:
            return "embedding"
        
        # Check for pooling layers
        if "pool" in layer_id_lower or "cls" in layer_id_lower or "global" in layer_id_lower:
            return "pooling"
        
        # Check based on activations structure
        if "attention_weights" in layer_data or "attention_scores" in layer_data:
            return "self_attention"
        
        if "normalized_features" in layer_data or "variance" in layer_data:
            return "layer_norm"
        
        # Default to feed_forward if can't determine
        return "feed_forward"
    
    def _analyze_layer(self, layer_id: str, layer_type: str, 
                    layer_data: Dict[str, Any], inputs: Dict[str, Any],
                    model_info: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a transformer layer based on its type.
        
        Args:
            layer_id: ID of the layer
            layer_type: Type of the layer
            layer_data: Layer activations and data
            inputs: Input data being processed
            model_info: Model information
            config: Monitoring configuration
            
        Returns:
            Dictionary with layer analysis
        """
        # Basic analysis common to all layers
        analysis = {
            "layer_id": layer_id,
            "layer_type": layer_type,
            "metrics": {},
            "patterns": []
        }
        
        # Get monitoring level
        monitoring_level = config.get("monitoring_level", "comprehensive")
        
        # Extract layer position information
        layer_position = self._extract_layer_position(layer_id, model_info)
        analysis["layer_position"] = layer_position
        
        # Type-specific analysis
        if layer_type == "self_attention":
            self._analyze_self_attention_layer(analysis, layer_data, inputs, model_info, config)
        
        elif layer_type == "cross_attention":
            self._analyze_cross_attention_layer(analysis, layer_data, inputs, model_info, config)
        
        elif layer_type == "feed_forward":
            self._analyze_feed_forward_layer(analysis, layer_data, model_info, config)
        
        elif layer_type == "layer_norm":
            self._analyze_layer_norm(analysis, layer_data, model_info, config)
        
        elif layer_type == "embedding":
            self._analyze_embedding_layer(analysis, layer_data, inputs, model_info, config)
        
        elif layer_type == "pooling":
            self._analyze_pooling_layer(analysis, layer_data, inputs, model_info, config)
        
        # Include comprehensive metrics if requested
        if monitoring_level in ["comprehensive", "detailed"]:
            for metric_name in self.monitoring_metrics:
                if metric_name not in analysis["metrics"]:
                    metric_value = self._calculate_metric(
                        metric_name, layer_data, layer_type, model_info
                    )
                    if metric_value is not None:
                        analysis["metrics"][metric_name] = metric_value
        
        # Add detailed information for highest level of monitoring
        if monitoring_level == "detailed":
            # Add activation histograms
            analysis["activation_distribution"] = self._compute_activation_distribution(layer_data)
            
            # Add token-level analysis if applicable
            if layer_type in ["self_attention", "cross_attention"] and "token_info" not in analysis:
                max_tokens = config.get("max_tokens_to_analyze", 50)
                analysis["token_info"] = self._analyze_token_representations(
                    layer_data, inputs, max_tokens
                )
        
        return analysis
    
    def _extract_layer_position(self, layer_id: str, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract position information for a layer.
        
        Args:
            layer_id: ID of the layer
            model_info: Model information
            
        Returns:
            Dictionary with layer position information
        """
        position_info = {
            "depth_category": "unknown",
            "absolute_position": -1,
            "relative_position": -1
        }
        
        # Try to extract layer number
        layer_num = -1
        parts = layer_id.split(".")
        
        for part in parts:
            if part.startswith("layer"):
                num_str = part.replace("layer", "")
                if num_str.isdigit():
                    layer_num = int(num_str)
                    break
            elif part.isdigit():
                layer_num = int(part)
                break
        
        # Set position information if layer number is found
        if layer_num >= 0:
            position_info["absolute_position"] = layer_num
            
            num_layers = model_info.get("num_layers", 0)
            if num_layers > 0:
                position_info["relative_position"] = layer_num / num_layers
                
                # Categorize by depth
                if position_info["relative_position"] < 0.33:
                    position_info["depth_category"] = "early"
                elif position_info["relative_position"] < 0.67:
                    position_info["depth_category"] = "middle"
                else:
                    position_info["depth_category"] = "deep"
        
        # Check if it's encoder or decoder
        if "encoder" in layer_id.lower() and "decoder" not in layer_id.lower():
            position_info["component"] = "encoder"
        elif "decoder" in layer_id.lower():
            position_info["component"] = "decoder"
        else:
            position_info["component"] = "unknown"
        
        return position_info
    
    def _analyze_self_attention_layer(self, analysis: Dict[str, Any], 
                                   layer_data: Dict[str, Any],
                                   inputs: Dict[str, Any],
                                   model_info: Dict[str, Any],
                                   config: Dict[str, Any]) -> None:
        """
        Analyze a self-attention layer.
        
        Args:
            analysis: Analysis dictionary to update
            layer_data: Layer activations and data
            inputs: Input data being processed
            model_info: Model information
            config: Monitoring configuration
            
        Returns:
            None (updates analysis in place)
        """
        # Extract attention weights
        attention_weights = layer_data.get("attention_weights", 
                                        layer_data.get("attention_probs", 
                                                    layer_data.get("attn_weights")))
        
        if attention_weights is None:
            analysis["error"] = "No attention weights found"
            return
        
        # Ensure attention_weights is in the right format (list of head matrices)
        heads_data = []
        if isinstance(attention_weights, list):
            heads_data = attention_weights
        elif isinstance(attention_weights, dict) and "heads" in attention_weights:
            heads_data = attention_weights["heads"]
        else:
            # Assume it's a single matrix for simplicity
            heads_data = [attention_weights]
        
        # Process each attention head
        head_analyses = []
        for head_idx, head_weights in enumerate(heads_data):
            head_analysis = self._analyze_attention_head(
                head_idx, head_weights, inputs, analysis["layer_position"]
            )
            head_analyses.append(head_analysis)
        
        # Add head analyses to the layer analysis
        analysis["heads"] = head_analyses
        
        # Calculate attention entropy across all heads
        if head_analyses:
            entropies = [head["attention_entropy"] for head in head_analyses if "attention_entropy" in head]
            if entropies:
                analysis["metrics"]["attention_entropy"] = sum(entropies) / len(entropies)
        
        # Detect attention patterns
        if config.get("analyze_patterns", True):
            detected_patterns = []
            for head in head_analyses:
                if "detected_pattern" in head:
                    detected_patterns.append(head["detected_pattern"])
            
            analysis["patterns"] = self._summarize_attention_patterns(detected_patterns)
        
        # Add token analysis if input tokens are available
        input_tokens = inputs.get("tokens", inputs.get("input_ids"))
        if input_tokens and config.get("monitoring_level") == "detailed":
            analysis["token_info"] = self._analyze_tokens_with_attention(
                input_tokens, heads_data, config.get("max_tokens_to_analyze", 50)
            )
    
    def _analyze_attention_head(self, head_idx: int, head_weights: Any, 
                             inputs: Dict[str, Any],
                             layer_position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single attention head.
        
        Args:
            head_idx: Index of the attention head
            head_weights: Attention weight matrix for this head
            inputs: Input data being processed
            layer_position: Position information for the layer
            
        Returns:
            Dictionary with head analysis
        """
        head_analysis = {
            "head_idx": head_idx,
            "metrics": {}
        }
        
        # Ensure head_weights is a 2D matrix
        if hasattr(head_weights, "shape") and len(head_weights.shape) > 2:
            # Take first batch item if it's batched
            head_weights = head_weights[0]
        
        # Convert to list of lists if it's not already
        if not isinstance(head_weights, list):
            try:
                head_weights = head_weights.tolist()
            except:
                # If conversion fails, create a simple placeholder
                head_weights = [[0.5 for _ in range(5)] for _ in range(5)]
                head_analysis["error"] = "Failed to process attention weights"
        
        # Convert to list of lists if it's a flat list
        if isinstance(head_weights, list) and head_weights and not isinstance(head_weights[0], list):
            seq_len = int(math.sqrt(len(head_weights)))
            if seq_len * seq_len == len(head_weights):
                # Reshape to square matrix
                reshaped = []
                for i in range(seq_len):
                    row = head_weights[i*seq_len:(i+1)*seq_len]
                    reshaped.append(row)
                head_weights = reshaped
            else:
                # Can't reshape properly
                head_analysis["error"] = "Failed to reshape attention weights"
                return head_analysis
        
        # Calculate attention entropy
        entropy = self._calculate_attention_entropy(head_weights)
        head_analysis["attention_entropy"] = entropy
        
        # Detect attention pattern
        pattern = self._detect_attention_pattern(head_weights, layer_position)
        if pattern:
            head_analysis["detected_pattern"] = pattern
        
        # Calculate attention statistics
        head_analysis["statistics"] = self._calculate_attention_statistics(head_weights)
        
        return head_analysis
    
    def _calculate_attention_entropy(self, attention_weights: List[List[float]]) -> float:
        """
        Calculate the entropy of attention weights.
        
        Args:
            attention_weights: 2D matrix of attention weights
            
        Returns:
            Entropy value (0-1 normalized)
        """
        if not attention_weights or not attention_weights[0]:
            return 0.0
        
        # Calculate entropy for each query position
        entropies = []
        for query_weights in attention_weights:
            # Skip empty or invalid rows
            if not query_weights or sum(query_weights) == 0:
                continue
            
            # Normalize weights to ensure they sum to 1
            total = sum(query_weights)
            normalized_weights = [w / total for w in query_weights]
            
            # Calculate entropy: -sum(p * log(p))
            entropy = 0
            for weight in normalized_weights:
                if weight > 0:
                    entropy -= weight * math.log2(weight)
            
            # Normalize by maximum possible entropy
            max_entropy = math.log2(len(normalized_weights))
            if max_entropy > 0:
                normalized_entropy = entropy / max_entropy
            else:
                normalized_entropy = 0
            
            entropies.append(normalized_entropy)
        
        # Return average entropy
        if entropies:
            return sum(entropies) / len(entropies)
        else:
            return 0.0
    
    def _detect_attention_pattern(self, attention_weights: List[List[float]], 
                               layer_position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect the attention pattern in a matrix.
        
        Args:
            attention_weights: 2D matrix of attention weights
            layer_position: Position information for the layer
            
        Returns:
            Dictionary with detected pattern information or None
        """
        if not attention_weights or not attention_weights[0]:
            return None
        
        # Calculate pattern scores
        scores = {}
        
        # 1. Diagonal pattern (attention focused near diagonal)
        diagonal_score = self._calculate_diagonal_score(attention_weights)
        if diagonal_score > self.attention_patterns["diagonal"]["detection_threshold"]:
            scores["diagonal"] = diagonal_score
        
        # 2. Vertical pattern (attention focused on specific key positions)
        vertical_score = self._calculate_vertical_score(attention_weights)
        if vertical_score > self.attention_patterns["vertical"]["detection_threshold"]:
            scores["vertical"] = vertical_score
        
        # 3. Horizontal pattern (queries focusing on many keys)
        horizontal_score = self._calculate_horizontal_score(attention_weights)
        if horizontal_score > self.attention_patterns["horizontal"]["detection_threshold"]:
            scores["horizontal"] = horizontal_score
        
        # 4. Global attention pattern (broad distribution)
        global_score = self._calculate_global_score(attention_weights)
        if global_score > self.attention_patterns["global"]["detection_threshold"]:
            scores["global"] = global_score
        
        # 5. Triangular pattern (attention only to previous tokens - causal mask)
        triangular_score = self._calculate_triangular_score(attention_weights)
        if triangular_score > self.attention_patterns["triangular"]["detection_threshold"]:
            scores["triangular"] = triangular_score
        
        # Find the strongest pattern
        if not scores:
            return None
        
        strongest_pattern = max(scores.items(), key=lambda x: x[1])
        pattern_type = strongest_pattern[0]
        pattern_score = strongest_pattern[1]
        
        # Check if this pattern is typical for this layer position
        typical = False
        if pattern_type in self.attention_patterns:
            typical_layers = self.attention_patterns[pattern_type]["typical_layers"]
            position_category = layer_position.get("depth_category", "unknown")
            component = layer_position.get("component", "unknown")
            
            for typical_layer in typical_layers:
                if (position_category in typical_layer and 
                    (component in typical_layer or "encoder" in typical_layer or "decoder" in typical_layer)):
                    typical = True
                    break
        
        return {
            "type": pattern_type,
            "score": pattern_score,
            "description": self.attention_patterns[pattern_type]["description"],
            "indication": self.attention_patterns[pattern_type]["indication"],
            "is_typical": typical
        }
    
    def _calculate_diagonal_score(self, matrix: List[List[float]]) -> float:
        """Calculate how strongly the matrix follows a diagonal pattern."""
        if not matrix or not matrix[0]:
            return 0.0
        
        n = len(matrix)
        m = len(matrix[0])
        
        # Calculate weight in diagonal band vs. outside
        diagonal_sum = 0
        total_sum = 0
        
        for i in range(n):
            for j in range(m):
                weight = matrix[i][j]
                distance = abs(i - j)
                
                total_sum += weight
                if distance <= max(1, n // 10):  # Consider diagonal band as 10% of sequence length
                    diagonal_sum += weight
        
        if total_sum == 0:
            return 0.0
        
        return diagonal_sum / total_sum
    
    def _calculate_vertical_score(self, matrix: List[List[float]]) -> float:
        """Calculate how strongly the matrix follows a vertical pattern."""
        if not matrix or not matrix[0]:
            return 0.0
        
        n = len(matrix)
        m = len(matrix[0])
        
        # Calculate column-wise concentration
        column_sums = [sum(matrix[i][j] for i in range(n)) for j in range(m)]
        column_max = max(column_sums) if column_sums else 0
        column_mean = sum(column_sums) / m if m > 0 else 0
        
        # Vertical pattern has some columns with much higher sums than others
        if column_mean == 0:
            return 0.0
        
        # Calculate how much the maximum column sum exceeds the mean
        vertical_strength = column_max / column_mean if column_mean > 0 else 0
        
        # Normalize to [0, 1]
        return min(1.0, max(0.0, (vertical_strength - 1) / 3))
    
    def _calculate_horizontal_score(self, matrix: List[List[float]]) -> float:
        """Calculate how strongly the matrix follows a horizontal pattern."""
        if not matrix or not matrix[0]:
            return 0.0
        
        n = len(matrix)
        
        # Calculate row-wise concentration
        row_sums = [sum(row) for row in matrix]
        row_max = max(row_sums) if row_sums else 0
        row_mean = sum(row_sums) / n if n > 0 else 0
        
        # Horizontal pattern has some rows with much higher sums than others
        if row_mean == 0:
            return 0.0
        
        # Calculate how much the maximum row sum exceeds the mean
        horizontal_strength = row_max / row_mean if row_mean > 0 else 0
        
        # Normalize to [0, 1]
        return min(1.0, max(0.0, (horizontal_strength - 1) / 3))
    
    def _calculate_global_score(self, matrix: List[List[float]]) -> float:
        """Calculate how strongly the matrix follows a global attention pattern."""
        if not matrix or not matrix[0]:
            return 0.0
        
        # Calculate entropy of the flattened matrix
        flat = [weight for row in matrix for weight in row]
        total = sum(flat)
        
        if total == 0:
            return 0.0
        
        # Normalize
        normalized = [w / total for w in flat]
        
        # Calculate entropy
        entropy = 0
        for weight in normalized:
            if weight > 0:
                entropy -= weight * math.log2(weight)
        
        # Normalize by maximum possible entropy
        max_entropy = math.log2(len(normalized))
        if max_entropy > 0:
            normalized_entropy = entropy / max_entropy
        else:
            normalized_entropy = 0
        
        # Global attention has high entropy
        return normalized_entropy
    
    def _calculate_triangular_score(self, matrix: List[List[float]]) -> float:
        """Calculate how strongly the matrix follows a triangular pattern (causal mask)."""
        if not matrix or not matrix[0]:
            return 0.0
        
        n = len(matrix)
        m = len(matrix[0])
        
        # For triangular pattern, weights above diagonal should be close to 0
        upper_sum = 0
        lower_sum = 0
        
        for i in range(n):
            for j in range(m):
                if j > i:  # Upper triangular
                    upper_sum += matrix[i][j]
                else:  # Lower triangular (including diagonal)
                    lower_sum += matrix[i][j]
        
        total_sum = upper_sum + lower_sum
        if total_sum == 0:
            return 0.0
        
        # High score means lower triangle dominates (causal mask)
        return lower_sum / total_sum
    
    def _calculate_attention_statistics(self, attention_weights: List[List[float]]) -> Dict[str, float]:
        """
        Calculate basic statistics for attention weights.
        
        Args:
            attention_weights: 2D matrix of attention weights
            
        Returns:
            Dictionary with attention statistics
        """
        if not attention_weights or not attention_weights[0]:
            return {
                "mean": 0,
                "max": 0,
                "sparsity": 0,
                "entropy": 0
            }
        
        # Flatten weights
        flat_weights = [w for row in attention_weights for w in row]
        
        # Calculate statistics
        mean_weight = sum(flat_weights) / len(flat_weights) if flat_weights else 0
        max_weight = max(flat_weights) if flat_weights else 0
        min_weight = min(flat_weights) if flat_weights else 0
        
        # Calculate sparsity (fraction of weights below threshold)
        threshold = 0.01  # Weights below this are considered "zero"
        sparsity = sum(1 for w in flat_weights if w < threshold) / len(flat_weights) if flat_weights else 0
        
        # Calculate coefficient of variation
        if flat_weights and mean_weight > 0:
            variance = sum((w - mean_weight) ** 2 for w in flat_weights) / len(flat_weights)
            std_dev = math.sqrt(variance)
            cv = std_dev / mean_weight
        else:
            cv = 0
        
        return {
            "mean": mean_weight,
            "max": max_weight,
            "min": min_weight,
            "sparsity": sparsity,
            "coefficient_of_variation": cv
        }
    
    def _analyze_tokens_with_attention(self, tokens: List[Any], 
                                     attention_heads: List[Any],
                                     max_tokens: int) -> List[Dict[str, Any]]:
        """
        Analyze how attention works on specific tokens.
        
        Args:
            tokens: Input tokens
            attention_heads: List of attention matrices
            max_tokens: Maximum number of tokens to analyze
            
        Returns:
            List of token analyses
        """
        if not tokens or not attention_heads:
            return []
        
        # Limit the number of tokens to analyze
        if len(tokens) > max_tokens:
            tokens = tokens[:max_tokens]
        
        # Prepare token analyses
        token_analyses = []
        
        for token_idx, token in enumerate(tokens):
            if token_idx >= max_tokens:
                break
            
            # Extract token identifier
            token_id = token
            if isinstance(token, dict) and "id" in token:
                token_id = token["id"]
            
            # Calculate statistics across all heads
            attending_to_token = []  # How much other tokens attend to this token
            token_attending_to = []  # How much this token attends to others
            
            for head_weights in attention_heads:
                if len(head_weights) <= token_idx:
                    continue
                    
                # How much this token attends to others (query perspective)
                if token_idx < len(head_weights):
                    token_attending_to.append(head_weights[token_idx])
                
                # How much others attend to this token (key perspective)
                for query_idx, query_weights in enumerate(head_weights):
                    if query_idx != token_idx and token_idx < len(query_weights):
                        attending_to_token.append(query_weights[token_idx])
            
            # Calculate statistics
            avg_attending_to = sum(sum(weights) for weights in token_attending_to) / len(token_attending_to) if token_attending_to else 0
            avg_attended_by = sum(attending_to_token) / len(attending_to_token) if attending_to_token else 0
            
            token_analyses.append({
                "token_idx": token_idx,
                "token_id": token_id,
                "attends_to_others": avg_attending_to,
                "attended_by_others": avg_attended_by,
                "attention_ratio": avg_attended_by / avg_attending_to if avg_attending_to > 0 else 0
            })
        
        return token_analyses
    
    def _summarize_attention_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Summarize detected attention patterns across heads.
        
        Args:
            patterns: List of patterns detected in attention heads
            
        Returns:
            List of summarized patterns with counts
        """
        if not patterns:
            return []
        
        # Count pattern types
        pattern_counts = {}
        
        for pattern in patterns:
            pattern_type = pattern["type"]
            if pattern_type in pattern_counts:
                pattern_counts[pattern_type]["count"] += 1
                pattern_counts[pattern_type]["score_sum"] += pattern["score"]
                pattern_counts[pattern_type]["typical_count"] += 1 if pattern.get("is_typical", False) else 0
            else:
                pattern_counts[pattern_type] = {
                    "type": pattern_type,
                    "count": 1,
                    "score_sum": pattern["score"],
                    "description": pattern["description"],
                    "indication": pattern["indication"],
                    "typical_count": 1 if pattern.get("is_typical", False) else 0
                }
        
        # Convert to list and sort by count
        summary = []
        for pattern_type, data in pattern_counts.items():
            summary.append({
                "type": pattern_type,
                "count": data["count"],
                "average_score": data["score_sum"] / data["count"],
                "description": data["description"],
                "indication": data["indication"],
                "typical_ratio": data["typical_count"] / data["count"]
            })
        
        summary.sort(key=lambda x: x["count"], reverse=True)
        return summary
    
    def _analyze_cross_attention_layer(self, analysis: Dict[str, Any], 
                                     layer_data: Dict[str, Any],
                                     inputs: Dict[str, Any],
                                     model_info: Dict[str, Any],
                                     config: Dict[str, Any]) -> None:
        """
        Analyze a cross-attention layer.
        
        Args:
            analysis: Analysis dictionary to update
            layer_data: Layer activations and data
            inputs: Input data being processed
            model_info: Model information
            config: Monitoring configuration
            
        Returns:
            None (updates analysis in place)
        """
        # Similar to self-attention but with focus on encoder-decoder alignment
        attention_weights = layer_data.get("attention_weights", 
                                        layer_data.get("cross_attention_weights"))
        
        if attention_weights is None:
            analysis["error"] = "No cross-attention weights found"
            return
        
        # Process attention heads similar to self-attention
        heads_data = []
        if isinstance(attention_weights, list):
            heads_data = attention_weights
        elif isinstance(attention_weights, dict) and "heads" in attention_weights:
            heads_data = attention_weights["heads"]
        else:
            heads_data = [attention_weights]
        
        # Process each attention head
        head_analyses = []
        for head_idx, head_weights in enumerate(heads_data):
            head_analysis = self._analyze_attention_head(
                head_idx, head_weights, inputs, analysis["layer_position"]
            )
            
            # Add additional cross-attention metrics
            if "encoder_hidden_states" in inputs and "decoder_hidden_states" in inputs:
                head_analysis["alignment_score"] = self._calculate_alignment_score(
                    head_weights, inputs["encoder_hidden_states"], inputs["decoder_hidden_states"]
                )
            
            head_analyses.append(head_analysis)
        
        # Add head analyses to the layer analysis
        analysis["heads"] = head_analyses
        
        # Calculate attention alignment score if available
        if any("alignment_score" in head for head in head_analyses):
            alignment_scores = [head["alignment_score"] for head in head_analyses if "alignment_score" in head]
            if alignment_scores:
                analysis["metrics"]["attention_alignment"] = sum(alignment_scores) / len(alignment_scores)
    
    def _calculate_alignment_score(self, attention_weights: Any, 
                                encoder_states: Any, 
                                decoder_states: Any) -> float:
        """
        Calculate how well cross-attention aligns encoder and decoder.
        
        Args:
            attention_weights: Cross-attention weights
            encoder_states: Encoder hidden states
            decoder_states: Decoder hidden states
            
        Returns:
            Alignment score (0-1)
        """
        # This is a simplified implementation
        # In a real system, would compute semantic alignment between attended encoder tokens
        # and the corresponding decoder states
        
        # For this demonstration, use a simpler metric based on attention concentration
        if not attention_weights or not attention_weights[0]:
            return 0.5  # Default value
        
        # Calculate concentration of attention (higher means more focused alignment)
        flat_weights = [w for row in attention_weights for w in row]
        if not flat_weights:
            return 0.5
        
        # Calculate statistics
        mean_weight = sum(flat_weights) / len(flat_weights)
        max_weight = max(flat_weights)
        
        # Alignment score based on concentration
        if mean_weight > 0:
            concentration = max_weight / mean_weight
            # Normalize to [0, 1]
            alignment = min(1.0, max(0.0, (concentration - 1) / 4))
            return alignment
        else:
            return 0.5
    
    def _analyze_feed_forward_layer(self, analysis: Dict[str, Any], 
                                 layer_data: Dict[str, Any],
                                 model_info: Dict[str, Any],
                                 config: Dict[str, Any]) -> None:
        """
        Analyze a feed-forward network layer.
        
        Args:
            analysis: Analysis dictionary to update
            layer_data: Layer activations and data
            model_info: Model information
            config: Monitoring configuration
            
        Returns:
            None (updates analysis in place)
        """
        # Extract activations
        activations = layer_data.get("activations", 
                                  layer_data.get("output", 
                                              layer_data.get("ffn_output")))
        
        intermediate_activations = layer_data.get("intermediate_activations", 
                                               layer_data.get("intermediate_output"))
        
        if activations is None and intermediate_activations is None:
            analysis["error"] = "No activations found"
            return
        
        # Use intermediate activations if available (these are typically after first linear + activation)
        activation_data = intermediate_activations if intermediate_activations is not None else activations
        
        # Calculate activation sparsity
        if activation_data is not None:
            flat_activations = self._flatten_activations(activation_data)
            
            if flat_activations:
                sparsity = self._calculate_activation_sparsity(flat_activations)
                analysis["metrics"]["activation_sparsity"] = sparsity
                
                # Calculate feature diversity
                diversity = self._calculate_feature_diversity(activation_data)
                analysis["metrics"]["feature_diversity"] = diversity
                
                # Add activation statistics
                analysis["activation_stats"] = self._calculate_activation_statistics(flat_activations)
        
        # Look for feature specialization patterns
        if config.get("analyze_patterns", True) and intermediate_activations is not None:
            patterns = self._detect_ffn_patterns(intermediate_activations)
            if patterns:
                analysis["patterns"] = patterns
    
    def _flatten_activations(self, activations: Any) -> List[float]:
        """
        Flatten activation tensor to a list of values.
        
        Args:
            activations: Activation tensor of any shape
            
        Returns:
            Flattened list of activation values
        """
        # Handle different activation formats
        if isinstance(activations, list):
            # If it's already a list, check if it needs flattening
            if isinstance(activations[0], list):
                return [x for sublist in activations for x in sublist]
            else:
                return activations
        
        # If it's a tensor-like object with shape and flatten method
        if hasattr(activations, 'flatten') and callable(getattr(activations, 'flatten')):
            try:
                return activations.flatten().tolist()
            except:
                pass
        
        # If it's a tensor-like object but no flatten method
        if hasattr(activations, 'shape'):
            try:
                # Try to convert to list
                return list(activations.reshape(-1))
            except:
                pass
        
        # If all else fails, return empty list
        return []
    
    def _calculate_activation_sparsity(self, activations: List[float]) -> float:
        """
        Calculate the sparsity of activations.
        
        Args:
            activations: List of activation values
            
        Returns:
            Sparsity (fraction of near-zero activations)
        """
        if not activations:
            return 0.0
        
        # Count near-zero activations
        threshold = 0.01
        zero_count = sum(1 for a in activations if abs(a) < threshold)
        
        # Calculate sparsity
        return zero_count / len(activations)
    
    def _calculate_feature_diversity(self, activations: Any) -> float:
        """
        Calculate the diversity of activated features.
        
        Args:
            activations: Activation tensor
            
        Returns:
            Feature diversity score (0-1)
        """
        # This is a simplified implementation
        # In a real system, would analyze activation patterns across different inputs
        
        # For this demonstration, use a simple estimate based on activation statistics
        flat_activations = self._flatten_activations(activations)
        if not flat_activations:
            return 0.5  # Default value
        
        # Calculate statistics
        mean = sum(flat_activations) / len(flat_activations)
        variance = sum((a - mean) ** 2 for a in flat_activations) / len(flat_activations)
        std_dev = math.sqrt(variance) if variance > 0 else 0
        
        # Coefficient of variation as a simple diversity metric
        if mean != 0:
            cv = std_dev / abs(mean)
            # Normalize to [0, 1]
            diversity = min(1.0, max(0.0, cv / 2.0))
            return diversity
        else:
            return 0.5
    
    def _calculate_activation_statistics(self, activations: List[float]) -> Dict[str, float]:
        """
        Calculate basic statistics for activations.
        
        Args:
            activations: List of activation values
            
        Returns:
            Dictionary with activation statistics
        """
        if not activations:
            return {
                "mean": 0,
                "max": 0,
                "min": 0,
                "std_dev": 0
            }
        
        # Calculate statistics
        mean = sum(activations) / len(activations)
        max_val = max(activations)
        min_val = min(activations)
        
        # Calculate standard deviation
        variance = sum((a - mean) ** 2 for a in activations) / len(activations)
        std_dev = math.sqrt(variance) if variance > 0 else 0
        
        return {
            "mean": mean,
            "max": max_val,
            "min": min_val,
            "std_dev": std_dev,
            "range": max_val - min_val
        }
    
    def _detect_ffn_patterns(self, activations: Any) -> List[Dict[str, Any]]:
        """
        Detect patterns in feed-forward network activations.
        
        Args:
            activations: Activation tensor
            
        Returns:
            List of detected patterns
        """
        # Simplified implementation - in a real system would do more sophisticated pattern detection
        flat_activations = self._flatten_activations(activations)
        if not flat_activations:
            return []
        
        patterns = []
        
        # Check for feature specialization (high variance)
        stats = self._calculate_activation_statistics(flat_activations)
        if stats["std_dev"] > 0.5 * abs(stats["mean"]):
            patterns.append({
                "type": "feature_specialization",
                "score": min(1.0, stats["std_dev"] / max(0.1, abs(stats["mean"]))),
                "description": "Neurons specializing in different features",
                "evidence": f"High activation variance (std={stats['std_dev']:.3f}, mean={stats['mean']:.3f})"
            })
        
        # Check for sparse activation
        sparsity = self._calculate_activation_sparsity(flat_activations)
        if sparsity > 0.5:
            patterns.append({
                "type": "sparse_activation",
                "score": sparsity,
                "description": "Only a small subset of neurons active",
                "evidence": f"Activation sparsity: {sparsity:.2f}"
            })
        
        return patterns
    
    def _analyze_layer_norm(self, analysis: Dict[str, Any], 
                         layer_data: Dict[str, Any],
                         model_info: Dict[str, Any],
                         config: Dict[str, Any]) -> None:
        """
        Analyze a layer normalization layer.
        
        Args:
            analysis: Analysis dictionary to update
            layer_data: Layer activations and data
            model_info: Model information
            config: Monitoring configuration
            
        Returns:
            None (updates analysis in place)
        """
        # Extract normalization data
        normalized_features = layer_data.get("normalized_features", 
                                          layer_data.get("output"))
        
        means = layer_data.get("means", layer_data.get("mean"))
        variances = layer_data.get("variances", layer_data.get("variance"))
        
        if normalized_features is None:
            analysis["error"] = "No normalized features found"
            return
        
        # Calculate normalization magnitude
        if means is not None and variances is not None:
            # Convert to lists if needed
            if not isinstance(means, list):
                try:
                    means = means.tolist()
                except:
                    means = [0]
            
            if not isinstance(variances, list):
                try:
                    variances = variances.tolist()
                except:
                    variances = [1]
            
            # Calculate average normalization magnitude
            if means and variances:
                avg_shift = sum(abs(m) for m in means) / len(means)
                avg_scale = sum(1 / math.sqrt(v) for v in variances if v > 0) / len(variances)
                
                analysis["metrics"]["normalization_magnitude"] = (avg_shift + avg_scale) / 2
        else:
            # If means/variances not available, calculate from normalized features
            flat_features = self._flatten_activations(normalized_features)
            if flat_features:
                mean = sum(flat_features) / len(flat_features)
                variance = sum((f - mean) ** 2 for f in flat_features) / len(flat_features)
                
                analysis["metrics"]["normalization_magnitude"] = 1 / (math.sqrt(variance) if variance > 0 else 1)
        
        # Calculate feature distribution metrics
        flat_features = self._flatten_activations(normalized_features)
        if flat_features:
            analysis["normalized_stats"] = self._calculate_activation_statistics(flat_features)
    
    def _analyze_embedding_layer(self, analysis: Dict[str, Any], 
                              layer_data: Dict[str, Any],
                              inputs: Dict[str, Any],
                              model_info: Dict[str, Any],
                              config: Dict[str, Any]) -> None:
        """
        Analyze an embedding layer.
        
        Args:
            analysis: Analysis dictionary to update
            layer_data: Layer activations and data
            inputs: Input data being processed
            model_info: Model information
            config: Monitoring configuration
            
        Returns:
            None (updates analysis in place)
        """
        # Extract embedding data
        embeddings = layer_data.get("embeddings", 
                                 layer_data.get("output"))
        
        if embeddings is None:
            analysis["error"] = "No embeddings found"
            return
        
        # Check if embeddings is a list of tensors or a single tensor
        if isinstance(embeddings, list) and isinstance(embeddings[0], dict) and "vector" in embeddings[0]:
            # List of embedding objects
            embedding_vectors = [e["vector"] for e in embeddings]
            embedding_tokens = [e.get("token", i) for i, e in enumerate(embeddings)]
        else:
            # Single tensor or list of vectors
            embedding_vectors = embeddings
            embedding_tokens = inputs.get("tokens", inputs.get("input_ids", []))
        
        # Calculate embedding utilization
        if isinstance(embedding_vectors, list):
            # Calculate average vector norm
            norms = []
            for vec in embedding_vectors:
                if isinstance(vec, list):
                    norm = math.sqrt(sum(v * v for v in vec))
                    norms.append(norm)
            
            if norms:
                avg_norm = sum(norms) / len(norms)
                analysis["metrics"]["embedding_utilization"] = min(1.0, avg_norm / math.sqrt(model_info.get("hidden_size", 768)))
        
        # Calculate semantic separation if enough tokens
        if len(embedding_vectors) > 1:
            separation = self._calculate_embedding_separation(embedding_vectors)
            analysis["metrics"]["semantic_separation"] = separation
        
        # Add token analysis if monitoring level is detailed
        if config.get("monitoring_level") == "detailed" and embedding_tokens:
            max_tokens = config.get("max_tokens_to_analyze", 50)
            analysis["token_info"] = self._analyze_token_embeddings(
                embedding_vectors, embedding_tokens, max_tokens
            )
    
    def _calculate_embedding_separation(self, embeddings: List[Any]) -> float:
        """
        Calculate how well separated embeddings are in the vector space.
        
        Args:
            embeddings: List of embedding vectors
            
        Returns:
            Separation score (0-1)
        """
        if not embeddings or len(embeddings) < 2:
            return 0.0
        
        # Calculate average cosine similarity between embeddings
        similarities = []
        
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                vec1 = embeddings[i]
                vec2 = embeddings[j]
                
                if isinstance(vec1, list) and isinstance(vec2, list) and len(vec1) == len(vec2):
                    # Calculate cosine similarity
                    dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
                    norm1 = math.sqrt(sum(v * v for v in vec1))
                    norm2 = math.sqrt(sum(v * v for v in vec2))
                    
                    if norm1 > 0 and norm2 > 0:
                        similarity = dot_product / (norm1 * norm2)
                        similarities.append(similarity)
        
        if not similarities:
            return 0.5  # Default value
        
        # Average similarity
        avg_similarity = sum(similarities) / len(similarities)
        
        # Convert to separation (1 - similarity)
        separation = 1 - avg_similarity
        
        # Normalize to [0, 1]
        return max(0.0, min(1.0, separation))
    
    def _analyze_token_embeddings(self, embeddings: List[Any], 
                               tokens: List[Any], 
                               max_tokens: int) -> List[Dict[str, Any]]:
        """
        Analyze embeddings at the token level.
        
        Args:
            embeddings: List of embedding vectors
            tokens: Corresponding tokens
            max_tokens: Maximum number of tokens to analyze
            
        Returns:
            List of token embedding analyses
        """
        if not embeddings or not tokens:
            return []
        
        # Limit the number of tokens
        num_tokens = min(len(embeddings), len(tokens), max_tokens)
        
        token_analyses = []
        
        for i in range(num_tokens):
            vec = embeddings[i]
            token = tokens[i]
            
            # Extract token identifier
            token_id = token
            if isinstance(token, dict) and "id" in token:
                token_id = token["id"]
            
            # Calculate vector norm
            if isinstance(vec, list):
                norm = math.sqrt(sum(v * v for v in vec))
            else:
                norm = 0.5  # Default value
            
            token_analyses.append({
                "token_idx": i,
                "token_id": token_id,
                "embedding_norm": norm,
                "relative_magnitude": norm / math.sqrt(len(vec)) if isinstance(vec, list) else 0.5
            })
        
        return token_analyses
    
    def _analyze_pooling_layer(self, analysis: Dict[str, Any], 
                            layer_data: Dict[str, Any],
                            inputs: Dict[str, Any],
                            model_info: Dict[str, Any],
                            config: Dict[str, Any]) -> None:
        """
        Analyze a pooling layer.
        
        Args:
            analysis: Analysis dictionary to update
            layer_data: Layer activations and data
            inputs: Input data being processed
            model_info: Model information
            config: Monitoring configuration
            
        Returns:
            None (updates analysis in place)
        """
        # Extract pooled representation
        pooled = layer_data.get("pooled_output", 
                             layer_data.get("output", 
                                         layer_data.get("cls_output")))
        
        if pooled is None:
            analysis["error"] = "No pooled output found"
            return
        
        # Calculate information retention
        # For pooling layers, this measures how much of the sequence information
        # is preserved in the pooled representation
        
        sequence_output = layer_data.get("sequence_output", inputs.get("sequence_output"))
        
        if sequence_output is not None:
            # Convert to lists if needed
            if not isinstance(pooled, list) and hasattr(pooled, 'tolist'):
                try:
                    pooled = pooled.tolist()
                except:
                    pooled = [0.5] * model_info.get("hidden_size", 768)
            
            if not isinstance(sequence_output, list) and hasattr(sequence_output, 'tolist'):
                try:
                    sequence_output = sequence_output.tolist()
                except:
                    sequence_output = [[0.5] * model_info.get("hidden_size", 768)]
            
            # Simplified calculation based on average sequence representation
            if isinstance(sequence_output, list) and sequence_output and isinstance(sequence_output[0], list):
                # Calculate average sequence representation
                seq_length = len(sequence_output)
                feature_dim = len(sequence_output[0])
                
                avg_sequence = [0] * feature_dim
                for seq_vec in sequence_output:
                    for i in range(min(len(seq_vec), feature_dim)):
                        avg_sequence[i] += seq_vec[i] / seq_length
                
                # Calculate similarity between pooled and average sequence
                if isinstance(pooled, list) and len(pooled) == len(avg_sequence):
                    dot_product = sum(p * s for p, s in zip(pooled, avg_sequence))
                    pooled_norm = math.sqrt(sum(p * p for p in pooled))
                    seq_norm = math.sqrt(sum(s * s for s in avg_sequence))
                    
                    if pooled_norm > 0 and seq_norm > 0:
                        similarity = dot_product / (pooled_norm * seq_norm)
                        analysis["metrics"]["information_retention"] = similarity
        
        # Calculate representation compactness
        if isinstance(pooled, list):
            # Measure sparsity of the pooled representation
            sparsity = self._calculate_activation_sparsity(pooled)
            analysis["metrics"]["representation_compactness"] = 1 - sparsity
    
    def _analyze_cross_layer_patterns(self, layers: Dict[str, Any], 
                                   layer_analyses: Dict[str, Dict[str, Any]],
                                   model_info: Dict[str, Any],
                                   config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze patterns across different layers.
        
        Args:
            layers: Layer activations dictionary
            layer_analyses: Individual layer analyses
            model_info: Model information
            config: Monitoring configuration
            
        Returns:
            Dictionary with cross-layer analysis
        """
        cross_analysis = {
            "information_flow": {},
            "attention_evolution": [],
            "layer_specialization": []
        }
        
        # Sort layers by depth/position if possible
        layer_positions = {}
        for layer_id, analysis in layer_analyses.items():
            position = analysis.get("layer_position", {}).get("absolute_position", -1)
            if position >= 0:
                layer_positions[layer_id] = position
        
        sorted_layers = sorted(layer_analyses.keys(), key=lambda x: layer_positions.get(x, -1))
        
        # Analyze attention pattern evolution
        attention_layers = [lid for lid in sorted_layers 
                           if layer_analyses[lid]["layer_type"] in ["self_attention", "cross_attention"]]
        
        if len(attention_layers) > 1:
            # Track patterns across layers
            patterns_by_layer = []
            
            for layer_id in attention_layers:
                analysis = layer_analyses[layer_id]
                layer_patterns = analysis.get("patterns", [])
                if layer_patterns:
                    patterns_by_layer.append({
                        "layer_id": layer_id,
                        "position": analysis.get("layer_position", {}).get("absolute_position", -1),
                        "patterns": layer_patterns
                    })
            
            # Sort by position
            patterns_by_layer.sort(key=lambda x: x["position"])
            
            # Find pattern transitions
            transitions = []
            for i in range(1, len(patterns_by_layer)):
                prev = patterns_by_layer[i-1]
                curr = patterns_by_layer[i]
                
                # Get dominant pattern for each layer
                prev_dominant = prev["patterns"][0] if prev["patterns"] else None
                curr_dominant = curr["patterns"][0] if curr["patterns"] else None
                
                if prev_dominant and curr_dominant and prev_dominant["type"] != curr_dominant["type"]:
                    transitions.append({
                        "from_layer": prev["layer_id"],
                        "to_layer": curr["layer_id"],
                        "from_pattern": prev_dominant["type"],
                        "to_pattern": curr_dominant["type"],
                        "position": curr["position"]
                    })
            
            cross_analysis["attention_evolution"] = {
                "pattern_by_layer": patterns_by_layer,
                "transitions": transitions
            }
        
        # Analyze layer specialization
        layer_types = {}
        for layer_id, analysis in layer_analyses.items():
            layer_type = analysis.get("layer_type")
            if layer_type:
                if layer_type in layer_types:
                    layer_types[layer_type].append(layer_id)
                else:
                    layer_types[layer_type] = [layer_id]
        
        specializations = []
        
        # For each type, find the layers with distinctive metrics
        for layer_type, type_layers in layer_types.items():
            if len(type_layers) < 2:
                continue
                
            # Collect metrics across layers of this type
            metric_values = {}
            
            for layer_id in type_layers:
                metrics = layer_analyses[layer_id].get("metrics", {})
                for metric, value in metrics.items():
                    if metric not in metric_values:
                        metric_values[metric] = []
                    metric_values[metric].append((layer_id, value))
            
            # For each metric, find outliers
            for metric, values in metric_values.items():
                if len(values) < 3:
                    continue
                    
                # Calculate mean and std dev
                metric_vals = [v[1] for v in values]
                mean = sum(metric_vals) / len(metric_vals)
                variance = sum((v - mean) ** 2 for v in metric_vals) / len(metric_vals)
                std_dev = math.sqrt(variance) if variance > 0 else 0
                
                if std_dev > 0:
                    # Find layers with values more than 1.5 std dev from mean
                    for layer_id, value in values:
                        z_score = (value - mean) / std_dev
                        if abs(z_score) > 1.5:
                            direction = "high" if z_score > 0 else "low"
                            specializations.append({
                                "layer_id": layer_id,
                                "layer_type": layer_type,
                                "metric": metric,
                                "value": value,
                                "z_score": z_score,
                                "direction": direction,
                                "typical_range": self.monitoring_metrics.get(metric, {}).get("typical_range", [0, 1])
                            })
        
        cross_analysis["layer_specialization"] = specializations
        
        # Analyze information flow if comprehensive monitoring
        if config.get("monitoring_level") in ["comprehensive", "detailed"]:
            # Build information flow through layers
            flow_nodes = []
            flow_edges = []
            
            for i, layer_id in enumerate(sorted_layers):
                analysis = layer_analyses[layer_id]
                layer_type = analysis.get("layer_type")
                
                # Create node
                node = {
                    "id": layer_id,
                    "layer_type": layer_type,
                    "position": i,
                    "depth": analysis.get("layer_position", {}).get("absolute_position", i)
                }
                
                # Add key metrics
                if layer_type == "self_attention":
                    entropy = analysis.get("metrics", {}).get("attention_entropy")
                    if entropy is not None:
                        node["attention_entropy"] = entropy
                
                elif layer_type == "feed_forward":
                    sparsity = analysis.get("metrics", {}).get("activation_sparsity")
                    if sparsity is not None:
                        node["activation_sparsity"] = sparsity
                
                flow_nodes.append(node)
                
                # Create edges
                if i > 0:
                    prev_id = sorted_layers[i-1]
                    edge = {
                        "source": prev_id,
                        "target": layer_id,
                        "weight": 1.0
                    }
                    
                    # Add edge metrics if available
                    prev_analysis = layer_analyses[prev_id]
                    
                    if "cross_layer_alignment" in prev_analysis.get("metrics", {}):
                        edge["alignment"] = prev_analysis["metrics"]["cross_layer_alignment"]
                    
                    flow_edges.append(edge)
            
            cross_analysis["information_flow"] = {
                "nodes": flow_nodes,
                "edges": flow_edges
            }
        
        return cross_analysis
    
    def _measure_efficiency(self, layer_activations: Dict[str, Any], 
                         layer_analyses: Dict[str, Dict[str, Any]],
                         model_info: Dict[str, Any]) -> Dict[str, float]:
        """
        Measure overall efficiency metrics for the model.
        
        Args:
            layer_activations: Layer activations dictionary
            layer_analyses: Individual layer analyses
            model_info: Model information
            
        Returns:
            Dictionary with efficiency metrics
        """
        efficiency_metrics = {
            "overall_sparsity": 0.0,
            "attention_efficiency": 0.0,
            "computational_utilization": 0.0,
            "information_density": 0.0
        }
        
        # Calculate overall activation sparsity
        sparsity_values = []
        
        for layer_id, analysis in layer_analyses.items():
            if "activation_sparsity" in analysis.get("metrics", {}):
                sparsity_values.append(analysis["metrics"]["activation_sparsity"])
        
        if sparsity_values:
            efficiency_metrics["overall_sparsity"] = sum(sparsity_values) / len(sparsity_values)
        
        # Calculate attention efficiency (how well attention is utilized)
        attention_entropy_values = []
        
        for layer_id, analysis in layer_analyses.items():
            if "attention_entropy" in analysis.get("metrics", {}):
                attention_entropy_values.append(analysis["metrics"]["attention_entropy"])
        
        if attention_entropy_values:
            # For attention, moderate entropy is most efficient
            # Too low = overfocused, too high = unfocused
            avg_entropy = sum(attention_entropy_values) / len(attention_entropy_values)
            
            # Optimal entropy around 0.5-0.6
            if avg_entropy < 0.3:
                efficiency = 0.7  # Too focused
            elif avg_entropy > 0.8:
                efficiency = 0.6  # Too diffuse
            else:
                efficiency = 1.0 - abs(avg_entropy - 0.6) / 0.6  # Optimal around 0.6
            
            efficiency_metrics["attention_efficiency"] = efficiency
        
        # Calculate computational utilization
        # This estimates how effectively the model's parameters are being used
        utilization_factors = []
        
        # Factor 1: Sparsity (moderate is good)
        if "overall_sparsity" in efficiency_metrics:
            sparsity = efficiency_metrics["overall_sparsity"]
            
            if sparsity < 0.2:
                utilization_factors.append(0.7)  # Too dense
            elif sparsity > 0.9:
                utilization_factors.append(0.5)  # Too sparse
            else:
                # Optimal sparsity around 0.5-0.7
                utilization_factors.append(1.0 - abs(sparsity - 0.6) / 0.6)
        
        # Factor 2: Layer gradients (if available)
        gradient_norms = []
        
        for layer_id, analysis in layer_analyses.items():
            if "layer_gradient_norm" in analysis.get("metrics", {}):
                gradient_norms.append(analysis["metrics"]["layer_gradient_norm"])
        
        if gradient_norms:
            avg_norm = sum(gradient_norms) / len(gradient_norms)
            
            if avg_norm < 0.01:
                utilization_factors.append(0.6)  # Too small gradients
            elif avg_norm > 0.5:
                utilization_factors.append(0.8)  # Very large gradients
            else:
                utilization_factors.append(1.0 - abs(avg_norm - 0.1) / 0.1)
        
        # Combine utilization factors
        if utilization_factors:
            efficiency_metrics["computational_utilization"] = sum(utilization_factors) / len(utilization_factors)
        else:
            # Default if no factors available
            efficiency_metrics["computational_utilization"] = 0.7
        
        # Calculate information density
        # This estimates how compactly information is represented
        feature_diversity_values = []
        for layer_id, analysis in layer_analyses.items():
            if "feature_diversity" in analysis.get("metrics", {}):
                feature_diversity_values.append(analysis["metrics"]["feature_diversity"])
        
        if feature_diversity_values:
            avg_diversity = sum(feature_diversity_values) / len(feature_diversity_values)
            
            # Higher diversity = higher information density, but not too high
            if avg_diversity < 0.2:
                density = 0.5  # Low diversity = low density
            elif avg_diversity > 0.9:
                density = 0.8  # Very high diversity (might be noise)
            else:
                density = 0.6 + avg_diversity * 0.4  # Scales from 0.6 to 1.0
            
            efficiency_metrics["information_density"] = density
        else:
            # Default if no values available
            efficiency_metrics["information_density"] = 0.7
        
        # Calculate overall efficiency score
        weighted_sum = (
            efficiency_metrics["overall_sparsity"] * 0.25 +
            efficiency_metrics["attention_efficiency"] * 0.25 +
            efficiency_metrics["computational_utilization"] * 0.25 +
            efficiency_metrics["information_density"] * 0.25
        )
        
        efficiency_metrics["overall_score"] = weighted_sum
        
        return efficiency_metrics
    
    def _calculate_metric(self, metric_name: str, layer_data: Dict[str, Any], 
                       layer_type: str, model_info: Dict[str, Any]) -> Optional[float]:
        """
        Calculate a specific metric for a layer.
        
        Args:
            metric_name: Name of the metric to calculate
            layer_data: Layer activations and data
            layer_type: Type of the layer
            model_info: Model information
            
        Returns:
            Calculated metric value or None if can't be calculated
        """
        # Different metrics require different types of data
        # This provides default implementations for metrics that weren't
        # calculated in the type-specific analysis functions
        
        if metric_name == "attention_entropy":
            if layer_type in ["self_attention", "cross_attention"]:
                attention_weights = layer_data.get("attention_weights", 
                                                layer_data.get("attention_probs"))
                if attention_weights is not None:
                    # Ensure it's a list of matrices
                    if isinstance(attention_weights, list) and attention_weights and isinstance(attention_weights[0], list):
                        matrices = attention_weights
                    else:
                        matrices = [attention_weights]
                    
                    # Calculate entropy for each matrix
                    entropies = []
                    for matrix in matrices:
                        entropy = self._calculate_attention_entropy(matrix)
                        entropies.append(entropy)
                    
                    # Return average
                    if entropies:
                        return sum(entropies) / len(entropies)
            
            return None
        
        elif metric_name == "activation_sparsity":
            activations = layer_data.get("activations", 
                                      layer_data.get("output", 
                                                  layer_data.get("ffn_output")))
            
            if activations is not None:
                flat_activations = self._flatten_activations(activations)
                if flat_activations:
                    return self._calculate_activation_sparsity(flat_activations)
            
            return None
        
        elif metric_name == "feature_diversity":
            activations = layer_data.get("activations", 
                                      layer_data.get("output"))
            
            if activations is not None:
                return self._calculate_feature_diversity(activations)
            
            return None
        
        elif metric_name == "token_influence":
            # This would normally require gradient information
            # Simplified implementation for demonstration
            if layer_type in ["self_attention", "cross_attention"]:
                attention_weights = layer_data.get("attention_weights")
                if attention_weights is not None:
                    # Calculate max influence per token
                    if isinstance(attention_weights, list) and attention_weights:
                        if isinstance(attention_weights[0], list):
                            # It's a single attention matrix
                            max_weights = [max(row) if row else 0 for row in attention_weights]
                            if max_weights:
                                return max(max_weights)
                        else:
                            # Try to handle other formats
                            try:
                                return max(attention_weights)
                            except:
                                pass
            
            return 0.5  # Default value
        
        elif metric_name == "layer_gradient_norm":
            # This would normally require gradient information
            # Return a simulated value based on layer position
            return 0.3  # Default value
        
        elif metric_name == "cross_layer_alignment":
            # This would require information from multiple layers
            # Return a simulated value
            return 0.7  # Default value
        
        elif metric_name == "normalization_magnitude":
            if layer_type == "layer_norm":
                variances = layer_data.get("variances", layer_data.get("variance"))
                if variances is not None:
                    if isinstance(variances, list):
                        if variances:
                            # Calculate average normalization scale (1/sqrt(var))
                            scales = [1 / math.sqrt(max(0.001, v)) for v in variances]
                            return sum(scales) / len(scales)
                    else:
                        # Single value
                        return 1 / math.sqrt(max(0.001, variances))
            
            return None
        
        elif metric_name == "attention_alignment":
            # This requires alignment between attention and expected patterns
            # Return a simulated value for demonstration
            return 0.8  # Default value
        
        # Return None for unknown metrics
        return None
    
    def _compute_activation_distribution(self, layer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute activation distribution histograms.
        
        Args:
            layer_data: Layer activations and data
            
        Returns:
            Dictionary with activation distribution information
        """
        # Extract activations
        activations = layer_data.get("activations", 
                                  layer_data.get("output"))
        
        if activations is None:
            return {
                "error": "No activations found",
                "histogram": []
            }
        
        # Flatten activations
        flat_activations = self._flatten_activations(activations)
        if not flat_activations:
            return {
                "error": "Failed to flatten activations",
                "histogram": []
            }
        
        # Compute histogram with 10 bins
        min_val = min(flat_activations)
        max_val = max(flat_activations)
        
        if min_val == max_val:
            # Handle constant activations
            return {
                "min": min_val,
                "max": max_val,
                "histogram": [(min_val, len(flat_activations))]
            }
        
        bin_width = (max_val - min_val) / 10
        bins = [min_val + i * bin_width for i in range(11)]
        
        histogram = [0] * 10
        for val in flat_activations:
            bin_idx = min(9, max(0, int((val - min_val) / bin_width)))
            histogram[bin_idx] += 1
        
        # Normalize histogram
        if flat_activations:
            normalized_histogram = [count / len(flat_activations) for count in histogram]
        else:
            normalized_histogram = histogram
        
        # Create result
        result = {
            "min": min_val,
            "max": max_val,
            "bins": bins,
            "counts": histogram,
            "normalized": normalized_histogram
        }
        
        return result
    
    def _analyze_token_representations(self, layer_data: Dict[str, Any], 
                                     inputs: Dict[str, Any],
                                     max_tokens: int) -> List[Dict[str, Any]]:
        """
        Analyze how individual tokens are represented in this layer.
        
        Args:
            layer_data: Layer activations and data
            inputs: Input data being processed
            max_tokens: Maximum number of tokens to analyze
            
        Returns:
            List of token representation analyses
        """
        # Extract token information
        input_tokens = inputs.get("tokens", inputs.get("input_ids", []))
        if not input_tokens:
            return []
        
        # Extract token representations
        token_features = layer_data.get("token_representations", 
                                     layer_data.get("hidden_states"))
        
        if token_features is None:
            return []
        
        # Ensure token_features is a list of vectors
        if not isinstance(token_features, list):
            # Try to convert to list
            try:
                token_features = token_features.tolist()
            except:
                return []
        
        # Limit number of tokens
        num_tokens = min(len(input_tokens), len(token_features), max_tokens)
        
        # Analyze each token
        token_analyses = []
        
        for i in range(num_tokens):
            token = input_tokens[i]
            features = token_features[i]
            
            # Extract token identifier
            token_id = token
            if isinstance(token, dict) and "id" in token:
                token_id = token["id"]
            
            # Calculate feature statistics
            if isinstance(features, list):
                # Calculate norm
                norm = math.sqrt(sum(f * f for f in features))
                
                # Calculate sparsity
                sparsity = sum(1 for f in features if abs(f) < 0.01) / len(features) if features else 0
                
                token_analyses.append({
                    "token_idx": i,
                    "token_id": token_id,
                    "feature_norm": norm,
                    "feature_sparsity": sparsity,
                    "feature_count": len(features)
                })
        
        return token_analyses
    
    def _detect_abnormalities(self, layer_id: str, layer_type: str, 
                           layer_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect abnormalities in layer behavior.
        
        Args:
            layer_id: ID of the layer
            layer_type: Type of the layer
            layer_analysis: Analysis of the layer
            
        Returns:
            List of detected abnormalities
        """
        abnormalities = []
        
        # Extract metrics
        metrics = layer_analysis.get("metrics", {})
        
        # Check each abnormality signature
        for abnormality_name, signature in self.abnormality_signatures.items():
            indicators = signature.get("indicators", {})
            matches = True
            
            for indicator_name, indicator_value in indicators.items():
                if indicator_name in metrics:
                    metric_value = metrics[indicator_name]
                    
                    # Check if value matches the indicator
                    if isinstance(indicator_value, str):
                        if indicator_value.startswith("<"):
                            # Less than
                            threshold = float(indicator_value[1:])
                            if metric_value >= threshold:
                                matches = False
                                break
                        elif indicator_value.startswith(">"):
                            # Greater than
                            threshold = float(indicator_value[1:])
                            if metric_value <= threshold:
                                matches = False
                                break
                        elif "for" in indicator_value:
                            # Complex condition like ">0.5 for <3 tokens"
                            # Skip these for simplicity in this implementation
                            matches = False
                            break
                    elif isinstance(indicator_value, (int, float)):
                        # Exact match
                        if metric_value != indicator_value:
                            matches = False
                            break
                else:
                    # Metric not available
                    matches = False
                    break
            
            # Check pattern-specific conditions
            if matches and abnormality_name == "attention_fragmentation":
                # Need to check attention patterns
                if "patterns" not in layer_analysis or not layer_analysis["patterns"]:
                    matches = False
            
            # If all indicators match, report abnormality
            if matches:
                abnormality = {
                    "type": abnormality_name,
                    "layer_id": layer_id,
                    "layer_type": layer_type,
                    "description": signature.get("description", ""),
                    "severity": signature.get("severity", "medium"),
                    "potential_causes": signature.get("potential_causes", []),
                    "matching_metrics": {
                        name: metrics[name] for name in indicators if name in metrics
                    }
                }
                
                abnormalities.append(abnormality)
        
        return abnormalities


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Transformer Layer Monitor (KA-55) on the provided data.
    
    Args:
        data: A dictionary containing model state, layer activations, and inputs
        
    Returns:
        Dictionary with monitoring results
    """
    model_state = data.get("model_state", {})
    layer_activations = data.get("layer_activations", {})
    inputs = data.get("inputs", {})
    config = data.get("config", None)
    
    # Generate sample data if requested
    if not model_state and not layer_activations and data.get("generate_sample", False):
        model_state, layer_activations, inputs = generate_sample_data(
            data.get("model_type", "encoder_decoder"),
            data.get("size", "medium")
        )
    
    # Validate inputs
    if not model_state or not layer_activations:
        return {
            "algorithm": "KA-55",
            "success": False,
            "error": "Missing model state or layer activations",
            "timestamp": time.time()
        }
    
    monitor = TransformerLayerMonitor()
    
    try:
        result = monitor.monitor_transformer_layers(
            model_state, layer_activations, inputs, config
        )
        
        if not result.get("success", False):
            return {
                "algorithm": "KA-55",
                "success": False,
                "error": result.get("error", "Unknown error"),
                "timestamp": time.time()
            }
        
        # Prepare output
        output = {
            "algorithm": "KA-55",
            "success": True,
            "model_info": result["results"]["model_info"],
            "layers_analyzed": result["results"]["layers_analyzed"],
            "cross_layer_analysis": result["results"]["cross_layer_analysis"],
            "efficiency_metrics": result["results"]["efficiency_metrics"],
            "abnormalities_detected": result["results"]["abnormalities_detected"],
            "abnormalities": result["results"]["abnormalities"],
            "timestamp": time.time()
        }
        
        # Include layer analyses if not too large
        if len(result["results"]["layers_analyzed"]) <= 20:
            output["layer_analyses"] = result["results"]["layer_analyses"]
        else:
            output["message"] = "Layer analyses too large to include in response, access specific layers if needed."
        
        return output
    
    except Exception as e:
        logger.error(f"Error in KA-55 Transformer Layer Monitor: {str(e)}")
        return {
            "algorithm": "KA-55",
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }


def generate_sample_data(model_type: str, size: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Generate sample data for testing.
    
    Args:
        model_type: Type of model to simulate (encoder, decoder, encoder_decoder)
        size: Size of the model (small, medium, large)
        
    Returns:
        Tuple of (model_state, layer_activations, inputs)
    """
    # Set dimensions based on size
    if size == "small":
        hidden_size = 256
        num_layers = 4
        num_heads = 4
    elif size == "medium":
        hidden_size = 512
        num_layers = 8
        num_heads = 8
    else:  # large
        hidden_size = 768
        num_layers = 12
        num_heads = 12
    
    # Create model state
    model_state = {
        "name": f"sample_{model_type}_{size}",
        "config": {
            "hidden_size": hidden_size,
            "num_hidden_layers": num_layers,
            "num_attention_heads": num_heads,
            "vocab_size": 30000
        },
        "parameters": {}
    }
    
    # Generate sample activations
    layer_activations = {}
    
    # Sample tokens
    tokens = [f"token_{i}" for i in range(10)]
    
    # Create inputs
    inputs = {
        "tokens": tokens,
        "input_ids": list(range(10)),
        "attention_mask": [1] * 10
    }
    
    # Generate activations for each layer
    if model_type in ["encoder", "encoder_decoder"]:
        # Encoder layers
        for layer_idx in range(num_layers):
            # Self-attention layer
            attention_layer_id = f"encoder.layer{layer_idx}.attention"
            
            # Generate attention weights
            attention_weights = []
            for head_idx in range(num_heads):
                # Create attention matrix with some pattern
                matrix = []
                for i in range(10):
                    row = []
                    for j in range(10):
                        # Create different patterns for different heads
                        if head_idx % 4 == 0:
                            # Diagonal pattern
                            weight = 0.1 + 0.8 * (1.0 / (1.0 + abs(i - j)))
                        elif head_idx % 4 == 1:
                            # Global attention to first token
                            weight = 0.7 if j == 0 else 0.3 / 9
                        elif head_idx % 4 == 2:
                            # Local window
                            weight = 0.2 + 0.7 * (1.0 if abs(i - j) <= 2 else 0.0)
                        else:
                            # Random but consistent
                            seed = i * 10 + j + head_idx * 100
                            random.seed(seed)
                            weight = 0.1 + 0.8 * random.random()
                        
                        row.append(weight)
                    
                    # Normalize
                    total = sum(row)
                    if total > 0:
                        row = [w / total for w in row]
                    
                    matrix.append(row)
                
                attention_weights.append(matrix)
            
            # Create activations
            token_representations = []
            for i in range(10):
                # Create vector
                features = []
                for j in range(hidden_size):
                    # Create some pattern in the features
                    seed = i * hidden_size + j + layer_idx * 1000
                    random.seed(seed)
                    feature = random.uniform(-1, 1)
                    features.append(feature)
                
                token_representations.append(features)
            
            layer_activations[attention_layer_id] = {
                "attention_weights": attention_weights,
                "token_representations": token_representations
            }
            
            # Feed-forward layer
            ffn_layer_id = f"encoder.layer{layer_idx}.ffn"
            
            # Create intermediate activations (after first linear + activation)
            intermediate_activations = []
            for i in range(10):
                features = []
                for j in range(hidden_size * 4):  # Typically 4x hidden size
                    seed = i * (hidden_size * 4) + j + layer_idx * 2000
                    random.seed(seed)
                    
                    # Create sparse activations (many zeros due to ReLU)
                    feature = random.uniform(-0.5, 1)
                    if feature < 0:
                        feature = 0  # ReLU
                    
                    features.append(feature)
                
                intermediate_activations.append(features)
            
            # Output activations (same shape as input)
            output_activations = []
            for i in range(10):
                features = []
                for j in range(hidden_size):
                    seed = i * hidden_size + j + layer_idx * 3000
                    random.seed(seed)
                    feature = random.uniform(-1, 1)
                    features.append(feature)
                
                output_activations.append(features)
            
            layer_activations[ffn_layer_id] = {
                "intermediate_activations": intermediate_activations,
                "activations": output_activations
            }
            
            # Layer norm
            norm_layer_id = f"encoder.layer{layer_idx}.norm"
            
            # Create normalized features
            normalized_features = []
            for i in range(10):
                features = []
                for j in range(hidden_size):
                    seed = i * hidden_size + j + layer_idx * 4000
                    random.seed(seed)
                    
                    # Normalized features have mean 0, variance 1
                    feature = random.normalvariate(0, 1)
                    features.append(feature)
                
                normalized_features.append(features)
            
            layer_activations[norm_layer_id] = {
                "normalized_features": normalized_features,
                "means": [0] * 10,
                "variances": [1] * 10
            }
    
    if model_type in ["decoder", "encoder_decoder"]:
        # Decoder layers
        for layer_idx in range(num_layers):
            # Self-attention layer
            attention_layer_id = f"decoder.layer{layer_idx}.self_attention"
            
            # Generate attention weights with causal mask
            attention_weights = []
            for head_idx in range(num_heads):
                # Create attention matrix with causal mask
                matrix = []
                for i in range(10):
                    row = []
                    for j in range(10):
                        # Causal mask - can only attend to previous positions
                        if j > i:
                            weight = 0.0
                        else:
                            # Create different patterns for different heads
                            if head_idx % 4 == 0:
                                # Focus on current position
                                weight = 0.7 if j == i else 0.3 / i if i > 0 else 0.0
                            elif head_idx % 4 == 1:
                                # Focus on first position
                                weight = 0.6 if j == 0 else 0.4 / max(1, i)
                            elif head_idx % 4 == 2:
                                # Local window
                                weight = 0.2 + 0.7 * (1.0 if abs(i - j) <= 2 and j <= i else 0.0)
                            else:
                                # Random but consistent
                                seed = i * 10 + j + head_idx * 100 + 5000
                                random.seed(seed)
                                weight = (0.1 + 0.8 * random.random()) if j <= i else 0.0
                        
                        row.append(weight)
                    
                    # Normalize
                    total = sum(row)
                    if total > 0:
                        row = [w / total for w in row]
                    
                    matrix.append(row)
                
                attention_weights.append(matrix)
            
            layer_activations[attention_layer_id] = {
                "attention_weights": attention_weights
            }
            
            # Cross-attention layer (if encoder-decoder)
            if model_type == "encoder_decoder":
                cross_attn_layer_id = f"decoder.layer{layer_idx}.cross_attention"
                
                # Generate cross-attention weights
                cross_attn_weights = []
                for head_idx in range(num_heads):
                    # Create attention matrix from decoder to encoder
                    matrix = []
                    for i in range(10):  # Decoder positions
                        row = []
                        for j in range(10):  # Encoder positions
                            # Create different patterns for different heads
                            if head_idx % 4 == 0:
                                # Aligned attention (attend to same position)
                                weight = 0.1 + 0.8 * (1.0 / (1.0 + abs(i - j)))
                            elif head_idx % 4 == 1:
                                # Focus on key positions
                                weight = 0.7 if j < 3 else 0.3 / 7
                            elif head_idx % 4 == 2:
                                # Local window around aligned position
                                weight = 0.2 + 0.7 * (1.0 if abs(i - j) <= 2 else 0.0)
                            else:
                                # Random but consistent
                                seed = i * 10 + j + head_idx * 100 + 10000
                                random.seed(seed)
                                weight = 0.1 + 0.8 * random.random()
                            
                            row.append(weight)
                        
                        # Normalize
                        total = sum(row)
                        if total > 0:
                            row = [w / total for w in row]
                        
                        matrix.append(row)
                    
                    cross_attn_weights.append(matrix)
                
                layer_activations[cross_attn_layer_id] = {
                    "attention_weights": cross_attn_weights
                }
            
            # Rest of decoder layer components (similar to encoder)
            ffn_layer_id = f"decoder.layer{layer_idx}.ffn"
            norm_layer_id = f"decoder.layer{layer_idx}.norm"
            
            # Create similar activations as encoder layers
            # (code omitted for brevity - would be similar to encoder layers)
    
    # Add embedding layer
    embedding_layer_id = "embeddings"
    
    # Create token embeddings
    token_embeddings = []
    for i in range(10):
        features = []
        for j in range(hidden_size):
            seed = i * hidden_size + j
            random.seed(seed)
            feature = random.uniform(-1, 1)
            features.append(feature)
        
        token_embeddings.append(features)
    
    layer_activations[embedding_layer_id] = {
        "embeddings": token_embeddings
    }
    
    # Add pooling layer (if needed)
    pooling_layer_id = "pooler"
    
    # Create pooled output
    pooled_output = []
    for j in range(hidden_size):
        seed = j
        random.seed(seed)
        feature = random.uniform(-1, 1)
        pooled_output.append(feature)
    
    layer_activations[pooling_layer_id] = {
        "pooled_output": pooled_output,
        "sequence_output": token_embeddings  # Reuse token embeddings for sequence output
    }
    
    return model_state, layer_activations, inputs