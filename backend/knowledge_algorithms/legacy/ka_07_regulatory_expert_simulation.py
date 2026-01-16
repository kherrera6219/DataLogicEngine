"""
KA-07: Regulatory Expert Simulation (Octopus Node)

This algorithm simulates a regulatory expert perspective, providing insights
on relevant regulations, requirements, and governance frameworks.
"""

import logging
from typing import Dict, List, Any, Optional, Set
import re
import time

logger = logging.getLogger(__name__)

class RegulatoryExpertSimulation:
    """
    KA-07: Simulates a regulatory expert to provide regulatory insights.
    
    This algorithm analyzes queries from a regulatory perspective, identifying
    relevant regulations, compliance requirements, and legal frameworks.
    """
    
    def __init__(self):
        """Initialize the Regulatory Expert Simulation."""
        self.regulatory_knowledge = self._initialize_regulatory_knowledge()
        logger.info("KA-07: Regulatory Expert Simulation initialized")
    
    def _initialize_regulatory_knowledge(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the regulatory knowledge base."""
        return {
            "aerospace": {
                "regulations": [
                    {"code": "FAR 25.853", "title": "Flammability Requirements", "category": "Safety"},
                    {"code": "FAR 12.202", "title": "Market Research", "category": "Procurement"},
                    {"code": "DFARS 252.227-7013", "title": "Rights in Technical Data", "category": "Intellectual Property"},
                    {"code": "FAR 25.1309", "title": "Equipment Systems Installation", "category": "Safety"},
                    {"code": "EASA Part 21", "title": "Certification Procedures", "category": "Certification"}
                ],
                "authorities": ["FAA", "EASA", "CAAC", "Transport Canada"],
                "frameworks": ["DO-178C", "DO-254", "ARP4754A"],
                "recent_changes": [
                    {"date": "2023-06-01", "description": "Updated cybersecurity requirements for avionics"},
                    {"date": "2024-01-15", "description": "New environmental sustainability standards"}
                ]
            },
            "healthcare": {
                "regulations": [
                    {"code": "21 CFR Part 820", "title": "Quality System Regulation", "category": "Quality"},
                    {"code": "45 CFR Part 160", "title": "HIPAA Privacy Rule", "category": "Privacy"},
                    {"code": "21 CFR Part 11", "title": "Electronic Records", "category": "Documentation"},
                    {"code": "EU MDR 2017/745", "title": "Medical Device Regulation", "category": "Certification"},
                    {"code": "21 CFR Part 50", "title": "Protection of Human Subjects", "category": "Ethics"}
                ],
                "authorities": ["FDA", "EMA", "MHRA", "Health Canada"],
                "frameworks": ["ISO 13485", "ISO 14971", "IEC 62304"],
                "recent_changes": [
                    {"date": "2023-08-12", "description": "Updated guidance on SaMD development"},
                    {"date": "2024-03-01", "description": "New requirements for AI/ML validation in medical devices"}
                ]
            },
            "finance": {
                "regulations": [
                    {"code": "12 CFR Part 1026", "title": "Truth in Lending (Regulation Z)", "category": "Consumer Protection"},
                    {"code": "17 CFR Part 240", "title": "Securities Exchange Act", "category": "Securities"},
                    {"code": "31 CFR Part 1010", "title": "Financial Recordkeeping/BSA", "category": "AML"},
                    {"code": "12 CFR Part 1022", "title": "Fair Credit Reporting (Regulation V)", "category": "Consumer Protection"},
                    {"code": "EU GDPR", "title": "General Data Protection Regulation", "category": "Privacy"}
                ],
                "authorities": ["SEC", "Federal Reserve", "FINRA", "OCC", "CFPB"],
                "frameworks": ["Basel III", "COSO", "PCI DSS"],
                "recent_changes": [
                    {"date": "2023-11-15", "description": "Updated KYC requirements for digital assets"},
                    {"date": "2024-02-28", "description": "New ESG disclosure requirements"}
                ]
            },
            "construction": {
                "regulations": [
                    {"code": "29 CFR Part 1926", "title": "Safety and Health Regulations for Construction", "category": "Safety"},
                    {"code": "FAR 36.601-3", "title": "Applicable Contracting Procedures", "category": "Procurement"},
                    {"code": "DFARS 236.609-70", "title": "Additional Provisions", "category": "Procurement"},
                    {"code": "IBC 2021", "title": "International Building Code", "category": "Building Standards"},
                    {"code": "40 CFR Part 60", "title": "Standards of Performance for New Stationary Sources", "category": "Environmental"}
                ],
                "authorities": ["OSHA", "EPA", "ICC", "GSA"],
                "frameworks": ["LEED", "WELL Building Standard", "ISO 45001"],
                "recent_changes": [
                    {"date": "2023-07-20", "description": "Updated energy efficiency requirements"},
                    {"date": "2024-01-05", "description": "New requirements for sustainable materials"}
                ]
            },
            "technology": {
                "regulations": [
                    {"code": "16 CFR Part 314", "title": "Safeguards Rule", "category": "Security"},
                    {"code": "EU GDPR", "title": "General Data Protection Regulation", "category": "Privacy"},
                    {"code": "CCPA/CPRA", "title": "California Consumer Privacy Act/Rights Act", "category": "Privacy"},
                    {"code": "NIST 800-171", "title": "Protecting Controlled Unclassified Information", "category": "Security"},
                    {"code": "Children's Online Privacy Protection Act", "title": "COPPA", "category": "Privacy"}
                ],
                "authorities": ["FTC", "NIST", "European Data Protection Board", "CISA"],
                "frameworks": ["NIST CSF", "ISO 27001", "SOC 2", "COBIT"],
                "recent_changes": [
                    {"date": "2023-09-10", "description": "Updated AI transparency requirements"},
                    {"date": "2024-04-15", "description": "New cross-border data transfer requirements"}
                ]
            }
        }
    
    def simulate(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Simulate a regulatory expert's analysis of the query.
        
        Args:
            query: The query text
            context: Optional context including domain, constraints, etc.
            
        Returns:
            Dictionary containing the regulatory expert's analysis
        """
        context = context or {}
        domain = context.get("domain", self._identify_domain(query))
        
        # Analyze query to extract relevant regulatory aspects
        regulatory_concerns = self._identify_regulatory_concerns(query)
        
        # Determine applicable regulations
        applicable_regulations = self._determine_applicable_regulations(domain, regulatory_concerns)
        
        # Identify relevant authorities and frameworks
        authorities = self._identify_authorities(domain)
        frameworks = self._identify_frameworks(domain, regulatory_concerns)
        
        # Generate regulatory guidance
        guidance = self._generate_regulatory_guidance(query, domain, applicable_regulations)
        
        # Calculate confidence in the analysis
        confidence = self._calculate_confidence(domain, regulatory_concerns, applicable_regulations)
        
        # Compile final response
        result = {
            "algorithm": "KA-07",
            "query": query,
            "domain": domain,
            "regulatory_concerns": regulatory_concerns,
            "applicable_regulations": applicable_regulations,
            "authorities": authorities,
            "frameworks": frameworks,
            "guidance": guidance,
            "confidence": confidence,
            "timestamp": time.time()
        }
        
        return result
    
    def _identify_domain(self, query: str) -> str:
        """
        Identify the domain from the query if not provided.
        
        Args:
            query: The query text
            
        Returns:
            The identified domain
        """
        query_lower = query.lower()
        
        # Domain-specific keywords
        domain_keywords = {
            "aerospace": ["aircraft", "aviation", "aerospace", "flight", "faa", "easa", "airworthiness"],
            "healthcare": ["health", "medical", "patient", "clinical", "fda", "hipaa", "hospital"],
            "finance": ["financial", "banking", "investment", "securities", "trading", "credit", "loan"],
            "construction": ["building", "construction", "infrastructure", "osha", "safety", "contractor"],
            "technology": ["software", "technology", "data", "privacy", "cybersecurity", "digital", "internet"]
        }
        
        # Count matches for each domain
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            domain_scores[domain] = score
        
        # Return domain with highest score, or general if no clear match
        max_domain = max(domain_scores.items(), key=lambda x: x[1])
        if max_domain[1] > 0:
            return max_domain[0]
        
        return "general"
    
    def _identify_regulatory_concerns(self, query: str) -> List[Dict[str, Any]]:
        """
        Identify regulatory concerns from the query.
        
        Args:
            query: The query text
            
        Returns:
            List of identified regulatory concerns
        """
        query_lower = query.lower()
        
        # Common regulatory concern categories
        concern_categories = {
            "compliance": ["comply", "compliance", "compliant", "adhere", "adherence", "conform"],
            "safety": ["safety", "hazard", "risk", "dangerous", "protect", "prevention"],
            "privacy": ["privacy", "confidential", "personal data", "sensitive information", "disclosure"],
            "security": ["security", "secure", "breach", "vulnerability", "unauthorized", "protect"],
            "licensing": ["license", "permit", "authorization", "certified", "accredited", "approval"],
            "reporting": ["report", "disclosure", "filing", "documentation", "record", "submission"],
            "standards": ["standard", "specification", "requirement", "guideline", "benchmark"],
            "governance": ["governance", "oversight", "control", "management", "accountability"]
        }
        
        # Identify concerns from the query
        identified_concerns = []
        for category, keywords in concern_categories.items():
            matches = [kw for kw in keywords if kw in query_lower]
            if matches:
                identified_concerns.append({
                    "category": category,
                    "keywords": matches,
                    "relevance": min(1.0, len(matches) * 0.2)  # Scale based on match count
                })
        
        # Check for explicit regulation mentions (e.g., "FAR 25.853")
        regulation_patterns = [
            r"FAR\s+(\d+\.\d+(?:-\d+)?)",
            r"DFARS\s+(\d+\.\d+(?:-\d+)?)",
            r"CFR\s+[Pp]art\s+(\d+)",
            r"(\d+)\s+CFR\s+[Pp]art\s+(\d+)",
            r"ISO\s+(\d+)",
            r"HIPAA",
            r"GDPR",
            r"CCPA"
        ]
        
        for pattern in regulation_patterns:
            matches = re.findall(pattern, query)
            if matches:
                identified_concerns.append({
                    "category": "specific_regulation",
                    "matches": matches,
                    "relevance": 1.0  # Direct regulation mentions are highly relevant
                })
        
        return identified_concerns
    
    def _determine_applicable_regulations(self, domain: str, regulatory_concerns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Determine regulations applicable to the query.
        
        Args:
            domain: The domain context
            regulatory_concerns: Identified regulatory concerns
            
        Returns:
            List of applicable regulations
        """
        # Get domain-specific regulations
        domain_regulations = []
        if domain in self.regulatory_knowledge:
            domain_regulations = self.regulatory_knowledge[domain].get("regulations", [])
        
        # If no domain-specific regulations, return empty list
        if not domain_regulations:
            return []
        
        # Match regulations based on concerns
        applicable_regs = []
        categories = set([concern["category"] for concern in regulatory_concerns if "category" in concern])
        
        # Include regulations that match the concern categories
        for reg in domain_regulations:
            if reg["category"] in categories:
                applicable_regs.append({
                    "code": reg["code"],
                    "title": reg["title"],
                    "category": reg["category"],
                    "relevance": "high"
                })
            else:
                # Include other domain regulations with lower relevance
                applicable_regs.append({
                    "code": reg["code"],
                    "title": reg["title"],
                    "category": reg["category"],
                    "relevance": "medium"
                })
        
        # Check for specific regulation mentions
        specific_concerns = [concern for concern in regulatory_concerns if concern["category"] == "specific_regulation"]
        for concern in specific_concerns:
            for match in concern.get("matches", []):
                for reg in applicable_regs:
                    if match in reg["code"]:
                        reg["relevance"] = "critical"  # Upgrade relevance for specifically mentioned regulations
        
        # Sort by relevance
        relevance_order = {"critical": 0, "high": 1, "medium": 2}
        applicable_regs.sort(key=lambda x: relevance_order.get(x["relevance"], 3))
        
        return applicable_regs
    
    def _identify_authorities(self, domain: str) -> List[Dict[str, str]]:
        """
        Identify relevant regulatory authorities.
        
        Args:
            domain: The domain context
            
        Returns:
            List of relevant authorities
        """
        authorities = []
        
        if domain in self.regulatory_knowledge:
            authority_list = self.regulatory_knowledge[domain].get("authorities", [])
            authorities = [{"name": auth, "domain": domain} for auth in authority_list]
        
        # Add general authorities
        general_authorities = [
            {"name": "ISO", "domain": "standards"},
            {"name": "IEC", "domain": "standards"}
        ]
        
        # Combine and return unique authorities
        all_authorities = authorities + [
            auth for auth in general_authorities 
            if not any(a["name"] == auth["name"] for a in authorities)
        ]
        
        return all_authorities
    
    def _identify_frameworks(self, domain: str, regulatory_concerns: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Identify relevant frameworks.
        
        Args:
            domain: The domain context
            regulatory_concerns: Identified regulatory concerns
            
        Returns:
            List of relevant frameworks
        """
        frameworks = []
        
        if domain in self.regulatory_knowledge:
            framework_list = self.regulatory_knowledge[domain].get("frameworks", [])
            frameworks = [{"name": fw, "domain": domain} for fw in framework_list]
        
        # Add concern-specific frameworks
        concern_frameworks = {
            "security": [
                {"name": "NIST CSF", "domain": "cybersecurity"},
                {"name": "ISO 27001", "domain": "information security"}
            ],
            "privacy": [
                {"name": "GDPR", "domain": "data protection"},
                {"name": "ISO 27701", "domain": "privacy information management"}
            ],
            "compliance": [
                {"name": "ISO 19600", "domain": "compliance management"},
                {"name": "COSO", "domain": "internal control"}
            ]
        }
        
        # Add frameworks based on concerns
        for concern in regulatory_concerns:
            category = concern.get("category")
            if category in concern_frameworks:
                for framework in concern_frameworks[category]:
                    if not any(f["name"] == framework["name"] for f in frameworks):
                        frameworks.append(framework)
        
        return frameworks
    
    def _generate_regulatory_guidance(self, query: str, domain: str, regulations: List[Dict[str, Any]]) -> str:
        """
        Generate regulatory guidance based on the analysis.
        
        Args:
            query: The query text
            domain: The domain context
            regulations: Applicable regulations
            
        Returns:
            Regulatory guidance text
        """
        # Structure guidance based on domain and regulations
        if not regulations:
            return "No specific regulatory guidance available for this query."
        
        # Create a structured guidance response
        guidance = [
            f"Based on a regulatory analysis in the {domain} domain, the following guidance is provided:"
        ]
        
        # Add critical regulations first
        critical_regs = [r for r in regulations if r["relevance"] == "critical"]
        if critical_regs:
            guidance.append("\nCritical Regulatory Considerations:")
            for reg in critical_regs:
                guidance.append(f"- {reg['code']}: {reg['title']} - This regulation directly applies to your query")
        
        # Add high relevance regulations
        high_regs = [r for r in regulations if r["relevance"] == "high"]
        if high_regs:
            guidance.append("\nPrimary Regulatory Considerations:")
            for reg in high_regs[:3]:  # Limit to top 3
                guidance.append(f"- {reg['code']}: {reg['title']}")
        
        # Add domain-specific guidance
        if domain == "healthcare":
            guidance.append("\nHealthcare Regulatory Advisory:")
            guidance.append("- Ensure all patient data handling complies with privacy regulations")
            guidance.append("- Maintain documentation of compliance efforts")
            guidance.append("- Consider consulting with a healthcare compliance specialist")
        
        elif domain == "finance":
            guidance.append("\nFinancial Regulatory Advisory:")
            guidance.append("- Verify all disclosure requirements are satisfied")
            guidance.append("- Maintain audit trail of compliance decisions")
            guidance.append("- Consider regulatory reporting obligations")
        
        elif domain == "aerospace":
            guidance.append("\nAerospace Regulatory Advisory:")
            guidance.append("- Ensure all safety requirements are fully addressed")
            guidance.append("- Maintain documentation of testing and verification")
            guidance.append("- Consider certification requirements early in development")
        
        elif domain == "technology":
            guidance.append("\nTechnology Regulatory Advisory:")
            guidance.append("- Address data privacy and security requirements")
            guidance.append("- Consider cross-jurisdictional compliance obligations")
            guidance.append("- Implement monitoring for regulatory changes")
        
        # General guidance for all domains
        guidance.append("\nGeneral Regulatory Recommendations:")
        guidance.append("- Establish a compliance monitoring process")
        guidance.append("- Document regulatory interpretations and compliance decisions")
        guidance.append("- Consider engaging regulatory specialists for complex matters")
        
        return "\n".join(guidance)
    
    def _calculate_confidence(self, domain: str, regulatory_concerns: List[Dict[str, Any]], regulations: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence in the regulatory analysis.
        
        Args:
            domain: The domain context
            regulatory_concerns: Identified regulatory concerns
            regulations: Applicable regulations
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence
        confidence = 0.5
        
        # Adjust based on domain knowledge
        if domain in self.regulatory_knowledge:
            confidence += 0.1
        
        # Adjust based on regulatory concerns identified
        if regulatory_concerns:
            concern_confidence = min(0.2, len(regulatory_concerns) * 0.05)
            confidence += concern_confidence
        
        # Adjust based on regulations found
        if regulations:
            # Critical regulations provide higher confidence
            critical_count = sum(1 for r in regulations if r["relevance"] == "critical")
            high_count = sum(1 for r in regulations if r["relevance"] == "high")
            
            reg_confidence = min(0.2, (critical_count * 0.1) + (high_count * 0.05))
            confidence += reg_confidence
        
        # Cap at 0.95
        return min(0.95, confidence)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Regulatory Expert Simulation (KA-07) on the provided data.
    
    Args:
        data: A dictionary containing the query and optional context
        
    Returns:
        Dictionary with regulatory expert analysis
    """
    query = data.get("query", "")
    context = data.get("context", {})
    
    if not query:
        return {
            "algorithm": "KA-07",
            "error": "No query provided",
            "success": False
        }
    
    simulator = RegulatoryExpertSimulation()
    result = simulator.simulate(query, context)
    
    return {
        **result,
        "success": True
    }