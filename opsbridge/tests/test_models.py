"""Tests for data models."""

import pytest
from hypothesis import given, settings, strategies as st
from pydantic import ValidationError

from opsbridge.models import (
    Diagnosis,
    LogEntry,
    RestartRequest,
    RestartResult,
    SessionHealthResult,
)


class TestLogEntry:
    """Test LogEntry model."""
    
    def test_valid_construction(self):
        """Test valid LogEntry construction."""
        log = LogEntry(
            timestamp="2025-01-15T10:23:01Z",
            level="ERROR",
            message="Aborting session for identity: null",
            transaction_id="2607884200"
        )
        assert log.timestamp == "2025-01-15T10:23:01Z"
        assert log.level == "ERROR"
        assert log.message == "Aborting session for identity: null"
        assert log.transaction_id == "2607884200"
    
    def test_valid_construction_without_transaction_id(self):
        """Test valid LogEntry construction without optional transaction_id."""
        log = LogEntry(
            timestamp="2025-01-15T10:23:01Z",
            level="INFO",
            message="Service health check passed"
        )
        assert log.timestamp == "2025-01-15T10:23:01Z"
        assert log.level == "INFO"
        assert log.message == "Service health check passed"
        assert log.transaction_id is None
    
    def test_missing_required_fields(self):
        """Test ValidationError when required fields are missing."""
        with pytest.raises(ValidationError):
            LogEntry(level="ERROR", message="test")  # Missing timestamp
        
        with pytest.raises(ValidationError):
            LogEntry(timestamp="2025-01-15T10:23:01Z", message="test")  # Missing level
        
        with pytest.raises(ValidationError):
            LogEntry(timestamp="2025-01-15T10:23:01Z", level="ERROR")  # Missing message
    
    def test_wrong_types(self):
        """Test ValidationError when fields have wrong types."""
        with pytest.raises(ValidationError):
            LogEntry(
                timestamp=123,  # Should be string
                level="ERROR",
                message="test"
            )
        
        with pytest.raises(ValidationError):
            LogEntry(
                timestamp="2025-01-15T10:23:01Z",
                level=123,  # Should be string
                message="test"
            )
        
        with pytest.raises(ValidationError):
            LogEntry(
                timestamp="2025-01-15T10:23:01Z",
                level="ERROR",
                message=123  # Should be string
            )


class TestSessionHealthResult:
    """Test SessionHealthResult model."""
    
    def test_valid_construction(self):
        """Test valid SessionHealthResult construction."""
        health = SessionHealthResult(
            used_keys=847,
            capacity=1000,
            eviction_policy="allkeys-lru"
        )
        assert health.used_keys == 847
        assert health.capacity == 1000
        assert health.eviction_policy == "allkeys-lru"
    
    def test_missing_required_fields(self):
        """Test ValidationError when required fields are missing."""
        with pytest.raises(ValidationError):
            SessionHealthResult(used_keys=847, capacity=1000)  # Missing eviction_policy
        
        with pytest.raises(ValidationError):
            SessionHealthResult(used_keys=847, eviction_policy="allkeys-lru")  # Missing capacity
        
        with pytest.raises(ValidationError):
            SessionHealthResult(capacity=1000, eviction_policy="allkeys-lru")  # Missing used_keys
    
    def test_wrong_types(self):
        """Test ValidationError when fields have wrong types."""
        with pytest.raises(ValidationError):
            SessionHealthResult(
                used_keys="not_a_number",  # Should be int and not convertible
                capacity=1000,
                eviction_policy="allkeys-lru"
            )


class TestRestartRequest:
    """Test RestartRequest model."""
    
    def test_valid_construction(self):
        """Test valid RestartRequest construction."""
        request = RestartRequest(service_name="target-service")
        assert request.service_name == "target-service"
    
    def test_missing_required_field(self):
        """Test ValidationError when service_name is missing."""
        with pytest.raises(ValidationError):
            RestartRequest()
    
    def test_wrong_type(self):
        """Test ValidationError when service_name has wrong type."""
        with pytest.raises(ValidationError):
            RestartRequest(service_name=123)  # Should be string


