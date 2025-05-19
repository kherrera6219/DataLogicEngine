"""
KA-27: Validation Logic Engine

This algorithm validates statements against established reference sources and knowledge bases
to determine their accuracy, relevance, and compliance with authoritative standards.
"""

import logging
from typing import Dict, List, Any, Optional, Set
import re
import time

logger = logging.getLogger(__name__)

class ValidationLogicEngine:
    """
    KA-27: Validates statements against established references and standards.
    
    This algorithm checks statements for validity against regulatory references,
    compliance standards, and other authoritative sources, providing confidence
    levels and validation sources.
    """
    
    def __init__(self):
        """Initialize the Validation Logic Engine."""
        self.reference_sources = self._initialize_reference_sources()
        self.validation_patterns = self._initialize_validation_patterns()
        logger.info("KA-27: Validation Logic Engine initialized")
    
    def _initialize_reference_sources(self) -> Dict[str, Dict[str, Any]]:
        """Initialize reference sources for validation."""
        return {
            "regulatory": {
                "FAR": {
                    "description": "Federal Acquisition Regulation",
                    "authority_level": "high",
                    "sections": ["Part 1-53"],
                    "valid_formats": [r"FAR\s+\d+(\.\d+)*", r"Federal Acquisition Regulation\s+\d+(\.\d+)*"]
                },
                "DFARS": {
                    "description": "Defense Federal Acquisition Regulation Supplement",
                    "authority_level": "high",
                    "sections": ["Part 201-253"],
                    "valid_formats": [r"DFARS\s+\d+(\.\d+)*", r"Defense Federal Acquisition Regulation\s+\d+(\.\d+)*"]
                },
                "CFR": {
                    "description": "Code of Federal Regulations",
                    "authority_level": "high",
                    "sections": ["Title 1-50"],
                    "valid_formats": [r"\d+\s+CFR\s+\d+(\.\d+)*", r"Code of Federal Regulations\s+\d+(\.\d+)*"]
                }
            },
            "compliance": {
                "ISO": {
                    "description": "International Organization for Standardization",
                    "authority_level": "high",
                    "standards": ["9001", "14001", "27001", "45001"],
                    "valid_formats": [r"ISO\s+\d+", r"International Standard\s+\d+"]
                },
                "NIST": {
                    "description": "National Institute of Standards and Technology",
                    "authority_level": "high",
                    "publications": ["SP 800-53", "SP 800-171", "CSF"],
                    "valid_formats": [r"NIST\s+SP\s+\d+-\d+", r"NIST\s+CSF"]
                }
            },
            "financial": {
                "GAAP": {
                    "description": "Generally Accepted Accounting Principles",
                    "authority_level": "high",
                    "areas": ["Revenue Recognition", "Financial Statements"],
                    "valid_formats": [r"GAAP", r"ASC\s+\d+"]
                },
                "SOX": {
                    "description": "Sarbanes-Oxley Act",
                    "authority_level": "high",
                    "sections": ["Section 302", "Section 404", "Section 906"],
                    "valid_formats": [r"SOX\s+Section\s+\d+", r"Sarbanes-Oxley\s+Section\s+\d+"]
                }
            },
            "healthcare": {
                "HIPAA": {
                    "description": "Health Insurance Portability and Accountability Act",
                    "authority_level": "high",
                    "sections": ["Privacy Rule", "Security Rule", "Breach Notification Rule"],
                    "valid_formats": [r"HIPAA", r"45\s+CFR\s+\d+(\.\d+)*"]
                },
                "FDA": {
                    "description": "Food and Drug Administration Regulations",
                    "authority_level": "high",
                    "sections": ["21 CFR Part 11", "21 CFR Part 820"],
                    "valid_formats": [r"21\s+CFR\s+Part\s+\d+", r"FDA\s+\d+\s+CFR\s+\d+"]
                }
            }
        }
    
    def _initialize_validation_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize validation patterns for different statement types."""
        return {
            "reference_citation": {
                "patterns": [
                    r"(?:according to|per|under|in accordance with|as stated in)\s+([A-Z]+(?:\s+[A-Z]+)*\s+\d+(?:\.\d+)*)",
                    r"([A-Z]+(?:\s+[A-Z]+)*\s+\d+(?:\.\d+)*)\s+(?:states|requires|mandates|specifies)"
                ],
                "validation_method": "reference_lookup",
                "confidence_base": 0.7
            },
            "regulatory_statement": {
                "patterns": [
                    r"(?:regulations|regulatory requirements|compliance requirements)\s+(?:require|mandate|specify)",
                    r"(?:must|shall|required to)\s+(?:comply with|adhere to|follow|meet)\s+(?:regulations|requirements)"
                ],
                "validation_method": "authority_check",
                "confidence_base": 0.5
            },
            "compliance_assertion": {
                "patterns": [
                    r"(?:compliant with|compliance with|adherence to|conformance to)\s+([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*)",
                    r"(?:complies with|adheres to|conforms to|meets the requirements of)\s+([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*)"
                ],
                "validation_method": "standard_check",
                "confidence_base": 0.6
            }
        }
    
    def validate_statement(self, statement: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a statement against reference sources.
        
        Args:
            statement: The statement to validate
            domain: Optional domain to narrow validation context
            
        Returns:
            Dictionary with validation results
        """
        # Determine domain if not provided
        if domain is None:
            domain = self._determine_domain(statement)
        
        # Extract references from statement
        references = self._extract_references(statement)
        
        # Determine statement type
        statement_type, matched_pattern = self._determine_statement_type(statement)
        
        # Set base validation status
        validation_result = {
            "validated": False,
            "confidence": 0.0,
            "references": [],
            "validation_sources": [],
            "domain": domain,
            "statement_type": statement_type
        }
        
        # Validate based on references found
        if references:
            valid_references = []
            validation_sources = []
            
            for ref in references:
                ref_source, ref_validity, ref_confidence = self._validate_reference(ref, domain)
                if ref_validity:
                    valid_references.append(ref)
                    validation_sources.append(ref_source)
            
            # Update validation result
            if valid_references:
                validation_result["validated"] = True
                validation_result["references"] = valid_references
                validation_result["validation_sources"] = validation_sources
                
                # Calculate confidence
                confidence_base = 0.5  # Default base confidence
                if statement_type in self.validation_patterns:
                    confidence_base = self.validation_patterns[statement_type]["confidence_base"]
                
                # Adjust confidence based on reference count and quality
                reference_factor = min(1.0, len(valid_references) * 0.2)
                validation_result["confidence"] = min(0.95, confidence_base + reference_factor)
        
        # If no direct references but contains known terms
        elif self._contains_known_terms(statement, domain):
            validation_result["validated"] = True
            validation_result["confidence"] = 0.6  # Moderate confidence for term-based validation
            validation_result["validation_sources"] = [f"{domain.title()} terminology"]
        
        return validation_result
    
    def _determine_domain(self, statement: str) -> str:
        """
        Determine the domain of the statement.
        
        Args:
            statement: The statement to analyze
            
        Returns:
            Determined domain
        """
        # Check for domain-specific references
        statement_lower = statement.lower()
        
        # Domain-specific keywords
        domain_keywords = {
            "regulatory": ["far", "dfars", "cfr", "federal acquisition", "regulation", "regulatory", "compliance"],
            "compliance": ["iso", "nist", "standard", "compliance", "conformance", "audit"],
            "financial": ["gaap", "sox", "financial", "accounting", "sarbanes", "audit"],
            "healthcare": ["hipaa", "fda", "medical", "health", "patient", "clinical"]
        }
        
        # Count matches for each domain
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in statement_lower)
            domain_scores[domain] = score
        
        # Return domain with highest score, or regulatory as fallback
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        
        return "regulatory"  # Default to regulatory
    
    def _extract_references(self, statement: str) -> List[str]:
        """
        Extract references from the statement.
        
        Args:
            statement: The statement to extract references from
            
        Returns:
            List of extracted references
        """
        references = []
        
        # Common reference patterns
        reference_patterns = [
            r"((?:FAR|DFARS|AFFARS|DFAR|NIST)\s+\d+(?:\.\d+)*)",
            r"(\d+\s+CFR\s+\d+(?:\.\d+)*)",
            r"(ISO\s+\d+(?::\d+)?)",
            r"(NIST\s+SP\s+\d+-\d+(?:[A-Z])?)",
            r"(SOX\s+Section\s+\d+)",
            r"(HIPAA\s+(?:Privacy|Security|Breach\s+Notification)\s+Rule)"
        ]
        
        # Extract references using patterns
        for pattern in reference_patterns:
            matches = re.findall(pattern, statement)
            references.extend(matches)
        
        return references
    
    def _determine_statement_type(self, statement: str) -> tuple:
        """
        Determine the type of statement based on patterns.
        
        Args:
            statement: The statement to analyze
            
        Returns:
            Tuple of (statement_type, matched_pattern)
        """
        for stmt_type, info in self.validation_patterns.items():
            for pattern in info["patterns"]:
                if re.search(pattern, statement, re.IGNORECASE):
                    return stmt_type, pattern
        
        return "general_statement", None
    
    def _validate_reference(self, reference: str, domain: str) -> tuple:
        """
        Validate a specific reference against known sources.
        
        Args:
            reference: The reference to validate
            domain: The domain context
            
        Returns:
            Tuple of (source, validity, confidence)
        """
        # Default values
        ref_source = "unknown"
        ref_validity = False
        ref_confidence = 0.0
        
        # Check against reference sources
        for source_domain, sources in self.reference_sources.items():
            if domain != "general" and source_domain != domain:
                continue  # Skip other domains if specific domain provided
            
            for source_name, source_info in sources.items():
                # Check if reference format matches any valid format
                for format_pattern in source_info["valid_formats"]:
                    if re.match(format_pattern, reference, re.IGNORECASE):
                        ref_source = f"{source_name} ({source_info['description']})"
                        ref_validity = True
                        
                        # Set confidence based on authority level
                        if source_info["authority_level"] == "high":
                            ref_confidence = 0.9
                        elif source_info["authority_level"] == "medium":
                            ref_confidence = 0.7
                        else:
                            ref_confidence = 0.5
                        
                        return ref_source, ref_validity, ref_confidence
        
        # Special case for FAR/DFARS references (core regulatory references)
        if re.match(r"(FAR|DFARS)\s+\d+(\.\d+)*", reference, re.IGNORECASE):
            ref_source = "Regulatory Reference"
            ref_validity = True
            ref_confidence = 0.8
        
        return ref_source, ref_validity, ref_confidence
    
    def _contains_known_terms(self, statement: str, domain: str) -> bool:
        """
        Check if statement contains domain-specific known terms.
        
        Args:
            statement: The statement to check
            domain: The domain context
            
        Returns:
            Boolean indicating if statement contains known terms
        """
        statement_lower = statement.lower()
        
        # Domain-specific terms
        domain_terms = {
            "regulatory": ["procurement", "acquisition", "contracting", "federal", "compliance", "contractor"],
            "compliance": ["standard", "requirement", "audit", "certification", "conformance", "assessment"],
            "financial": ["accounting", "financial", "report", "disclosure", "audit", "control"],
            "healthcare": ["patient", "medical", "health", "privacy", "protected health information", "phi"]
        }
        
        # Check for domain terms
        if domain in domain_terms:
            for term in domain_terms[domain]:
                if term in statement_lower:
                    return True
        
        return False


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Validation Logic Engine (KA-27) on the provided data.
    
    Args:
        data: A dictionary containing the statement to validate
        
    Returns:
        Dictionary with validation results
    """
    statement = data.get("statement", "")
    domain = data.get("domain")
    
    if not statement:
        return {
            "algorithm": "KA-27",
            "error": "No statement provided for validation",
            "success": False
        }
    
    engine = ValidationLogicEngine()
    result = engine.validate_statement(statement, domain)
    
    return {
        "algorithm": "KA-27",
        "statement": statement,
        **result,
        "timestamp": time.time(),
        "success": True
    }