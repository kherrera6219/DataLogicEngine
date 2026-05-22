"""
TruthCore LLM Router

Provides task-based LLM routing for optimal model selection.
"""

import logging
from typing import Dict, Any, List
from backend.llm_gateway.model_defaults import (
    ANTHROPIC_PRIMARY_MODEL,
    GOOGLE_PRIMARY_MODEL,
    OPENAI_LATEST_MODEL,
)

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    LLM routing engine with task-based model selection.
    
    Routes queries to optimal LLM backend based on:
    - Task type (code, analysis, long_context, reasoning)
    - Context length requirements
    - Performance requirements
    """
    
    ROUTING_PROFILES = {
        'code': {
            'primary': 'codestral',
            'fallback': OPENAI_LATEST_MODEL,
            'description': 'Code generation and debugging',
            'keywords': ['code', 'function', 'program', 'debug', 'script', 'api']
        },
        'analysis': {
            'primary': ANTHROPIC_PRIMARY_MODEL,
            'fallback': OPENAI_LATEST_MODEL,
            'description': 'Deep analysis and evaluation',
            'keywords': ['analyze', 'evaluate', 'assess', 'review', 'examine']
        },
        'long_context': {
            'primary': GOOGLE_PRIMARY_MODEL,
            'fallback': ANTHROPIC_PRIMARY_MODEL,
            'description': 'Long document processing',
            'keywords': [],
            'context_threshold': 50000
        },
        'reasoning': {
            'primary': 'grok-4-fast',
            'fallback': OPENAI_LATEST_MODEL,
            'description': 'Complex reasoning and logic',
            'keywords': ['reason', 'logic', 'deduce', 'infer', 'conclude']
        },
        'default': {
            'primary': OPENAI_LATEST_MODEL,
            'fallback': ANTHROPIC_PRIMARY_MODEL,
            'description': 'General purpose',
            'keywords': []
        }
    }
    
    SUPPORTED_MODELS = {
        OPENAI_LATEST_MODEL: {'provider': 'openai', 'context_window': 1050000},
        ANTHROPIC_PRIMARY_MODEL: {'provider': 'anthropic', 'context_window': 1000000},
        GOOGLE_PRIMARY_MODEL: {'provider': 'google', 'context_window': 1048576},
        'grok-4-fast': {'provider': 'xai', 'context_window': 131072},
        'codestral': {'provider': 'mistral', 'context_window': 32000},
        'llama-3-70b': {'provider': 'meta', 'context_window': 8192}
    }

    def __init__(self, available_models: List[str] = None):
        """Initialize router with available models."""
        self.available_models = available_models or [OPENAI_LATEST_MODEL]
        logger.info(f"LLM Router initialized with models: {self.available_models}")

    def route(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route query to optimal LLM based on task analysis.
        
        Returns routing decision with model and profile.
        """
        context = context or {}
        
        if context.get('model'):
            return self._create_routing_decision(context['model'], 'explicit', query)
        
        profile = self._detect_profile(query, context)
        model = self._select_model(profile)
        
        return self._create_routing_decision(model, profile, query)

    def _detect_profile(self, query: str, context: Dict[str, Any]) -> str:
        """Detect routing profile from query content."""
        query_lower = query.lower()
        query_length = len(query)
        
        for profile_name, profile_config in self.ROUTING_PROFILES.items():
            if profile_name == 'default':
                continue
            
            if profile_name == 'long_context':
                threshold = profile_config.get('context_threshold', 50000)
                if query_length > threshold or context.get('context_length', 0) > threshold:
                    return 'long_context'
            
            keywords = profile_config.get('keywords', [])
            if any(kw in query_lower for kw in keywords):
                return profile_name
        
        return 'default'

    def _select_model(self, profile: str) -> str:
        """Select best available model for profile."""
        profile_config = self.ROUTING_PROFILES.get(profile, self.ROUTING_PROFILES['default'])
        
        primary = profile_config.get('primary', OPENAI_LATEST_MODEL)
        if primary in self.available_models:
            return primary
        
        fallback = profile_config.get('fallback', OPENAI_LATEST_MODEL)
        if fallback in self.available_models:
            return fallback
        
        return self.available_models[0] if self.available_models else OPENAI_LATEST_MODEL

    def _create_routing_decision(self, model: str, profile: str, query: str) -> Dict[str, Any]:
        """Create routing decision object."""
        model_info = self.SUPPORTED_MODELS.get(model, {})
        profile_config = self.ROUTING_PROFILES.get(profile, {})
        
        return {
            'model': model,
            'profile': profile,
            'provider': model_info.get('provider', 'unknown'),
            'context_window': model_info.get('context_window', 128000),
            'profile_description': profile_config.get('description', 'General purpose'),
            'query_length': len(query),
            'routing_reason': f"Selected {model} based on {profile} profile"
        }

    def get_model_info(self, model: str = None) -> Dict[str, Any]:
        """Get information about models."""
        if model:
            return self.SUPPORTED_MODELS.get(model, {})
        return self.SUPPORTED_MODELS

    def get_profile_info(self, profile: str = None) -> Dict[str, Any]:
        """Get information about routing profiles."""
        if profile:
            return self.ROUTING_PROFILES.get(profile, {})
        return self.ROUTING_PROFILES
