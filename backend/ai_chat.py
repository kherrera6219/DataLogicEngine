"""
AI Chat API for Universal Knowledge Graph queries.

This module provides AI-powered chat functionality using Replit's AI Integrations
service for OpenAI-compatible API access.
"""

import os
import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_login import login_required, current_user

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
from openai import OpenAI

logger = logging.getLogger(__name__)

# Create blueprint
ai_chat_bp = Blueprint('ai_chat', __name__, url_prefix='/api/ai')

# Initialize OpenAI client using Replit AI Integrations
AI_INTEGRATIONS_OPENAI_API_KEY = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
AI_INTEGRATIONS_OPENAI_BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")

openai_client = OpenAI(
    api_key=AI_INTEGRATIONS_OPENAI_API_KEY,
    base_url=AI_INTEGRATIONS_OPENAI_BASE_URL
)

# System prompt for the UKG assistant
UKG_SYSTEM_PROMPT = """You are the Universal Knowledge Graph (UKG) AI Assistant, an advanced computational intelligence system designed for multi-perspective knowledge synthesis and expert simulation.

You have access to a 13-axis knowledge framework that organizes information across:
1. Identity Axis - User and entity identification
2. Sector Axis - Industry and sector classification
3. Domain Axis - Knowledge domain categorization
4. Knowledge Axis - Core knowledge areas
5. Methods Axis - Methodologies and approaches
6. Honeycomb Axis - Interconnected knowledge cells
7. Regulatory Axis - Legal and regulatory frameworks
8. Compliance Axis - Standards and compliance requirements
9. Knowledge Expert Axis - Subject matter expertise
10. Sector Expert Axis - Industry expertise
11. Contextual Expert Axis - Context-aware expertise
12. Location Axis - Geographic and spatial context
13. Time Axis - Temporal context and evolution

You also have a 10-layer simulation stack for deep analysis:
- Layer 1: Knowledge Base
- Layer 2: Quad Persona Engine
- Layer 3: Simulation Memory
- Layer 4: Reasoning Layer
- Layer 5: Integration Layer
- Layer 6: Enhancement Layer
- Layer 7: AGI System
- Layer 8: Quantum Computing Layer
- Layer 9: Recursive Core
- Layer 10: Self-Awareness Engine

When answering questions:
1. Consider multiple perspectives using the quad persona approach (Analyst, Expert, Critic, Synthesizer)
2. Reference relevant axes when discussing knowledge domains
3. Provide structured, well-reasoned responses
4. Acknowledge uncertainty when appropriate
5. Suggest related topics or deeper exploration paths

You are helpful, accurate, and thorough in your responses."""


@ai_chat_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """
    Handle chat requests with the UKG AI assistant.
    
    Request body:
        message: str - The user's message
        context: dict (optional) - Additional context for the conversation
        conversation_history: list (optional) - Previous messages in the conversation
    
    Returns:
        JSON response with the AI's reply
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message']
        context = data.get('context', {})
        conversation_history = data.get('conversation_history', [])
        
        # Build messages array
        messages = [{"role": "system", "content": UKG_SYSTEM_PROMPT}]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            if 'role' in msg and 'content' in msg:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # Add context if provided
        if context:
            context_str = f"\n\nCurrent context:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            user_message = user_message + context_str
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_completion_tokens=2048
        )
        
        assistant_message = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'message': assistant_message,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0
            }
        })
        
    except Exception as e:
        logger.error(f"AI chat error: {str(e)}")
        error_message = str(e)
        
        # Check for budget exceeded error
        if "FREE_CLOUD_BUDGET_EXCEEDED" in error_message:
            return jsonify({
                'error': 'Cloud budget exceeded. Please check your Replit credits.',
                'code': 'BUDGET_EXCEEDED'
            }), 402
        
        return jsonify({'error': 'An error occurred processing your request'}), 500


@ai_chat_bp.route('/chat/stream', methods=['POST'])
@login_required
def chat_stream():
    """
    Handle streaming chat requests with the UKG AI assistant.
    
    Request body:
        message: str - The user's message
        context: dict (optional) - Additional context for the conversation
        conversation_history: list (optional) - Previous messages in the conversation
    
    Returns:
        Server-Sent Events stream with the AI's reply
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message']
        context = data.get('context', {})
        conversation_history = data.get('conversation_history', [])
        
        # Build messages array
        messages = [{"role": "system", "content": UKG_SYSTEM_PROMPT}]
        
        # Add conversation history
        for msg in conversation_history[-10:]:
            if 'role' in msg and 'content' in msg:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # Add context if provided
        if context:
            context_str = f"\n\nCurrent context:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            user_message = user_message + context_str
        
        messages.append({"role": "user", "content": user_message})
        
        def generate():
            try:
                # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
                # do not change this unless explicitly requested by the user
                stream = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_completion_tokens=2048,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        yield f"data: {content}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                yield f"data: [ERROR] {str(e)}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        logger.error(f"AI chat stream error: {str(e)}")
        return jsonify({'error': 'An error occurred processing your request'}), 500


