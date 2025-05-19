"""
KA-30: Sanity Check + Hallucination Filter

This algorithm detects and filters potential hallucinations, fabrications, and
unsupported assertions in generated content and agent outputs.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
import re
import time

logger = logging.getLogger(__name__)

class HallucinationFilter:
    """
    KA-30: Detects and filters hallucinations in generated content.
    
    This algorithm analyzes text for signs of hallucination, fabrication, or
    unsupported assertions, providing confidence scores and filtering options.
    """
    
    def __init__(self):
        """Initialize the Hallucination Filter."""
        self.hallucination_indicators = self._initialize_hallucination_indicators()
        self.domain_specific_checks = self._initialize_domain_specific_checks()
        logger.info("KA-30: Hallucination Filter initialized")
    
    def _initialize_hallucination_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns and indicators of hallucination."""
        return {
            "uncertain_language": {
                "patterns": [
                    r"\b(?:might|may|could|possibly|perhaps|probably|likely|unlikely|seems|appears)\b",
                    r"\bI (?:believe|think|assume|suppose|guess)\b",
                    r"\b(?:not entirely clear|unclear|uncertain|unknown)\b"
                ],
                "severity": "low",
                "description": "Use of hedging or uncertain language",
                "requires_context": False
            },
            "unreferenced_specifics": {
                "patterns": [
                    r"\bin (\d{4}),",
                    r"\b(?:according to|cited by|referenced in) (?!the )(?!FAR )(?!DFARS )(?!NIST )(?!ISO )([A-Z][a-z]+ (?:[A-Z][a-z]* )?(?:[A-Z][a-z]*))",
                    r"\b([A-Z][a-z]+ (?:[A-Z][a-z]* )?(?:[A-Z][a-z]*)) (?:found|discovered|determined|identified|confirmed|showed|stated|argued|suggested)"
                ],
                "severity": "medium",
                "description": "Specific claims without proper references",
                "requires_context": True
            },
            "overt_fabrication": {
                "patterns": [
                    r"\b(?:unverified|fabricated|made up|fictional|invented|contrived)\b",
                    r"\bno (?:evidence|proof|validation|verification|confirmation|source|citation)\b",
                    r"\b(?:imaginary|hypothetical|speculative)\s+(?:scenario|situation|case|example)\b"
                ],
                "severity": "high",
                "description": "Explicit indicators of fabrication or lack of evidence",
                "requires_context": False
            },
            "statistical_claims": {
                "patterns": [
                    r"\b(\d{1,3})(?:\.\d+)?\s*(?:percent|%)",
                    r"\bapproximately (\d+)",
                    r"\b(?:most|many|numerous|several|various|few) studies"
                ],
                "severity": "medium",
                "description": "Statistical claims that require verification",
                "requires_context": True
            },
            "impossible_knowledge": {
                "patterns": [
                    r"\b(?:all|every|always|never|none|no one)\b.{0,30}\b(?:will|would|does|do|should|must|has|have|can|could)\b",
                    r"\b(?:universally|globally|worldwide|everywhere|nowhere)\b"
                ],
                "severity": "high",
                "description": "Absolute or impossible knowledge claims",
                "requires_context": False
            },
            "temporal_inconsistency": {
                "patterns": [
                    r"\bcurrently\b.{0,50}\bin (?:2026|2027|2028|2029|2030)\b",
                    r"\b(?:recent|latest|newest|current)\b.{0,50}\bin (?:2000|200[1-5]|19\d{2})\b"
                ],
                "severity": "high",
                "description": "Inconsistent temporal references",
                "requires_context": False
            }
        }
    
    def _initialize_domain_specific_checks(self) -> Dict[str, Dict[str, Any]]:
        """Initialize domain-specific hallucination checks."""
        return {
            "regulatory": {
                "critical_references": [
                    r"FAR \d+(\.\d+)*",
                    r"DFARS \d+(\.\d+)*",
                    r"\d+ CFR \d+(\.\d+)*",
                    r"NIST SP \d+-\d+"
                ],
                "verification_threshold": 0.8,
                "special_cases": {
                    "far_section_range": r"FAR (5[3-9]|\d{3,})\.\d+",  # FAR sections only go up to 52
                    "impossible_regulation": r"FAR 0\.0"
                }
            },
            "healthcare": {
                "critical_references": [
                    r"FDA approval",
                    r"clinical trials? (?:showed|proved|confirmed|demonstrated)",
                    r"(?:effective|efficacious) (?:treatment|therapy|medication|intervention)"
                ],
                "verification_threshold": 0.9,
                "special_cases": {
                    "medical_certainty": r"(?:guaranteed|100% effective|completely safe|cures all)",
                    "fda_dates": r"FDA approved in (\d{4})"
                }
            },
            "financial": {
                "critical_references": [
                    r"SEC Rule \d+-\d+",
                    r"(?:guaranteed|assured) (?:return|profit|gain|income)",
                    r"historical (?:return|performance|yield) of (\d{1,3})(?:\.\d+)?\s*(?:percent|%)"
                ],
                "verification_threshold": 0.85,
                "special_cases": {
                    "investment_certainty": r"(?:risk-free|certain|guaranteed) investment",
                    "market_prediction": r"(?:will|is going to) (?:rise|increase|grow|fall|decrease) by (\d{1,3})(?:\.\d+)?\s*(?:percent|%)"
                }
            },
            "technical": {
                "critical_references": [
                    r"benchmark(?:s|ing)? (?:showed|proved|confirmed|demonstrated)",
                    r"(?:all|every) implementation(?:s)? (?:must|should|will|can)",
                    r"(?:always|never) (?:causes|results in|leads to)"
                ],
                "verification_threshold": 0.75,
                "special_cases": {
                    "performance_claims": r"(?:increases|decreases|improves|reduces) (?:performance|efficiency|speed) by (\d{1,3})(?:\.\d+)?\s*(?:percent|%)",
                    "compatibility": r"(?:compatible|works) with (?:all|every|any)"
                }
            }
        }
    
    def analyze_content(self, content: str, context: Optional[Dict[str, Any]] = None, 
                      domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze content for potential hallucinations.
        
        Args:
            content: The text content to analyze
            context: Optional context including references, valid entities, etc.
            domain: Optional domain for domain-specific checks
            
        Returns:
            Dictionary with hallucination analysis results
        """
        # Determine domain if not provided
        if domain is None:
            domain = self._determine_domain(content)
        
        # Extract context information
        valid_references = context.get("valid_references", []) if context else []
        verified_entities = context.get("verified_entities", []) if context else []
        verified_facts = context.get("verified_facts", []) if context else []
        
        # Detect hallucination indicators
        detected_indicators = self._detect_hallucination_indicators(content)
        
        # Perform domain-specific checks
        domain_issues = self._check_domain_specific_issues(content, domain, valid_references)
        
        # Consolidate all detected issues
        all_issues = detected_indicators + domain_issues
        
        # Calculate hallucination probability
        hallucination_probability = self._calculate_hallucination_probability(all_issues, domain)
        
        # Check if content contains explicit hallucination terms
        hallucination_detected = any(
            issue["severity"] == "high" for issue in all_issues
        ) or hallucination_probability > 0.7
        
        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(all_issues, domain)
        
        return {
            "hallucination_detected": hallucination_detected,
            "hallucination_probability": hallucination_probability,
            "domain": domain,
            "issues_detected": all_issues,
            "high_severity_count": sum(1 for issue in all_issues if issue["severity"] == "high"),
            "medium_severity_count": sum(1 for issue in all_issues if issue["severity"] == "medium"),
            "low_severity_count": sum(1 for issue in all_issues if issue["severity"] == "low"),
            "improvement_suggestions": suggestions
        }
    
    def filter_content(self, content: str, context: Optional[Dict[str, Any]] = None,
                    domain: Optional[str] = None, threshold: float = 0.7) -> Dict[str, Any]:
        """
        Filter content to remove or flag potential hallucinations.
        
        Args:
            content: The text content to filter
            context: Optional context including references, valid entities, etc.
            domain: Optional domain for domain-specific checks
            threshold: Probability threshold for filtering actions
            
        Returns:
            Dictionary with filtered content and filtering results
        """
        # Analyze content first
        analysis = self.analyze_content(content, context, domain)
        
        # Initialize filtering result
        filtering_result = {
            "original_content": content,
            "filtered_content": content,
            "analysis": analysis,
            "filtering_actions": [],
            "filtering_level": "none",
            "filtered_segments": []
        }
        
        # Determine filtering level based on hallucination probability
        probability = analysis["hallucination_probability"]
        
        if probability < 0.3:
            # Low probability - no filtering needed
            filtering_result["filtering_level"] = "none"
        elif probability < threshold:
            # Medium probability - add caution indicators
            filtering_result["filtering_level"] = "caution"
            filtered_content, actions, segments = self._add_caution_indicators(content, analysis["issues_detected"])
            filtering_result["filtered_content"] = filtered_content
            filtering_result["filtering_actions"] = actions
            filtering_result["filtered_segments"] = segments
        else:
            # High probability - replace or heavily flag content
            filtering_result["filtering_level"] = "critical"
            filtered_content, actions, segments = self._replace_critical_hallucinations(content, analysis["issues_detected"])
            filtering_result["filtered_content"] = filtered_content
            filtering_result["filtering_actions"] = actions
            filtering_result["filtered_segments"] = segments
        
        return filtering_result
    
    def _determine_domain(self, content: str) -> str:
        """
        Determine the domain of the content.
        
        Args:
            content: The content to analyze
            
        Returns:
            Determined domain
        """
        content_lower = content.lower()
        
        # Domain-specific keywords
        domain_keywords = {
            "regulatory": ["regulation", "compliance", "law", "legal", "statute", "procurement", 
                          "far", "dfars", "cfr", "federal", "requirement", "policy"],
            "healthcare": ["medical", "health", "patient", "clinical", "doctor", "hospital", 
                          "treatment", "diagnosis", "therapy", "care", "fda", "drug"],
            "financial": ["finance", "financial", "money", "bank", "investment", "tax", 
                         "accounting", "audit", "budget", "cost", "expense", "revenue"],
            "technical": ["technology", "software", "hardware", "system", "network", "computer", 
                         "data", "algorithm", "code", "programming", "application", "cloud"]
        }
        
        # Score domains based on keyword matches
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            domain_scores[domain] = score
        
        # Return highest scoring domain, or general if all scores are zero
        if domain_scores:
            max_domain = max(domain_scores.items(), key=lambda x: x[1])
            if max_domain[1] > 0:
                return max_domain[0]
        
        return "general"
    
    def _detect_hallucination_indicators(self, content: str) -> List[Dict[str, Any]]:
        """
        Detect hallucination indicators in content.
        
        Args:
            content: The content to analyze
            
        Returns:
            List of detected hallucination indicators
        """
        detected_indicators = []
        
        # Check each indicator type
        for indicator_type, indicator_info in self.hallucination_indicators.items():
            patterns = indicator_info["patterns"]
            severity = indicator_info["severity"]
            description = indicator_info["description"]
            
            # Check each pattern within this indicator type
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    detected_indicators.append({
                        "type": indicator_type,
                        "severity": severity,
                        "description": description,
                        "matched_text": match.group(0),
                        "position": (match.start(), match.end()),
                        "context": content[max(0, match.start() - 20):min(len(content), match.end() + 20)]
                    })
        
        return detected_indicators
    
    def _check_domain_specific_issues(self, content: str, domain: str, valid_references: List[str]) -> List[Dict[str, Any]]:
        """
        Check for domain-specific hallucination issues.
        
        Args:
            content: The content to analyze
            domain: The domain context
            valid_references: List of known valid references
            
        Returns:
            List of domain-specific issues detected
        """
        domain_issues = []
        
        # Skip if domain not in specific checks
        if domain not in self.domain_specific_checks:
            return domain_issues
        
        domain_checks = self.domain_specific_checks[domain]
        
        # Check critical references
        for ref_pattern in domain_checks["critical_references"]:
            matches = re.finditer(ref_pattern, content)
            for match in matches:
                # Check if this is a valid reference
                reference_text = match.group(0)
                if reference_text not in valid_references:
                    domain_issues.append({
                        "type": "unverified_reference",
                        "severity": "high",
                        "description": f"Unverified {domain} reference",
                        "matched_text": reference_text,
                        "position": (match.start(), match.end()),
                        "context": content[max(0, match.start() - 20):min(len(content), match.end() + 20)]
                    })
        
        # Check special cases
        for case_name, case_pattern in domain_checks["special_cases"].items():
            matches = re.finditer(case_pattern, content)
            for match in matches:
                domain_issues.append({
                    "type": "domain_specific_issue",
                    "severity": "high",
                    "description": f"Potential {domain} domain hallucination: {case_name}",
                    "matched_text": match.group(0),
                    "position": (match.start(), match.end()),
                    "context": content[max(0, match.start() - 20):min(len(content), match.end() + 20)]
                })
        
        return domain_issues
    
    def _calculate_hallucination_probability(self, issues: List[Dict[str, Any]], domain: str) -> float:
        """
        Calculate the probability that content contains hallucinations.
        
        Args:
            issues: The detected issues
            domain: The domain context
            
        Returns:
            Probability value between 0 and 1
        """
        # No issues means low probability
        if not issues:
            return 0.1  # Base probability - nothing is absolutely certain
        
        # Count issues by severity
        high_count = sum(1 for issue in issues if issue["severity"] == "high")
        medium_count = sum(1 for issue in issues if issue["severity"] == "medium")
        low_count = sum(1 for issue in issues if issue["severity"] == "low")
        
        # Calculate basic probability
        base_probability = min(1.0, (high_count * 0.25) + (medium_count * 0.1) + (low_count * 0.03))
        
        # Apply domain-specific verification threshold if available
        if domain in self.domain_specific_checks:
            threshold = self.domain_specific_checks[domain]["verification_threshold"]
            
            # Higher verification thresholds increase probability for the same issues
            domain_factor = threshold / 0.8  # Normalize to a reference value of 0.8
            base_probability = min(1.0, base_probability * domain_factor)
        
        return base_probability
    
    def _generate_improvement_suggestions(self, issues: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
        """
        Generate suggestions to improve content and reduce hallucination.
        
        Args:
            issues: The detected issues
            domain: The domain context
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        issue_types_seen = set()
        
        # Generate suggestion for each unique issue type, prioritizing high severity
        high_severity_issues = [issue for issue in issues if issue["severity"] == "high"]
        other_issues = [issue for issue in issues if issue["severity"] != "high"]
        
        # Process high severity issues first
        for issue in high_severity_issues:
            issue_type = issue["type"]
            if issue_type not in issue_types_seen:
                issue_types_seen.add(issue_type)
                
                suggestion = {
                    "issue_type": issue_type,
                    "severity": issue["severity"],
                    "suggestion": self._get_suggestion_for_issue(issue_type, domain),
                    "example": issue["matched_text"]
                }
                suggestions.append(suggestion)
        
        # Process other issues
        for issue in other_issues:
            issue_type = issue["type"]
            if issue_type not in issue_types_seen:
                issue_types_seen.add(issue_type)
                
                suggestion = {
                    "issue_type": issue_type,
                    "severity": issue["severity"],
                    "suggestion": self._get_suggestion_for_issue(issue_type, domain),
                    "example": issue["matched_text"]
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _get_suggestion_for_issue(self, issue_type: str, domain: str) -> str:
        """
        Get specific suggestion for an issue type.
        
        Args:
            issue_type: The type of issue
            domain: The domain context
            
        Returns:
            Suggestion text
        """
        common_suggestions = {
            "uncertain_language": "Replace uncertain language with specific, verifiable statements or explicitly note uncertainty",
            "unreferenced_specifics": "Add proper citations for specific claims and numeric data",
            "overt_fabrication": "Remove explicitly fabricated or unverified content",
            "statistical_claims": "Verify and cite sources for statistical claims",
            "impossible_knowledge": "Avoid absolute statements that imply universal knowledge",
            "temporal_inconsistency": "Correct temporal references to align with known timeframes",
            "unverified_reference": "Verify references against authoritative sources",
            "domain_specific_issue": "Address domain-specific technical accuracy issues"
        }
        
        # Domain-specific suggestions
        domain_suggestions = {
            "regulatory": {
                "unreferenced_specifics": "Cite specific FAR, DFARS, or CFR sections for regulatory claims",
                "unverified_reference": "Verify regulatory references against official sources like acquisition.gov",
                "domain_specific_issue": "Ensure regulatory citations follow official numbering conventions"
            },
            "healthcare": {
                "unreferenced_specifics": "Cite peer-reviewed medical literature or official guidelines",
                "statistical_claims": "Provide specific clinical trial or study references for medical claims",
                "domain_specific_issue": "Verify FDA approval dates and treatment efficacy claims"
            },
            "financial": {
                "statistical_claims": "Cite specific financial data sources and include timeframes",
                "domain_specific_issue": "Avoid claims of guaranteed returns or certain market outcomes"
            },
            "technical": {
                "unreferenced_specifics": "Provide specific technical documentation or standard references",
                "domain_specific_issue": "Verify performance claims with benchmark data"
            }
        }
        
        # Return domain-specific suggestion if available, otherwise use common suggestion
        if domain in domain_suggestions and issue_type in domain_suggestions[domain]:
            return domain_suggestions[domain][issue_type]
        
        return common_suggestions.get(issue_type, "Verify and improve accuracy of content")
    
    def _add_caution_indicators(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Add caution indicators to content with medium probability issues.
        
        Args:
            content: The original content
            issues: The detected issues
            
        Returns:
            Tuple of (filtered_content, actions_taken, filtered_segments)
        """
        filtered_content = content
        actions = []
        segments = []
        
        # Sort issues by position to process from end to beginning (to maintain offsets)
        sorted_issues = sorted(issues, key=lambda x: x["position"][0], reverse=True)
        
        for issue in sorted_issues:
            if issue["severity"] in ["medium", "high"]:
                start, end = issue["position"]
                match_text = issue["matched_text"]
                
                # Add caution indicator
                indicator = f"{match_text} [CAUTION: Requires verification]"
                
                # Replace in content
                filtered_content = filtered_content[:start] + indicator + filtered_content[end:]
                
                # Record action
                actions.append({
                    "type": "caution_indicator",
                    "issue_type": issue["type"],
                    "position": (start, end),
                    "original_text": match_text
                })
                
                # Record segment
                segments.append({
                    "start": start,
                    "end": end,
                    "original_text": match_text,
                    "filtered_text": indicator,
                    "reason": issue["description"]
                })
        
        return filtered_content, actions, segments
    
    def _replace_critical_hallucinations(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Replace critical hallucinations in content.
        
        Args:
            content: The original content
            issues: The detected issues
            
        Returns:
            Tuple of (filtered_content, actions_taken, filtered_segments)
        """
        filtered_content = content
        actions = []
        segments = []
        
        # Sort issues by position to process from end to beginning (to maintain offsets)
        sorted_issues = sorted(issues, key=lambda x: x["position"][0], reverse=True)
        
        for issue in sorted_issues:
            if issue["severity"] == "high":
                start, end = issue["position"]
                match_text = issue["matched_text"]
                
                # Replace with warning
                replacement = f"[CONTENT REMOVED: Potential hallucination - {issue['description']}]"
                
                # Replace in content
                filtered_content = filtered_content[:start] + replacement + filtered_content[end:]
                
                # Record action
                actions.append({
                    "type": "critical_replacement",
                    "issue_type": issue["type"],
                    "position": (start, end),
                    "original_text": match_text
                })
                
                # Record segment
                segments.append({
                    "start": start,
                    "end": end,
                    "original_text": match_text,
                    "filtered_text": replacement,
                    "reason": issue["description"]
                })
            elif issue["severity"] == "medium":
                # Add caution for medium severity issues
                start, end = issue["position"]
                match_text = issue["matched_text"]
                
                # Add strong caution indicator
                indicator = f"{match_text} [WARNING: Unverified information]"
                
                # Replace in content
                filtered_content = filtered_content[:start] + indicator + filtered_content[end:]
                
                # Record action
                actions.append({
                    "type": "warning_indicator",
                    "issue_type": issue["type"],
                    "position": (start, end),
                    "original_text": match_text
                })
                
                # Record segment
                segments.append({
                    "start": start,
                    "end": end,
                    "original_text": match_text,
                    "filtered_text": indicator,
                    "reason": issue["description"]
                })
        
        return filtered_content, actions, segments


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Hallucination Filter (KA-30) on the provided data.
    
    Args:
        data: A dictionary containing the content to analyze or filter
        
    Returns:
        Dictionary with analysis or filtering results
    """
    content = data.get("agent_output", data.get("content", ""))
    context = data.get("context", {})
    domain = data.get("domain")
    operation = data.get("operation", "analyze")  # analyze or filter
    
    if not content:
        return {
            "algorithm": "KA-30",
            "error": "No content provided for analysis",
            "success": False
        }
    
    filter_engine = HallucinationFilter()
    
    if operation == "filter":
        threshold = data.get("threshold", 0.7)
        result = filter_engine.filter_content(content, context, domain, threshold)
    else:
        # Default to analyze
        result = filter_engine.analyze_content(content, context, domain)
    
    return {
        "algorithm": "KA-30",
        "operation": operation,
        **result,
        "timestamp": time.time(),
        "success": True
    }