"""
Universal Knowledge Graph (UKG) System - Simple Demo App

This file creates a simplified Flask app for demonstrating the Quad Persona system.
It avoids the complexities of the main app while keeping the core functionality.
"""

import os
import logging
from flask import Flask, render_template, jsonify, request, redirect, url_for

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create app
app = Flask(__name__)
# Security: Get secret key from environment
if os.environ.get('FLASK_ENV') == 'development':
    app.secret_key = os.environ.get("SECRET_KEY", "dev-simple-app-key-for-local-development-only")
else:
    app.secret_key = os.environ.get("SECRET_KEY")
    if not app.secret_key:
        raise ValueError("SECRET_KEY environment variable must be set for production!")

# Import quad persona components for direct implementation
try:
    from quad_persona.quad_engine import create_quad_persona_engine
    from simulation.simulation_engine import create_simulation_engine
    
    # Initialize engines
    quad_engine = create_quad_persona_engine()
    simulation_engine = create_simulation_engine()
    
    QUAD_PERSONA_AVAILABLE = True
    logger.info("Quad Persona Engine initialized successfully")
except ImportError as e:
    logger.warning(f"Quad Persona Engine import failed: {str(e)}")
    QUAD_PERSONA_AVAILABLE = False

# Routes
@app.route('/')
def home():
    """Render the home page."""
    return redirect(url_for('persona_demo'))

@app.route('/persona-demo')
def persona_demo():
    """Render the quad persona engine demo page."""
    return render_template('persona_demo.html', title="Quad Persona Engine Demo - Universal Knowledge Graph")

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "online",
        "system": "UKG Quad Persona Demo",
        "version": "1.0.0",
        "quad_persona_available": QUAD_PERSONA_AVAILABLE
    })

@app.route('/api/persona/query', methods=['POST'])
def process_query():
    """
    Process a query through the Quad Persona Engine.
    
    Expected JSON payload:
    {
        "query": "The query text to process",
        "context": {
            "domain": "optional_domain",
            "persona_weights": {...}
        }
    }
    """
    data = request.json
    if not data or 'query' not in data:
        return jsonify({
            'error': 'Invalid request format, query is required'
        }), 400
    
    query = data['query']
    context = data.get('context', {})
    
    try:
        if QUAD_PERSONA_AVAILABLE:
            # Process the query with the simulation engine
            result = simulation_engine.process_query(query, context)
            return jsonify(result)
        else:
            # Simulate response if engine not available
            return generate_simulated_response(query, context)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({
            'error': 'Failed to process query',
            'details': str(e)
        }), 500

