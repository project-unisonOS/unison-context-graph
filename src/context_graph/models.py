"""Pydantic models for the context graph API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ContextDimension(BaseModel):
    name: str
    value: Any


class ContextPreferences(BaseModel):
    preferences: Dict[str, Any] = Field(default_factory=dict)


class ContextState(BaseModel):
    user_id: str
    dimensions: List[ContextDimension] = Field(default_factory=list)
    preferences: ContextPreferences = Field(default_factory=ContextPreferences)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContextUpdateRequest(BaseModel):
    user_id: str
    dimensions: Optional[List[ContextDimension]] = None
    preferences: Optional[ContextPreferences] = None


class ContextQueryRequest(BaseModel):
    user_id: str


class ContextStateResponse(BaseModel):
    state: ContextState


class EventTrace(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReplayRequest(BaseModel):
    user_id: str
    trace: List[EventTrace] = Field(default_factory=list)


class TraceListResponse(BaseModel):
    traces: List[EventTrace] = Field(default_factory=list)
