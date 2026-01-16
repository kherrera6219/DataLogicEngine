"""
KA-09: Conflict Resolution Engine

This algorithm detects and resolves conflicts between different regulatory
requirements, compliance standards, and other potentially contradictory elements.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import re
import time

logger = logging.getLogger(__name__)

class ConflictResolutionEngine:
    """
    KA-09: Detects and resolves conflicts among regulatory and compliance elements.
    
    This algorithm identifies potential conflicts between different requirements,
    standards, or clauses, and provides resolution strategies and priorities.
    """
    
    def __init__(self):
        """Initialize the Conflict Resolution Engine."""
        self.conflict_patterns = self._initialize_conflict_patterns()
        self.resolution_strategies = self._initialize_resolution_strategies()
        logger.info("KA-09: Conflict Resolution Engine initialized")
    
    def _initialize_conflict_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for detecting potential conflicts."""
        return {
            "contradictory_requirements": {
                "patterns": [
                    r"conflict(s|ing)?\s+(?:with|between)",
                    r"contradict(s|ory|ion)?",
                    r"inconsistent\s+(?:with|requirements)",
                    r"incompatible\s+(?:with|requirements)",
                    r"mutual(?:ly)?\s+exclusive"
                ],
                "severity": "high",
                "description": "Direct contradiction between requirements"
            },
            "overlapping_jurisdiction": {
                "patterns": [
                    r"overlapping\s+jurisdiction",
                    r"multiple\s+(?:regulatory|authorities)",
                    r"cross[- ]border",
                    r"conflicting\s+(?:jurisdiction|authority)"
                ],
                "severity": "high",
                "description": "Multiple jurisdictions with potentially conflicting requirements"
            },
            "timing_conflicts": {
                "patterns": [
                    r"timing\s+(?:conflict|issue)",
                    r"deadline\s+(?:conflict|incompatible)",
                    r"schedule\s+(?:conflict|issue)",
                    r"concurrent\s+(?:requirement|obligation)"
                ],
                "severity": "medium",
                "description": "Conflicts in timing or scheduling requirements"
            },
            "resource_allocation": {
                "patterns": [
                    r"resource\s+(?:conflict|allocation|constraint)",
                    r"competing\s+(?:priorities|resources)",
                    r"insufficient\s+(?:resources|capacity)"
                ],
                "severity": "medium",
                "description": "Conflicts due to limited resources for compliance activities"
            },
            "technical_incompatibility": {
                "patterns": [
                    r"technical(?:ly)?\s+(?:incompatible|conflict)",
                    r"system\s+(?:conflict|incompatibility)",
                    r"integration\s+(?:issue|problem)"
                ],
                "severity": "medium",
                "description": "Technical incompatibilities in implementation requirements"
            },
            "standard_inconsistency": {
                "patterns": [
                    r"standard\s+(?:conflict|inconsistency)",
                    r"different\s+(?:standard|specification)",
                    r"incompatible\s+(?:standard|framework)",
                    r"divergent\s+(?:requirement|specification)"
                ],
                "severity": "medium",
                "description": "Inconsistencies between different standards or frameworks"
            },
            "definition_ambiguity": {
                "patterns": [
                    r"definition\s+(?:conflict|ambiguity)",
                    r"term\s+(?:ambiguity|inconsistency)",
                    r"inconsistent\s+(?:definition|terminology)",
                    r"different\s+(?:interpretation|meaning)"
                ],
                "severity": "low",
                "description": "Ambiguities or inconsistencies in terminology or definitions"
            }
        }
    
    def _initialize_resolution_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize resolution strategies for different conflict types."""
        return {
            "contradictory_requirements": [
                {
                    "strategy": "Hierarchical Prioritization",
                    "description": "Apply a hierarchy of authority, with higher-level requirements taking precedence",
                    "applicability": "high"
                },
                {
                    "strategy": "Regulatory Consultation",
                    "description": "Consult with regulatory authorities for official guidance on conflicting requirements",
                    "applicability": "high"
                },
                {
                    "strategy": "Strictest Standard Approach",
                    "description": "Apply the strictest standard or requirement to ensure compliance with all obligations",
                    "applicability": "medium"
                }
            ],
            "overlapping_jurisdiction": [
                {
                    "strategy": "Jurisdictional Mapping",
                    "description": "Create a comprehensive map of jurisdictional requirements and identify areas of overlap",
                    "applicability": "high"
                },
                {
                    "strategy": "Local Legal Counsel",
                    "description": "Engage legal counsel in each jurisdiction to provide guidance on compliance priorities",
                    "applicability": "high"
                },
                {
                    "strategy": "Mutual Recognition Analysis",
                    "description": "Identify mutual recognition agreements between jurisdictions that may simplify compliance",
                    "applicability": "medium"
                }
            ],
            "timing_conflicts": [
                {
                    "strategy": "Phased Implementation",
                    "description": "Develop a phased approach that addresses highest priority requirements first",
                    "applicability": "high"
                },
                {
                    "strategy": "Extension Request",
                    "description": "Formally request extensions or deferrals for certain deadlines when conflicts exist",
                    "applicability": "medium"
                },
                {
                    "strategy": "Resource Optimization",
                    "description": "Optimize resource allocation to meet concurrent deadlines where possible",
                    "applicability": "medium"
                }
            ],
            "resource_allocation": [
                {
                    "strategy": "Risk-Based Prioritization",
                    "description": "Allocate resources based on risk assessment and compliance criticality",
                    "applicability": "high"
                },
                {
                    "strategy": "Resource Augmentation",
                    "description": "Temporarily increase resources to address competing compliance requirements",
                    "applicability": "medium"
                },
                {
                    "strategy": "Compliance Technology",
                    "description": "Implement compliance technology to automate and streamline resource-intensive activities",
                    "applicability": "medium"
                }
            ],
            "technical_incompatibility": [
                {
                    "strategy": "Integration Architecture",
                    "description": "Design an integration architecture that accommodates conflicting technical requirements",
                    "applicability": "high"
                },
                {
                    "strategy": "Middleware Solution",
                    "description": "Implement middleware to bridge incompatible systems or requirements",
                    "applicability": "high"
                },
                {
                    "strategy": "Variance Request",
                    "description": "Request technical variances where appropriate for conflicting technical requirements",
                    "applicability": "medium"
                }
            ],
            "standard_inconsistency": [
                {
                    "strategy": "Gap Analysis",
                    "description": "Conduct a detailed gap analysis between standards to identify true conflicts vs. perceived conflicts",
                    "applicability": "high"
                },
                {
                    "strategy": "Consolidated Framework",
                    "description": "Develop a consolidated compliance framework that addresses all applicable standards",
                    "applicability": "medium"
                },
                {
                    "strategy": "Standard-Specific Controls",
                    "description": "Implement controls specific to each standard where consolidation is not possible",
                    "applicability": "medium"
                }
            ],
            "definition_ambiguity": [
                {
                    "strategy": "Terminology Framework",
                    "description": "Develop an internal terminology framework that maps between different definitions",
                    "applicability": "high"
                },
                {
                    "strategy": "Documentation Clarity",
                    "description": "Explicitly document which definition is being applied in each context",
                    "applicability": "high"
                },
                {
                    "strategy": "Clarification Request",
                    "description": "Formally request clarification from standards bodies or regulatory authorities",
                    "applicability": "medium"
                }
            ],
            "general": [
                {
                    "strategy": "Cross-Functional Review",
                    "description": "Engage cross-functional experts to review and address conflicts",
                    "applicability": "high"
                },
                {
                    "strategy": "Documentation Strategy",
                    "description": "Document all conflicts, resolution decisions, and their rationale",
                    "applicability": "high"
                },
                {
                    "strategy": "External Expertise",
                    "description": "Engage external subject matter experts for complex conflict resolution",
                    "applicability": "medium"
                }
            ]
        }
    
    def analyze(self, clauses: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze clauses for conflicts and provide resolution strategies.
        
        Args:
            clauses: List of clause texts to analyze for conflicts
            context: Optional context with domain, sector, etc.
            
        Returns:
            Dictionary with conflict analysis results
        """
        context = context or {}
        domain = context.get("domain", "general")
        sector = context.get("sector", "general")
        
        # Detect conflicts within clauses
        detected_conflicts = self._detect_conflicts(clauses)
        
        # Check for conflicts between clauses
        inter_clause_conflicts = self._detect_inter_clause_conflicts(clauses)
        for conflict in inter_clause_conflicts:
            if conflict not in detected_conflicts:
                detected_conflicts.append(conflict)
        
        # Determine conflict resolution status
        if not detected_conflicts:
            status = "resolved"  # No conflicts detected
        else:
            high_severity = any(conflict["severity"] == "high" for conflict in detected_conflicts)
            if high_severity:
                status = "critical_review_required"
            else:
                status = "review_recommended"
        
        # Generate resolution strategies for detected conflicts
        resolution_strategies = self._generate_resolution_strategies(detected_conflicts, domain, sector)
        
        # Create overall resolution plan if conflicts exist
        resolution_plan = None
        if detected_conflicts:
            resolution_plan = self._create_resolution_plan(detected_conflicts, resolution_strategies, domain, sector)
        
        # Calculate confidence in the analysis
        confidence = self._calculate_confidence(clauses, detected_conflicts, context)
        
        return {
            "algorithm": "KA-09",
            "clauses_analyzed": len(clauses),
            "conflicts_detected": detected_conflicts,
            "resolution_strategies": resolution_strategies,
            "resolution_plan": resolution_plan,
            "status": status,
            "confidence": confidence,
            "timestamp": time.time()
        }
    
    def _detect_conflicts(self, clauses: List[str]) -> List[Dict[str, Any]]:
        """
        Detect conflicts within individual clauses.
        
        Args:
            clauses: List of clause texts
            
        Returns:
            List of detected conflicts
        """
        detected_conflicts = []
        
        for i, clause in enumerate(clauses):
            clause_lower = clause.lower()
            
            # Check each conflict pattern
            for conflict_type, conflict_info in self.conflict_patterns.items():
                patterns = conflict_info["patterns"]
                
                for pattern in patterns:
                    matches = re.findall(pattern, clause_lower)
                    if matches:
                        conflict = {
                            "type": conflict_type,
                            "clause_index": i,
                            "clause_text": clause,
                            "severity": conflict_info["severity"],
                            "description": conflict_info["description"],
                            "pattern_matched": pattern,
                            "conflict_source": "internal"  # Conflict within a single clause
                        }
                        detected_conflicts.append(conflict)
                        break  # Found a match for this conflict type, move to next
        
        return detected_conflicts
    
    def _detect_inter_clause_conflicts(self, clauses: List[str]) -> List[Dict[str, Any]]:
        """
        Detect conflicts between different clauses.
        
        Args:
            clauses: List of clause texts
            
        Returns:
            List of detected inter-clause conflicts
        """
        inter_clause_conflicts = []
        
        # Look for potential contradictions between clauses
        for i, clause1 in enumerate(clauses):
            clause1_lower = clause1.lower()
            
            for j, clause2 in enumerate(clauses):
                if i >= j:  # Only compare each pair once, and don't compare a clause to itself
                    continue
                
                clause2_lower = clause2.lower()
                
                # Check for potential requirement contradictions
                contradiction_indicators = self._detect_contradiction_indicators(clause1_lower, clause2_lower)
                
                if contradiction_indicators:
                    conflict = {
                        "type": "inter_clause_contradiction",
                        "clause_indices": [i, j],
                        "clause_texts": [clause1, clause2],
                        "severity": "high",
                        "description": "Potential contradiction between clauses",
                        "indicators": contradiction_indicators,
                        "conflict_source": "between_clauses"
                    }
                    inter_clause_conflicts.append(conflict)
        
        return inter_clause_conflicts
    
    def _detect_contradiction_indicators(self, clause1: str, clause2: str) -> List[str]:
        """
        Detect indicators of contradiction between two clause texts.
        
        Args:
            clause1: First clause text (lowercase)
            clause2: Second clause text (lowercase)
            
        Returns:
            List of contradiction indicators found
        """
        indicators = []
        
        # Check for opposing requirements
        requirement_pairs = [
            ("must", "must not"),
            ("shall", "shall not"),
            ("required", "not required"),
            ("prohibited", "permitted"),
            ("allowed", "not allowed"),
            ("approval", "no approval"),
            ("necessary", "unnecessary"),
            ("mandatory", "optional")
        ]
        
        for req1, req2 in requirement_pairs:
            if req1 in clause1 and req2 in clause2:
                indicators.append(f"Opposing requirements: '{req1}' vs '{req2}'")
            elif req2 in clause1 and req1 in clause2:
                indicators.append(f"Opposing requirements: '{req2}' vs '{req1}'")
        
        # Check for timing conflicts
        timing_terms = ["immediately", "within 24 hours", "within 48 hours", "within 7 days", 
                        "monthly", "quarterly", "annually"]
        
        found_timing_terms1 = [term for term in timing_terms if term in clause1]
        found_timing_terms2 = [term for term in timing_terms if term in clause2]
        
        if found_timing_terms1 and found_timing_terms2 and found_timing_terms1 != found_timing_terms2:
            indicators.append(f"Potentially conflicting timing requirements: '{found_timing_terms1}' vs '{found_timing_terms2}'")
        
        # Check for potentially conflicting references to standards or regulations
        std_pattern = r"(ISO|IEC|NIST|HIPAA|GDPR|SOX)\s+[\w\d\-\.]+"
        std1 = re.findall(std_pattern, clause1)
        std2 = re.findall(std_pattern, clause2)
        
        if std1 and std2 and set(std1) != set(std2):
            indicators.append(f"Different standards referenced: '{std1}' vs '{std2}'")
        
        return indicators
    
    def _generate_resolution_strategies(self, conflicts: List[Dict[str, Any]], domain: str, sector: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate resolution strategies for detected conflicts.
        
        Args:
            conflicts: List of detected conflicts
            domain: The domain context
            sector: The sector context
            
        Returns:
            Dictionary mapping conflict types to resolution strategies
        """
        if not conflicts:
            return {}
        
        strategies_by_type = {}
        
        for conflict in conflicts:
            conflict_type = conflict["type"]
            
            # Skip if we've already generated strategies for this conflict type
            if conflict_type in strategies_by_type:
                continue
            
            # Get appropriate strategies for this conflict type
            if conflict_type in self.resolution_strategies:
                strategies = self.resolution_strategies[conflict_type]
            elif conflict_type == "inter_clause_contradiction":
                # For contradictions between clauses, use the contradictory_requirements strategies
                strategies = self.resolution_strategies["contradictory_requirements"]
            else:
                # If no specific strategies, use general ones
                strategies = self.resolution_strategies["general"]
            
            # Sort strategies by applicability
            applicability_order = {"high": 0, "medium": 1, "low": 2}
            sorted_strategies = sorted(strategies, key=lambda x: applicability_order.get(x["applicability"], 3))
            
            # Store strategies for this conflict type
            strategies_by_type[conflict_type] = sorted_strategies
        
        # Always include general strategies
        if "general" not in strategies_by_type and conflicts:
            strategies_by_type["general"] = self.resolution_strategies["general"]
        
        return strategies_by_type
    
    def _create_resolution_plan(self, conflicts: List[Dict[str, Any]], strategies: Dict[str, List[Dict[str, Any]]], 
                              domain: str, sector: str) -> Dict[str, Any]:
        """
        Create an overall resolution plan for the detected conflicts.
        
        Args:
            conflicts: List of detected conflicts
            strategies: Resolution strategies by conflict type
            domain: The domain context
            sector: The sector context
            
        Returns:
            Resolution plan dictionary
        """
        # Count conflicts by severity
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for conflict in conflicts:
            severity = conflict.get("severity", "medium")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Determine overall priority level
        if severity_counts["high"] > 0:
            priority = "high"
        elif severity_counts["medium"] > 0:
            priority = "medium"
        else:
            priority = "low"
        
        # Create recommended steps based on conflict types and severities
        recommended_steps = []
        
        if severity_counts["high"] > 0:
            # Steps for high-severity conflicts
            recommended_steps.append({
                "step": 1,
                "action": "Conduct immediate review of high-severity conflicts",
                "priority": "high",
                "timeframe": "immediate"
            })
            recommended_steps.append({
                "step": 2,
                "action": "Engage appropriate subject matter experts for conflict resolution",
                "priority": "high",
                "timeframe": "1-3 days"
            })
        
        # Add sector-specific recommended steps
        if sector == "finance" and (severity_counts["high"] > 0 or severity_counts["medium"] > 0):
            recommended_steps.append({
                "step": len(recommended_steps) + 1,
                "action": "Consult with financial compliance officer or legal counsel",
                "priority": "high" if severity_counts["high"] > 0 else "medium",
                "timeframe": "1-5 days"
            })
        elif sector == "healthcare" and (severity_counts["high"] > 0 or severity_counts["medium"] > 0):
            recommended_steps.append({
                "step": len(recommended_steps) + 1,
                "action": "Consult with healthcare privacy and compliance experts",
                "priority": "high" if severity_counts["high"] > 0 else "medium",
                "timeframe": "1-5 days"
            })
        
        # Add general resolution steps
        recommended_steps.append({
            "step": len(recommended_steps) + 1,
            "action": "Document all conflicts and resolution decisions",
            "priority": "medium",
            "timeframe": "ongoing"
        })
        
        recommended_steps.append({
            "step": len(recommended_steps) + 1,
            "action": "Develop implementation plan for conflict resolutions",
            "priority": "medium",
            "timeframe": "within 2 weeks"
        })
        
        recommended_steps.append({
            "step": len(recommended_steps) + 1,
            "action": "Schedule follow-up review to confirm resolution effectiveness",
            "priority": "medium",
            "timeframe": "30-60 days"
        })
        
        return {
            "priority": priority,
            "severity_counts": severity_counts,
            "total_conflicts": len(conflicts),
            "recommended_steps": recommended_steps,
            "domain": domain,
            "sector": sector
        }
    
    def _calculate_confidence(self, clauses: List[str], conflicts: List[Dict[str, Any]], context: Dict[str, Any]) -> float:
        """
        Calculate confidence in the conflict analysis.
        
        Args:
            clauses: The analyzed clauses
            conflicts: Detected conflicts
            context: Analysis context
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence
        confidence = 0.65  # Start with moderate confidence
        
        # Adjust based on number of clauses analyzed
        if len(clauses) >= 10:
            confidence += 0.1  # More clauses provide more context
        elif len(clauses) <= 2:
            confidence -= 0.1  # Very few clauses provide limited context
        
        # Adjust based on clause length and complexity
        avg_clause_length = sum(len(clause.split()) for clause in clauses) / max(1, len(clauses))
        if avg_clause_length > 50:
            confidence -= 0.05  # Very long clauses may be more ambiguous
        elif avg_clause_length < 10:
            confidence -= 0.05  # Very short clauses may lack context
        
        # Adjust based on conflict detection
        if conflicts:
            # More distinct conflict types suggest more reliable detection
            conflict_types = set(conflict["type"] for conflict in conflicts)
            if len(conflict_types) >= 3:
                confidence += 0.05
            
            # Inter-clause conflicts are generally more reliable detections
            inter_clause_count = sum(1 for conflict in conflicts if conflict.get("conflict_source") == "between_clauses")
            if inter_clause_count > 0:
                confidence += 0.05
        else:
            # No conflicts detected - could be correct, or could be missing conflicts
            if len(clauses) > 5:
                confidence -= 0.05  # More clauses without conflicts is somewhat suspicious
        
        # Adjust based on domain-specific context
        if "domain" in context and context["domain"] != "general":
            confidence += 0.05  # Domain context increases confidence
        
        if "sector" in context and context["sector"] != "general":
            confidence += 0.05  # Sector context increases confidence
        
        # Cap at 0.95
        return min(0.95, confidence)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Conflict Resolution Engine (KA-09) on the provided data.
    
    Args:
        data: A dictionary containing clauses to analyze and optional context
        
    Returns:
        Dictionary with conflict analysis results
    """
    clauses = data.get("clauses", [])
    context = data.get("context", {})
    
    if not clauses:
        return {
            "algorithm": "KA-09",
            "error": "No clauses provided for analysis",
            "success": False
        }
    
    engine = ConflictResolutionEngine()
    result = engine.analyze(clauses, context)
    
    return {
        **result,
        "success": True
    }