
#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) System - Data Generator

This module generates sample data for the UKG 13-axis system.
"""

import logging
import random
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def generate_pillar_levels():
    """Generate data for Axis 1: Pillar Levels."""
    return [
        {
            "label": "Universal",
            "level": 1,
            "description": "Universal principles and concepts at the highest abstraction level"
        },
        {
            "label": "Conceptual",
            "level": 2,
            "description": "Broad conceptual frameworks and theoretical constructs"
        },
        {
            "label": "Domain",
            "level": 3,
            "description": "Specific knowledge domains and disciplines"
        },
        {
            "label": "Applied",
            "level": 4,
            "description": "Applied knowledge in specific contexts"
        },
        {
            "label": "Implementation",
            "level": 5,
            "description": "Specific implementations, instances, and concrete applications"
        }
    ]

def generate_sectors():
    """Generate data for Axis 2: Sectors."""
    return [
        {
            "label": "Technology",
            "level": 1,
            "description": "Information technology, software, hardware, and digital systems"
        },
        {
            "label": "Healthcare",
            "level": 1,
            "description": "Medical services, health systems, and patient care"
        },
        {
            "label": "Finance",
            "level": 1,
            "description": "Banking, investment, insurance, and financial services"
        },
        {
            "label": "Education",
            "level": 1,
            "description": "Academic institutions, learning systems, and educational services"
        },
        {
            "label": "Government",
            "level": 1,
            "description": "Public administration, policy, and governance"
        },
        {
            "label": "Manufacturing",
            "level": 1,
            "description": "Production, industrial processes, and manufacturing systems"
        }
    ]

def generate_topics():
    """Generate data for Axis 3: Topics."""
    return [
        {
            "label": "Artificial Intelligence",
            "level": 1,
            "description": "Study and development of computer systems that mimic human intelligence",
            "attributes": {"sector": "Technology"}
        },
        {
            "label": "Cybersecurity",
            "level": 1,
            "description": "Protection of computer systems and networks from information disclosure",
            "attributes": {"sector": "Technology"}
        },
        {
            "label": "Patient Care",
            "level": 1,
            "description": "Medical treatment and care of patients in healthcare settings",
            "attributes": {"sector": "Healthcare"}
        },
        {
            "label": "Investment Banking",
            "level": 1,
            "description": "Financial services for raising capital and providing advisory services",
            "attributes": {"sector": "Finance"}
        },
        {
            "label": "Higher Education",
            "level": 1,
            "description": "Post-secondary education in colleges and universities",
            "attributes": {"sector": "Education"}
        }
    ]

def generate_methods():
    """Generate data for Axis 4: Methods."""
    return [
        {
            "label": "Machine Learning",
            "level": 1,
            "description": "Algorithms and statistical models for computer systems to perform tasks",
            "attributes": {"topics": ["Artificial Intelligence"]}
        },
        {
            "label": "Network Security Analysis",
            "level": 1,
            "description": "Analysis of networks for vulnerabilities and security issues",
            "attributes": {"topics": ["Cybersecurity"]}
        },
        {
            "label": "Patient-Centered Care",
            "level": 1,
            "description": "Approach to healthcare focusing on individual patient needs",
            "attributes": {"topics": ["Patient Care"]}
        },
        {
            "label": "Financial Modeling",
            "level": 1,
            "description": "Creating abstract representations of financial situations",
            "attributes": {"topics": ["Investment Banking"]}
        },
        {
            "label": "Active Learning",
            "level": 1,
            "description": "Educational approach emphasizing student engagement",
            "attributes": {"topics": ["Higher Education"]}
        }
    ]

def generate_tools():
    """Generate data for Axis 5: Tools."""
    return [
        {
            "label": "TensorFlow",
            "level": 1,
            "description": "Open-source machine learning framework",
            "attributes": {"methods": ["Machine Learning"]}
        },
        {
            "label": "Wireshark",
            "level": 1,
            "description": "Network protocol analyzer for security testing",
            "attributes": {"methods": ["Network Security Analysis"]}
        },
        {
            "label": "Electronic Health Records",
            "level": 1,
            "description": "Digital version of patients' paper charts in healthcare settings",
            "attributes": {"methods": ["Patient-Centered Care"]}
        },
        {
            "label": "Bloomberg Terminal",
            "level": 1,
            "description": "Financial software system providing financial data",
            "attributes": {"methods": ["Financial Modeling"]}
        },
        {
            "label": "Learning Management Systems",
            "level": 1,
            "description": "Software applications for administration and delivery of educational courses",
            "attributes": {"methods": ["Active Learning"]}
        }
    ]

def generate_regulatory_frameworks():
    """Generate data for Axis 6: Regulatory Frameworks."""
    return [
        {
            "label": "GDPR",
            "level": 1,
            "description": "General Data Protection Regulation for data protection in EU",
            "attributes": {"sectors": ["Technology", "Healthcare", "Finance"]}
        },
        {
            "label": "HIPAA",
            "level": 1,
            "description": "Health Insurance Portability and Accountability Act for healthcare data",
            "attributes": {"sectors": ["Healthcare"]}
        },
        {
            "label": "Basel III",
            "level": 1,
            "description": "Global regulatory framework for bank capital adequacy and stress testing",
            "attributes": {"sectors": ["Finance"]}
        },
        {
            "label": "FERPA",
            "level": 1,
            "description": "Family Educational Rights and Privacy Act for educational records",
            "attributes": {"sectors": ["Education"]}
        },
        {
            "label": "FAR",
            "level": 1,
            "description": "Federal Acquisition Regulation for government procurement",
            "attributes": {"sectors": ["Government"]}
        }
    ]

def generate_compliance_standards():
    """Generate data for Axis 7: Compliance Standards."""
    return [
        {
            "label": "ISO 27001",
            "level": 1,
            "description": "Information security management standard",
            "attributes": {"frameworks": ["GDPR"]}
        },
        {
            "label": "HITRUST CSF",
            "level": 1,
            "description": "Health Information Trust Alliance Common Security Framework",
            "attributes": {"frameworks": ["HIPAA"]}
        },
        {
            "label": "PCI DSS",
            "level": 1,
            "description": "Payment Card Industry Data Security Standard",
            "attributes": {"frameworks": ["Basel III"]}
        },
        {
            "label": "SOC 2",
            "level": 1,
            "description": "Service Organization Control 2 for data security",
            "attributes": {"frameworks": ["GDPR", "HIPAA"]}
        },
        {
            "label": "NIST SP 800-53",
            "level": 1,
            "description": "Security controls for federal information systems",
            "attributes": {"frameworks": ["FAR"]}
        }
    ]

def generate_personas():
    """Generate data for Axes 8-11: Personas."""
    return {
        8: [  # Knowledge Expert
            {
                "label": "AI Research Scientist",
                "level": 1,
                "description": "Expert in artificial intelligence research and development",
                "attributes": {"topics": ["Artificial Intelligence"]}
            },
            {
                "label": "Cybersecurity Analyst",
                "level": 1,
                "description": "Expert in analyzing and preventing cybersecurity threats",
                "attributes": {"topics": ["Cybersecurity"]}
            }
        ],
        9: [  # Sector Expert
            {
                "label": "Healthcare Administrator",
                "level": 1,
                "description": "Expert in healthcare management and operations",
                "attributes": {"sectors": ["Healthcare"]}
            },
            {
                "label": "Investment Banker",
                "level": 1,
                "description": "Expert in financial investments and capital markets",
                "attributes": {"sectors": ["Finance"]}
            }
        ],
        10: [  # Regulatory Expert
            {
                "label": "Data Protection Officer",
                "level": 1,
                "description": "Expert in data protection regulations like GDPR",
                "attributes": {"frameworks": ["GDPR"]}
            },
            {
                "label": "Healthcare Compliance Officer",
                "level": 1,
                "description": "Expert in healthcare regulations like HIPAA",
                "attributes": {"frameworks": ["HIPAA"]}
            }
        ],
        11: [  # Compliance Expert
            {
                "label": "Information Security Auditor",
                "level": 1,
                "description": "Expert in auditing information security compliance",
                "attributes": {"standards": ["ISO 27001", "SOC 2"]}
            },
            {
                "label": "Financial Compliance Specialist",
                "level": 1,
                "description": "Expert in financial compliance standards",
                "attributes": {"standards": ["PCI DSS"]}
            }
        ]
    }

def generate_locations():
    """Generate data for Axis 12: Locations."""
    return [
        {
            "label": "European Union",
            "level": 1,
            "description": "Political and economic union of 27 member states in Europe",
            "attributes": {"frameworks": ["GDPR"]}
        },
        {
            "label": "United States",
            "level": 1,
            "description": "Federal republic of 50 states in North America",
            "attributes": {"frameworks": ["HIPAA", "FERPA", "FAR"]}
        },
        {
            "label": "Global",
            "level": 1,
            "description": "Worldwide context covering all regions",
            "attributes": {"frameworks": ["Basel III"]}
        }
    ]

def generate_time_periods():
    """Generate data for Axis 13: Time."""
    return [
        {
            "label": "Current",
            "level": 1,
            "description": "Present time period (2020s)",
            "attributes": {"frameworks": ["GDPR", "HIPAA", "Basel III", "FERPA", "FAR"]}
        },
        {
            "label": "Pre-GDPR Era",
            "level": 1,
            "description": "Period before GDPR implementation (before 2018)",
            "attributes": {"frameworks": ["HIPAA", "Basel III", "FERPA", "FAR"]}
        },
        {
            "label": "Future Compliance",
            "level": 1,
            "description": "Anticipated future regulatory environment",
            "attributes": {"evolution": "predicted"}
        }
    ]

def generate_all_axis_data():
    """Generate sample data for all 13 axes."""
    return {
        1: generate_pillar_levels(),
        2: generate_sectors(),
        3: generate_topics(),
        4: generate_methods(),
        5: generate_tools(),
        6: generate_regulatory_frameworks(),
        7: generate_compliance_standards(),
        8: generate_personas()[8],
        9: generate_personas()[9],
        10: generate_personas()[10],
        11: generate_personas()[11],
        12: generate_locations(),
        13: generate_time_periods()
    }

def generate_relationships(nodes_by_axis):
    """
    Generate relationships between nodes.
    
    Args:
        nodes_by_axis: Dictionary of nodes indexed by axis
        
    Returns:
        List of relationship dictionaries
    """
    relationships = []
    
    # Connect pillar levels hierarchically (Axis 1)
    for i in range(len(nodes_by_axis[1]) - 1):
        parent = nodes_by_axis[1][i]
        child = nodes_by_axis[1][i + 1]
        relationships.append({
            "source_id": parent["node_id"],
            "target_id": child["node_id"],
            "rel_type": "contains",
            "weight": 0.9,
            "attributes": {"hierarchical": True}
        })
    
    # Connect sectors to topics (Axis 2 -> Axis 3)
    for sector in nodes_by_axis[2]:
        sector_name = sector["label"].lower()
        for topic in nodes_by_axis[3]:
            if "sector" in topic.get("attributes", {}) and topic["attributes"]["sector"].lower() == sector_name:
                relationships.append({
                    "source_id": sector["node_id"],
                    "target_id": topic["node_id"],
                    "rel_type": "contains",
                    "weight": 0.8,
                    "attributes": {}
                })
    
    # Connect topics to methods (Axis 3 -> Axis 4)
    for topic in nodes_by_axis[3]:
        topic_name = topic["label"]
        for method in nodes_by_axis[4]:
            if "topics" in method.get("attributes", {}) and topic_name in method["attributes"]["topics"]:
                relationships.append({
                    "source_id": topic["node_id"],
                    "target_id": method["node_id"],
                    "rel_type": "uses",
                    "weight": 0.7,
                    "attributes": {}
                })
    
    # Connect methods to tools (Axis 4 -> Axis 5)
    for method in nodes_by_axis[4]:
        method_name = method["label"]
        for tool in nodes_by_axis[5]:
            if "methods" in tool.get("attributes", {}) and method_name in tool["attributes"]["methods"]:
                relationships.append({
                    "source_id": method["node_id"],
                    "target_id": tool["node_id"],
                    "rel_type": "employs",
                    "weight": 0.7,
                    "attributes": {}
                })
    
    # Connect regulatory frameworks to compliance standards (Axis 6 -> Axis 7)
    for framework in nodes_by_axis[6]:
        framework_name = framework["label"]
        for standard in nodes_by_axis[7]:
            if "frameworks" in standard.get("attributes", {}) and framework_name in standard["attributes"]["frameworks"]:
                relationships.append({
                    "source_id": framework["node_id"],
                    "target_id": standard["node_id"],
                    "rel_type": "enforces",
                    "weight": 0.9,
                    "attributes": {}
                })
    
    # Connect quad persona cycle (Axes 8-11)
    persona_axis_order = [8, 9, 10, 11, 8]  # Complete cycle
    for i in range(len(persona_axis_order) - 1):
        source_axis = persona_axis_order[i]
        target_axis = persona_axis_order[i + 1]
        
        for source_persona in nodes_by_axis[source_axis]:
            for target_persona in nodes_by_axis[target_axis]:
                relationships.append({
                    "source_id": source_persona["node_id"],
                    "target_id": target_persona["node_id"],
                    "rel_type": "informs",
                    "weight": 0.8,
                    "attributes": {"quad_persona_cycle": True}
                })
    
    # Connect regulatory frameworks to locations (Axis 6 -> Axis 12)
    for framework in nodes_by_axis[6]:
        framework_name = framework["label"]
        for location in nodes_by_axis[12]:
            if "frameworks" in location.get("attributes", {}) and framework_name in location["attributes"]["frameworks"]:
                relationships.append({
                    "source_id": framework["node_id"],
                    "target_id": location["node_id"],
                    "rel_type": "applies_in",
                    "weight": 0.7,
                    "attributes": {}
                })
    
    # Connect time periods to regulatory frameworks (Axis 13 -> Axis 6)
    for time_period in nodes_by_axis[13]:
        if "frameworks" in time_period.get("attributes", {}):
            for framework_name in time_period["attributes"]["frameworks"]:
                for framework in nodes_by_axis[6]:
                    if framework["label"] == framework_name:
                        relationships.append({
                            "source_id": time_period["node_id"],
                            "target_id": framework["node_id"],
                            "rel_type": "contains",
                            "weight": 0.7,
                            "attributes": {"temporal": True}
                        })
    
    # Add some random connections to make the graph more interesting
    for _ in range(20):
        source_axis = random.randint(1, 13)
        target_axis = random.randint(1, 13)
        
        if not nodes_by_axis[source_axis] or not nodes_by_axis[target_axis]:
            continue
            
        source = random.choice(nodes_by_axis[source_axis])
        target = random.choice(nodes_by_axis[target_axis])
        
        if source["node_id"] == target["node_id"]:
            continue
            
        rel_types = ["relates_to", "influences", "associated_with", "connected_to"]
        
        relationships.append({
            "source_id": source["node_id"],
            "target_id": target["node_id"],
            "rel_type": random.choice(rel_types),
            "weight": random.uniform(0.5, 0.9),
            "attributes": {"generated": True}
        })
    
    return relationships
