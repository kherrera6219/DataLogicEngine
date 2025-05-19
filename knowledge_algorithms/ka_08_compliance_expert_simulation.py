"""
KA-08: Compliance Expert Simulation (Spiderweb Node)

This algorithm simulates a compliance expert perspective, focusing on standards,
verification methods, audit requirements, and compliance frameworks.
"""

import logging
from typing import Dict, List, Any, Optional, Set
import re
import time

logger = logging.getLogger(__name__)

class ComplianceExpertSimulation:
    """
    KA-08: Simulates a compliance expert to provide compliance insights.
    
    This algorithm analyzes queries from a compliance perspective, identifying
    relevant standards, verification protocols, audit requirements, and
    documentation needs.
    """
    
    def __init__(self):
        """Initialize the Compliance Expert Simulation."""
        self.compliance_knowledge = self._initialize_compliance_knowledge()
        logger.info("KA-08: Compliance Expert Simulation initialized")
    
    def _initialize_compliance_knowledge(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the compliance knowledge base."""
        return {
            "finance": {
                "standards": [
                    {"id": "SOX Section 404", "title": "Internal Control Over Financial Reporting", "category": "Financial Controls"},
                    {"id": "SEC 17a-4", "title": "Records Preservation Requirements", "category": "Record Keeping"},
                    {"id": "PCI DSS", "title": "Payment Card Industry Data Security Standard", "category": "Data Security"},
                    {"id": "FINRA Rule 4511", "title": "Books and Records", "category": "Record Keeping"},
                    {"id": "Basel III", "title": "Capital Adequacy Framework", "category": "Risk Management"}
                ],
                "verification_methods": [
                    {"name": "External Audit", "description": "Independent examination by qualified auditors"},
                    {"name": "Internal Control Testing", "description": "Systematic evaluation of control effectiveness"},
                    {"name": "Compliance Certification", "description": "Formal attestation of adherence to requirements"}
                ],
                "documentation_requirements": [
                    "Policies and procedures documentation",
                    "Risk assessment records",
                    "Audit trails of transactions",
                    "Staff training records",
                    "Third-party due diligence documentation"
                ],
                "common_issues": [
                    "Inadequate separation of duties",
                    "Insufficient documentation of controls",
                    "Incomplete transaction records",
                    "Delayed regulatory reporting",
                    "Inadequate oversight of third parties"
                ]
            },
            "healthcare": {
                "standards": [
                    {"id": "HIPAA 164.308", "title": "Administrative Safeguards", "category": "Privacy & Security"},
                    {"id": "HITECH Subtitle D", "title": "Privacy Provisions", "category": "Privacy & Security"},
                    {"id": "ISO 13485", "title": "Medical Devices Quality Management Systems", "category": "Quality"},
                    {"id": "21 CFR Part 11", "title": "Electronic Records and Signatures", "category": "Documentation"},
                    {"id": "NIST SP 800-66", "title": "HIPAA Security Rule Guidelines", "category": "Privacy & Security"}
                ],
                "verification_methods": [
                    {"name": "Security Risk Assessment", "description": "Systematic evaluation of security controls"},
                    {"name": "Privacy Impact Assessment", "description": "Analysis of privacy implications and controls"},
                    {"name": "Compliance Audit", "description": "Structured evaluation of adherence to requirements"}
                ],
                "documentation_requirements": [
                    "Privacy policies and procedures",
                    "Security incident response plans",
                    "Business associate agreements",
                    "Patient authorization forms",
                    "Staff training documentation"
                ],
                "common_issues": [
                    "Unauthorized access to protected health information",
                    "Inadequate encryption of sensitive data",
                    "Missing business associate agreements",
                    "Insufficient audit controls",
                    "Delayed breach notification"
                ]
            },
            "technology": {
                "standards": [
                    {"id": "ISO 27001", "title": "Information Security Management System", "category": "Security"},
                    {"id": "SOC 2", "title": "Service Organization Control 2", "category": "Trust Services"},
                    {"id": "GDPR", "title": "General Data Protection Regulation", "category": "Privacy"},
                    {"id": "CCPA", "title": "California Consumer Privacy Act", "category": "Privacy"},
                    {"id": "NIST 800-53", "title": "Security and Privacy Controls", "category": "Security"}
                ],
                "verification_methods": [
                    {"name": "ISMS Audit", "description": "Audit of information security management system"},
                    {"name": "Penetration Testing", "description": "Simulated cyberattack to identify vulnerabilities"},
                    {"name": "Data Protection Impact Assessment", "description": "Evaluation of privacy risks and controls"}
                ],
                "documentation_requirements": [
                    "Information security policies",
                    "Privacy notices and consent mechanisms",
                    "Data processing records",
                    "Risk assessment documentation",
                    "Incident response procedures"
                ],
                "common_issues": [
                    "Inadequate data subject access mechanisms",
                    "Insufficient breach detection capabilities",
                    "Incomplete data inventory",
                    "Missing technical controls documentation",
                    "Inadequate vendor security assessment"
                ]
            },
            "manufacturing": {
                "standards": [
                    {"id": "ISO 9001", "title": "Quality Management Systems", "category": "Quality"},
                    {"id": "ISO 14001", "title": "Environmental Management Systems", "category": "Environmental"},
                    {"id": "ISO 45001", "title": "Occupational Health and Safety", "category": "Safety"},
                    {"id": "AS9100", "title": "Aerospace Quality Management", "category": "Quality"},
                    {"id": "IATF 16949", "title": "Automotive Quality Management", "category": "Quality"}
                ],
                "verification_methods": [
                    {"name": "Quality Audit", "description": "Structured review of quality management system"},
                    {"name": "Process Validation", "description": "Confirmation that processes meet specifications"},
                    {"name": "Product Certification", "description": "Formal verification of product compliance"}
                ],
                "documentation_requirements": [
                    "Quality manual and procedures",
                    "Process control documentation",
                    "Calibration and maintenance records",
                    "Nonconformity and corrective action records",
                    "Material certification documentation"
                ],
                "common_issues": [
                    "Inadequate process documentation",
                    "Insufficient calibration of measurement equipment",
                    "Missing traceability records",
                    "Incomplete corrective action implementation",
                    "Inadequate change management"
                ]
            },
            "energy": {
                "standards": [
                    {"id": "ISO 50001", "title": "Energy Management Systems", "category": "Energy"},
                    {"id": "NERC CIP", "title": "Critical Infrastructure Protection", "category": "Security"},
                    {"id": "API 1173", "title": "Pipeline Safety Management Systems", "category": "Safety"},
                    {"id": "IEEE 1547", "title": "Interconnection Standards", "category": "Technical"},
                    {"id": "ISO 14064", "title": "Greenhouse Gas Accounting", "category": "Environmental"}
                ],
                "verification_methods": [
                    {"name": "Energy Audit", "description": "Systematic analysis of energy usage and efficiency"},
                    {"name": "Compliance Assessment", "description": "Evaluation against regulatory requirements"},
                    {"name": "Environmental Impact Assessment", "description": "Analysis of environmental effects"}
                ],
                "documentation_requirements": [
                    "Energy management policies",
                    "Emissions monitoring records",
                    "Safety procedure documentation",
                    "Reliability and maintenance records",
                    "Emergency response plans"
                ],
                "common_issues": [
                    "Incomplete emissions monitoring",
                    "Inadequate safety procedure documentation",
                    "Insufficient reliability testing",
                    "Missing calibration of monitoring equipment",
                    "Outdated emergency response procedures"
                ]
            }
        }
    
    def simulate(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Simulate a compliance expert's analysis of the query.
        
        Args:
            query: The query text
            context: Optional context including sector, constraints, etc.
            
        Returns:
            Dictionary containing the compliance expert's analysis
        """
        context = context or {}
        sector = context.get("sector", self._identify_sector(query))
        
        # Analyze query to identify compliance concerns
        compliance_concerns = self._identify_compliance_concerns(query)
        
        # Determine applicable standards
        applicable_standards = self._determine_applicable_standards(sector, compliance_concerns)
        
        # Identify verification methods
        verification_methods = self._identify_verification_methods(sector, compliance_concerns)
        
        # Generate documentation recommendations
        documentation_recommendations = self._generate_documentation_recommendations(sector, compliance_concerns)
        
        # Identify compliance risks
        compliance_risks = self._identify_compliance_risks(sector, compliance_concerns)
        
        # Generate compliance guidance
        guidance = self._generate_compliance_guidance(query, sector, applicable_standards, compliance_risks)
        
        # Calculate confidence in the analysis
        confidence = self._calculate_confidence(sector, compliance_concerns, applicable_standards)
        
        # Compile final response
        result = {
            "algorithm": "KA-08",
            "query": query,
            "sector": sector,
            "compliance_concerns": compliance_concerns,
            "applicable_standards": applicable_standards,
            "verification_methods": verification_methods,
            "documentation_recommendations": documentation_recommendations,
            "compliance_risks": compliance_risks,
            "guidance": guidance,
            "confidence": confidence,
            "timestamp": time.time()
        }
        
        return result
    
    def _identify_sector(self, query: str) -> str:
        """
        Identify the sector from the query if not provided.
        
        Args:
            query: The query text
            
        Returns:
            The identified sector
        """
        query_lower = query.lower()
        
        # Sector-specific keywords
        sector_keywords = {
            "finance": ["bank", "financial", "investment", "loan", "credit", "trading", "capital", "fund", "payment"],
            "healthcare": ["health", "medical", "patient", "hospital", "clinical", "care", "provider", "treatment"],
            "technology": ["software", "technology", "data", "digital", "cyber", "cloud", "platform", "application"],
            "manufacturing": ["manufacturing", "production", "assembly", "factory", "quality", "product", "supply chain"],
            "energy": ["energy", "power", "utility", "electricity", "grid", "generation", "renewable", "plant"]
        }
        
        # Count matches for each sector
        sector_scores = {}
        for sector, keywords in sector_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            sector_scores[sector] = score
        
        # Return sector with highest score, or general if no clear match
        max_sector = max(sector_scores.items(), key=lambda x: x[1])
        if max_sector[1] > 0:
            return max_sector[0]
        
        return "general"
    
    def _identify_compliance_concerns(self, query: str) -> List[Dict[str, Any]]:
        """
        Identify compliance concerns from the query.
        
        Args:
            query: The query text
            
        Returns:
            List of identified compliance concerns
        """
        query_lower = query.lower()
        
        # Common compliance concern categories
        concern_categories = {
            "data_protection": ["data protection", "privacy", "GDPR", "personal data", "confidentiality", "data security"],
            "record_keeping": ["record", "documentation", "audit trail", "evidence", "log", "retention"],
            "quality_management": ["quality", "standard", "ISO", "QMS", "process control", "specification"],
            "reporting": ["report", "disclosure", "filing", "submission", "notification", "transparency"],
            "certification": ["certification", "certified", "attestation", "compliance certificate", "accreditation"],
            "audit": ["audit", "inspection", "assessment", "evaluation", "review", "examination"],
            "controls": ["control", "verification", "validation", "check", "testing", "monitoring"]
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
        
        # Check for explicit standard mentions (e.g., "ISO 9001", "SOX 404")
        standard_patterns = [
            r"ISO\s+(\d+)",
            r"SOX\s+[Ss]ection\s+(\d+)",
            r"HIPAA\s+(\d+\.\d+)",
            r"PCI\s+DSS",
            r"SOC\s+[12]",
            r"GDPR",
            r"CCPA"
        ]
        
        for pattern in standard_patterns:
            matches = re.findall(pattern, query)
            if matches:
                identified_concerns.append({
                    "category": "specific_standard",
                    "matches": matches,
                    "relevance": 1.0  # Direct standard mentions are highly relevant
                })
        
        return identified_concerns
    
    def _determine_applicable_standards(self, sector: str, compliance_concerns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Determine standards applicable to the query.
        
        Args:
            sector: The sector context
            compliance_concerns: Identified compliance concerns
            
        Returns:
            List of applicable standards
        """
        # Get sector-specific standards
        sector_standards = []
        if sector in self.compliance_knowledge:
            sector_standards = self.compliance_knowledge[sector].get("standards", [])
        
        # If no sector-specific standards, return empty list
        if not sector_standards:
            return []
        
        # Match standards based on concerns
        applicable_standards = []
        categories = set([concern["category"] for concern in compliance_concerns if "category" in concern])
        
        # Specific standard mentions take priority
        specific_standards = []
        for concern in compliance_concerns:
            if concern["category"] == "specific_standard":
                for match in concern.get("matches", []):
                    for std in sector_standards:
                        if match in std["id"]:
                            specific_standards.append({
                                "id": std["id"],
                                "title": std["title"],
                                "category": std["category"],
                                "relevance": "critical"
                            })
        
        # Include standards that match the concern categories
        for std in sector_standards:
            # Skip if already included as a critical standard
            if any(s["id"] == std["id"] for s in specific_standards):
                continue
                
            if any(category in std["category"].lower() for category in categories):
                applicable_standards.append({
                    "id": std["id"],
                    "title": std["title"],
                    "category": std["category"],
                    "relevance": "high"
                })
            else:
                # Include other sector standards with lower relevance
                applicable_standards.append({
                    "id": std["id"],
                    "title": std["title"],
                    "category": std["category"],
                    "relevance": "medium"
                })
        
        # Combine and sort by relevance
        all_standards = specific_standards + applicable_standards
        relevance_order = {"critical": 0, "high": 1, "medium": 2}
        all_standards.sort(key=lambda x: relevance_order.get(x["relevance"], 3))
        
        return all_standards
    
    def _identify_verification_methods(self, sector: str, compliance_concerns: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Identify relevant verification methods.
        
        Args:
            sector: The sector context
            compliance_concerns: Identified compliance concerns
            
        Returns:
            List of relevant verification methods
        """
        verification_methods = []
        
        if sector in self.compliance_knowledge:
            methods = self.compliance_knowledge[sector].get("verification_methods", [])
            verification_methods = methods.copy()
        
        # Add concern-specific verification methods
        concern_methods = {
            "data_protection": [
                {"name": "Data Protection Impact Assessment", "description": "Systematic evaluation of privacy risks and controls"},
                {"name": "Privacy Audit", "description": "Examination of privacy practices and controls"}
            ],
            "quality_management": [
                {"name": "Process Audit", "description": "Evaluation of process conformance to requirements"},
                {"name": "Management Review", "description": "Formal review by management of system effectiveness"}
            ],
            "controls": [
                {"name": "Control Testing", "description": "Examination of control design and operating effectiveness"},
                {"name": "Compliance Monitoring", "description": "Ongoing verification of adherence to requirements"}
            ]
        }
        
        # Add verification methods based on concerns
        for concern in compliance_concerns:
            category = concern.get("category")
            if category in concern_methods:
                for method in concern_methods[category]:
                    if method not in verification_methods:
                        verification_methods.append(method)
        
        return verification_methods
    
    def _generate_documentation_recommendations(self, sector: str, compliance_concerns: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Generate documentation recommendations.
        
        Args:
            sector: The sector context
            compliance_concerns: Identified compliance concerns
            
        Returns:
            List of documentation recommendations
        """
        recommendations = []
        
        # Sector-specific documentation requirements
        if sector in self.compliance_knowledge:
            sector_docs = self.compliance_knowledge[sector].get("documentation_requirements", [])
            recommendations = [{"type": "sector_specific", "item": doc} for doc in sector_docs]
        
        # Add concern-specific documentation recommendations
        concern_docs = {
            "data_protection": [
                "Data protection impact assessment",
                "Data subject request procedures",
                "Consent management documentation",
                "Data transfer records"
            ],
            "record_keeping": [
                "Records retention schedule",
                "Record classification system",
                "Audit trail logs",
                "Records destruction procedures"
            ],
            "audit": [
                "Audit planning documentation",
                "Audit findings reports",
                "Corrective action plans",
                "Management responses to audit findings"
            ],
            "controls": [
                "Control matrix",
                "Control test plans",
                "Control deficiency remediation plans",
                "Control environment documentation"
            ]
        }
        
        # Add documentation recommendations based on concerns
        for concern in compliance_concerns:
            category = concern.get("category")
            if category in concern_docs:
                for doc in concern_docs[category]:
                    if not any(r["item"] == doc for r in recommendations):
                        recommendations.append({"type": "concern_specific", "item": doc})
        
        # Add general recommendations
        general_docs = [
            "Compliance policies and procedures",
            "Training records",
            "Risk assessment documentation",
            "Management review minutes"
        ]
        
        for doc in general_docs:
            if not any(r["item"] == doc for r in recommendations):
                recommendations.append({"type": "general", "item": doc})
        
        return recommendations
    
    def _identify_compliance_risks(self, sector: str, compliance_concerns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify compliance risks based on sector and concerns.
        
        Args:
            sector: The sector context
            compliance_concerns: Identified compliance concerns
            
        Returns:
            List of compliance risks
        """
        risks = []
        
        # Sector-specific common issues
        if sector in self.compliance_knowledge:
            sector_issues = self.compliance_knowledge[sector].get("common_issues", [])
            risks = [{"description": issue, "source": "sector_common", "severity": "medium"} for issue in sector_issues]
        
        # Add concern-specific risks
        concern_risks = {
            "data_protection": [
                {"description": "Unauthorized access to protected data", "severity": "high"},
                {"description": "Inadequate data subject rights procedures", "severity": "medium"},
                {"description": "Insufficient data protection controls", "severity": "high"}
            ],
            "record_keeping": [
                {"description": "Incomplete or missing records", "severity": "high"},
                {"description": "Inadequate retention of required documentation", "severity": "medium"},
                {"description": "Poor audit trail maintenance", "severity": "medium"}
            ],
            "quality_management": [
                {"description": "Inconsistent process implementation", "severity": "medium"},
                {"description": "Incomplete quality management system", "severity": "medium"},
                {"description": "Inadequate corrective action processes", "severity": "high"}
            ],
            "audit": [
                {"description": "Insufficient audit coverage", "severity": "medium"},
                {"description": "Unaddressed audit findings", "severity": "high"},
                {"description": "Inadequate audit independence", "severity": "medium"}
            ],
            "controls": [
                {"description": "Ineffective controls", "severity": "high"},
                {"description": "Inadequate control monitoring", "severity": "medium"},
                {"description": "Missing key controls", "severity": "high"}
            ]
        }
        
        # Add risks based on concerns
        for concern in compliance_concerns:
            category = concern.get("category")
            if category in concern_risks:
                for risk in concern_risks[category]:
                    risk_copy = risk.copy()
                    risk_copy["source"] = "concern_specific"
                    if not any(r["description"] == risk["description"] for r in risks):
                        risks.append(risk_copy)
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        risks.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return risks
    
    def _generate_compliance_guidance(self, query: str, sector: str, standards: List[Dict[str, Any]], risks: List[Dict[str, Any]]) -> str:
        """
        Generate compliance guidance based on the analysis.
        
        Args:
            query: The query text
            sector: The sector context
            standards: Applicable standards
            risks: Identified compliance risks
            
        Returns:
            Compliance guidance text
        """
        # Structure guidance based on sector and standards
        if not standards and not risks:
            return "No specific compliance guidance available for this query."
        
        # Create a structured guidance response
        guidance = [
            f"Based on a compliance analysis in the {sector} sector, the following guidance is provided:"
        ]
        
        # Add critical standards first
        critical_stds = [s for s in standards if s["relevance"] == "critical"]
        if critical_stds:
            guidance.append("\nCritical Compliance Standards:")
            for std in critical_stds:
                guidance.append(f"- {std['id']}: {std['title']} - This standard directly applies to your query")
        
        # Add high relevance standards
        high_stds = [s for s in standards if s["relevance"] == "high"]
        if high_stds:
            guidance.append("\nPrimary Compliance Standards:")
            for std in high_stds[:3]:  # Limit to top 3
                guidance.append(f"- {std['id']}: {std['title']}")
        
        # Add high severity risks
        high_risks = [r for r in risks if r["severity"] == "high"]
        if high_risks:
            guidance.append("\nKey Compliance Risks:")
            for risk in high_risks[:3]:  # Limit to top 3
                guidance.append(f"- {risk['description']}")
        
        # Add sector-specific guidance
        if sector == "finance":
            guidance.append("\nFinancial Compliance Advisory:")
            guidance.append("- Ensure transparent documentation of all control activities")
            guidance.append("- Maintain evidence of reconciliations and approvals")
            guidance.append("- Consider regulatory reporting timelines in compliance planning")
        
        elif sector == "healthcare":
            guidance.append("\nHealthcare Compliance Advisory:")
            guidance.append("- Implement rigorous access controls for protected health information")
            guidance.append("- Document all privacy and security safeguards")
            guidance.append("- Maintain evidence of required training completion")
        
        elif sector == "technology":
            guidance.append("\nTechnology Compliance Advisory:")
            guidance.append("- Document data flows and processing activities")
            guidance.append("- Implement and record privacy by design considerations")
            guidance.append("- Maintain evidence of security control implementations")
        
        elif sector == "manufacturing":
            guidance.append("\nManufacturing Compliance Advisory:")
            guidance.append("- Document all process validation activities")
            guidance.append("- Maintain calibration records for all measurement equipment")
            guidance.append("- Implement robust nonconformance management procedures")
        
        elif sector == "energy":
            guidance.append("\nEnergy Compliance Advisory:")
            guidance.append("- Document environmental monitoring and testing results")
            guidance.append("- Maintain comprehensive safety procedure documentation")
            guidance.append("- Implement robust emergency response testing and documentation")
        
        # General guidance for all sectors
        guidance.append("\nGeneral Compliance Recommendations:")
        guidance.append("- Implement a comprehensive compliance documentation system")
        guidance.append("- Establish regular compliance monitoring activities")
        guidance.append("- Document all compliance-related decisions and their rationale")
        guidance.append("- Consider independent verification of compliance status")
        
        return "\n".join(guidance)
    
    def _calculate_confidence(self, sector: str, compliance_concerns: List[Dict[str, Any]], standards: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence in the compliance analysis.
        
        Args:
            sector: The sector context
            compliance_concerns: Identified compliance concerns
            standards: Applicable standards
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence
        confidence = 0.5
        
        # Adjust based on sector knowledge
        if sector in self.compliance_knowledge:
            confidence += 0.1
        
        # Adjust based on compliance concerns identified
        if compliance_concerns:
            concern_confidence = min(0.2, len(compliance_concerns) * 0.05)
            confidence += concern_confidence
        
        # Adjust based on standards found
        if standards:
            # Critical standards provide higher confidence
            critical_count = sum(1 for s in standards if s["relevance"] == "critical")
            high_count = sum(1 for s in standards if s["relevance"] == "high")
            
            std_confidence = min(0.2, (critical_count * 0.1) + (high_count * 0.05))
            confidence += std_confidence
        
        # Cap at 0.95
        return min(0.95, confidence)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Compliance Expert Simulation (KA-08) on the provided data.
    
    Args:
        data: A dictionary containing the query and optional context
        
    Returns:
        Dictionary with compliance expert analysis
    """
    query = data.get("query", "")
    context = data.get("context", {})
    
    if not query:
        return {
            "algorithm": "KA-08",
            "error": "No query provided",
            "success": False
        }
    
    simulator = ComplianceExpertSimulation()
    result = simulator.simulate(query, context)
    
    return {
        **result,
        "success": True
    }