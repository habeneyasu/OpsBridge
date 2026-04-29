# Implementation Plan: OpsBridge MCP Server

## Overview

Implement a single-process Python MCP server (`stdio` transport) demonstrating the three-layer MCP architecture. Build foundation-first: project scaffolding → data models → mock state → logging utility → MCP primitives (resource, tools, prompt) → analyst logic → server wiring → entry point → tests → Claude Desktop config.

## Tasks

- [ ] 1. Project scaffolding
  - Create `opsbridge/` directory with `__init__.py`, `models.py`, `mock_state.py`, `prompts.py`, `server.py`
  - Create `opsbridge/scripts/` with `__init__.py` and `run_mcp_local.py`
  - Create `opsbridge/tests/` with `__init__.py` and empty test files: `test_models.py`, `test_mock_state.py`, `test_tools.py`, `test_resource.py`, `test_prompts.py`, `test_analyst_logic.py`
  - Create `pyproject.toml` with `[project]` metadata, dependencies (`mcp`, `pydantic>=2`, `hypothesis`, `pytest`), and `[build-system]` using `hatchling`
  - _Requirements: 0.1, 0.2_

- [ ] 2. Data models (`models.py`)
  - [ ] 2.1 Implement `LogEntry`, `SessionHealthResult`, `RestartRequest`, `RestartResult`, and `Diagnosis` Pydantic v2 models exactly as specified in the design
    - All fields typed; `Optional` fields have defaults; no business logic in models
    - _Requirements: 0.4, 2.3, 3.6, 5.5_

  - [ ]* 2.2 Write unit tests for data models (`test_models.py`)
    - Test valid construction, missing required fields raise `ValidationError`, wrong types raise `ValidationError`
    - Test `RestartResult.status` accepts `"simulated_complete"`, `"rejected"`, `"timeout"`
    - _Requirements: 0.4_

  - [ ]* 2.3 Write property test for malformed input rejection (`test_models.py`)
    - **Property 2: Malformed Input Rejection**
    - **Validates: Requirements 0.4**

- [ ] 3. Mock state (`mock_state.py`)
  - [ ] 3.1 Implement `MOCK_STATE` dict with `"logs"` and `"session_cache"` keys populated with the demo data from the design document
    - Include at least 10 log entries for `"target-service"` mixing `ERROR`, `INFO`, `WARN` levels; include the `"Aborting session for identity: null"` error entries
    - _Requirements: 1.1, 2.2_

  - [ ] 3.2 Implement `get_logs(service_name: str) -> list[dict]` and `get_session_cache() -> dict` accessor functions
    - `get_logs` returns empty list for unknown service names (no exception)
    - `get_session_cache` returns zero-value dict when key absent
    - _Requirements: 1.6, 2.4_

  - [ ]* 3.3 Write unit tests for mock state accessors (`test_mock_state.py`)
    - Test unknown service returns `[]`, absent session cache returns zero values, known service returns non-empty list
    - _Requirements: 1.6, 2.4_

  - [ ]* 3.4 Write property test for resource idempotence (`test_mock_state.py`)
    - **Property 1: Resource Idempotence**
    - **Validates: Requirements 0.3, 1.1, 1.4**

  - [ ]* 3.5 Write property test for session health round-trip (`test_mock_state.py`)
    - **Property 4: Session Health Round-Trip**
    - **Validates: Requirements 2.1, 2.4**

- [ ] 4. Structured logging utility (`server.py` — `emit_structured_log`)
  - [ ] 4.1 Implement `emit_structured_log(tool: str, intent: str, status: str, **extra) -> None` that writes a single JSON object to `sys.stderr`
    - JSON object must contain: `trace_id` (uuid4), `timestamp` (ISO 8601), `layer="mcp_server"`, `tool`, `intent`, `status`
    - Accept `**extra` kwargs (e.g., `error="..."`) merged into the emitted object
    - _Requirements: 0.6, 8.5_

  - [ ]* 4.2 Write property test for structured log emission (`test_tools.py`)
    - **Property 3: Structured Log Emission**
    - **Validates: Requirements 0.6, 8.5**

