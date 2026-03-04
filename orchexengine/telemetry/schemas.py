"""Pydantic schemas for telemetry data"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class RoutingDecision(BaseModel):
    """Routing decision information"""
    target: str = Field(..., description="Selected provider: 'local' or 'cloud'")
    reason: str = Field(..., description="Reason for routing decision")
    can_fallback: bool = Field(default=True, description="Whether fallback is allowed")


class TelemetryData(BaseModel):
    """Telemetry data for a single request"""
    request_id: str = Field(..., description="Unique request identifier")
    selected_model: str = Field(..., description="Model used for the request")
    provider: str = Field(..., description="Provider: 'local' or 'cloud'")
    latency_ms: int = Field(..., description="Response latency in milliseconds")
    input_tokens: int = Field(default=0, description="Prompt tokens used")
    output_tokens: int = Field(default=0, description="Completion tokens used")
    estimated_cost: Optional[float] = Field(default=None, description="Estimated cost in USD")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    routing_reason: str = Field(..., description="Why this model was selected")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "abc123",
                "selected_model": "ollama/qwen3:8b",
                "provider": "local",
                "latency_ms": 1250,
                "input_tokens": 150,
                "output_tokens": 300,
                "estimated_cost": None,
                "error": None,
                "routing_reason": "Default to local model",
            }
        }
