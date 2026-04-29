"""Mock state and accessor functions for OpsBridge MCP server."""

from typing import Any, Dict, List


# Single source of truth for demo state
MOCK_STATE: Dict[str, Any] = {
    "logs": {
        "target-service": [
            {
                "timestamp": "2025-01-15T10:23:00Z",
                "level": "ERROR",
                "message": "Aborting session for identity: null",
                "transaction_id": "2607884200"
            },
            {
                "timestamp": "2025-01-15T10:23:01Z",
                "level": "INFO",
                "message": "Subscription status: SUCCESS - Regular Product",
                "transaction_id": "2607884201"
            },
            {
                "timestamp": "2025-01-15T10:23:02Z",
                "level": "WARN",
                "message": "Cache utilization approaching threshold: 85%",
                "transaction_id": "2607884202"
            },
            {
                "timestamp": "2025-01-15T10:23:03Z",
                "level": "INFO",
                "message": "Service health check passed",
                "transaction_id": "2607884203"
            },
            {
                "timestamp": "2025-01-15T10:23:04Z",
                "level": "ERROR",
                "message": "Aborting session for identity: null",
                "transaction_id": "2607884204"
            },
            {
                "timestamp": "2025-01-15T10:23:05Z",
                "level": "INFO",
                "message": "User authentication successful",
                "transaction_id": "2607884205"
            },
            {
                "timestamp": "2025-01-15T10:23:06Z",
                "level": "DEBUG",
                "message": "Session cache stats: 847/1000 keys used",
                "transaction_id": "2607884206"
            },
            {
                "timestamp": "2025-01-15T10:23:07Z",
                "level": "INFO",
                "message": "Request processed successfully",
                "transaction_id": "2607884207"
            },
            {
                "timestamp": "2025-01-15T10:23:08Z",
                "level": "WARN",
                "message": "High memory usage detected in session cache",
                "transaction_id": "2607884208"
            },
            {
                "timestamp": "2025-01-15T10:23:09Z",
                "level": "ERROR",
                "message": "Aborting session for identity: null",
                "transaction_id": "2607884209"
            },
            {
                "timestamp": "2025-01-15T10:23:10Z",
                "level": "INFO",
                "message": "Service restart initiated",
                "transaction_id": "2607884210"
            },
            {
                "timestamp": "2025-01-15T10:23:11Z",
                "level": "INFO",
                "message": "Service restart completed successfully",
                "transaction_id": "2607884211"
            }
        ]
    },
    "session_cache": {
        "used_keys": 847,
        "capacity": 1000,
        "eviction_policy": "allkeys-lru"
    }
}


def get_logs(service_name: str) -> List[Dict[str, Any]]:
    """Get log entries for a specific service.
    
    Args:
        service_name: Name of the service to get logs for
        
    Returns:
        List of log entry dictionaries, empty list if service not found
    """
    return MOCK_STATE.get("logs", {}).get(service_name, [])


def get_session_cache() -> Dict[str, Any]:
    """Get session cache metrics.
    
    Returns:
        Dictionary containing session cache metrics, or zero values if not available
    """
    return MOCK_STATE.get("session_cache", {
        "used_keys": 0,
        "capacity": 0,
        "eviction_policy": "unknown"
    })
