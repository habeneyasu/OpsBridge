"""Pydantic data models for OpsBridge MCP server."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """Represents a single line from the mock log stream."""
    
    timestamp: str = Field(..., description="ISO 8601 timestamp, e.g. '2025-01-15T10:23:01Z'")
    level: str = Field(..., description="Log level: ERROR, INFO, WARN, or DEBUG")
    message: str = Field(..., description="Raw log message text")
    transaction_id: Optional[str] = Field(None, description="Correlation ID, may be absent")


class SessionHealthResult(BaseModel):
    """Returned by check_session_health. Maps directly to MOCK_STATE['session_cache']."""
    
    used_keys: int = Field(..., description="Number of keys currently in cache")
    capacity: int = Field(..., description="Maximum key capacity")
    eviction_policy: str = Field(..., description="Redis eviction policy string, e.g. 'allkeys-lru'")


class RestartRequest(BaseModel):
    """Input schema for restart_target_service."""
    
    service_name: str = Field(..., description="Identifier of the service to restart")


class RestartResult(BaseModel):
    """Output of restart_target_service on both approval and rejection paths."""
    
    service_name: str = Field(..., description="Name of the restarted service")
    restart_timestamp: str = Field(..., description="ISO 8601 timestamp of when restart was simulated")
    status: str = Field(..., description="Status: 'simulated_complete', 'rejected', or 'timeout'")


class Diagnosis(BaseModel):
    """Produced by the Analyst persona. Passed to the Remedy persona and referenced in the incident report prompt."""
    
    error_classification: str = Field(..., description="Error classification: 'isolated_glitch' or 'service_wide_failure'")
    affected_component: str = Field(..., description="e.g. 'ServiceHandler'")
    probable_root_cause: str = Field(..., description="Human-readable root cause string")
    session_cache_utilization: SessionHealthResult = Field(..., description="Session cache metrics")
    recommended_action: str = Field(..., description="Recommended action: 'rolling_restart' or 'monitor'")
    diagnosis_id: str = Field(default_factory=lambda: str(uuid4()), description="UUID4 string for traceability")
