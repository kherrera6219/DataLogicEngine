"""
Universal Knowledge Graph (UKG) Database Initialization

This script initializes the UKG database with sample data for testing and development.
"""

import os
import sys
import datetime
import logging
import uuid
from app import app, db
from models import (
    User, APIKey, 
    KnowledgeNode, SectorNode, DomainNode, MethodNode, ContextNode,
    ProblemNode, SolutionNode, RoleNode, ExpertNode, RegulationNode,
    ComplianceNode, LocationNode, TimeNode, Edge,
    KnowledgeAlgorithm, KnowledgeAlgorithmExecution, SimulationSession
)

logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with tables and sample data."""
    # Create tables
    with app.app_context():
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully.")
        
        # Check if database is already initialized
        if User.query.filter_by(username='admin').first():
            logger.info("Database already initialized.")
            return
        
        # Create admin user
        logger.info("Creating admin user...")
        admin_user = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        # Create demo user
        demo_user = User(
            username='demo',
            email='demo@example.com',
            first_name='Demo',
            last_name='User',
            is_admin=False
        )
        demo_user.set_password('demo123')
        db.session.add(demo_user)
        
        # Create API key for admin
        api_key = APIKey(
            key=str(uuid.uuid4()),
            name='Admin API Key',
            description='API key for admin user',
            user=admin_user,
            is_admin=True,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=365)
        )
        db.session.add(api_key)
        
        db.session.commit()
        logger.info(f"Admin API Key: {api_key.key}")
        
        # Create sample nodes for each axis
        logger.info("Creating sample nodes for all 13 axes...")
        
        # Axis 1: Knowledge Nodes
        knowledge_nodes = []
        for i in range(1, 11):
            node = KnowledgeNode(
                label=f"Knowledge {i}",
                axis_number=1,
                description=f"Sample knowledge node {i}",
                title=f"Knowledge Title {i}",
                content=f"This is sample content for knowledge node {i}. It contains information relevant to the Universal Knowledge Graph system.",
                content_type='markdown' if i % 2 == 0 else 'text',
                confidence_score=0.85 + (i / 100),
                source='UKG System'
            )
            db.session.add(node)
            knowledge_nodes.append(node)
        
        # Axis 2: Sector Nodes
        sector_nodes = []
        sector_codes = ['GOV', 'FIN', 'TECH', 'HEALTH', 'EDU', 'MAN', 'INFRA', 'DEF', 'AGRI', 'ENERGY']
        sector_names = ['Government', 'Finance', 'Technology', 'Healthcare', 'Education', 
                      'Manufacturing', 'Infrastructure', 'Defense', 'Agriculture', 'Energy']
        
        for i in range(10):
            node = SectorNode(
                label=sector_names[i],
                axis_number=2,
                description=f"The {sector_names[i]} sector",
                sector_code=sector_codes[i]
            )
            db.session.add(node)
            sector_nodes.append(node)
        
        # Add subsectors
        subsectors = [
            ('FIN-BANK', 'Banking', 'FIN'),
            ('FIN-INS', 'Insurance', 'FIN'),
            ('TECH-SW', 'Software', 'TECH'),
            ('TECH-HW', 'Hardware', 'TECH'),
            ('HEALTH-HOSP', 'Hospitals', 'HEALTH')
        ]
        
        for code, name, parent_code in subsectors:
            parent = next((s for s in sector_nodes if s.sector_code == parent_code), None)
            if parent:
                node = SectorNode(
                    label=name,
                    axis_number=2,
                    description=f"The {name} subsector of {parent.label}",
                    sector_code=code,
                    parent_sector=parent
                )
                db.session.add(node)
                sector_nodes.append(node)
        
        # Axis 3: Domain Nodes
        domain_nodes = []
        domain_codes = ['FEDGOV', 'STATEGOV', 'RETAIL', 'INVBANK', 'CLOUD', 'AI', 'CLINIC', 'K12', 'HIGHER', 'AUTO']
        domain_names = ['Federal Government', 'State Government', 'Retail Banking', 'Investment Banking', 
                       'Cloud Computing', 'Artificial Intelligence', 'Clinical Care', 'K-12 Education', 
                       'Higher Education', 'Automotive Manufacturing']
        
        # Map domains to sectors
        domain_to_sector = {
            'FEDGOV': 'GOV',
            'STATEGOV': 'GOV',
            'RETAIL': 'FIN',
            'INVBANK': 'FIN',
            'CLOUD': 'TECH',
            'AI': 'TECH',
            'CLINIC': 'HEALTH',
            'K12': 'EDU',
            'HIGHER': 'EDU',
            'AUTO': 'MAN'
        }
        
        for i in range(10):
            code = domain_codes[i]
            sector_code = domain_to_sector[code]
            sector = next((s for s in sector_nodes if s.sector_code == sector_code), None)
            
            node = DomainNode(
                label=domain_names[i],
                axis_number=3,
                description=f"The {domain_names[i]} domain",
                domain_code=code,
                sector=sector
            )
            db.session.add(node)
            domain_nodes.append(node)
        
        # Axis 4: Method Nodes
        method_nodes = []
        method_codes = ['AGILE', 'WATERFALL', 'LEAN', 'SIX_SIGMA', 'DEVOPS', 'TQM', 'KANBAN', 'SCRUM', 'XP', 'PRINCE2']
        method_names = ['Agile', 'Waterfall', 'Lean', 'Six Sigma', 'DevOps', 
                       'Total Quality Management', 'Kanban', 'Scrum', 'Extreme Programming', 'PRINCE2']
        
        for i in range(10):
            node = MethodNode(
                label=method_names[i],
                axis_number=4,
                description=f"The {method_names[i]} methodology",
                method_code=method_codes[i]
            )
            db.session.add(node)
            method_nodes.append(node)
        
        # Add submethods
        submethods = [
            ('SCRUM_SPRINT', 'Sprint Planning', 'SCRUM'),
            ('SCRUM_REVIEW', 'Sprint Review', 'SCRUM'),
            ('XP_PAIR', 'Pair Programming', 'XP')
        ]
        
        for code, name, parent_code in submethods:
            parent = next((m for m in method_nodes if m.method_code == parent_code), None)
            if parent:
                node = MethodNode(
                    label=name,
                    axis_number=4,
                    description=f"The {name} technique within {parent.label}",
                    method_code=code,
                    parent_method=parent
                )
                db.session.add(node)
                method_nodes.append(node)
        
        # Axis 5: Context Nodes
        context_nodes = []
        context_types = ['business', 'technical', 'social', 'political', 'economic', 
                        'environmental', 'legal', 'ethical', 'cultural', 'strategic']
        context_labels = ['Business Context', 'Technical Context', 'Social Context', 'Political Context', 
                         'Economic Context', 'Environmental Context', 'Legal Context', 'Ethical Context', 
                         'Cultural Context', 'Strategic Context']
        
        for i in range(10):
            node = ContextNode(
                label=context_labels[i],
                axis_number=5,
                description=f"The {context_labels[i].lower()} within which decisions are made",
                context_type=context_types[i]
            )
            db.session.add(node)
            context_nodes.append(node)
        
        # Axis 6: Problem Nodes
        problem_nodes = []
        problem_types = ['technical', 'business', 'compliance', 'security', 'performance', 
                        'scalability', 'usability', 'integration', 'maintenance', 'documentation']
        problem_labels = ['Technical Issue', 'Business Challenge', 'Compliance Gap', 'Security Vulnerability', 
                         'Performance Bottleneck', 'Scalability Limitation', 'Usability Problem', 
                         'Integration Issue', 'Maintenance Burden', 'Documentation Gap']
        
        for i in range(10):
            node = ProblemNode(
                label=problem_labels[i],
                axis_number=6,
                description=f"A {problem_types[i]} problem that needs to be addressed",
                problem_type=problem_types[i],
                severity=(i % 5) + 1  # Severity from 1-5
            )
            db.session.add(node)
            problem_nodes.append(node)
        
        # Axis 7: Solution Nodes
        solution_nodes = []
        solution_types = ['technical', 'business', 'compliance', 'security', 'performance', 
                         'scalability', 'usability', 'integration', 'maintenance', 'documentation']
        solution_labels = ['Technical Solution', 'Business Strategy', 'Compliance Framework', 
                          'Security Architecture', 'Performance Optimization', 'Scalability Strategy', 
                          'Usability Improvement', 'Integration Pattern', 'Maintenance Approach', 
                          'Documentation Standard']
        
        for i in range(10):
            node = SolutionNode(
                label=solution_labels[i],
                axis_number=7,
                description=f"A {solution_types[i]} solution to address related problems",
                solution_type=solution_types[i],
                effectiveness=0.7 + (i / 30)  # Effectiveness from 0.7 to 1.0
            )
            db.session.add(node)
            solution_nodes.append(node)
        
        # Axis 8: Role Nodes
        role_nodes = []
        role_codes = ['CEO', 'CTO', 'CFO', 'CISO', 'PM', 'DEV', 'QA', 'BA', 'ARCH', 'DBA']
        role_labels = ['Chief Executive Officer', 'Chief Technology Officer', 'Chief Financial Officer', 
                      'Chief Information Security Officer', 'Project Manager', 'Developer', 
                      'Quality Assurance', 'Business Analyst', 'Solutions Architect', 'Database Administrator']
        
        for i in range(10):
            node = RoleNode(
                label=role_labels[i],
                axis_number=8,
                description=f"The {role_labels[i]} role within an organization",
                role_code=role_codes[i],
                responsibilities=f"Key responsibilities for {role_labels[i]} include strategic planning, leadership, and decision-making appropriate to the role."
            )
            db.session.add(node)
            role_nodes.append(node)
        
        # Axis 9: Expert Nodes
        expert_nodes = []
        expertise_areas = [
            'Artificial Intelligence',
            'Cloud Architecture',
            'Cybersecurity',
            'Data Science',
            'DevOps',
            'Enterprise Architecture',
            'Financial Regulations',
            'Healthcare IT',
            'Software Engineering',
            'Systems Integration'
        ]
        
        for i in range(10):
            node = ExpertNode(
                label=f"{expertise_areas[i]} Expert",
                axis_number=9,
                description=f"An expert in {expertise_areas[i]}",
                expertise_areas=expertise_areas[i],
                expertise_level=0.8 + (i / 50),  # Expertise level from 0.8 to 1.0
                certifications=f"Certified in {expertise_areas[i]}",
                education="Master's Degree in Computer Science"
            )
            db.session.add(node)
            expert_nodes.append(node)
        
        # Axis 10: Regulation Nodes
        regulation_nodes = []
        reg_codes = ['GDPR', 'HIPAA', 'PCI_DSS', 'SOX', 'CCPA', 'FISMA', 'FERPA', 'BASEL_III', 'NIST_800_53', 'ISO_27001']
        reg_names = ['General Data Protection Regulation', 'Health Insurance Portability and Accountability Act', 
                    'Payment Card Industry Data Security Standard', 'Sarbanes-Oxley Act', 
                    'California Consumer Privacy Act', 'Federal Information Security Management Act', 
                    'Family Educational Rights and Privacy Act', 'Basel III', 
                    'NIST Special Publication 800-53', 'ISO/IEC 27001']
        
        for i in range(10):
            node = RegulationNode(
                label=reg_names[i],
                axis_number=10,
                description=f"The {reg_names[i]} regulation",
                regulation_code=reg_codes[i],
                issuing_authority='European Union' if i == 0 else 'US Government' if i < 7 else 'International Standards',
                effective_date=datetime.datetime(2018, 5, 25) if i == 0 else datetime.datetime(2020, 1, 1),
                text=f"This is sample regulatory text for {reg_names[i]}."
            )
            db.session.add(node)
            regulation_nodes.append(node)
        
        # Axis 11: Compliance Nodes
        compliance_nodes = []
        compliance_types = ['data_privacy', 'financial', 'security', 'healthcare', 'environmental', 
                           'labor', 'accessibility', 'trade', 'tax', 'antitrust']
        compliance_labels = ['Data Privacy Compliance', 'Financial Compliance', 'Security Compliance', 
                            'Healthcare Compliance', 'Environmental Compliance', 'Labor Compliance', 
                            'Accessibility Compliance', 'Trade Compliance', 'Tax Compliance', 'Antitrust Compliance']
        
        for i in range(10):
            reg_node = regulation_nodes[i % len(regulation_nodes)]
            node = ComplianceNode(
                label=compliance_labels[i],
                axis_number=11,
                description=f"Compliance requirements for {compliance_labels[i].lower()}",
                compliance_type=compliance_types[i],
                regulation=reg_node,
                status='compliant' if i % 3 == 0 else 'in-progress' if i % 3 == 1 else 'non-compliant',
                due_date=datetime.datetime.utcnow() + datetime.timedelta(days=90)
            )
            db.session.add(node)
            compliance_nodes.append(node)
        
        # Axis 12: Location Nodes
        location_nodes = []
        location_types = ['country', 'country', 'country', 'city', 'city', 
                         'city', 'region', 'region', 'virtual', 'virtual']
        location_labels = ['United States', 'European Union', 'Japan', 'New York', 'London', 
                          'Tokyo', 'West Coast', 'EMEA', 'Cloud Environment', 'Virtual Office']
        
        # Coordinates for physical locations (approximate)
        coordinates = [
            (37.0902, -95.7129),  # US
            (50.8503, 4.3517),    # EU
            (36.2048, 138.2529),  # Japan
            (40.7128, -74.0060),  # New York
            (51.5074, -0.1278),   # London
            (35.6762, 139.6503),  # Tokyo
            (37.7749, -122.4194), # West Coast (SF)
            (48.8566, 2.3522),    # EMEA (Paris)
            (None, None),         # Cloud - no physical location
            (None, None),         # Virtual Office - no physical location
        ]
        
        for i in range(10):
            lat, lon = coordinates[i]
            node = LocationNode(
                label=location_labels[i],
                axis_number=12,
                description=f"The {location_labels[i]} location",
                location_type=location_types[i],
                latitude=lat,
                longitude=lon
            )
            db.session.add(node)
            location_nodes.append(node)
        
        # Create parent-child relationships for locations
        city_to_country = {
            'New York': 'United States',
            'London': 'European Union',
            'Tokyo': 'Japan'
        }
        
        for node in location_nodes:
            if node.location_type == 'city':
                parent_label = city_to_country.get(node.label)
                if parent_label:
                    parent = next((l for l in location_nodes if l.label == parent_label), None)
                    if parent:
                        node.parent_location = parent
        
        # Axis 13: Time Nodes
        time_nodes = []
        time_types = ['historical', 'historical', 'current', 'current', 'future', 
                     'future', 'recurring', 'recurring', 'project', 'career_stage']
        time_labels = ['Past Decade', 'Early 2000s', 'Current Quarter', 'Current Year', 
                      'Next Quarter', 'Five Year Plan', 'Annual Review', 'Quarterly Reporting', 
                      'Project Timeline', 'Career Progression']
        
        # Set start and end dates
        now = datetime.datetime.utcnow()
        time_ranges = [
            (now - datetime.timedelta(days=3650), now - datetime.timedelta(days=1)),  # Past Decade
            (datetime.datetime(2000, 1, 1), datetime.datetime(2010, 12, 31)),        # Early 2000s
            (now - datetime.timedelta(days=90), now + datetime.timedelta(days=1)),    # Current Quarter
            (datetime.datetime(now.year, 1, 1), datetime.datetime(now.year, 12, 31)), # Current Year
            (now + datetime.timedelta(days=1), now + datetime.timedelta(days=90)),    # Next Quarter
            (now, now + datetime.timedelta(days=1825)),                              # Five Year Plan
            (datetime.datetime(now.year, 1, 1), datetime.datetime(now.year, 12, 31)), # Annual Review (recurring)
            (now - datetime.timedelta(days=90), now),                                # Quarterly Reporting (recurring)
            (now, now + datetime.timedelta(days=365)),                               # Project Timeline
            (now - datetime.timedelta(days=3650), now + datetime.timedelta(days=3650)) # Career Progression
        ]
        
        for i in range(10):
            start_date, end_date = time_ranges[i]
            recurring = time_types[i] == 'recurring'
            granularity = 'year' if i == 0 or i == 1 else 'day' if i == 8 else 'quarter' if i == 2 or i == 4 or i == 7 else 'month'
            
            node = TimeNode(
                label=time_labels[i],
                axis_number=13,
                description=f"Time context: {time_labels[i]}",
                time_type=time_types[i],
                start_date=start_date,
                end_date=end_date,
                granularity=granularity,
                recurring=recurring
            )
            db.session.add(node)
            time_nodes.append(node)
        
        # Create edges between nodes to form the knowledge graph
        logger.info("Creating edges between nodes...")
        
        # Connect knowledge nodes to sectors
        for i in range(min(len(knowledge_nodes), len(sector_nodes))):
            edge = Edge(
                edge_type='knowledge_to_sector',
                label='relates to',
                source_node=knowledge_nodes[i],
                target_node=sector_nodes[i],
                weight=0.85
            )
            db.session.add(edge)
        
        # Connect sectors to domains
        for domain_node in domain_nodes:
            if domain_node.sector:
                edge = Edge(
                    edge_type='sector_to_domain',
                    label='contains',
                    source_node=domain_node.sector,
                    target_node=domain_node,
                    weight=1.0
                )
                db.session.add(edge)
        
        # Connect domains to methods
        for i in range(min(len(domain_nodes), len(method_nodes))):
            edge = Edge(
                edge_type='domain_to_method',
                label='uses',
                source_node=domain_nodes[i],
                target_node=method_nodes[i],
                weight=0.75
            )
            db.session.add(edge)
        
        # Connect problems to solutions
        for i in range(min(len(problem_nodes), len(solution_nodes))):
            edge = Edge(
                edge_type='problem_to_solution',
                label='resolved by',
                source_node=problem_nodes[i],
                target_node=solution_nodes[i],
                weight=0.9
            )
            db.session.add(edge)
        
        # Connect roles to experts
        for i in range(min(len(role_nodes), len(expert_nodes))):
            edge = Edge(
                edge_type='role_to_expert',
                label='filled by',
                source_node=role_nodes[i],
                target_node=expert_nodes[i],
                weight=0.8
            )
            db.session.add(edge)
        
        # Connect regulations to compliance
        for compliance_node in compliance_nodes:
            if compliance_node.regulation:
                edge = Edge(
                    edge_type='regulation_to_compliance',
                    label='requires',
                    source_node=compliance_node.regulation,
                    target_node=compliance_node,
                    weight=1.0
                )
                db.session.add(edge)
        
        # Connect domains to locations
        for i in range(min(len(domain_nodes), len(location_nodes))):
            edge = Edge(
                edge_type='domain_to_location',
                label='located in',
                source_node=domain_nodes[i],
                target_node=location_nodes[i],
                weight=0.7
            )
            db.session.add(edge)
        
        # Connect nodes to time contexts
        # Knowledge evolves over time
        for i, knowledge_node in enumerate(knowledge_nodes):
            time_node = time_nodes[i % len(time_nodes)]
            edge = Edge(
                edge_type='knowledge_to_time',
                label='relevant during',
                source_node=knowledge_node,
                target_node=time_node,
                weight=0.8
            )
            db.session.add(edge)
        
        # Regulations are effective during specific time periods
        for i, regulation_node in enumerate(regulation_nodes):
            time_node = time_nodes[i % len(time_nodes)]
            edge = Edge(
                edge_type='regulation_to_time',
                label='effective during',
                source_node=regulation_node,
                target_node=time_node,
                weight=1.0
            )
            db.session.add(edge)
        
        # Create a few sample knowledge algorithms
        logger.info("Creating sample knowledge algorithms...")
        
        algorithm1 = KnowledgeAlgorithm(
            algorithm_id='KA-01',
            name='Knowledge Graph Traversal',
            description='Traverses the knowledge graph to find paths between concepts',
            version='1.0.0',
            code='''
def traverse_graph(start_node_id, end_node_id, max_depth=5):
    """
    Traverse the knowledge graph to find paths between concepts.
    
    Args:
        start_node_id: The ID of the starting node
        end_node_id: The ID of the target node
        max_depth: Maximum traversal depth
        
    Returns:
        List of paths between the nodes
    """
    # Implementation would go here
    return {'paths': [['node1', 'node2', 'node3']]}
''',
            language='python',
            input_schema={
                'type': 'object',
                'properties': {
                    'start_node_id': {'type': 'string'},
                    'end_node_id': {'type': 'string'},
                    'max_depth': {'type': 'integer', 'default': 5}
                },
                'required': ['start_node_id', 'end_node_id']
            },
            output_schema={
                'type': 'object',
                'properties': {
                    'paths': {
                        'type': 'array',
                        'items': {
                            'type': 'array',
                            'items': {'type': 'string'}
                        }
                    }
                }
            }
        )
        db.session.add(algorithm1)
        
        algorithm2 = KnowledgeAlgorithm(
            algorithm_id='KA-02',
            name='Confidence Aggregation',
            description='Aggregates confidence scores across multiple knowledge nodes',
            version='1.0.0',
            code='''
def aggregate_confidence(node_ids, method='weighted_average'):
    """
    Aggregate confidence scores across multiple knowledge nodes.
    
    Args:
        node_ids: List of node IDs to aggregate
        method: Aggregation method (weighted_average, min, max)
        
    Returns:
        Aggregated confidence score
    """
    # Implementation would go here
    return {'confidence': 0.92, 'method': method}
''',
            language='python',
            input_schema={
                'type': 'object',
                'properties': {
                    'node_ids': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    },
                    'method': {
                        'type': 'string',
                        'enum': ['weighted_average', 'min', 'max'],
                        'default': 'weighted_average'
                    }
                },
                'required': ['node_ids']
            },
            output_schema={
                'type': 'object',
                'properties': {
                    'confidence': {'type': 'number'},
                    'method': {'type': 'string'}
                }
            }
        )
        db.session.add(algorithm2)
        
        # Create sample algorithm executions
        execution1 = KnowledgeAlgorithmExecution(
            algorithm=algorithm1,
            user=admin_user,
            status='completed',
            input_params={
                'start_node_id': knowledge_nodes[0].uid,
                'end_node_id': knowledge_nodes[5].uid,
                'max_depth': 3
            },
            output_results={
                'paths': [
                    [knowledge_nodes[0].uid, sector_nodes[0].uid, domain_nodes[0].uid, knowledge_nodes[5].uid],
                    [knowledge_nodes[0].uid, method_nodes[0].uid, knowledge_nodes[5].uid]
                ]
            },
            started_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2),
            completed_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2, minutes=1),
            execution_time=65.2  # seconds
        )
        db.session.add(execution1)
        
        # Create sample simulation session
        simulation1 = SimulationSession(
            session_id=str(uuid.uuid4()),
            name='Sample Simulation',
            user=admin_user,
            parameters={
                'query': 'What are the compliance requirements for financial institutions?',
                'confidenceThreshold': 0.85,
                'maxLayer': 5,
                'refinementSteps': 8
            },
            status='completed',
            current_step=8,
            total_steps=8,
            results={
                'response': 'Financial institutions must comply with regulations such as PCI DSS for payment data, SOX for financial reporting, and GDPR or CCPA for customer data privacy. Compliance requires data protection measures, security controls, and regular audits.',
                'confidenceScore': 0.92,
                'activeLayer': 4,
                'insightsGenerated': [
                    {'type': 'regulatory', 'text': 'PCI DSS compliance is mandatory for handling payment data.'},
                    {'type': 'sector', 'text': 'Financial institutions face the most stringent regulatory requirements.'},
                    {'type': 'compliance', 'text': 'Regular security audits are required across all financial data systems.'}
                ]
            },
            started_at=datetime.datetime.utcnow() - datetime.timedelta(days=1),
            last_step_at=datetime.datetime.utcnow() - datetime.timedelta(days=1, minutes=5),
            completed_at=datetime.datetime.utcnow() - datetime.timedelta(days=1, minutes=5)
        )
        db.session.add(simulation1)
        
        # Commit all changes
        db.session.commit()
        logger.info("Database initialized successfully with sample data.")

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        init_db()
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        sys.exit(1)