- [ ] 5. Log Stream Resource (`server.py`)
  - [ ] 5.1 Register the `logs://{service_name}/tail` resource handler using the MCP SDK's URI template API
    - Handler calls `get_logs(service_name)`, serializes each entry as a `LogEntry`, returns list as resource content
    - Include icon metadata annotation (`type="icon"`, `name="activity"`) on the resource definition
    - Return empty list (not an error) when service name is absent from `MOCK_STATE`
    - Emit one structured log entry per read via `emit_structured_log` with `intent="monitor_detection"`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_

  - [ ]* 5.2 Write unit tests for the log resource (`test_resource.py`)
    - Test known service returns non-empty list of valid `LogEntry`-shaped dicts
    - Test unknown service returns empty list without error
    - Test resource definition includes icon metadata (`type="icon"`, `name="activity"`)
    - _Requirements: 1.3, 1.6_

- [ ] 6. Session Health Tool (`server.py`)
  - [ ] 6.1 Register the `check_session_health` tool handler
    - No input parameters required; return `SessionHealthResult` sourced from `get_session_cache()`
    - Emit structured log with `intent="analyst_correlation"`, `status="ok"`
    - Return zero-value `SessionHealthResult` (not an exception) when cache is absent
    - _Requirements: 2.1, 2.2, 2.4_

  - [ ]* 6.2 Write unit tests for `check_session_health` (`test_tools.py`)
    - Test normal path returns values matching `MOCK_STATE["session_cache"]`
    - Test absent cache key returns zero values
    - _Requirements: 2.1, 2.4_

- [ ] 7. Restart Service Tool (`server.py`)
  - [ ] 7.1 Register the `restart_target_service` tool handler with `RestartRequest` as input schema
    - Call `ctx.elicit()` with a message containing the service name and approval prompt before any restart logic
    - On approval: `time.sleep(1)`, emit structured log with `status="elicitation_approved"`, return `RestartResult(status="simulated_complete")`
    - On rejection: emit log with `status="elicitation_rejected"`, return `RestartResult(status="rejected")`
    - On timeout: emit log with `status="error"` and `error="Elicitation timed out after 300s"`, return `RestartResult(status="timeout")`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 6.1, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 7.2 Write unit tests for `restart_target_service` (`test_tools.py`)
    - Test rejection path returns `status="rejected"` without sleeping
    - Test timeout path returns `status="timeout"`
    - Test approved path returns `status="simulated_complete"` with non-empty `restart_timestamp`
    - _Requirements: 3.4, 6.4, 6.5_

  - [ ]* 7.3 Write property test for elicitation required before restart (`test_tools.py`)
    - **Property 5: Elicitation Required Before Restart**
    - **Validates: Requirements 3.2, 3.5, 6.6**

  - [ ]* 7.4 Write property test for restart result completeness (`test_tools.py`)
    - **Property 6: Restart Result Completeness**
    - **Validates: Requirements 3.1, 3.4**

- [ ] 8. Checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Analyst logic (`server.py` or `models.py`)
  - [ ] 9.1 Implement `classify_error_ratio(ratio: float) -> str`
    - Returns `"isolated_glitch"` when `ratio < 0.10`, `"service_wide_failure"` when `ratio >= 0.10`
    - Boundary value `0.10` must return `"service_wide_failure"`
    - _Requirements: 5.2, 5.3, 5.4_

  - [ ] 9.2 Implement `build_diagnosis(log_entries: list[dict], cache_health: SessionHealthResult) -> Diagnosis`
    - Compute error ratio from `log_entries`, call `classify_error_ratio`
    - Set `affected_component="ServiceHandler"`, derive `probable_root_cause` from classification and cache state
    - Set `recommended_action="rolling_restart"` when root cause is session state corruption
    - Note cache unavailability in `probable_root_cause` when `cache_health.capacity == 0`
    - Generate `diagnosis_id` as a UUID4 string
    - _Requirements: 5.1, 5.2, 5.5, 5.6, 5.7_

  - [ ] 9.3 Implement `find_errors_after_restart(entries: list[dict], restart_timestamp: str) -> list[dict]`
    - Return only entries where `timestamp > restart_timestamp` AND `"identity: null"` in `message`
    - Entries at or before the restart timestamp must be excluded
    - _Requirements: 7.2_

  - [ ]* 9.4 Write property test for error ratio classification (`test_analyst_logic.py`)
    - **Property 7: Error Ratio Classification**
    - **Validates: Requirements 5.2, 5.3, 5.4**

  - [ ]* 9.5 Write property test for diagnosis completeness (`test_analyst_logic.py`)
    - **Property 8: Diagnosis Completeness**
    - **Validates: Requirements 5.5, 5.6**

  - [ ]* 9.6 Write property test for post-restart error detection (`test_analyst_logic.py`)
    - **Property 10: Post-Restart Error Detection**
    - **Validates: Requirements 7.2**

  - [ ]* 9.7 Write unit tests for analyst logic (`test_analyst_logic.py`)
    - Test `classify_error_ratio(0.0)` → `"isolated_glitch"`, `classify_error_ratio(0.10)` → `"service_wide_failure"`, `classify_error_ratio(0.50)` → `"service_wide_failure"`
    - Test `build_diagnosis` with zero-capacity cache notes unavailability in `probable_root_cause`
    - Test `find_errors_after_restart` excludes entries at or before restart timestamp
    - _Requirements: 5.3, 5.4, 5.7, 7.2_

