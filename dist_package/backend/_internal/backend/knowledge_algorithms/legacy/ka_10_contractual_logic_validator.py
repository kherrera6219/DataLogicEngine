"""
KA-10: Contractual Logic Validator

This algorithm validates the logical consistency, completeness, and compliance 
of contractual clauses and agreements against regulatory requirements.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import re
import time

logger = logging.getLogger(__name__)

class ContractualLogicValidator:
    """
    KA-10: Validates contractual clauses for logical consistency and compliance.
    
    This algorithm analyzes contract clauses to identify logical issues, missing
    elements, and regulatory compliance concerns in contractual language.
    """
    
    def __init__(self):
        """Initialize the Contractual Logic Validator."""
        self.validation_rules = self._initialize_validation_rules()
        self.regulatory_requirements = self._initialize_regulatory_requirements()
        logger.info("KA-10: Contractual Logic Validator initialized")
    
    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize validation rules for contractual clauses."""
        return {
            "obligation_clarity": {
                "description": "Clear statement of obligations using 'shall' or 'must'",
                "patterns": [
                    r"\bshall\b",
                    r"\bmust\b",
                    r"\bis required to\b",
                    r"\bis obligated to\b"
                ],
                "severity": "high",
                "rule_type": "presence",
                "applicability": "all"
            },
            "prohibition_clarity": {
                "description": "Clear statement of prohibitions using 'shall not' or 'must not'",
                "patterns": [
                    r"\bshall not\b",
                    r"\bmust not\b",
                    r"\bis prohibited from\b",
                    r"\bmay not\b"
                ],
                "severity": "high",
                "rule_type": "conditional",
                "applicability": "prohibition"
            },
            "permission_clarity": {
                "description": "Clear statement of permissions using 'may' or 'is permitted to'",
                "patterns": [
                    r"\bmay\b",
                    r"\bis permitted to\b",
                    r"\bis allowed to\b",
                    r"\bhas the right to\b"
                ],
                "severity": "medium",
                "rule_type": "conditional",
                "applicability": "permission"
            },
            "definition_reference": {
                "description": "Terms that should be defined in the contract",
                "patterns": [
                    r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Capitalized multi-word terms
                    r"\b[A-Z][A-Z]+\b"  # Acronyms
                ],
                "severity": "medium",
                "rule_type": "reference",
                "applicability": "all"
            },
            "conditional_completeness": {
                "description": "Conditionals should have both condition and consequence",
                "patterns": [
                    r"\bif\b.{3,}(,|\.)?\s+(then)?\s+\b(shall|must|may|will)\b",
                    r"\bin the event\b.{3,}(,|\.)?\s+(then)?\s+\b(shall|must|may|will)\b",
                    r"\bwhen\b.{3,}(,|\.)?\s+(then)?\s+\b(shall|must|may|will)\b"
                ],
                "severity": "high",
                "rule_type": "structure",
                "applicability": "conditional"
            },
            "temporal_specificity": {
                "description": "Specific time periods or deadlines",
                "patterns": [
                    r"\bwithin\s+(\d+)\s+(day|week|month|year)s?\b",
                    r"\bno later than\b",
                    r"\bby\s+(\d{1,2}\/\d{1,2}\/\d{2,4})\b",
                    r"\bimmediately\b"
                ],
                "severity": "medium",
                "rule_type": "presence",
                "applicability": "timing"
            },
            "ambiguity_avoidance": {
                "description": "Potentially ambiguous terms to avoid",
                "patterns": [
                    r"\breasonable\b",
                    r"\bpromptly\b",
                    r"\bsubstantial\b",
                    r"\bmaterial\b",
                    r"\bappropriate\b",
                    r"\bsatisfactory\b"
                ],
                "severity": "medium",
                "rule_type": "absence",
                "applicability": "all"
            },
            "vague_reference": {
                "description": "Vague references that could cause ambiguity",
                "patterns": [
                    r"\bherein\b",
                    r"\bthereof\b",
                    r"\bsaid\b",
                    r"\bsuch\b",
                    r"\baforesaid\b"
                ],
                "severity": "low",
                "rule_type": "caution",
                "applicability": "all"
            },
            "logical_consistency": {
                "description": "Consistency in logical expressions",
                "patterns": [
                    r"\ball\b.{1,50}\bany\b",
                    r"\bnot\b.{1,30}\bunless\b",
                    r"\bnot\b.{1,30}\bexcept\b"
                ],
                "severity": "high",
                "rule_type": "structure",
                "applicability": "logical"
            }
        }
    
    def _initialize_regulatory_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Initialize regulatory requirements for different contract types."""
        return {
            "employment": {
                "required_clauses": [
                    {"topic": "compensation", "patterns": [r"\bsalary\b", r"\bcompensation\b", r"\bwage\b", r"\bpay\b"]},
                    {"topic": "termination", "patterns": [r"\btermination\b", r"\bterminate\b"]},
                    {"topic": "confidentiality", "patterns": [r"\bconfidential\b", r"\bnon-disclosure\b"]}
                ],
                "prohibited_clauses": [
                    {"topic": "non-compete", "jurisdictions": ["California"], 
                     "patterns": [r"\bnon-compete\b", r"\bnoncompete\b", r"\bnot\s+(?:\w+\s+){0,5}compete\b"]}
                ]
            },
            "service_agreement": {
                "required_clauses": [
                    {"topic": "service_description", "patterns": [r"\bservice\b.{1,50}\bdescription\b", r"\bscope\s+of\s+(?:\w+\s+){0,2}service"]},
                    {"topic": "payment_terms", "patterns": [r"\bpayment\b.{1,30}\bterm", r"\bfee\b", r"\bcompensation\b"]},
                    {"topic": "termination", "patterns": [r"\btermination\b", r"\bterminate\b"]}
                ],
                "prohibited_clauses": []
            },
            "software_license": {
                "required_clauses": [
                    {"topic": "grant_of_license", "patterns": [r"\bgrant\b.{1,30}\blicense\b", r"\blicense\b.{1,30}\bgrant"]},
                    {"topic": "restrictions", "patterns": [r"\brestrict", r"\blimitation\b"]},
                    {"topic": "intellectual_property", "patterns": [r"\bintellectual\s+property\b", r"\bcopyright\b", r"\btrademark\b"]}
                ],
                "prohibited_clauses": []
            },
            "data_processing": {
                "required_clauses": [
                    {"topic": "data_protection", "patterns": [r"\bdata\s+protection\b", r"\bprivacy\b"]},
                    {"topic": "data_subject_rights", "patterns": [r"\bdata\s+subject\b", r"\bright\s+to\s+access\b", r"\bright\s+to\s+(?:\w+\s+){0,2}erasure\b"]},
                    {"topic": "data_breach", "patterns": [r"\bbreach\b.{1,30}\bnotification\b", r"\bdata\s+breach\b"]}
                ],
                "prohibited_clauses": []
            }
        }
    
    def validate(self, contract_clauses: List[str], contract_type: Optional[str] = None, 
               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate contract clauses for logical consistency and compliance.
        
        Args:
            contract_clauses: List of contract clause texts
            contract_type: Type of contract (e.g., "employment", "service_agreement")
            context: Optional context with jurisdiction, sector, etc.
            
        Returns:
            Dictionary with validation results
        """
        context = context or {}
        jurisdiction = context.get("jurisdiction", "general")
        
        # Determine contract type if not provided
        if not contract_type:
            contract_type = self._determine_contract_type(contract_clauses)
        
        # Validate general clause logic
        clause_validations = self._validate_clause_logic(contract_clauses)
        
        # Validate regulatory compliance
        regulatory_validations = self._validate_regulatory_compliance(contract_clauses, contract_type, jurisdiction)
        
        # Check for missing required clauses
        missing_clauses = self._check_missing_clauses(contract_clauses, contract_type)
        
        # Determine overall validity
        valid_contract = self._determine_validity(clause_validations, regulatory_validations, missing_clauses)
        
        # Generate improvement recommendations
        recommendations = self._generate_recommendations(clause_validations, regulatory_validations, missing_clauses)
        
        # Calculate confidence in validation
        confidence = self._calculate_confidence(contract_clauses, contract_type, context)
        
        return {
            "algorithm": "KA-10",
            "contract_type": contract_type,
            "clauses_analyzed": len(contract_clauses),
            "valid_contract": valid_contract,
            "clause_validations": clause_validations,
            "regulatory_validations": regulatory_validations,
            "missing_clauses": missing_clauses,
            "recommendations": recommendations,
            "confidence": confidence,
            "timestamp": time.time()
        }
    
    def _determine_contract_type(self, clauses: List[str]) -> str:
        """
        Determine the type of contract based on clause content.
        
        Args:
            clauses: List of contract clause texts
            
        Returns:
            Determined contract type
        """
        # Join clauses for easier analysis
        all_text = " ".join(clauses).lower()
        
        # Contract type indicators
        type_indicators = {
            "employment": ["employment", "employee", "employer", "salary", "work", "position", "job"],
            "service_agreement": ["services", "provider", "client", "scope of service", "deliverable"],
            "software_license": ["software", "license", "licensee", "licensor", "intellectual property", "code"],
            "data_processing": ["data", "processing", "controller", "processor", "personal data", "data subject"],
            "lease": ["lease", "tenant", "landlord", "premises", "rent", "property"],
            "sale_of_goods": ["seller", "buyer", "goods", "purchase", "sale", "product", "delivery"]
        }
        
        # Count matches for each contract type
        type_scores = {}
        for ctype, indicators in type_indicators.items():
            score = sum(1 for indicator in indicators if indicator in all_text)
            type_scores[ctype] = score
        
        # Return the contract type with highest score, or general if no clear match
        max_type = max(type_scores.items(), key=lambda x: x[1])
        if max_type[1] > 0:
            return max_type[0]
        
        return "general_contract"
    
    def _validate_clause_logic(self, clauses: List[str]) -> List[Dict[str, Any]]:
        """
        Validate the logical structure and clarity of contract clauses.
        
        Args:
            clauses: List of contract clause texts
            
        Returns:
            List of validation results for each clause
        """
        validations = []
        
        for i, clause in enumerate(clauses):
            clause_validation = {
                "clause_index": i,
                "clause_text": clause,
                "issues": [],
                "valid": True
            }
            
            # Apply validation rules
            for rule_name, rule in self.validation_rules.items():
                rule_type = rule["rule_type"]
                patterns = rule["patterns"]
                
                if rule_type == "presence":
                    # Check for required patterns
                    matches = any(re.search(pattern, clause, re.IGNORECASE) for pattern in patterns)
                    if not matches:
                        clause_validation["issues"].append({
                            "type": rule_name,
                            "description": f"Missing {rule['description']}",
                            "severity": rule["severity"]
                        })
                        if rule["severity"] == "high":
                            clause_validation["valid"] = False
                
                elif rule_type == "absence":
                    # Check for patterns that should be absent
                    for pattern in patterns:
                        matches = re.findall(pattern, clause, re.IGNORECASE)
                        if matches:
                            clause_validation["issues"].append({
                                "type": rule_name,
                                "description": f"Contains potentially ambiguous term: '{matches[0]}'",
                                "severity": rule["severity"],
                                "matches": matches
                            })
                
                elif rule_type == "structure":
                    # Check for structural patterns
                    if rule_name == "conditional_completeness":
                        if re.search(r"\bif\b|\bin the event\b|\bwhen\b", clause, re.IGNORECASE):
                            matches = any(re.search(pattern, clause, re.IGNORECASE) for pattern in patterns)
                            if not matches:
                                clause_validation["issues"].append({
                                    "type": rule_name,
                                    "description": "Conditional statement without clear consequence",
                                    "severity": rule["severity"]
                                })
                                if rule["severity"] == "high":
                                    clause_validation["valid"] = False
                
                elif rule_type == "caution":
                    # Highlight terms that may need attention
                    for pattern in patterns:
                        matches = re.findall(pattern, clause, re.IGNORECASE)
                        if matches:
                            clause_validation["issues"].append({
                                "type": rule_name,
                                "description": f"Contains potentially vague reference: '{matches[0]}'",
                                "severity": rule["severity"],
                                "matches": matches
                            })
            
            validations.append(clause_validation)
        
        return validations
    
    def _validate_regulatory_compliance(self, clauses: List[str], contract_type: str, jurisdiction: str) -> Dict[str, Any]:
        """
        Validate contract clauses against regulatory requirements.
        
        Args:
            clauses: List of contract clause texts
            contract_type: Type of contract
            jurisdiction: Legal jurisdiction
            
        Returns:
            Regulatory compliance validation results
        """
        # Initialize compliance result
        compliance_result = {
            "compliant": True,
            "contract_type": contract_type,
            "jurisdiction": jurisdiction,
            "issues": []
        }
        
        # Skip if contract type not in our regulatory requirements
        if contract_type not in self.regulatory_requirements:
            compliance_result["contract_type"] = "unknown"
            return compliance_result
        
        requirements = self.regulatory_requirements[contract_type]
        
        # Join all clauses for easier analysis
        all_text = " ".join(clauses).lower()
        
        # Check for required clauses
        for required in requirements.get("required_clauses", []):
            topic = required["topic"]
            patterns = required["patterns"]
            
            # Check if any pattern matches
            matches = any(re.search(pattern, all_text, re.IGNORECASE) for pattern in patterns)
            
            if not matches:
                compliance_result["issues"].append({
                    "type": "missing_required",
                    "topic": topic,
                    "description": f"Missing required clause topic: {topic}",
                    "severity": "high"
                })
                compliance_result["compliant"] = False
        
        # Check for prohibited clauses
        for prohibited in requirements.get("prohibited_clauses", []):
            topic = prohibited["topic"]
            patterns = prohibited["patterns"]
            relevant_jurisdictions = prohibited.get("jurisdictions", [])
            
            # Skip if jurisdiction-specific and not relevant
            if relevant_jurisdictions and jurisdiction not in relevant_jurisdictions:
                continue
            
            # Check if any pattern matches
            for pattern in patterns:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                if matches:
                    compliance_result["issues"].append({
                        "type": "prohibited_included",
                        "topic": topic,
                        "description": f"Contains prohibited clause topic: {topic} in jurisdiction: {jurisdiction}",
                        "severity": "high",
                        "matches": matches
                    })
                    compliance_result["compliant"] = False
                    break
        
        return compliance_result
    
    def _check_missing_clauses(self, clauses: List[str], contract_type: str) -> List[Dict[str, Any]]:
        """
        Check for common clauses that may be missing from the contract.
        
        Args:
            clauses: List of contract clause texts
            contract_type: Type of contract
            
        Returns:
            List of missing common clauses
        """
        missing_clauses = []
        
        # Common clauses by contract type
        common_clauses = {
            "employment": [
                {"name": "Governing Law", "patterns": [r"governing law", r"governed by the law"]},
                {"name": "Dispute Resolution", "patterns": [r"dispute", r"arbitration", r"mediation"]},
                {"name": "Entire Agreement", "patterns": [r"entire agreement", r"complete agreement"]}
            ],
            "service_agreement": [
                {"name": "Limitation of Liability", "patterns": [r"limitation of liability", r"limit(s|ed) liability"]},
                {"name": "Warranty", "patterns": [r"warrant(y|ies)", r"guarantees?"]},
                {"name": "Force Majeure", "patterns": [r"force majeure", r"act(s)? of god"]}
            ],
            "software_license": [
                {"name": "Indemnification", "patterns": [r"indemnif(y|ication)", r"hold harmless"]},
                {"name": "Warranty Disclaimer", "patterns": [r"disclaim(s|er) warranty", r"no warranty"]},
                {"name": "Export Compliance", "patterns": [r"export", r"sanction"]}
            ],
            "general_contract": [
                {"name": "Governing Law", "patterns": [r"governing law", r"governed by the law"]},
                {"name": "Assignment", "patterns": [r"assign(ment)?", r"transfer of rights"]},
                {"name": "Notice", "patterns": [r"notice", r"notification"]}
            ]
        }
        
        # Get the relevant common clauses list
        relevant_clauses = common_clauses.get(contract_type, common_clauses["general_contract"])
        
        # Join all clauses for easier analysis
        all_text = " ".join(clauses).lower()
        
        # Check for each common clause
        for clause in relevant_clauses:
            name = clause["name"]
            patterns = clause["patterns"]
            
            # Check if any pattern matches
            matches = any(re.search(pattern, all_text, re.IGNORECASE) for pattern in patterns)
            
            if not matches:
                missing_clauses.append({
                    "name": name,
                    "severity": "medium",
                    "description": f"Common clause '{name}' appears to be missing"
                })
        
        return missing_clauses
    
    def _determine_validity(self, clause_validations: List[Dict[str, Any]], 
                          regulatory_validations: Dict[str, Any], 
                          missing_clauses: List[Dict[str, Any]]) -> bool:
        """
        Determine overall contract validity based on all validations.
        
        Args:
            clause_validations: Results of clause logic validations
            regulatory_validations: Results of regulatory compliance validations
            missing_clauses: List of identified missing clauses
            
        Returns:
            Boolean indicating if contract is valid
        """
        # Contract is invalid if any clause has high-severity issues
        if any(not clause["valid"] for clause in clause_validations):
            return False
        
        # Contract is invalid if not compliant with regulations
        if not regulatory_validations["compliant"]:
            return False
        
        # Missing common clauses don't automatically invalidate the contract
        # But they should be addressed in recommendations
        
        return True
    
    def _generate_recommendations(self, clause_validations: List[Dict[str, Any]], 
                                regulatory_validations: Dict[str, Any], 
                                missing_clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate recommendations for improving the contract.
        
        Args:
            clause_validations: Results of clause logic validations
            regulatory_validations: Results of regulatory compliance validations
            missing_clauses: List of identified missing clauses
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Add recommendations for clause issues
        for i, validation in enumerate(clause_validations):
            for issue in validation["issues"]:
                if issue["severity"] in ["high", "medium"]:
                    reco = {
                        "type": "clause_improvement",
                        "clause_index": validation["clause_index"],
                        "issue": issue["type"],
                        "description": issue["description"],
                        "recommendation": self._get_issue_recommendation(issue["type"]),
                        "priority": "high" if issue["severity"] == "high" else "medium"
                    }
                    recommendations.append(reco)
        
        # Add recommendations for regulatory issues
        for issue in regulatory_validations.get("issues", []):
            reco = {
                "type": "regulatory_compliance",
                "issue": issue["type"],
                "description": issue["description"],
                "recommendation": self._get_regulatory_recommendation(issue["type"], issue["topic"]),
                "priority": "high"
            }
            recommendations.append(reco)
        
        # Add recommendations for missing clauses
        for missing in missing_clauses:
            reco = {
                "type": "missing_clause",
                "clause_name": missing["name"],
                "description": missing["description"],
                "recommendation": f"Consider adding a '{missing['name']}' clause to the contract",
                "priority": "medium"
            }
            recommendations.append(reco)
        
        # Sort recommendations by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return recommendations
    
    def _get_issue_recommendation(self, issue_type: str) -> str:
        """
        Get a recommendation for a specific issue type.
        
        Args:
            issue_type: The type of issue
            
        Returns:
            Recommendation text
        """
        recommendations = {
            "obligation_clarity": "Use clear obligation language such as 'shall' or 'must' to specify required actions",
            "prohibition_clarity": "Use clear prohibition language such as 'shall not' or 'must not' for forbidden actions",
            "permission_clarity": "Use clear permission language such as 'may' to indicate allowed actions",
            "definition_reference": "Ensure capitalized terms are defined in the contract's definitions section",
            "conditional_completeness": "Ensure conditional statements have both a clear condition and consequence",
            "temporal_specificity": "Specify exact timeframes instead of vague timing references",
            "ambiguity_avoidance": "Replace ambiguous terms with specific, measurable criteria",
            "vague_reference": "Replace vague references with specific section or clause references",
            "logical_consistency": "Review for logical consistency in expressions using 'all', 'any', 'not', etc."
        }
        
        return recommendations.get(issue_type, "Review and revise this issue to improve clarity and enforceability")
    
    def _get_regulatory_recommendation(self, issue_type: str, topic: str) -> str:
        """
        Get a recommendation for a regulatory issue.
        
        Args:
            issue_type: The type of regulatory issue
            topic: The topic of the issue
            
        Returns:
            Recommendation text
        """
        if issue_type == "missing_required":
            return f"Add a clause addressing {topic} to meet regulatory requirements"
        elif issue_type == "prohibited_included":
            return f"Remove or revise clauses related to {topic} as they may not be enforceable in this jurisdiction"
        else:
            return "Address this regulatory issue to ensure compliance"
    
    def _calculate_confidence(self, clauses: List[str], contract_type: str, context: Dict[str, Any]) -> float:
        """
        Calculate confidence in the validation results.
        
        Args:
            clauses: The contract clauses
            contract_type: Type of contract
            context: Analysis context
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence
        confidence = 0.7  # Start with moderately high confidence
        
        # Adjust based on number of clauses analyzed
        if len(clauses) <= 3:
            confidence -= 0.1  # Very few clauses provides limited context
        elif len(clauses) >= 15:
            confidence += 0.05  # More clauses provide better context
        
        # Adjust based on contract type certainty
        if contract_type == "general_contract":
            confidence -= 0.1  # Less certain about general contracts
        elif context.get("contract_type") == contract_type:
            confidence += 0.05  # Higher confidence if contract type was explicitly provided
        
        # Adjust based on jurisdiction specificity
        if context.get("jurisdiction") and context["jurisdiction"] != "general":
            confidence += 0.05  # Jurisdiction context increases confidence
        
        # Adjust based on clause complexity
        avg_clause_length = sum(len(clause.split()) for clause in clauses) / max(1, len(clauses))
        if avg_clause_length > 100:
            confidence -= 0.05  # Very complex clauses are harder to validate
        
        # Cap at 0.95
        return min(0.95, confidence)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Contractual Logic Validator (KA-10) on the provided data.
    
    Args:
        data: A dictionary containing contract clauses and optional context
        
    Returns:
        Dictionary with validation results
    """
    contract_clauses = data.get("contract_clauses", [])
    contract_type = data.get("contract_type")
    context = data.get("context", {})
    
    if not contract_clauses:
        return {
            "algorithm": "KA-10",
            "error": "No contract clauses provided for validation",
            "success": False
        }
    
    validator = ContractualLogicValidator()
    result = validator.validate(contract_clauses, contract_type, context)
    
    return {
        **result,
        "success": True
    }