def generate_simulated_response(query, context):
    """Generate a simulated response when the quad persona engine is not available."""
    domain = context.get('domain', 'general')
    weights = context.get('persona_weights', {
        'knowledge': 0.25,
        'sector': 0.25,
        'regulatory': 0.25,
        'compliance': 0.25
    })
    
    # Calculate simulated processing time based on query complexity
    processing_time = 500 + (len(query) * 5)
    
    # Generate persona responses
    knowledge_result = {
        "response": f"As a Knowledge Expert, I can provide the following insights: This query relates to fundamental concepts in {domain} domains. The academic literature suggests multiple approaches to understanding this topic, with varying levels of empirical support and theoretical grounding.",
        "confidence": 0.7 + (weights.get('knowledge', 0.25) * 0.2),
        "persona_name": "Knowledge Expert"
    }
    
    sector_result = {
        "response": f"From a sector perspective, I observe that: Industry trends in the {domain} sector indicate evolving practices in this area. Market leaders are adopting innovative approaches, with regulatory and competitive factors driving adoption.",
        "confidence": 0.7 + (weights.get('sector', 0.25) * 0.2),
        "persona_name": "Sector Expert"
    }
    
    regulatory_result = {
        "response": f"As a Regulatory Expert analyzing the regulatory landscape, I can state that: The regulatory environment surrounding this topic in {domain} is complex and multi-layered. Compliance requirements vary by jurisdiction, with some regions implementing more stringent standards than others.",
        "confidence": 0.7 + (weights.get('regulatory', 0.25) * 0.2),
        "persona_name": "Regulatory Expert"
    }
    
    compliance_result = {
        "response": f"Speaking as a Compliance Expert with a focus on interconnected requirements in {domain}, I recommend: To ensure full compliance across overlapping requirements, a structured approach is necessary. Organizations should implement robust documentation, regular audits, and clear accountability frameworks.",
        "confidence": 0.7 + (weights.get('compliance', 0.25) * 0.2),
        "persona_name": "Compliance Expert"
    }
    
    # Generate combined response
    combined_response = f"Synthesizing insights from all expert perspectives on \"{query}\" in the {domain} domain:\n\n" + \
        f"📚 From a knowledge perspective:\n{knowledge_result['response']}\n\n" + \
        f"🏢 From an industry perspective:\n{sector_result['response']}\n\n" + \
        f"⚖️ From a regulatory standpoint:\n{regulatory_result['response']}\n\n" + \
        f"✓ For ensuring compliance:\n{compliance_result['response']}\n\n" + \
        f"🔄 Integrated Summary:\nWhen combining all four perspectives, a comprehensive approach emerges that addresses theoretical foundations, practical industry applications, regulatory requirements, and compliance frameworks in a cohesive manner. This multi-dimensional analysis provides a more complete understanding than any single perspective could offer."
    
    # Calculate average confidence
    avg_confidence = (
        knowledge_result['confidence'] * weights.get('knowledge', 0.25) +
        sector_result['confidence'] * weights.get('sector', 0.25) +
        regulatory_result['confidence'] * weights.get('regulatory', 0.25) +
        compliance_result['confidence'] * weights.get('compliance', 0.25)
    )
    
    # Complete simulated response
    return jsonify({
        'query': query,
        'response': combined_response,
        'persona_results': {
            'knowledge': knowledge_result,
            'sector': sector_result,
            'regulatory': regulatory_result,
            'compliance': compliance_result
        },
        'active_personas': ['knowledge', 'sector', 'regulatory', 'compliance'],
        'confidence': avg_confidence,
        'processing_time_ms': processing_time,
        'status': 'completed'
    })

@app.route('/api/persona/personas', methods=['GET'])
def get_personas():
    """Get information about available personas in the system."""
    try:
        # Return a static list of available personas
        personas = {
            'knowledge': [{
                'id': 'knowledge_default',
                'name': 'Knowledge Expert',
                'description': 'Expert in domain-specific knowledge and academic concepts',
                'axis_number': 8
            }],
            'sector': [{
                'id': 'sector_default',
                'name': 'Sector Expert',
                'description': 'Expert in industry-specific practices and standards',
                'axis_number': 9
            }],
            'regulatory': [{
                'id': 'regulatory_default',
                'name': 'Regulatory Expert',
                'description': 'Expert in legal frameworks, regulations, and policy',
                'axis_number': 10
            }],
            'compliance': [{
                'id': 'compliance_default',
                'name': 'Compliance Expert',
                'description': 'Expert in ensuring adherence to standards and requirements',
                'axis_number': 11
            }]
        }
        
        return jsonify(personas)
    except Exception as e:
        logger.error(f"Error getting personas: {str(e)}")
        return jsonify({
            'error': 'Failed to get personas',
            'details': str(e)
        }), 500

@app.route('/api/persona/axis-map', methods=['GET'])
def get_axis_map():
    """Get information about the 13-axis coordinate system."""
    try:
        axis_map = {
            'core_axes': {
                1: 'Knowledge Framework (Pillar Levels)',
                2: 'Sectors',
                3: 'Domains',
                4: 'Methods',
                5: 'Temporal Context',
                6: 'Regulatory',
                7: 'Compliance'
            },
            'persona_axes': {
                8: 'Knowledge Expert',
                9: 'Sector Expert',
                10: 'Regulatory Expert (Octopus Node)',
                11: 'Compliance Expert (Spiderweb Node)'
            },
            'integration_axes': {
                12: 'Integration Context',
                13: 'Application Context'
            }
        }
        
        return jsonify(axis_map)
    except Exception as e:
        logger.error(f"Error getting axis map: {str(e)}")
        return jsonify({
            'error': 'Failed to get axis map',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)