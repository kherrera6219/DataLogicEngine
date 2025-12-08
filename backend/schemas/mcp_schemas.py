"""
Request validation schemas for MCP API endpoints using Pydantic
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime


class MCPServerCreateSchema(BaseModel):
    """Schema for creating an MCP server"""
    name: str = Field(..., min_length=1, max_length=100, description="Server name")
    version: str = Field(default="1.0.0", max_length=20, description="Server version")
    description: str = Field(default="", max_length=500, description="Server description")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Server configuration")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Server metadata")

    @field_validator('name')
    @classmethod
    def name_must_be_alphanumeric(cls, v: str) -> str:
        if not v.replace('-', '').replace('_', '').replace(' ', '').isalnum():
            raise ValueError('Name must contain only alphanumeric characters, hyphens, underscores, and spaces')
        return v


class MCPResourceCreateSchema(BaseModel):
    """Schema for creating an MCP resource"""
    name: str = Field(..., min_length=1, max_length=100, description="Resource name")
    uri: str = Field(..., min_length=1, max_length=500, description="Resource URI")
    mime_type: Optional[str] = Field(default="text/plain", max_length=100, description="MIME type")
    description: Optional[str] = Field(default="", max_length=500, description="Resource description")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Resource metadata")


class MCPToolCallSchema(BaseModel):
    """Schema for calling an MCP tool"""
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")

    @field_validator('arguments')
    @classmethod
    def validate_arguments(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure arguments is a dictionary
        if not isinstance(v, dict):
            raise ValueError('Arguments must be a dictionary')
        # Check for reasonable size (prevent DoS)
        if len(str(v)) > 10000:  # 10KB limit
            raise ValueError('Arguments payload too large (max 10KB)')
        return v


class MCPPromptGetSchema(BaseModel):
    """Schema for getting an MCP prompt"""
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Prompt arguments")

    @field_validator('arguments')
    @classmethod
    def validate_arguments(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError('Arguments must be a dictionary')
        if len(str(v)) > 10000:  # 10KB limit
            raise ValueError('Arguments payload too large (max 10KB)')
        return v


class MCPClientCreateSchema(BaseModel):
    """Schema for creating an MCP client"""
    name: str = Field(..., min_length=1, max_length=100, description="Client name")
    description: Optional[str] = Field(default="", max_length=500, description="Client description")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Client configuration")

    @field_validator('name')
    @classmethod
    def name_must_be_alphanumeric(cls, v: str) -> str:
        if not v.replace('-', '').replace('_', '').replace(' ', '').isalnum():
            raise ValueError('Name must contain only alphanumeric characters, hyphens, underscores, and spaces')
        return v
