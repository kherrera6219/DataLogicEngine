"""
Simulation Validation Schemas

Marshmallow schemas for validating simulation-related requests.
Provides input validation and sanitization for simulation endpoints.
"""

from marshmallow import Schema, fields, validate, validates, ValidationError, EXCLUDE
import bleach


class CreateSimulationSchema(Schema):
    """Schema for validating simulation creation requests."""

    class Meta:
        unknown = EXCLUDE  # Ignore unknown fields

    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=128, error="Name must be between 1 and 128 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9\s\-_\.]+$',
                error="Name can only contain letters, numbers, spaces, hyphens, underscores, and periods"
            )
        ],
        metadata={"description": "Simulation name"}
    )

    description = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000, error="Description must be max 1000 characters"),
        metadata={"description": "Simulation description"}
    )

    sim_type = fields.Str(
        required=True,
        validate=validate.OneOf(
            ['layer7_agi', 'layer8_quantum', 'layer9_recursive', 'layer10_synthesis',
             'standard', 'advanced', 'expert'],
            error="Invalid simulation type"
        ),
        metadata={"description": "Type of simulation to run"}
    )

    refinement_steps = fields.Int(
        required=False,
        missing=12,
        validate=[
            validate.Range(min=1, max=100, error="Refinement steps must be between 1 and 100")
        ],
        metadata={"description": "Number of refinement steps (default: 12)"}
    )

    confidence_threshold = fields.Float(
        required=False,
        missing=0.85,
        validate=[
            validate.Range(min=0.0, max=1.0, error="Confidence threshold must be between 0 and 1")
        ],
        metadata={"description": "Confidence threshold (default: 0.85)"}
    )

    entropy_sampling = fields.Bool(
        required=False,
        missing=False,
        metadata={"description": "Enable entropy sampling"}
    )

    auto_start = fields.Bool(
        required=False,
        missing=False,
        metadata={"description": "Automatically start simulation after creation"}
    )

    @validates('name')
    def sanitize_name(self, value):
        """Sanitize name to prevent XSS."""
        if value:
            # Remove any HTML tags
            sanitized = bleach.clean(value, tags=[], strip=True)
            if sanitized != value:
                raise ValidationError("Name contains invalid characters or HTML")
        return value

    @validates('description')
    def sanitize_description(self, value):
        """Sanitize description to prevent XSS."""
        if value:
            # Allow only safe HTML tags
            sanitized = bleach.clean(
                value,
                tags=['b', 'i', 'u', 'em', 'strong', 'p', 'br'],
                strip=True
            )
            return sanitized
        return value


class UpdateSimulationSchema(Schema):
    """Schema for validating simulation update requests."""

    class Meta:
        unknown = EXCLUDE

    name = fields.Str(
        required=False,
        validate=[
            validate.Length(min=1, max=128),
            validate.Regexp(r'^[a-zA-Z0-9\s\-_\.]+$')
        ]
    )

    description = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000)
    )

    status = fields.Str(
        required=False,
        validate=validate.OneOf(
            ['pending', 'running', 'paused', 'completed', 'failed', 'cancelled'],
            error="Invalid status"
        )
    )


class SimulationQuerySchema(Schema):
    """Schema for validating simulation query parameters."""

    class Meta:
        unknown = EXCLUDE

    page = fields.Int(
        required=False,
        missing=1,
        validate=validate.Range(min=1, max=10000, error="Page must be between 1 and 10000")
    )

    per_page = fields.Int(
        required=False,
        missing=10,
        validate=validate.Range(min=1, max=100, error="Per page must be between 1 and 100")
    )

    status = fields.Str(
        required=False,
        validate=validate.OneOf(
            ['pending', 'running', 'paused', 'completed', 'failed', 'cancelled', 'all']
        )
    )

    sort_by = fields.Str(
        required=False,
        missing='created_at',
        validate=validate.OneOf(['created_at', 'name', 'status', 'updated_at'])
    )

    sort_order = fields.Str(
        required=False,
        missing='desc',
        validate=validate.OneOf(['asc', 'desc'])
    )


class SimulationExportSchema(Schema):
    """Schema for validating simulation export requests."""

    class Meta:
        unknown = EXCLUDE

    format = fields.Str(
        required=False,
        missing='json',
        validate=validate.OneOf(['json', 'csv', 'xlsx'], error="Invalid export format")
    )

    include_parameters = fields.Bool(
        required=False,
        missing=True
    )

    include_results = fields.Bool(
        required=False,
        missing=True
    )


def validate_simulation_creation(data: dict) -> tuple[dict, list]:
    """
    Validate simulation creation data.

    Args:
        data: Raw request data

    Returns:
        Tuple of (validated_data, errors)
    """
    schema = CreateSimulationSchema()
    try:
        validated = schema.load(data)
        return validated, []
    except ValidationError as e:
        return None, e.messages


def validate_simulation_update(data: dict) -> tuple[dict, list]:
    """
    Validate simulation update data.

    Args:
        data: Raw request data

    Returns:
        Tuple of (validated_data, errors)
    """
    schema = UpdateSimulationSchema()
    try:
        validated = schema.load(data)
        return validated, []
    except ValidationError as e:
        return None, e.messages


def validate_simulation_query(params: dict) -> tuple[dict, list]:
    """
    Validate simulation query parameters.

    Args:
        params: Raw query parameters

    Returns:
        Tuple of (validated_params, errors)
    """
    schema = SimulationQuerySchema()
    try:
        validated = schema.load(params)
        return validated, []
    except ValidationError as e:
        return None, e.messages
