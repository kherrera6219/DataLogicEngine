"""
Marshmallow Validation Schemas

Provides comprehensive input validation for all API endpoints.
Prevents injection attacks, data corruption, and invalid inputs.
"""

from marshmallow import Schema, fields, validate, validates, ValidationError, validates_schema
import re


class UserRegistrationSchema(Schema):
    """Schema for user registration"""
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=64, error="Username must be between 3 and 64 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9_-]+$',
                error="Username can only contain letters, numbers, underscores, and hyphens"
            )
        ]
    )
    email = fields.Email(
        required=True,
        validate=validate.Length(max=120, error="Email must not exceed 120 characters")
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=12, error="Password must be at least 12 characters")
    )

    @validates('password')
    def validate_password_strength(self, value):
        """Additional password strength validation"""
        from backend.security.password_security import PasswordSecurity

        is_valid, errors = PasswordSecurity.validate_password_strength(value)
        if not is_valid:
            raise ValidationError(errors)


class UserLoginSchema(Schema):
    """Schema for user login"""
    username = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=64, error="Username must be between 1 and 64 characters")
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=1, error="Password is required")
    )


class PasswordChangeSchema(Schema):
    """Schema for password change"""
    current_password = fields.Str(required=True)
    new_password = fields.Str(
        required=True,
        validate=validate.Length(min=12, error="Password must be at least 12 characters")
    )
    confirm_password = fields.Str(required=True)

    @validates('new_password')
    def validate_password_strength(self, value):
        """Validate password strength"""
        from backend.security.password_security import PasswordSecurity

        is_valid, errors = PasswordSecurity.validate_password_strength(value)
        if not is_valid:
            raise ValidationError(errors)

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that new password and confirmation match"""
        if data.get('new_password') != data.get('confirm_password'):
            raise ValidationError('New password and confirmation do not match', 'confirm_password')


class SimulationCreateSchema(Schema):
    """Schema for creating a simulation"""
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=128, error="Name must be between 1 and 128 characters")
    )
    description = fields.Str(
        validate=validate.Length(max=1000, error="Description must not exceed 1000 characters")
    )
    sim_type = fields.Str(
        validate=validate.OneOf(
            ['standard', 'advanced', 'custom'],
            error="Simulation type must be 'standard', 'advanced', or 'custom'"
        )
    )
    refinement_steps = fields.Int(
        validate=validate.Range(min=1, max=20, error="Refinement steps must be between 1 and 20")
    )
    confidence_threshold = fields.Float(
        validate=validate.Range(min=0.0, max=1.0, error="Confidence threshold must be between 0.0 and 1.0")
    )
    parameters = fields.Dict()


class SimulationUpdateSchema(Schema):
    """Schema for updating a simulation"""
    name = fields.Str(
        validate=validate.Length(min=1, max=128, error="Name must be between 1 and 128 characters")
    )
    description = fields.Str(
        validate=validate.Length(max=1000, error="Description must not exceed 1000 characters")
    )
    status = fields.Str(
        validate=validate.OneOf(
            ['pending', 'running', 'completed', 'failed', 'stopped'],
            error="Invalid status value"
        )
    )


class KnowledgeNodeCreateSchema(Schema):
    """Schema for creating a knowledge node"""
    node_id = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=64, error="Node ID must be between 1 and 64 characters"),
            validate.Regexp(r'^[a-zA-Z0-9_-]+$', error="Node ID can only contain letters, numbers, underscores, and hyphens")
        ]
    )
    label = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=128, error="Label must be between 1 and 128 characters")
    )
    node_type = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=32, error="Node type must be between 1 and 32 characters")
    )
    description = fields.Str(
        validate=validate.Length(max=2000, error="Description must not exceed 2000 characters")
    )
    data = fields.Dict()


class APIKeyCreateSchema(Schema):
    """Schema for creating an API key"""
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=120, error="Name must be between 1 and 120 characters")
    )
    description = fields.Str(
        validate=validate.Length(max=500, error="Description must not exceed 500 characters")
    )


class QuerySchema(Schema):
    """Schema for general query validation"""
    query = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=5000, error="Query must be between 1 and 5000 characters")
    )
    limit = fields.Int(
        validate=validate.Range(min=1, max=1000, error="Limit must be between 1 and 1000")
    )
    offset = fields.Int(
        validate=validate.Range(min=0, error="Offset must be non-negative")
    )


class PaginationSchema(Schema):
    """Schema for pagination parameters"""
    page = fields.Int(
        validate=validate.Range(min=1, error="Page must be at least 1")
    )
    per_page = fields.Int(
        validate=validate.Range(min=1, max=100, error="Per page must be between 1 and 100")
    )


class EmailSchema(Schema):
    """Schema for email validation"""
    email = fields.Email(required=True)
    subject = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200, error="Subject must be between 1 and 200 characters")
    )
    message = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=10000, error="Message must be between 1 and 10000 characters")
    )


# Helper function to validate request data
def validate_request_data(schema_class, data):
    """
    Validate request data against a schema.

    Args:
        schema_class: The Marshmallow schema class to use
        data: The data to validate (dict)

    Returns:
        Tuple of (is_valid, validated_data_or_errors)

    Example:
        is_valid, result = validate_request_data(UserLoginSchema, request.json)
        if not is_valid:
            return jsonify({'error': 'Validation failed', 'details': result}), 400
        # Use validated data
        username = result['username']
    """
    schema = schema_class()
    try:
        validated_data = schema.load(data)
        return True, validated_data
    except ValidationError as err:
        return False, err.messages


# Decorator for automatic validation
def validate_with_schema(schema_class):
    """
    Decorator to automatically validate request data with a schema.

    Args:
        schema_class: The Marshmallow schema class to use

    Example:
        @app.route('/api/users/register', methods=['POST'])
        @validate_with_schema(UserRegistrationSchema)
        def register(validated_data):
            # validated_data is guaranteed to be valid
            username = validated_data['username']
            ...
    """
    from functools import wraps
    from flask import request, jsonify

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get request data
            data = request.get_json() if request.is_json else request.form.to_dict()

            # Validate
            is_valid, result = validate_request_data(schema_class, data)

            if not is_valid:
                return jsonify({
                    'error': 'Validation failed',
                    'details': result
                }), 400

            # Pass validated data to the route function
            return f(result, *args, **kwargs)

        return decorated_function
    return decorator
