
"""
Universal Knowledge Graph (UKG) System - Axis 13: Time

This module implements the Time axis for the UKG system,
providing temporal context for knowledge and enabling historical,
present, and future time mapping.
"""

import os
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import and_, or_, func
from app import db
from models import TimeContext, KnowledgeNode

logger = logging.getLogger(__name__)

class TimeAxis:
    """Handler for Axis 13: Time - Temporal Context"""
    
    def __init__(self):
        """Initialize the Time axis handler."""
        self.axis_number = 13
        self.axis_name = "Time"
        self.description = "Temporal context for knowledge elements, projects, and career paths"
        
        # Time granularity levels
        self.granularity_levels = [
            "millennium", "century", "decade", "year", 
            "quarter", "month", "week", "day", 
            "hour", "minute", "second"
        ]
        
        # Time context types
        self.context_types = [
            "historical", "current", "future", "project", 
            "career_stage", "task", "deadline", "milestone",
            "recurring", "seasonal", "indefinite"
        ]
    
    def navigate(self, **kwargs) -> Dict[str, Any]:
        """
        Navigate the Time axis based on provided parameters.
        
        Parameters:
        - time_id (int): ID of a specific time context
        - time_type (str): Type of time context (e.g., "historical", "project", "career_stage")
        - start_date (datetime): Start date/time for filtering
        - end_date (datetime): End date/time for filtering
        - reference_date (datetime): Reference date for relative time queries
        - granularity (str): Time granularity (e.g., "year", "month", "day")
        - include_nodes (bool): Whether to include associated knowledge nodes
        
        Returns:
        - Dict containing the navigation results
        """
        # Extract parameters
        time_id = kwargs.get('time_id')
        time_type = kwargs.get('time_type')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        reference_date = kwargs.get('reference_date', datetime.utcnow())
        granularity = kwargs.get('granularity')
        include_nodes = kwargs.get('include_nodes', False)
        
        # Build query for time contexts
        query = db.session.query(TimeContext)
        
        # Apply filters based on provided parameters
        if time_id is not None:
            query = query.filter(TimeContext.id == time_id)
        
        if time_type is not None:
            query = query.filter(TimeContext.time_type == time_type)
        
        if start_date is not None:
            query = query.filter(TimeContext.end_date >= start_date)
        
        if end_date is not None:
            query = query.filter(TimeContext.start_date <= end_date)
        
        if granularity is not None:
            query = query.filter(TimeContext.granularity == granularity)
        
        # Execute query
        try:
            time_contexts = query.all()
            
            # Convert to dictionary format
            result_data = {
                "axis": self.axis_number,
                "name": self.axis_name,
                "time_contexts": [tc.to_dict() for tc in time_contexts],
                "count": len(time_contexts),
                "reference_date": reference_date.isoformat() if reference_date else None
            }
            
            # Include associated knowledge nodes if requested
            if include_nodes and time_contexts:
                # Get all time context IDs
                time_context_ids = [tc.id for tc in time_contexts]
                
                # Query for associated knowledge nodes
                nodes_query = db.session.query(KnowledgeNode).filter(
                    KnowledgeNode.time_context_id.in_(time_context_ids)
                )
                
                nodes = nodes_query.all()
                result_data["knowledge_nodes"] = [node.to_dict() for node in nodes]
                result_data["node_count"] = len(nodes)
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error navigating Time axis: {str(e)}")
            return {
                "axis": self.axis_number,
                "name": self.axis_name,
                "error": str(e)
            }
    
    def get_time_context(self, time_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific time context by its ID.
        
        Parameters:
        - time_id (int): The time context ID
        
        Returns:
        - Optional[Dict]: The time context data or None if not found
        """
        try:
            time_context = db.session.query(TimeContext).get(time_id)
            
            if time_context:
                return time_context.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving time context {time_id}: {str(e)}")
            return None
    
    def create_time_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new time context.
        
        Parameters:
        - data (Dict): Data for the new time context
        
        Returns:
        - Dict: Result of the creation operation
        """
        try:
            # Check for required fields
            required_fields = ['name', 'time_type', 'start_date']
            for field in required_fields:
                if field not in data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Ensure dates are in proper format
            start_date = data['start_date']
            end_date = data.get('end_date')
            
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            
            if end_date and isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            
            # Create new time context
            time_context = TimeContext(
                uid=str(uuid.uuid4()),
                name=data['name'],
                time_type=data['time_type'],
                start_date=start_date,
                end_date=end_date,
                granularity=data.get('granularity', 'day'),
                recurring=data.get('recurring', False),
                parent_time_id=data.get('parent_time_id'),
                attributes=data.get('attributes')
            )
            
            db.session.add(time_context)
            db.session.commit()
            
            return {
                "success": True,
                "time_context": time_context.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating time context: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_time_context(self, time_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing time context.
        
        Parameters:
        - time_id (int): ID of the time context to update
        - data (Dict): Updated data
        
        Returns:
        - Dict: Result of the update operation
        """
        try:
            # Find the time context
            time_context = db.session.query(TimeContext).get(time_id)
            
            if not time_context:
                return {
                    "success": False,
                    "error": f"Time context with ID {time_id} not found"
                }
            
            # Update fields
            updateable_fields = [
                'name', 'time_type', 'start_date', 'end_date',
                'granularity', 'recurring', 'parent_time_id', 'attributes'
            ]
            
            for field in updateable_fields:
                if field in data:
                    # Handle date fields
                    if field in ['start_date', 'end_date'] and data[field] and isinstance(data[field], str):
                        data[field] = datetime.fromisoformat(data[field])
                    
                    setattr(time_context, field, data[field])
            
            # Save changes
            db.session.commit()
            
            return {
                "success": True,
                "time_context": time_context.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating time context {time_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_career_timeline(self, persona_id: str, include_nodes: bool = False) -> Dict[str, Any]:
        """
        Get a timeline of career stages for a specific persona.
        
        Parameters:
        - persona_id (str): ID of the persona
        - include_nodes (bool): Whether to include associated knowledge nodes
        
        Returns:
        - Dict: Career timeline data
        """
        try:
            # Query for career stage time contexts for this persona
            query = db.session.query(TimeContext).filter(
                TimeContext.time_type == 'career_stage',
                TimeContext.attributes.contains({'persona_id': persona_id})
            ).order_by(TimeContext.start_date)
            
            career_stages = query.all()
            
            # Build timeline data
            timeline_data = {
                "persona_id": persona_id,
                "career_stages": [stage.to_dict() for stage in career_stages],
                "total_years": sum(
                    ((stage.end_date or datetime.utcnow()) - stage.start_date).days / 365
                    for stage in career_stages if stage.start_date
                ),
                "stage_count": len(career_stages)
            }
            
            # Include associated knowledge nodes if requested
            if include_nodes and career_stages:
                stage_ids = [stage.id for stage in career_stages]
                
                nodes_query = db.session.query(KnowledgeNode).filter(
                    KnowledgeNode.time_context_id.in_(stage_ids)
                )
                
                nodes = nodes_query.all()
                timeline_data["knowledge_nodes"] = [node.to_dict() for node in nodes]
            
            return {
                "success": True,
                "timeline": timeline_data
            }
            
        except Exception as e:
            logger.error(f"Error getting career timeline for persona {persona_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_project_timeline(self, project_id: str) -> Dict[str, Any]:
        """
        Get a timeline for a specific project, including tasks and milestones.
        
        Parameters:
        - project_id (str): ID of the project
        
        Returns:
        - Dict: Project timeline data
        """
        try:
            # Get project time context
            project = db.session.query(TimeContext).filter(
                TimeContext.time_type == 'project',
                TimeContext.attributes.contains({'project_id': project_id})
            ).first()
            
            if not project:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} not found"
                }
            
            # Get tasks and milestones
            tasks_and_milestones = db.session.query(TimeContext).filter(
                TimeContext.time_type.in_(['task', 'milestone']),
                TimeContext.parent_time_id == project.id
            ).order_by(TimeContext.start_date).all()
            
            # Build timeline data
            timeline_data = {
                "project": project.to_dict(),
                "tasks": [item.to_dict() for item in tasks_and_milestones if item.time_type == 'task'],
                "milestones": [item.to_dict() for item in tasks_and_milestones if item.time_type == 'milestone'],
                "duration_days": (
                    (project.end_date or datetime.utcnow()) - project.start_date
                ).days if project.start_date else None,
                "completion_percentage": self._calculate_project_completion(project, tasks_and_milestones)
            }
            
            return {
                "success": True,
                "timeline": timeline_data
            }
            
        except Exception as e:
            logger.error(f"Error getting project timeline for {project_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_project_completion(self, project: TimeContext, tasks: List[TimeContext]) -> float:
        """
        Calculate project completion percentage based on completed tasks.
        
        Parameters:
        - project: The project time context
        - tasks: List of task time contexts
        
        Returns:
        - float: Completion percentage (0-100)
        """
        if not tasks:
            return 0.0
        
        completed_tasks = [
            task for task in tasks 
            if task.attributes and task.attributes.get('status') == 'completed'
        ]
        
        return (len(completed_tasks) / len(tasks)) * 100
    
    def get_historical_periods(self, start_year: Optional[int] = None, 
                               end_year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get historical time periods within an optional year range.
        
        Parameters:
        - start_year (Optional[int]): Start year (inclusive)
        - end_year (Optional[int]): End year (inclusive)
        
        Returns:
        - Dict: Historical periods data
        """
        try:
            # Build query for historical time contexts
            query = db.session.query(TimeContext).filter(
                TimeContext.time_type == 'historical'
            )
            
            # Apply year range filters if provided
            if start_year is not None:
                start_date = datetime(start_year, 1, 1)
                query = query.filter(TimeContext.end_date >= start_date)
            
            if end_year is not None:
                end_date = datetime(end_year, 12, 31)
                query = query.filter(TimeContext.start_date <= end_date)
            
            # Execute query and order by start date
            periods = query.order_by(TimeContext.start_date).all()
            
            return {
                "success": True,
                "periods": [period.to_dict() for period in periods],
                "count": len(periods),
                "start_year": start_year,
                "end_year": end_year
            }
            
        except Exception as e:
            logger.error(f"Error getting historical periods: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
