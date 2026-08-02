"""Pydantic schemas for SFT, DPO, and PRM export formats."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Standard OpenAI / HuggingFace chat message."""
    role: str
    content: str


class SFTRow(BaseModel):
    """Supervised Fine-Tuning row format for SFTTrainer."""
    messages: list[ChatMessage]
    metadata: dict[str, Any] = Field(default_factory=dict)


class DPORow(BaseModel):
    """Direct Preference Optimization row format for DPOTrainer."""
    prompt: list[ChatMessage]
    chosen: list[ChatMessage]
    rejected: list[ChatMessage]
    metadata: dict[str, Any] = Field(default_factory=dict)


class PRMRow(BaseModel):
    """Process Reward Model row format for PRMTrainer."""
    prompt: str
    completions: list[str]
    labels: list[float]
    metadata: dict[str, Any] = Field(default_factory=dict)
