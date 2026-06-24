"""Request-validation schemas for the API.

Active schemas are Pydantic models in the submodules:

- ``api_request_schemas`` — query/simulation/pillar/sector/domain/knowledge/
  compliance request models (used by ``backend/routes/*``).
- ``request_schemas`` — storage-test / audio-synthesize / pillar-create models.

A legacy Marshmallow validation layer (this file's ``UserRegistrationSchema``/
``validate_with_schema``/… plus ``simulation_schemas.py``) was removed in the
A27 audit: it had zero importers after request validation migrated to Pydantic,
and its multi-user auth schemas were obsolete under single-mode. Import the
Pydantic models directly from the submodules above.
"""
