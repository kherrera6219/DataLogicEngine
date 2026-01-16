"""
KA-43: Confidence Heatmap Visualizer

This algorithm visualizes confidence levels across multiple simulation passes,
generating heatmap data to display confidence evolution and decision boundaries.
"""

import logging
from typing import Dict, List, Any, Optional
import time

logger = logging.getLogger(__name__)

class ConfidenceHeatmapVisualizer:
    """
    KA-43: Visualizes confidence levels as heatmap data.
    
    This algorithm processes confidence measurements across multiple passes or dimensions,
    creating visualization-ready heatmap data to track confidence evolution.
    """
    
    def __init__(self):
        """Initialize the Confidence Heatmap Visualizer."""
        self.visualization_formats = self._initialize_visualization_formats()
        logger.info("KA-43: Confidence Heatmap Visualizer initialized")
    
    def _initialize_visualization_formats(self) -> Dict[str, Dict[str, Any]]:
        """Initialize supported visualization formats."""
        return {
            "percentage": {
                "description": "Format confidence as percentage strings",
                "formatter": lambda c: f"{int(c*100)}%",
                "value_type": "string"
            },
            "decimal": {
                "description": "Format confidence as decimal values",
                "formatter": lambda c: round(c, 2),
                "value_type": "number"
            },
            "color_code": {
                "description": "Format confidence as CSS-compatible color codes",
                "formatter": lambda c: self._confidence_to_color(c),
                "value_type": "string"
            },
            "stars": {
                "description": "Format confidence as star ratings",
                "formatter": lambda c: "★" * int(round(c * 5)),
                "value_type": "string"
            },
            "emoji": {
                "description": "Format confidence as emoji indicators",
                "formatter": lambda c: self._confidence_to_emoji(c),
                "value_type": "string"
            }
        }
    
    def _confidence_to_color(self, confidence: float) -> str:
        """
        Convert confidence to color code.
        
        Args:
            confidence: Confidence value (0-1)
            
        Returns:
            CSS-compatible color code
        """
        # Red (low confidence) to green (high confidence) gradient
        r = int(255 * (1 - confidence))
        g = int(255 * confidence)
        b = 0
        
        return f"rgb({r},{g},{b})"
    
    def _confidence_to_emoji(self, confidence: float) -> str:
        """
        Convert confidence to emoji indicator.
        
        Args:
            confidence: Confidence value (0-1)
            
        Returns:
            Emoji representation
        """
        if confidence >= 0.9:
            return "🟢"  # Very high confidence
        elif confidence >= 0.7:
            return "🟩"  # High confidence
        elif confidence >= 0.5:
            return "🟨"  # Medium confidence
        elif confidence >= 0.3:
            return "🟧"  # Low confidence
        else:
            return "🟥"  # Very low confidence
    
    def generate_heatmap(self, confidence_levels: List[float],
                        dimension_labels: Optional[List[str]] = None,
                        format_type: str = "percentage",
                        include_gradient: bool = True) -> Dict[str, Any]:
        """
        Generate heatmap visualization data from confidence levels.
        
        Args:
            confidence_levels: List of confidence values (0-1)
            dimension_labels: Optional labels for dimensions
            format_type: Visualization format type
            include_gradient: Whether to include color gradient data
            
        Returns:
            Dictionary with heatmap visualization data
        """
        # Validate inputs
        if not confidence_levels:
            return {
                "error": "No confidence levels provided",
                "success": False
            }
        
        # Normalize confidence values
        normalized_levels = [max(0.0, min(1.0, level)) for level in confidence_levels]
        
        # Get formatter for selected format
        if format_type not in self.visualization_formats:
            format_type = "percentage"  # Default to percentage
        
        formatter = self.visualization_formats[format_type]["formatter"]
        
        # Generate dimension labels if not provided
        if dimension_labels is None or len(dimension_labels) != len(normalized_levels):
            dimension_labels = [f"pass_{i+1}" for i in range(len(normalized_levels))]
        
        # Generate formatted values
        formatted_values = [formatter(level) for level in normalized_levels]
        
        # Create heatmap entries
        heatmap_entries = {}
        for label, value, raw_value in zip(dimension_labels, formatted_values, normalized_levels):
            heatmap_entries[label] = {
                "formatted": value,
                "raw": raw_value
            }
        
        # Generate gradient data if requested
        gradient_data = None
        if include_gradient:
            gradient_data = self._generate_gradient_data(normalized_levels)
        
        # Calculate summary statistics
        summary = self._calculate_summary_statistics(normalized_levels)
        
        # Prepare heatmap data
        heatmap_data = {
            "entries": heatmap_entries,
            "format": format_type,
            "format_info": self.visualization_formats[format_type],
            "dimension_count": len(normalized_levels),
            "dimension_labels": dimension_labels,
            "gradient": gradient_data,
            "summary": summary
        }
        
        return heatmap_data
    
    def _generate_gradient_data(self, confidence_levels: List[float]) -> Dict[str, Any]:
        """
        Generate gradient visualization data.
        
        Args:
            confidence_levels: List of confidence values
            
        Returns:
            Dictionary with gradient data
        """
        # Calculate color codes for each level
        color_codes = [self._confidence_to_color(level) for level in confidence_levels]
        
        # Generate CSS gradient
        if len(confidence_levels) <= 1:
            css_gradient = f"linear-gradient(to right, {color_codes[0]}, {color_codes[0]})"
        else:
            stops = [f"{color_codes[i]} {int(100 * i / (len(color_codes) - 1))}%" for i in range(len(color_codes))]
            css_gradient = f"linear-gradient(to right, {', '.join(stops)})"
        
        # Generate 5-point scale
        scale_points = [0.0, 0.25, 0.5, 0.75, 1.0]
        scale_colors = [self._confidence_to_color(level) for level in scale_points]
        scale_labels = ["Very Low", "Low", "Medium", "High", "Very High"]
        
        scale = [
            {"value": point, "color": color, "label": label}
            for point, color, label in zip(scale_points, scale_colors, scale_labels)
        ]
        
        # Prepare gradient data
        gradient_data = {
            "colors": color_codes,
            "css_gradient": css_gradient,
            "scale": scale
        }
        
        return gradient_data
    
    def _calculate_summary_statistics(self, confidence_levels: List[float]) -> Dict[str, Any]:
        """
        Calculate summary statistics for confidence levels.
        
        Args:
            confidence_levels: List of confidence values
            
        Returns:
            Dictionary with summary statistics
        """
        if not confidence_levels:
            return {
                "average": 0.0,
                "min": 0.0,
                "max": 0.0,
                "trend": "none"
            }
        
        # Calculate basic statistics
        avg_confidence = sum(confidence_levels) / len(confidence_levels)
        min_confidence = min(confidence_levels)
        max_confidence = max(confidence_levels)
        
        # Determine trend
        if len(confidence_levels) < 2:
            trend = "stable"
        else:
            first_half = confidence_levels[:len(confidence_levels)//2]
            second_half = confidence_levels[len(confidence_levels)//2:]
            
            first_half_avg = sum(first_half) / len(first_half)
            second_half_avg = sum(second_half) / len(second_half)
            
            if second_half_avg > first_half_avg * 1.1:
                trend = "increasing"
            elif second_half_avg < first_half_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        
        # Calculate volatility
        if len(confidence_levels) < 2:
            volatility = 0.0
        else:
            differences = [abs(confidence_levels[i] - confidence_levels[i-1]) for i in range(1, len(confidence_levels))]
            volatility = sum(differences) / (len(differences))
        
        # Prepare summary
        summary = {
            "average": round(avg_confidence, 3),
            "min": round(min_confidence, 3),
            "max": round(max_confidence, 3),
            "range": round(max_confidence - min_confidence, 3),
            "trend": trend,
            "volatility": round(volatility, 3),
            "final": round(confidence_levels[-1], 3),
            "initial": round(confidence_levels[0], 3),
            "change": round(confidence_levels[-1] - confidence_levels[0], 3) if len(confidence_levels) > 1 else 0.0
        }
        
        return summary
    
    def generate_2d_heatmap(self, confidence_matrix: List[List[float]],
                          row_labels: Optional[List[str]] = None,
                          column_labels: Optional[List[str]] = None,
                          format_type: str = "percentage") -> Dict[str, Any]:
        """
        Generate 2D heatmap visualization data from confidence matrix.
        
        Args:
            confidence_matrix: 2D list of confidence values
            row_labels: Optional labels for rows
            column_labels: Optional labels for columns
            format_type: Visualization format type
            
        Returns:
            Dictionary with 2D heatmap visualization data
        """
        # Validate inputs
        if not confidence_matrix or not all(isinstance(row, list) for row in confidence_matrix):
            return {
                "error": "Invalid confidence matrix provided",
                "success": False
            }
        
        # Ensure all rows have same length
        row_lengths = [len(row) for row in confidence_matrix]
        if len(set(row_lengths)) > 1:
            return {
                "error": "All rows in confidence matrix must have same length",
                "success": False
            }
        
        # Get row and column counts
        row_count = len(confidence_matrix)
        col_count = row_lengths[0] if row_count > 0 else 0
        
        # Generate labels if not provided
        if row_labels is None or len(row_labels) != row_count:
            row_labels = [f"row_{i+1}" for i in range(row_count)]
        
        if column_labels is None or len(column_labels) != col_count:
            column_labels = [f"col_{i+1}" for i in range(col_count)]
        
        # Get formatter for selected format
        if format_type not in self.visualization_formats:
            format_type = "percentage"  # Default to percentage
        
        formatter = self.visualization_formats[format_type]["formatter"]
        
        # Generate 2D heatmap data
        heatmap_data = []
        all_confidence_values = []
        
        for i, row in enumerate(confidence_matrix):
            row_data = []
            
            for j, value in enumerate(row):
                # Normalize confidence value
                normalized = max(0.0, min(1.0, value))
                all_confidence_values.append(normalized)
                
                # Format value
                formatted = formatter(normalized)
                
                # Create cell data
                cell = {
                    "row": i,
                    "col": j,
                    "row_label": row_labels[i],
                    "col_label": column_labels[j],
                    "raw": normalized,
                    "formatted": formatted,
                    "color": self._confidence_to_color(normalized)
                }
                
                row_data.append(cell)
            
            heatmap_data.append(row_data)
        
        # Calculate summary statistics
        summary = self._calculate_summary_statistics(all_confidence_values)
        
        # Prepare result
        result = {
            "heatmap": heatmap_data,
            "format": format_type,
            "format_info": self.visualization_formats[format_type],
            "row_count": row_count,
            "col_count": col_count,
            "row_labels": row_labels,
            "col_labels": column_labels,
            "summary": summary
        }
        
        return result


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Confidence Heatmap Visualizer (KA-43) on the provided data.
    
    Args:
        data: A dictionary containing confidence levels to visualize
        
    Returns:
        Dictionary with heatmap visualization data
    """
    confidence_levels = data.get("confidence_levels", [])
    dimension_labels = data.get("dimension_labels")
    format_type = data.get("format", "percentage")
    include_gradient = data.get("include_gradient", True)
    
    # Check if 2D heatmap is requested
    confidence_matrix = data.get("confidence_matrix")
    if confidence_matrix is not None:
        row_labels = data.get("row_labels")
        column_labels = data.get("column_labels")
        
        visualizer = ConfidenceHeatmapVisualizer()
        result = visualizer.generate_2d_heatmap(
            confidence_matrix, 
            row_labels, 
            column_labels, 
            format_type
        )
        
        if "error" in result:
            return {
                "algorithm": "KA-43",
                "error": result["error"],
                "success": False
            }
        
        return {
            "algorithm": "KA-43",
            "heatmap_type": "2d",
            "heatmap_data": result,
            "timestamp": time.time(),
            "success": True
        }
    
    # Process 1D heatmap
    visualizer = ConfidenceHeatmapVisualizer()
    result = visualizer.generate_heatmap(
        confidence_levels, 
        dimension_labels, 
        format_type, 
        include_gradient
    )
    
    if "error" in result:
        return {
            "algorithm": "KA-43",
            "error": result["error"],
            "success": False
        }
    
    # Extract simplified heatmap for response
    heatmap = {label: entry["formatted"] for label, entry in result["entries"].items()}
    
    return {
        "algorithm": "KA-43",
        "heatmap": heatmap,
        "heatmap_data": result,
        "timestamp": time.time(),
        "success": True
    }