
"""
Location API endpoints for the UKG system
"""

from flask import Blueprint, request, jsonify
from models import Location, db
import logging
import uuid
from datetime import datetime
from geopy.distance import geodesic

# Create blueprint
location_api = Blueprint('location_api', __name__)
logger = logging.getLogger(__name__)

@location_api.route('/api/locations', methods=['GET'])
def get_locations():
    """Get locations based on query parameters"""
    try:
        # Extract query parameters
        location_type = request.args.get('type')
        parent_id = request.args.get('parent_id')
        name_search = request.args.get('name')
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', 50, type=float)  # Default 50km radius
        
        # Build query
        query = db.session.query(Location)
        
        # Apply filters
        if location_type:
            query = query.filter(Location.location_type == location_type)
        
        if parent_id:
            query = query.filter(Location.parent_location_id == parent_id)
            
        if name_search:
            query = query.filter(Location.name.ilike(f'%{name_search}%'))
        
        # Execute query
        locations = query.all()
        
        # Filter by geo proximity if coordinates provided
        if lat is not None and lng is not None:
            reference_point = (lat, lng)
            filtered_locations = []
            
            for loc in locations:
                if loc.latitude is not None and loc.longitude is not None:
                    loc_point = (loc.latitude, loc.longitude)
                    distance = geodesic(reference_point, loc_point).kilometers
                    
                    if distance <= radius:
                        loc_dict = loc.to_dict()
                        loc_dict['distance'] = round(distance, 2)
                        filtered_locations.append(loc_dict)
            
            locations_data = filtered_locations
            # Sort by distance
            locations_data.sort(key=lambda x: x['distance'])
        else:
            # Convert to dicts without distance calculation
            locations_data = [loc.to_dict() for loc in locations]
        
        return jsonify({
            "success": True,
            "count": len(locations_data),
            "locations": locations_data
        })
        
    except Exception as e:
        logger.error(f"Error getting locations: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@location_api.route('/api/locations/<uid>', methods=['GET'])
def get_location(uid):
    """Get a specific location by UID"""
    try:
        location = db.session.query(Location).filter_by(uid=uid).first()
        
        if not location:
            return jsonify({
                "success": False,
                "error": f"Location with UID {uid} not found"
            }), 404
            
        # Get children if they exist
        children = db.session.query(Location).filter_by(parent_location_id=location.id).all()
        children_data = [child.to_dict() for child in children]
        
        # Get parent if it exists
        parent_data = None
        if location.parent_location_id:
            parent = db.session.query(Location).get(location.parent_location_id)
            if parent:
                parent_data = parent.to_dict()
        
        # Build response with location, children, and parent
        location_data = location.to_dict()
        location_data['children'] = children_data
        location_data['parent'] = parent_data
        
        return jsonify({
            "success": True,
            "location": location_data
        })
        
    except Exception as e:
        logger.error(f"Error getting location {uid}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@location_api.route('/api/locations', methods=['POST'])
def create_location():
    """Create a new location"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name') or not data.get('location_type'):
            return jsonify({
                "success": False,
                "error": "Name and location_type are required"
            }), 400
        
        # Create new location
        new_location = Location(
            uid=str(uuid.uuid4()),
            name=data['name'],
            location_type=data['location_type'],
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            parent_location_id=data.get('parent_location_id'),
            attributes=data.get('attributes', {})
        )
        
        db.session.add(new_location)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "location": new_location.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating location: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@location_api.route('/api/locations/<uid>', methods=['PUT'])
def update_location(uid):
    """Update an existing location"""
    try:
        location = db.session.query(Location).filter_by(uid=uid).first()
        
        if not location:
            return jsonify({
                "success": False,
                "error": f"Location with UID {uid} not found"
            }), 404
            
        data = request.json
        
        # Update fields if provided
        if 'name' in data:
            location.name = data['name']
            
        if 'location_type' in data:
            location.location_type = data['location_type']
            
        if 'latitude' in data:
            location.latitude = data['latitude']
            
        if 'longitude' in data:
            location.longitude = data['longitude']
            
        if 'parent_location_id' in data:
            location.parent_location_id = data['parent_location_id']
            
        if 'attributes' in data:
            location.attributes = data['attributes']
            
        location.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "location": location.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating location {uid}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@location_api.route('/api/locations/hierarchy', methods=['GET'])
def get_location_hierarchy():
    """Get location hierarchy starting from optional root"""
    try:
        root_uid = request.args.get('root_uid')
        
        if root_uid:
            # Get hierarchy starting from specific location
            root_location = db.session.query(Location).filter_by(uid=root_uid).first()
            
            if not root_location:
                return jsonify({
                    "success": False,
                    "error": f"Root location with UID {root_uid} not found"
                }), 404
                
            hierarchy = _build_location_hierarchy(root_location)
            
            return jsonify({
                "success": True,
                "hierarchy": hierarchy
            })
        else:
            # Get all top-level locations (no parent)
            top_level_locations = db.session.query(Location).filter(
                Location.parent_location_id == None
            ).all()
            
            hierarchies = [_build_location_hierarchy(loc) for loc in top_level_locations]
            
            return jsonify({
                "success": True,
                "hierarchies": hierarchies
            })
            
    except Exception as e:
        logger.error(f"Error getting location hierarchy: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def _build_location_hierarchy(location):
    """Recursively build location hierarchy"""
    result = location.to_dict()
    
    # Get children
    children = db.session.query(Location).filter_by(parent_location_id=location.id).all()
    
    # Recursively build hierarchy for children
    if children:
        result['children'] = [_build_location_hierarchy(child) for child in children]
    else:
        result['children'] = []
        
    return result

@location_api.route('/api/locations/nearest', methods=['GET'])
def find_nearest_locations():
    """Find locations nearest to specified coordinates"""
    try:
        # Get parameters
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', 50, type=float)  # Default 50km
        limit = request.args.get('limit', 10, type=int)      # Default 10 results
        location_type = request.args.get('type')             # Optional type filter
        
        if lat is None or lng is None:
            return jsonify({
                "success": False,
                "error": "Latitude and longitude are required"
            }), 400
            
        # Get all locations with coordinates
        query = db.session.query(Location).filter(
            Location.latitude.isnot(None),
            Location.longitude.isnot(None)
        )
        
        # Apply type filter if provided
        if location_type:
            query = query.filter(Location.location_type == location_type)
            
        locations = query.all()
        
        # Calculate distances and filter by radius
        reference_point = (lat, lng)
        result_locations = []
        
        for location in locations:
            loc_point = (location.latitude, location.longitude)
            distance = geodesic(reference_point, loc_point).kilometers
            
            if distance <= radius:
                loc_dict = location.to_dict()
                loc_dict['distance'] = round(distance, 2)
                result_locations.append(loc_dict)
        
        # Sort by distance and apply limit
        result_locations.sort(key=lambda x: x['distance'])
        if limit:
            result_locations = result_locations[:limit]
        
        return jsonify({
            "success": True,
            "center": {"latitude": lat, "longitude": lng},
            "radius": radius,
            "count": len(result_locations),
            "locations": result_locations
        })
        
    except Exception as e:
        logger.error(f"Error finding nearest locations: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
