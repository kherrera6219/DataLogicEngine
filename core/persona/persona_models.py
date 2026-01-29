"""
Universal Knowledge Graph (UKG) System - Quad Persona Models

This module defines database models for the Quad Persona System,
enabling persistent storage of persona-based knowledge processing.
"""

import os
import logging
import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app import db

logger = logging.getLogger(__name__)

from models import db, Persona, Perspective, IntegratedView, KnowledgeGraphNode as KnowledgeNode