- [ ] 10. MCP Prompt (`prompts.py`)
  - [ ] 10.1 Implement `build_incident_report_prompt(service_name: str, error_pattern: str, diagnosis_summary: str) -> mcp.types.PromptMessage`
    - Returned message text must contain all four sections: Detected Anomaly, System Health, Recommended Action, Approval Status
    - Message text must contain the literal `service_name` and `error_pattern` values
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ] 10.2 Register the `opsbridge_incident_report` prompt handler in `server.py`
    - Accept `service_name`, `error_pattern`, `diagnosis_summary` as prompt arguments
    - Delegate to `build_incident_report_prompt` and return the result
    - _Requirements: 9.1, 9.2_

  - [ ]* 10.3 Write unit tests for the prompt (`test_prompts.py`)
    - Test prompt exists and returns a `PromptMessage`
    - Test returned text contains `service_name`, `error_pattern`, and all four required sections
    - _Requirements: 9.2, 9.3, 9.5_

  - [ ]* 10.4 Write property test for prompt content completeness (`test_prompts.py`)
    - **Property 12: Prompt Content Completeness**
    - **Validates: Requirements 9.2, 9.3, 9.5**

- [ ] 11. Server wiring (`server.py`)
  - [ ] 11.1 Instantiate the `mcp.Server` instance and register all primitives: `logs://{service_name}/tail` resource, `check_session_health` tool, `restart_target_service` tool, `opsbridge_incident_report` prompt
    - Ensure all handlers are wired before `main()` is called
    - _Requirements: 0.1, 0.5_

  - [ ] 11.2 Implement `main()` that calls `mcp.run_stdio()` to start the stdio event loop
    - Guard with `if __name__ == "__main__": main()`
    - _Requirements: 0.2_

- [ ] 12. Entry point (`scripts/run_mcp_local.py`)
  - Implement thin entry point: `from opsbridge import server; server.main()`
  - This is the stable path referenced by the Claude Desktop config
  - _Requirements: 0.2_

- [ ] 13. Audit log helper (`server.py`)
  - [ ] 13.1 Implement `append_audit_log(outcome: dict, log_path: str = "opsbridge_audit.log") -> None`
    - Append one JSON line per call; each line contains the outcome dict serialized as JSON
    - _Requirements: 7.5_

  - [ ]* 13.2 Write property test for audit log round-trip (`test_tools.py`)
    - **Property 11: Audit Log Round-Trip**
    - **Validates: Requirements 7.5**

- [ ] 14. Checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Claude Desktop configuration and system prompt persona
  - [ ] 15.1 Create `claude_desktop_config.json` at the repo root with the MCP server entry for `"opsbridge"` using `uv --directory ... run scripts/run_mcp_local.py` and `ENVIRONMENT=local`
    - _Requirements: 0.2_

  - [ ] 15.2 Create `system_prompt.md` at the repo root defining the three agent personas (Monitor, Analyst, Remedy) with instructions for each role on which MCP primitive to call and when to hand off to the next persona
    - Monitor: read `logs://target-service/tail`, detect `"identity: null"` pattern
    - Analyst: call `check_session_health`, compute error ratio, produce Diagnosis summary
    - Remedy: call `restart_target_service` (requires elicitation), then call `opsbridge_incident_report`
    - _Requirements: 4.1, 4.2, 5.1, 6.1, 8.1, 8.2, 8.4_

- [ ] 16. Final checkpoint — ensure all tests pass
  - Run `pytest tests/ -v --hypothesis-show-statistics` and confirm all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Property tests use Hypothesis with `@settings(max_examples=100)` minimum; use 200 for Properties 7 and 10
- Each property test must include a comment: `# Feature: sentinel-cloud-mcp, Property N: <Title>`
- `emit_structured_log` must be implemented before any tool or resource handler (Task 4 before Tasks 5–7)
- Analyst logic functions (Task 9) are pure functions — no MCP SDK dependency — making them straightforward to unit and property test
- The `ctx.elicit()` call in `restart_target_service` must be mocked in tests using a fake context object
