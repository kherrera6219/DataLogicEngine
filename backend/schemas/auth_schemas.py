from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=1, max_length=512)
    remember: bool = False


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    username: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=512)


class TokenRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    token: str = Field(..., min_length=1, max_length=32)
