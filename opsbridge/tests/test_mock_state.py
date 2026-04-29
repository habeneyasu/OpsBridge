"""Tests for mock state accessors."""

from hypothesis import given, settings, strategies as st

from opsbridge.mock_state import get_logs, get_session_cache, MOCK_STATE


class TestMockStateAccessors:
    """Test mock state accessor functions."""
    
    def test_get_logs_known_service(self):
        """Test get_logs returns non-empty list for known service."""
        logs = get_logs("target-service")
        assert isinstance(logs, list)
        assert len(logs) > 0
        assert all(isinstance(log, dict) for log in logs)
        assert all("timestamp" in log for log in logs)
        assert all("level" in log for log in logs)
        assert all("message" in log for log in logs)
    
    def test_get_logs_unknown_service(self):
        """Test get_logs returns empty list for unknown service."""
        logs = get_logs("nonexistent-service-xyz")
        assert logs == []
        assert isinstance(logs, list)
    
    def test_get_session_cache_normal(self):
        """Test get_session_cache returns normal values."""
        cache = get_session_cache()
        assert isinstance(cache, dict)
        assert "used_keys" in cache
        assert "capacity" in cache
        assert "eviction_policy" in cache
        assert cache["used_keys"] > 0
        assert cache["capacity"] > 0
        assert cache["eviction_policy"] != "unknown"
    
    def test_get_session_cache_zero_values(self):
        """Test get_session_cache returns zero values when cache absent."""
        # Temporarily remove session cache
        original_cache = MOCK_STATE.pop("session_cache", None)
        
        try:
            cache = get_session_cache()
            assert cache["used_keys"] == 0
            assert cache["capacity"] == 0
            assert cache["eviction_policy"] == "unknown"
        finally:
            # Restore original cache
            if original_cache:
                MOCK_STATE["session_cache"] = original_cache
    
    def test_get_logs_structure(self):
        """Test get_logs returns properly structured entries."""
        logs = get_logs("target-service")
        for log in logs:
            assert isinstance(log["timestamp"], str)
            assert isinstance(log["level"], str)
            assert isinstance(log["message"], str)
            assert log["level"] in ["ERROR", "INFO", "WARN", "DEBUG"]
            # transaction_id is optional
            if "transaction_id" in log:
                assert isinstance(log["transaction_id"], str)
    
    def test_null_identity_errors_present(self):
        """Test that null identity error entries are present."""
        logs = get_logs("target-service")
        error_logs = [
            log for log in logs 
            if log["level"] == "ERROR" and "identity: null" in log["message"]
        ]
        assert len(error_logs) > 0
        assert all("Aborting session for identity: null" in log["message"] for log in error_logs)


# Feature: sentinel-cloud-mcp, Property 1: Resource Idempotence
@given(service_name=st.sampled_from(list(MOCK_STATE["logs"].keys())))
@settings(max_examples=100)
def test_resource_idempotence(service_name):
    """Property 1: Resource Idempotence - Validates: Requirements 0.3, 1.1, 1.4"""
    result_a = get_logs(service_name)
    result_b = get_logs(service_name)
    assert result_a == result_b
    for entry in result_a:
        assert entry["timestamp"] is not None
        assert entry["level"] is not None
        assert entry["message"] is not None


# Feature: sentinel-cloud-mcp, Property 4: Session Health Round-Trip
@given(used=st.integers(min_value=0, max_value=10000),
       capacity=st.integers(min_value=1, max_value=10000),
       policy=st.sampled_from(["allkeys-lru", "volatile-lru", "noeviction"]))
@settings(max_examples=100)
def test_session_health_round_trip(used, capacity, policy):
    """Property 4: Session Health Round-Trip - Validates: Requirements 2.1, 2.4"""
    # Temporarily set session cache
    original_cache = MOCK_STATE.get("session_cache")
    MOCK_STATE["session_cache"] = {"used_keys": used, "capacity": capacity, "eviction_policy": policy}
    
    try:
        result = get_session_cache()
        assert result["used_keys"] == used
        assert result["capacity"] == capacity
        assert result["eviction_policy"] == policy
    finally:
        # Restore original cache
        if original_cache:
            MOCK_STATE["session_cache"] = original_cache
        else:
            MOCK_STATE.pop("session_cache", None)
