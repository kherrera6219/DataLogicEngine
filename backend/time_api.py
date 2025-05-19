
"""
Time API endpoints for the UKG system
"""

from flask import Blueprint, request, jsonify
from models import TimeContext, db
import logging
import uuid
from datetime import datetime
import json

# Create blueprint
time_api = Blueprint('time_api', __name__)
logger = logging.getLogger(__name__)

@time_api.route('/api/time', methods=['GET'])
def get_time_contexts():
    """Get time contexts based on query parameters"""
    try:
        # Extract query parameters
        time_type = request.args.get('type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        parent_id = request.args.get('parent_id')
        granularity = request.args.get('granularity')
        
        # Build query
        query = db.session.query(TimeContext)
        
        # Apply filters
        if time_type:
            query = query.filter(TimeContext.time_type == time_type)
        
        if parent_id:
            query = query.filter(TimeContext.parent_time_id == parent_id)
            
        if start_date:
            try:
                start_date_obj = datetime.fromisoformat(start_date)
                query = query.filter(TimeContext.end_date >= start_date_obj)
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)."
                }), 400
        
        if end_date:
            try:
                end_date_obj = datetime.fromisoformat(end_date)
                query = query.filter(TimeContext.start_date <= end_date_obj)
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)."
                }), 400
                
        if granularity:
            query = query.filter(TimeContext.granularity == granularity)
        
        # Execute query
        time_contexts = query.all()
        
        # Convert to dicts
        contexts_data = [tc.to_dict() for tc in time_contexts]
        
        return jsonify({
            "success": True,
            "count": len(contexts_data),
            "time_contexts": contexts_data
        })
        
    except Exception as e:
        logger.error(f"Error getting time contexts: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@time_api.route('/api/time/<uid>', methods=['GET'])
def get_time_context(uid):
    """Get a specific time context by UID"""
    try:
        time_context = db.session.query(TimeContext).filter_by(uid=uid).first()
        
        if not time_context:
            return jsonify({
                "success": False,
                "error": f"Time context with UID {uid} not found"
            }), 404
            
        # Get children if they exist
        children = db.session.query(TimeContext).filter_by(parent_time_id=time_context.id).all()
        children_data = [child.to_dict() for child in children]
        
        # Get parent if it exists
        parent_data = None
        if time_context.parent_time_id:
            parent = db.session.query(TimeContext).get(time_context.parent_time_id)
            if parent:
                parent_data = parent.to_dict()
        
        # Build response
        time_context_data = time_context.to_dict()
        time_context_data['children'] = children_data
        time_context_data['parent'] = parent_data
        
        return jsonify({
            "success": True,
            "time_context": time_context_data
        })
        
    except Exception as e:
        logger.error(f"Error getting time context {uid}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@time_api.route('/api/time', methods=['POST'])
def create_time_context():
    """Create a new time context"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name') or not data.get('time_type') or not data.get('start_date'):
            return jsonify({
                "success": False,
                "error": "Name, time_type, and start_date are required"
            }), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(data['start_date'])
            end_date = datetime.fromisoformat(data['end_date']) if data.get('end_date') else None
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)."
            }), 400
        
        # Create new time context
        new_time_context = TimeContext(
            uid=str(uuid.uuid4()),
            name=data['name'],
            time_type=data['time_type'],
            start_date=start_date,
            end_date=end_date,
            granularity=data.get('granularity', 'day'),
            recurring=data.get('recurring', False),
            parent_time_id=data.get('parent_time_id'),
            attributes=data.get('attributes', {})
        )
        
        db.session.add(new_time_context)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "time_context": new_time_context.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating time context: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@time_api.route('/api/time/<uid>', methods=['PUT'])
def update_time_context(uid):
    """Update an existing time context"""
    try:
        time_context = db.session.query(TimeContext).filter_by(uid=uid).first()
        
        if not time_context:
            return jsonify({
                "success": False,
                "error": f"Time context with UID {uid} not found"
            }), 404
            
        data = request.json
        
        # Update fields if provided
        if 'name' in data:
            time_context.name = data['name']
            
        if 'time_type' in data:
            time_context.time_type = data['time_type']
            
        if 'start_date' in data:
            try:
                time_context.start_date = datetime.fromisoformat(data['start_date'])
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)."
                }), 400
            
        if 'end_date' in data:
            try:
                time_context.end_date = datetime.fromisoformat(data['end_date']) if data['end_date'] else None
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)."
                }), 400
            
        if 'granularity' in data:
            time_context.granularity = data['granularity']
            
        if 'recurring' in data:
            time_context.recurring = data['recurring']
            
        if 'parent_time_id' in data:
            time_context.parent_time_id = data['parent_time_id']
            
        if 'attributes' in data:
            time_context.attributes = data['attributes']
            
        time_context.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "time_context": time_context.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating time context {uid}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@time_api.route('/api/time/<uid>', methods=['DELETE'])
def delete_time_context(uid):
    """Delete a time context"""
    try:
        time_context = db.session.query(TimeContext).filter_by(uid=uid).first()
        
        if not time_context:
            return jsonify({
                "success": False,
                "error": f"Time context with UID {uid} not found"
            }), 404
        
        # Check for children
        children = db.session.query(TimeContext).filter_by(parent_time_id=time_context.id).all()
        if children:
            return jsonify({
                "success": False,
                "error": f"Cannot delete time context with {len(children)} child contexts",
                "children_count": len(children)
            }), 400
        
        db.session.delete(time_context)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Time context '{time_context.name}' successfully deleted"
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting time context {uid}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@time_api.route('/api/time/career/<persona_id>', methods=['GET'])
def get_career_timeline(persona_id):
    """Get career timeline for a persona"""
    try:
        # Query for career stage time contexts for this persona
        career_stages = db.session.query(TimeContext).filter(
            TimeContext.time_type == 'career_stage',
            TimeContext.attributes.contains({"persona_id": persona_id})
        ).order_by(TimeContext.start_date).all()
        
        # Calculate total years of experience
        total_years = 0
        for stage in career_stages:
            if stage.start_date:
                end = stage.end_date or datetime.utcnow()
                duration_days = (end - stage.start_date).days
                total_years += duration_days / 365
        
        return jsonify({
            "success": True,
            "persona_id": persona_id,
            "career_stages": [stage.to_dict() for stage in career_stages],
            "stage_count": len(career_stages),
            "total_years": round(total_years, 1)
        })
        
    except Exception as e:
        logger.error(f"Error getting career timeline for {persona_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@time_api.route('/api/time/project/<project_id>', methods=['GET'])
def get_project_timeline(project_id):
    """Get timeline for a project"""
    try:
        # Get project time context
        project = db.session.query(TimeContext).filter(
            TimeContext.time_type == 'project',
            TimeContext.attributes.contains({"project_id": project_id})
        ).first()
        
        if not project:
            return jsonify({
                "success": False,
                "error": f"Project with ID {project_id} not found"
            }), 404
        
        # Get tasks and milestones
        tasks_and_milestones = db.session.query(TimeContext).filter(
            TimeContext.time_type.in_(['task', 'milestone']),
            TimeContext.parent_time_id == project.id
        ).order_by(TimeContext.start_date).all()
        
        # Calculate project completion
        total_tasks = len([t for t in tasks_and_milestones if t.time_type == 'task'])
        completed_tasks = len([
            t for t in tasks_and_milestones 
            if t.time_type == 'task' and t.attributes and t.attributes.get('status') == 'completed'
        ])
        
        completion_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        return jsonify({
            "success": True,
            "project": project.to_dict(),
            "tasks": [t.to_dict() for t in tasks_and_milestones if t.time_type == 'task'],
            "milestones": [t.to_dict() for t in tasks_and_milestones if t.time_type == 'milestone'],
            "completion_percentage": round(completion_percentage, 1)
        })
        
    except Exception as e:
        logger.error(f"Error getting project timeline for {project_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@time_api.route('/api/time/historical', methods=['GET'])
def get_historical_periods():
    """Get historical time periods"""
    try:
        # Get optional year range parameters
        start_year = request.args.get('start_year', type=int)
        end_year = request.args.get('end_year', type=int)
        
        # Build query
        query = db.session.query(TimeContext).filter(TimeContext.time_type == 'historical')
        
        # Apply year filters if provided
        if start_year is not None:
            start_date = datetime(start_year, 1, 1)
            query = query.filter(TimeContext.end_date >= start_date)
        
        if end_year is not None:
            end_date = datetime(end_year, 12, 31)
            query = query.filter(TimeContext.start_date <= end_date)
        
        # Execute query
        periods = query.order_by(TimeContext.start_date).all()
        
        return jsonify({
            "success": True,
            "periods": [period.to_dict() for period in periods],
            "count": len(periods)
        })
        
    except Exception as e:
        logger.error(f"Error getting historical periods: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
