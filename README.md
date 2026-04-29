# OpsBridge MCP Server

A demonstration of the three-layer Model Context Protocol (MCP) architecture for cloud operations automation.

## Overview

OpsBridge showcases how MCP eliminates the N×M integration problem in multi-agent systems by providing a standardized protocol layer where agents consume Resources, invoke Tools, and receive Prompts through a single, composable interface.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  HOST APPLICATION (Claude Desktop / Cursor)                     │
│                                                                 │
│  System Prompt defines three personas:                          │
│    1. Monitor  → reads logs Resource, detects anomalies         │
│    2. Analyst  → calls check_session_health, produces Diagnosis │
│    3. Remedy   → calls restart_target_service (with elicitation)│
│                                                                 │
│  Orchestration: Host LLM switches persona based on data flow    │
└────────────────────────┬────────────────────────────────────────┘
                         │  JSON-RPC over stdio
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  MCP CLIENT (Python MCP SDK)                                    │
│                                                                 │
│  - Negotiates capabilities with server                          │
│  - Serializes/deserializes JSON-RPC messages                    │
│  - Routes resources/read, tools/call, prompts/get requests      │
│  - Handles elicitation response lifecycle                       │
└────────────────────────┬────────────────────────────────────────┘
                         │  stdio (stdin/stdout)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  MCP SERVER (opsbridge/server.py)                               │
│                                                                 │
│  ├── Resource:  logs://{service_name}/tail                      │
│  ├── Tool:      check_session_health                            │
│  ├── Tool:      restart_target_service                          │
│  └── Prompt:    opsbridge_incident_report                       │
│                                                                 │
│  All handlers emit structured JSON logs to stderr               │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Status

### ✅ Completed Tasks

- **Task 1**: Project scaffolding
  - Directory structure with `opsbridge/`, `opsbridge/scripts/`, `opsbridge/tests/`
  - `pyproject.toml` with MCP, Pydantic, and testing dependencies
  - Empty test files for all components

- **Task 2**: Data models
  - `LogEntry`, `SessionHealthResult`, `RestartRequest`, `RestartResult`, `Diagnosis` Pydantic models
  - Comprehensive unit and property testing (19 tests total)
  - Property 2: Malformed Input Rejection validation

- **Task 3**: Mock state
  - `MOCK_STATE` dict with demo log data and session cache metrics
  - `get_logs()` and `get_session_cache()` accessor functions
  - Unit and property tests (8 tests total)
  - Property 1: Resource Idempotence
  - Property 4: Session Health Round-Trip

### 🚧 In Progress

- **Task 4**: Structured logging utility
- **Task 5**: Log Stream Resource
- **Task 6**: Session Health Tool
- **Task 7**: Restart Service Tool

### 📋 Planned

- **Task 8**: Analyst logic functions
- **Task 9**: MCP Prompt
- **Task 10**: Server wiring
- **Task 11**: Entry point
- **Task 12**: Comprehensive testing
- **Task 13**: Claude Desktop configuration

## Agent Flow

The system simulates a cloud operations incident response workflow:

1. **Monitor** reads from `logs://target-service/tail` Resource
2. **Monitor** detects "Aborting session for identity: null" anomalies
3. **Analyst** calls `check_session_health` Tool to assess system state
4. **Analyst** computes error ratio and produces Diagnosis
5. **Remedy** requests human approval via `ctx.elicit()` for service restart
6. **Remedy** calls `restart_target_service` Tool (if approved)
7. **Remedy** generates incident report using `opsbridge_incident_report` Prompt

## Development

### Prerequisites

- Python 3.8+
- uv (recommended) or pip
- Claude Desktop or Cursor (for MCP integration)

### Setup

```bash
# Clone the repository
git clone https://github.com/habeneyasu/OpsBridge.git
cd OpsBridge

# Install dependencies
uv sync  # or: pip install -e ".[dev]"

# Run tests
pytest opsbridge/tests/ -v --hypothesis-show-statistics
```

### Project Structure

```
opsbridge/
├── __init__.py              # Package initialization
├── models.py                # Pydantic data models
├── mock_state.py            # Mock state and accessors
├── server.py                # MCP server implementation
├── analyst_logic.py         # Error classification logic
├── prompts.py               # MCP prompt definitions
└── scripts/
    └── run_mcp_local.py     # Entry point for Claude Desktop
```

## Testing

The project uses both unit tests and property-based testing:

- **Unit tests**: Verify specific examples and edge cases
- **Property tests**: Use Hypothesis to validate universal behaviors

Run tests with:
```bash
pytest opsbridge/tests/ -v --hypothesis-show-statistics
```

## MCP Integration

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "opsbridge": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/opsbridge",
        "run",
        "scripts/run_mcp_local.py"
      ],
      "env": {
        "ENVIRONMENT": "local"
      }
    }
  }
}
```

## Production Roadmap

Each demo component maps to production equivalents:

| Demo Component | Production Equivalent |
|---|---|
| `MOCK_STATE["logs"]` | CloudWatch Logs Insights / Grafana Loki |
| `MOCK_STATE["session_cache"]` | Redis with INFO memory + DBSIZE commands |
| `stdio` transport | HTTP with SSE + OAuth 2.1 PKCE |
| `time.sleep(1)` restart | Docker SDK or AWS ECS restart signal |
| Single-process roles | Separate agent processes with A2A coordination |

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Ensure all tests pass
5. Submit a pull request

## Requirements Traceability

- **Requirement 0.1**: Three-layer MCP architecture ✅
- **Requirement 0.2**: stdio transport configuration ✅
- **Requirement 0.4**: Input schema validation ✅
- **Requirement 1.1**: Log Resource implementation 🚧
- **Requirement 2.2**: Session cache metrics ✅
- **Requirement 3.6**: Restart Tool models ✅
- **Requirement 5.5**: Diagnosis model ✅