@ai_chat_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_query():
    """
    Analyze a query using the 13-axis knowledge framework.
    
    Request body:
        query: str - The query to analyze
        axes: list (optional) - Specific axes to focus on
    
    Returns:
        JSON response with axis-based analysis
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        axes = data.get('axes', [])
        
        analysis_prompt = f"""Analyze the following query using the Universal Knowledge Graph's 13-axis framework.

Query: {query}

Please provide:
1. Relevant axes identification (which of the 13 axes are most relevant)
2. Key entities and concepts extracted
3. Knowledge domains involved
4. Regulatory/compliance considerations (if any)
5. Recommended expert perspectives to consult
6. Suggested simulation layers to engage

Format your response as structured JSON."""

        if axes:
            analysis_prompt += f"\n\nFocus particularly on these axes: {', '.join(axes)}"
        
        messages = [
            {"role": "system", "content": UKG_SYSTEM_PROMPT},
            {"role": "user", "content": analysis_prompt}
        ]
        
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_completion_tokens=2048,
            response_format={"type": "json_object"}
        )
        
        analysis = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'query': query,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Query analysis error: {str(e)}")
        return jsonify({'error': 'An error occurred analyzing the query'}), 500


@ai_chat_bp.route('/simulate', methods=['POST'])
@login_required
def simulate_perspective():
    """
    Simulate a multi-perspective analysis using the Quad Persona Engine.
    
    Request body:
        topic: str - The topic to analyze
        personas: list (optional) - Specific personas to simulate
    
    Returns:
        JSON response with multi-perspective analysis
    """
    try:
        data = request.get_json()
        
        if not data or 'topic' not in data:
            return jsonify({'error': 'Topic is required'}), 400
        
        topic = data['topic']
        personas = data.get('personas', ['Analyst', 'Expert', 'Critic', 'Synthesizer'])
        
        simulation_prompt = f"""Perform a multi-perspective analysis on the following topic using the Quad Persona Engine.

Topic: {topic}

Simulate the following personas and provide their unique perspectives:
{', '.join(personas)}

For each persona, provide:
1. Their core perspective on the topic
2. Key insights unique to their viewpoint
3. Questions they would raise
4. Recommendations from their expertise

Then provide a synthesis that integrates all perspectives.

Format your response as structured JSON with a section for each persona and a final synthesis section."""
        
        messages = [
            {"role": "system", "content": UKG_SYSTEM_PROMPT},
            {"role": "user", "content": simulation_prompt}
        ]
        
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_completion_tokens=4096,
            response_format={"type": "json_object"}
        )
        
        simulation = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'topic': topic,
            'personas': personas,
            'simulation': simulation
        })
        
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        return jsonify({'error': 'An error occurred during simulation'}), 500


@ai_chat_bp.route('/health', methods=['GET'])
def ai_health():
    """Check AI service health."""
    try:
        # Quick test of the API
        if AI_INTEGRATIONS_OPENAI_API_KEY and AI_INTEGRATIONS_OPENAI_BASE_URL:
            return jsonify({
                'status': 'ok',
                'service': 'Replit AI Integrations',
                'configured': True
            })
        else:
            return jsonify({
                'status': 'degraded',
                'service': 'Replit AI Integrations',
                'configured': False,
                'message': 'AI integration not fully configured'
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