class TestRestartResult:
    """Test RestartResult model."""
    
    def test_valid_construction_simulated_complete(self):
        """Test valid RestartResult construction with simulated_complete status."""
        result = RestartResult(
            service_name="target-service",
            restart_timestamp="2025-01-15T10:23:01Z",
            status="simulated_complete"
        )
        assert result.service_name == "target-service"
        assert result.restart_timestamp == "2025-01-15T10:23:01Z"
        assert result.status == "simulated_complete"
    
    def test_valid_construction_rejected(self):
        """Test valid RestartResult construction with rejected status."""
        result = RestartResult(
            service_name="target-service",
            restart_timestamp="2025-01-15T10:23:01Z",
            status="rejected"
        )
        assert result.status == "rejected"
    
    def test_valid_construction_timeout(self):
        """Test valid RestartResult construction with timeout status."""
        result = RestartResult(
            service_name="target-service",
            restart_timestamp="2025-01-15T10:23:01Z",
            status="timeout"
        )
        assert result.status == "timeout"
    
    def test_missing_required_fields(self):
        """Test ValidationError when required fields are missing."""
        with pytest.raises(ValidationError):
            RestartResult(
                service_name="target-service",
                restart_timestamp="2025-01-15T10:23:01Z"
            )  # Missing status


class TestDiagnosis:
    """Test Diagnosis model."""
    
    def test_valid_construction(self):
        """Test valid Diagnosis construction."""
        health = SessionHealthResult(
            used_keys=847,
            capacity=1000,
            eviction_policy="allkeys-lru"
        )
        
        diagnosis = Diagnosis(
            error_classification="isolated_glitch",
            affected_component="ServiceHandler",
            probable_root_cause="Transient session identity reference loss",
            session_cache_utilization=health,
            recommended_action="monitor"
        )
        
        assert diagnosis.error_classification == "isolated_glitch"
        assert diagnosis.affected_component == "ServiceHandler"
        assert diagnosis.probable_root_cause == "Transient session identity reference loss"
        assert diagnosis.session_cache_utilization == health
        assert diagnosis.recommended_action == "monitor"
        assert diagnosis.diagnosis_id is not None  # Auto-generated UUID
        assert len(diagnosis.diagnosis_id) == 36  # UUID format
    
    def test_auto_generated_diagnosis_id(self):
        """Test that diagnosis_id is auto-generated and unique."""
        health = SessionHealthResult(
            used_keys=847,
            capacity=1000,
            eviction_policy="allkeys-lru"
        )
        
        diagnosis1 = Diagnosis(
            error_classification="isolated_glitch",
            affected_component="ServiceHandler",
            probable_root_cause="Transient session identity reference loss",
            session_cache_utilization=health,
            recommended_action="monitor"
        )
        
        diagnosis2 = Diagnosis(
            error_classification="isolated_glitch",
            affected_component="ServiceHandler",
            probable_root_cause="Transient session identity reference loss",
            session_cache_utilization=health,
            recommended_action="monitor"
        )
        
        assert diagnosis1.diagnosis_id != diagnosis2.diagnosis_id


# Feature: sentinel-cloud-mcp, Property 2: Malformed Input Rejection
@given(bad_input=st.fixed_dictionaries({"wrong_field": st.text()}))
@settings(max_examples=100)
def test_malformed_restart_input_rejection(bad_input):
    """Property 2: Malformed Input Rejection - Validates: Requirements 0.4"""
    with pytest.raises(ValidationError):
        RestartRequest(**bad_input)


@given(bad_input=st.fixed_dictionaries({"timestamp": st.just(123), "level": st.just("ERROR"), "message": st.just("test")}))
@settings(max_examples=100)
def test_malformed_log_entry_input_rejection(bad_input):
    """Property 2: Malformed Input Rejection - Validates: Requirements 0.4"""
    with pytest.raises(ValidationError):
        LogEntry(**bad_input)


@given(bad_input=st.fixed_dictionaries({"used_keys": st.just("not_a_number"), "capacity": st.just(1000), "eviction_policy": st.just("allkeys-lru")}))
@settings(max_examples=100)
def test_malformed_session_health_input_rejection(bad_input):
    """Property 2: Malformed Input Rejection - Validates: Requirements 0.4"""
    with pytest.raises(ValidationError):
        SessionHealthResult(**bad_input)
