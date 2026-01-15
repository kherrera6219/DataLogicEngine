"""
KA-56: Recursive Planning AGI Core

This algorithm enables recursive planning and goal decomposition,
implementing a hierarchical planning system that breaks complex goals
into manageable sub-goals with dependency tracking.

REFACTORED: Implementation moved to knowledge_algorithms.ka56.core
"""

import logging
from knowledge_algorithms.ka56.core import RecursivePlanningAGICore

# Re-export the class for backward compatibility
RecursivePlanningAGICore = RecursivePlanningAGICore

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Simple test execution
    planner = RecursivePlanningAGICore()
    print("KA-56 Core (Refactored) initialized successfully.")