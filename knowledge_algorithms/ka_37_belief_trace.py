"""
KA-37: Belief Trace Exporter

This algorithm tracks and exports the reasoning path and belief development process,
providing transparency into how conclusions and decisions are formed.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import time
import json

logger = logging.getLogger(__name__)

class BeliefTraceExporter:
    """
    KA-37: Exports reasoning paths and belief development traces.
    
    This algorithm records and formats the evolution of beliefs and reasoning
    chains, enabling transparency and analysis of the decision-making process.
    """
    
    def __init__(self):
        """Initialize the Belief Trace Exporter."""
        self.trace_formats = self._initialize_trace_formats()
        self.trace_annotations = self._initialize_trace_annotations()
        logger.info("KA-37: Belief Trace Exporter initialized")
    
    def _initialize_trace_formats(self) -> Dict[str, Dict[str, Any]]:
        """Initialize supported trace export formats."""
        return {
            "text": {
                "description": "Plain text format with structured sections",
                "extension": "txt",
                "content_type": "text/plain",
                "hierarchical": False
            },
            "json": {
                "description": "Structured JSON format with metadata",
                "extension": "json",
                "content_type": "application/json",
                "hierarchical": True
            },
            "markdown": {
                "description": "Markdown format with headings and sections",
                "extension": "md",
                "content_type": "text/markdown",
                "hierarchical": True
            },
            "html": {
                "description": "HTML format with interactive elements",
                "extension": "html",
                "content_type": "text/html",
                "hierarchical": True
            },
            "graph": {
                "description": "Node-edge graph representation",
                "extension": "json",
                "content_type": "application/json",
                "hierarchical": True
            }
        }
    
    def _initialize_trace_annotations(self) -> Dict[str, Dict[str, Any]]:
        """Initialize annotation types for belief traces."""
        return {
            "confidence": {
                "description": "Confidence level in a belief or reasoning step",
                "value_type": "numeric",
                "range": [0.0, 1.0],
                "visualization": "color_gradient"
            },
            "source": {
                "description": "Source of information supporting a belief",
                "value_type": "string",
                "examples": ["inference", "memory", "external_reference"],
                "visualization": "icon"
            },
            "epistemic_status": {
                "description": "Knowledge certainty classification",
                "value_type": "enum",
                "values": ["fact", "inference", "assumption", "hypothesis", "unknown"],
                "visualization": "badge"
            },
            "reasoning_type": {
                "description": "Type of reasoning applied",
                "value_type": "enum",
                "values": ["deductive", "inductive", "abductive", "analogical", "counterfactual"],
                "visualization": "style"
            },
            "dependency": {
                "description": "Dependencies between beliefs or reasoning steps",
                "value_type": "reference",
                "visualization": "arrow"
            }
        }
    
    def export_trace(self, reasoning_path: List[Dict[str, Any]], 
                   format_type: str = "text",
                   include_metadata: bool = True,
                   annotate: bool = True) -> Dict[str, Any]:
        """
        Export reasoning path as a structured belief trace.
        
        Args:
            reasoning_path: List of reasoning steps with metadata
            format_type: Export format type
            include_metadata: Whether to include metadata in export
            annotate: Whether to include annotations
            
        Returns:
            Dictionary with exported trace
        """
        # Validate reasoning path
        if not reasoning_path:
            return {
                "error": "Empty reasoning path provided",
                "success": False
            }
        
        # Validate format type
        if format_type not in self.trace_formats:
            format_type = "text"  # Default to text if invalid format
        
        # Get format information
        format_info = self.trace_formats[format_type]
        
        # Prepare for export
        trace_content = self._format_trace(reasoning_path, format_type, include_metadata, annotate)
        
        # Generate export metadata
        export_metadata = {
            "timestamp": time.time(),
            "format": format_type,
            "steps_count": len(reasoning_path),
            "content_type": format_info["content_type"],
            "annotations_included": annotate,
            "metadata_included": include_metadata
        }
        
        # Prepare final export
        export_result = {
            "trace_content": trace_content,
            "metadata": export_metadata if include_metadata else None,
            "format": format_type,
            "success": True
        }
        
        return export_result
    
    def _format_trace(self, reasoning_path: List[Dict[str, Any]], 
                    format_type: str,
                    include_metadata: bool,
                    annotate: bool) -> str:
        """
        Format reasoning path according to specified format.
        
        Args:
            reasoning_path: List of reasoning steps
            format_type: Export format type
            include_metadata: Whether to include metadata
            annotate: Whether to include annotations
            
        Returns:
            Formatted trace content
        """
        # Call appropriate formatter based on format type
        if format_type == "text":
            return self._format_as_text(reasoning_path, include_metadata, annotate)
        elif format_type == "json":
            return self._format_as_json(reasoning_path, include_metadata, annotate)
        elif format_type == "markdown":
            return self._format_as_markdown(reasoning_path, include_metadata, annotate)
        elif format_type == "html":
            return self._format_as_html(reasoning_path, include_metadata, annotate)
        elif format_type == "graph":
            return self._format_as_graph(reasoning_path, include_metadata, annotate)
        else:
            # Default to text
            return self._format_as_text(reasoning_path, include_metadata, annotate)
    
    def _format_as_text(self, reasoning_path: List[Dict[str, Any]], 
                      include_metadata: bool,
                      annotate: bool) -> str:
        """Format reasoning path as plain text."""
        lines = ["BELIEF TRACE EXPORT", "=================", ""]
        
        # Add metadata header if requested
        if include_metadata:
            lines.extend([
                "METADATA:",
                f"Timestamp: {time.time()}",
                f"Steps: {len(reasoning_path)}",
                f"Annotations: {'Included' if annotate else 'Excluded'}",
                ""
            ])
        
        # Add each reasoning step
        for i, step in enumerate(reasoning_path):
            step_num = i + 1
            step_text = step.get("text", "")
            step_type = step.get("type", "reasoning_step")
            
            # Format step header
            lines.append(f"STEP {step_num}: {step_type.upper()}")
            lines.append("-" * (len(f"STEP {step_num}: {step_type.upper()}")))
            lines.append(step_text)
            
            # Add annotations if requested
            if annotate:
                lines.append("")
                lines.append("Annotations:")
                
                # Add confidence if available
                if "confidence" in step:
                    lines.append(f"  Confidence: {step['confidence']:.2f}")
                
                # Add source if available
                if "source" in step:
                    lines.append(f"  Source: {step['source']}")
                
                # Add epistemic status if available
                if "epistemic_status" in step:
                    lines.append(f"  Epistemic Status: {step['epistemic_status']}")
                
                # Add reasoning type if available
                if "reasoning_type" in step:
                    lines.append(f"  Reasoning Type: {step['reasoning_type']}")
                
                # Add dependencies if available
                if "dependencies" in step and step["dependencies"]:
                    deps = ", ".join([str(d) for d in step["dependencies"]])
                    lines.append(f"  Dependencies: {deps}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_as_json(self, reasoning_path: List[Dict[str, Any]], 
                      include_metadata: bool,
                      annotate: bool) -> str:
        """Format reasoning path as JSON."""
        # Create structured JSON object
        export_data = {
            "belief_trace": []
        }
        
        # Add metadata if requested
        if include_metadata:
            export_data["metadata"] = {
                "timestamp": time.time(),
                "steps_count": len(reasoning_path),
                "annotations_included": annotate
            }
        
        # Process each reasoning step
        for i, step in enumerate(reasoning_path):
            step_data = {
                "step_number": i + 1,
                "text": step.get("text", ""),
                "type": step.get("type", "reasoning_step")
            }
            
            # Add annotations if requested
            if annotate:
                annotations = {}
                
                # Include relevant annotations if available
                for annotation_type in ["confidence", "source", "epistemic_status", "reasoning_type", "dependencies"]:
                    if annotation_type in step:
                        annotations[annotation_type] = step[annotation_type]
                
                if annotations:
                    step_data["annotations"] = annotations
            
            export_data["belief_trace"].append(step_data)
        
        # Convert to formatted JSON string
        return json.dumps(export_data, indent=2)
    
    def _format_as_markdown(self, reasoning_path: List[Dict[str, Any]], 
                         include_metadata: bool,
                         annotate: bool) -> str:
        """Format reasoning path as Markdown."""
        lines = ["# Belief Trace Export", ""]
        
        # Add metadata if requested
        if include_metadata:
            lines.extend([
                "## Metadata",
                "",
                f"- **Timestamp:** {time.time()}",
                f"- **Steps:** {len(reasoning_path)}",
                f"- **Annotations:** {'Included' if annotate else 'Excluded'}",
                ""
            ])
        
        # Add each reasoning step
        for i, step in enumerate(reasoning_path):
            step_num = i + 1
            step_text = step.get("text", "")
            step_type = step.get("type", "reasoning_step")
            
            # Format step header
            lines.append(f"## Step {step_num}: {step_type.title()}")
            lines.append("")
            lines.append(step_text)
            lines.append("")
            
            # Add annotations if requested
            if annotate:
                lines.append("### Annotations")
                lines.append("")
                
                # Add confidence if available
                if "confidence" in step:
                    confidence = step["confidence"]
                    confidence_stars = "★" * int(confidence * 5)
                    lines.append(f"- **Confidence:** {confidence:.2f} {confidence_stars}")
                
                # Add source if available
                if "source" in step:
                    lines.append(f"- **Source:** {step['source']}")
                
                # Add epistemic status if available
                if "epistemic_status" in step:
                    lines.append(f"- **Epistemic Status:** `{step['epistemic_status']}`")
                
                # Add reasoning type if available
                if "reasoning_type" in step:
                    lines.append(f"- **Reasoning Type:** _{step['reasoning_type']}_")
                
                # Add dependencies if available
                if "dependencies" in step and step["dependencies"]:
                    deps = ", ".join([f"Step {d}" for d in step["dependencies"]])
                    lines.append(f"- **Dependencies:** {deps}")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def _format_as_html(self, reasoning_path: List[Dict[str, Any]], 
                      include_metadata: bool,
                      annotate: bool) -> str:
        """Format reasoning path as HTML."""
        lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "  <title>Belief Trace Export</title>",
            "  <style>",
            "    body { font-family: Arial, sans-serif; margin: 20px; }",
            "    .metadata { background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; }",
            "    .step { margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }",
            "    .step-header { background-color: #f1f1f1; padding: 8px; margin: -15px -15px 15px -15px; border-radius: 5px 5px 0 0; }",
            "    .annotations { background-color: #f8f8f8; padding: 10px; margin-top: 10px; border-radius: 5px; }",
            "    .confidence { margin-top: 5px; }",
            "    .confidence-bar { height: 10px; background-color: #ddd; border-radius: 5px; }",
            "    .confidence-level { height: 100%; background-color: #4CAF50; border-radius: 5px; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <h1>Belief Trace Export</h1>"
        ]
        
        # Add metadata if requested
        if include_metadata:
            lines.extend([
                "  <div class='metadata'>",
                "    <h2>Metadata</h2>",
                f"    <p><strong>Timestamp:</strong> {time.time()}</p>",
                f"    <p><strong>Steps:</strong> {len(reasoning_path)}</p>",
                f"    <p><strong>Annotations:</strong> {'Included' if annotate else 'Excluded'}</p>",
                "  </div>"
            ])
        
        # Add each reasoning step
        for i, step in enumerate(reasoning_path):
            step_num = i + 1
            step_text = step.get("text", "")
            step_type = step.get("type", "reasoning_step")
            
            # Format step
            lines.extend([
                f"  <div class='step' id='step-{step_num}'>",
                f"    <div class='step-header'>",
                f"      <h2>Step {step_num}: {step_type.title()}</h2>",
                f"    </div>",
                f"    <p>{step_text}</p>"
            ])
            
            # Add annotations if requested
            if annotate:
                lines.append("    <div class='annotations'>")
                lines.append("      <h3>Annotations</h3>")
                
                # Add confidence if available
                if "confidence" in step:
                    confidence = step["confidence"]
                    confidence_percent = int(confidence * 100)
                    lines.extend([
                        "      <div class='confidence'>",
                        f"        <p><strong>Confidence:</strong> {confidence:.2f}</p>",
                        "        <div class='confidence-bar'>",
                        f"          <div class='confidence-level' style='width: {confidence_percent}%;'></div>",
                        "        </div>",
                        "      </div>"
                    ])
                
                # Add source if available
                if "source" in step:
                    lines.append(f"      <p><strong>Source:</strong> {step['source']}</p>")
                
                # Add epistemic status if available
                if "epistemic_status" in step:
                    lines.append(f"      <p><strong>Epistemic Status:</strong> <code>{step['epistemic_status']}</code></p>")
                
                # Add reasoning type if available
                if "reasoning_type" in step:
                    lines.append(f"      <p><strong>Reasoning Type:</strong> <em>{step['reasoning_type']}</em></p>")
                
                # Add dependencies if available
                if "dependencies" in step and step["dependencies"]:
                    deps = ", ".join([f"<a href='#step-{d}'>Step {d}</a>" for d in step["dependencies"]])
                    lines.append(f"      <p><strong>Dependencies:</strong> {deps}</p>")
                
                lines.append("    </div>")
            
            lines.append("  </div>")
        
        lines.extend([
            "</body>",
            "</html>"
        ])
        
        return "\n".join(lines)
    
    def _format_as_graph(self, reasoning_path: List[Dict[str, Any]], 
                       include_metadata: bool,
                       annotate: bool) -> str:
        """Format reasoning path as a graph representation (JSON)."""
        # Create graph structure
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Add metadata if requested
        if include_metadata:
            graph["metadata"] = {
                "timestamp": time.time(),
                "steps_count": len(reasoning_path),
                "annotations_included": annotate
            }
        
        # Process each reasoning step as a node
        for i, step in enumerate(reasoning_path):
            step_num = i + 1
            step_text = step.get("text", "")
            step_type = step.get("type", "reasoning_step")
            
            # Create node
            node = {
                "id": f"step-{step_num}",
                "label": f"Step {step_num}",
                "type": step_type,
                "text": step_text
            }
            
            # Add annotations if requested
            if annotate:
                for annotation_type in ["confidence", "source", "epistemic_status", "reasoning_type"]:
                    if annotation_type in step:
                        node[annotation_type] = step[annotation_type]
            
            graph["nodes"].append(node)
            
            # Add edges for dependencies
            if "dependencies" in step and step["dependencies"]:
                for dep in step["dependencies"]:
                    edge = {
                        "source": f"step-{dep}",
                        "target": f"step-{step_num}",
                        "type": "depends_on"
                    }
                    graph["edges"].append(edge)
        
        # Convert to JSON
        return json.dumps(graph, indent=2)
    
    def merge_traces(self, traces: List[Dict[str, Any]], format_type: str = "json") -> Dict[str, Any]:
        """
        Merge multiple belief traces into a unified trace.
        
        Args:
            traces: List of belief trace export results
            format_type: Format for the merged trace
            
        Returns:
            Dictionary with merged trace
        """
        # Validate input
        if not traces:
            return {
                "error": "No traces provided for merging",
                "success": False
            }
        
        # Extract reasoning paths from each trace
        reasoning_paths = []
        for trace in traces:
            # Skip invalid traces
            if not trace.get("success", False) or "trace_content" not in trace:
                continue
            
            # Parse trace content based on format
            trace_format = trace.get("format", "text")
            content = trace["trace_content"]
            
            if trace_format == "json":
                try:
                    parsed = json.loads(content)
                    if "belief_trace" in parsed and isinstance(parsed["belief_trace"], list):
                        reasoning_paths.append(parsed["belief_trace"])
                except:
                    # Skip invalid JSON
                    pass
            else:
                # For non-JSON formats, we can't easily extract the reasoning path
                # In a real implementation, this would parse different formats
                pass
        
        # If no valid reasoning paths found, return error
        if not reasoning_paths:
            return {
                "error": "No valid reasoning paths found in provided traces",
                "success": False
            }
        
        # Merge reasoning paths
        merged_path = []
        step_counter = 0
        
        for path in reasoning_paths:
            for step in path:
                step_counter += 1
                
                # Create merged step with original trace info
                merged_step = {
                    "text": step.get("text", ""),
                    "type": step.get("type", "reasoning_step"),
                    "original_step": step.get("step_number"),
                    "merged_step": step_counter
                }
                
                # Copy annotations if available
                if "annotations" in step:
                    for key, value in step["annotations"].items():
                        merged_step[key] = value
                
                merged_path.append(merged_step)
        
        # Export merged trace
        return self.export_trace(merged_path, format_type)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Belief Trace Exporter (KA-37) on the provided data.
    
    Args:
        data: A dictionary containing reasoning path and export options
        
    Returns:
        Dictionary with belief trace export
    """
    reasoning_path = data.get("reasoning_path", [])
    format_type = data.get("format", "text")
    include_metadata = data.get("include_metadata", True)
    annotate = data.get("annotate", True)
    
    # Handle trace merging if requested
    if "traces_to_merge" in data:
        exporter = BeliefTraceExporter()
        result = exporter.merge_traces(data["traces_to_merge"], format_type)
        
        if result.get("success", False):
            return {
                "algorithm": "KA-37",
                "belief_trace": result["trace_content"],
                "format": result["format"],
                "timestamp": time.time(),
                "success": True
            }
        else:
            return {
                "algorithm": "KA-37",
                "error": result.get("error", "Failed to merge traces"),
                "success": False
            }
    
    # Handle regular export
    if not reasoning_path:
        return {
            "algorithm": "KA-37",
            "error": "No reasoning path provided",
            "success": False
        }
    
    exporter = BeliefTraceExporter()
    result = exporter.export_trace(reasoning_path, format_type, include_metadata, annotate)
    
    return {
        "algorithm": "KA-37",
        "belief_trace": result["trace_content"],
        "format": result["format"],
        "timestamp": time.time(),
        "success": True
    }