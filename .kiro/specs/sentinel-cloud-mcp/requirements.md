# Requirements Document

## Introduction

OpsBridge is a demo MCP server that showcases the three-layer Model Context Protocol (MCP) architecture: Host Application → MCP Client → MCP Server. This architecture eliminates the N×M point-to-point integration problem that plagues traditional agent-to-service communication. Instead of each agent implementing custom connectors to every service, MCP provides a standardized protocol layer where agents consume Resources, invoke Tools, and receive Prompts through a single, composable interface.

This demo runs on `stdio` transport. Production deployment would add OAuth 2.1, Redis, OpenTelemetry, and circuit breakers — see Production Roadmap.

The system simulates a live service monitoring scenario: a Monitor role reads from a mock log Resource, an Analyst role correlates anomalies against mock session health, and a Remedy role requests human approval via `ctx.elicit()` before simulating a service restart. All three roles are implemented as logic within a single MCP server script. The Host (Claude Desktop or Cursor) orchestrates the Monitor → Analyst → Remedy flow via system prompt persona instructions.

---

## Glossary

- **MCP_Host**: The AI application layer (e.g., Claude Desktop, Cursor) that initiates connections, manages UI, and controls user preferences.
- **MCP_Client**: The protocol layer (Python MCP SDK) that negotiates with the server and handles JSON-RPC messages.
- **MCP_Server**: The custom server script that exposes Resources, Tools, and Prompts to the Host.
- **Transport**: `stdio` for this demo; HTTP with SSE for production.
- **Resource**: An MCP primitive that exposes read-only or subscribable data (e.g., mock log entries).
- **Tool**: An MCP primitive that exposes executable actions with a validated JSON Schema `inputSchema`.
- **Prompt**: An MCP primitive that provides pre-canned instructions guiding the LLM on when and how to use a tool or interpret a situation.
- **Elicitation**: An MCP-native human-in-the-loop approval mechanism (`ctx.elicit()`) that pauses execution for operator confirmation before dangerous actions.
- **Mock_State**: The in-memory Python dict simulating external service state (session cache, log entries) for demo purposes.
- **Monitor_Agent**: The agent role responsible for reading the mock log Resource and detecting anomalies.
- **Analyst_Agent**: The agent role responsible for correlating detected anomalies with mock session health and producing a Diagnosis.
- **Remedy_Agent**: The agent role responsible for requesting human approval and simulating a service restart.
- **Log_Stream**: The mock log feed exposed as the MCP Resource `logs://{service_name}/tail`.
- **Target_Service**: The microservice under observation, identified as `ServiceHandler`.
- **Session_Cache**: In-memory Python dict (demo); Redis-backed cache (production).
- **Null_Identity_Error**: The anomaly pattern `"Aborting session for identity: null"` indicating a lost identity reference during an Abort handshake.
- **Diagnosis**: A structured Pydantic model produced by the Analyst role describing the error classification, affected component, and recommended action.

---

## Requirements

### Requirement 0: MCP Architecture Foundation

**User Story:** As a system architect, I want the demo to be built on the three-layer MCP model using stdio transport, so that the architecture is clearly demonstrable without production infrastructure dependencies.

#### Acceptance Criteria

1. THE MCP_Server SHALL implement the three-layer MCP architecture: Host Application → MCP Client → MCP Server.
2. THE MCP_Server SHALL use `stdio` transport for all client-server communication in this demo.
3. THE MCP_Server SHALL be stateless by design — each `tools/call` and `resources/read` request SHALL be processable independently using Mock_State, without relying on in-process variables shared across requests.
4. ALL Tool definitions SHALL include a complete Pydantic model defining the `inputSchema`; the server SHALL validate inputs against this schema and reject malformed requests with standard JSON-RPC error codes.
5. THE MCP_Server SHALL expose at least one MCP Prompt to guide the LLM on how to interpret and summarize an incident.
6. THE MCP_Server SHALL emit structured JSON logs to stderr for every Tool invocation and Resource read, including: `trace_id`, `tool_name` or `resource_uri`, `intent`, and `result_status`.

> Production Roadmap: OAuth 2.1 + PKCE (mandatory for remote MCP servers per March 2025 spec), Redis-backed Session_Cache, OpenTelemetry tracing with JSON-RPC span tracking, circuit breakers via pybreaker, Redis token-bucket rate limiting, secrets via AWS Secrets Manager or Doppler.

---

### Requirement 1: MCP Server — Log Stream Resource

**User Story:** As an agent or operator, I want to read recent mock service logs through a stable MCP Resource, so that the demo proves the N×M problem solution via URI-templated Resources.

#### Acceptance Criteria

1. THE MCP_Server SHALL expose a Resource using URI template `logs://{service_name}/tail` that returns the most recent entries from the in-memory mock log list for the requested service.
2. THE Resource SHALL support dynamic service name substitution so any service identifier can be passed as the `service_name` parameter.
3. THE Resource SHALL include icon metadata so it is visually identifiable in MCP Inspector and compatible UIs.
4. WHEN a client reads `logs://{service_name}/tail`, THE MCP_Server SHALL return the mock log entries in structured format, preserving timestamp, log level, and message fields.
5. WHEN a client subscribes to `logs://{service_name}/tail`, THE MCP_Server SHALL push updated mock log entries to the client as new entries are appended to the in-memory list.
6. IF the requested `service_name` has no entries in Mock_State, THEN THE MCP_Server SHALL return an empty list and SHALL NOT return an error.

---

### Requirement 2: MCP Server — Session Health Tool

**User Story:** As the Analyst role, I want to query mock session cache utilization on demand, so that I can determine whether a Null_Identity_Error is caused by cache exhaustion or eviction.

#### Acceptance Criteria

1. THE MCP_Server SHALL expose a Tool named `check_session_health` that returns current Mock_State session utilization metrics.
2. WHEN `check_session_health` is invoked, THE MCP_Server SHALL return: `used_keys` count, `capacity`, and `eviction_policy` string — all sourced from Mock_State.
3. THE Tool input and output SHALL be defined as Pydantic models enforcing strict JSON Schema validation.
4. IF Mock_State is empty or uninitialized, THEN THE MCP_Server SHALL return a structured response with zero values rather than raising an unhandled exception.

> Production equivalent: `check_session_health` queries a live Redis instance for `INFO memory` and `DBSIZE` metrics.

---

### Requirement 3: MCP Server — Restart Service Tool

**User Story:** As the Remedy role, I want to simulate a controlled restart of the Target_Service through an MCP Tool, so that the demo shows human-approved remediation without requiring real container infrastructure.

#### Acceptance Criteria

1. THE MCP_Server SHALL expose a Tool named `restart_target_service` that simulates a restart of the named service.
2. WHEN `restart_target_service` is invoked, THE MCP_Server SHALL require prior human approval via `ctx.elicit()` before executing any restart simulation.
3. WHEN the restart simulation runs, THE MCP_Server SHALL execute `time.sleep(1)` and emit a structured JSON log entry to stderr indicating the simulated restart completed.
4. WHEN `restart_target_service` completes, THE MCP_Server SHALL return a status object containing: `service_name`, `restart_timestamp`, and `status` field set to `"simulated_complete"`.
5. IF a restart invocation is received without a preceding approved Elicitation for that request, THEN THE MCP_Server SHALL reject the invocation and return a JSON-RPC error.
6. THE Tool input and output SHALL be defined as Pydantic models enforcing strict JSON Schema validation.

> Production equivalent: `restart_target_service` sends a restart signal to a Docker daemon or AWS ECS task via the container orchestration API.

---

### Requirement 4: Monitor Role — Anomaly Detection

**User Story:** As an operator, I want the Monitor role to detect Null_Identity_Error patterns in the mock log Resource, so that the demo shows automated anomaly detection without manual log watching.

#### Acceptance Criteria

1. THE Monitor_Agent SHALL read from the `logs://{service_name}/tail` Resource to obtain the current mock log entries.
2. WHEN a log entry matching the pattern `"Aborting session for identity: null"` is found, THE Monitor_Agent SHALL emit an anomaly event containing: the matched log line, associated transaction ID, timestamp, and current error rate (errors per minute derived from mock data).
3. THE Monitor_Agent SHALL track the count of Null_Identity_Error occurrences within the in-memory mock log list and include the count in each anomaly event.
4. WHEN the Monitor_Agent emits an anomaly event, THE Monitor_Agent SHALL make the event available for the Analyst role to consume via an MCP Tool call or Resource read — not via a direct in-process function call.
5. IF no Null_Identity_Error pattern is found in the current log entries, THEN THE Monitor_Agent SHALL emit a clean-state event indicating no anomalies detected.

---

### Requirement 5: Analyst Role — Error Correlation and Diagnosis

**User Story:** As an operator, I want the Analyst role to distinguish between isolated glitches and service-wide failures using mock data, so that the remediation response is proportionate to the simulated impact.

#### Acceptance Criteria

1. WHEN the Analyst_Agent receives an anomaly event, THE Analyst_Agent SHALL invoke `check_session_health` to retrieve current Mock_State metrics before producing a Diagnosis.
2. WHEN producing a Diagnosis, THE Analyst_Agent SHALL compute the ratio of failed-to-successful sessions from the mock log entries within the available window.
3. WHEN the failed-to-successful session ratio is below 10%, THE Analyst_Agent SHALL classify the anomaly as an isolated glitch in the Diagnosis.
4. WHEN the failed-to-successful session ratio is 10% or above, THE Analyst_Agent SHALL classify the anomaly as a service-wide failure in the Diagnosis.
5. THE Diagnosis SHALL be a Pydantic model containing: `error_classification`, `affected_component`, `probable_root_cause`, `session_cache_utilization`, and `recommended_action`.
6. WHEN the Diagnosis identifies probable root cause as session state corruption, THE Analyst_Agent SHALL set `recommended_action` to `"rolling_restart"`.
7. IF `check_session_health` returns zero values, THEN THE Analyst_Agent SHALL produce a Diagnosis based on log data alone and SHALL note cache unavailability in the `probable_root_cause` field.

---

### Requirement 6: Remedy Role — Human-in-the-Loop Approval

**User Story:** As an operator, I want to approve or reject any restart action before it is executed, so that automated remediation cannot disrupt the service without my explicit consent.

#### Acceptance Criteria

1. WHEN the Remedy_Agent receives a Diagnosis with `recommended_action` set to `"rolling_restart"`, THE Remedy_Agent SHALL invoke `ctx.elicit()` presenting the operator with the message: "OpsBridge wants to restart the Service Handler to fix session null errors. Approve?"
2. THE Elicitation SHALL include: the Diagnosis summary, the affected component name, and the proposed action.
3. WHEN the operator approves the Elicitation, THE Remedy_Agent SHALL invoke `restart_target_service` within 5 seconds of receiving approval.
4. WHEN the operator rejects the Elicitation, THE Remedy_Agent SHALL emit a structured JSON log entry recording the rejection with timestamp and SHALL take no further automated action for that Diagnosis.
5. IF the Elicitation receives no response within 5 minutes, THEN THE Remedy_Agent SHALL treat the request as rejected and SHALL emit a timeout log entry.
6. THE Remedy_Agent SHALL NOT invoke `restart_target_service` under any circumstance without a prior affirmative `ctx.elicit()` response for that specific Diagnosis.

---

### Requirement 7: Remedy Role — Post-Restart Verification

**User Story:** As an operator, I want confirmation that a simulated restart cleared the session null errors, so that the demo shows end-to-end remediation verification.

#### Acceptance Criteria

1. WHEN `restart_target_service` completes, THE Remedy_Agent SHALL read the mock log Resource again to begin a 30-second observation window (simulated for demo).
2. WHEN the observation window completes, THE Remedy_Agent SHALL check the mock log entries for any new Null_Identity_Error occurrences appended after the restart timestamp.
3. WHEN zero new Null_Identity_Error occurrences are found in the observation window, THE Remedy_Agent SHALL emit a remediation-success event containing: Diagnosis ID, restart timestamp, and observation window duration.
4. WHEN one or more new Null_Identity_Error occurrences are found in the observation window, THE Remedy_Agent SHALL emit a remediation-failure event and SHALL trigger a new `ctx.elicit()` recommending escalation to a human operator.
5. THE Remedy_Agent SHALL append all remediation outcomes (success or failure) to a local `.log` file for audit purposes.

---

### Requirement 8: Agent Coordination via MCP

**User Story:** As a system integrator, I want all three agent roles to communicate through MCP primitives, so that the demo proves the architecture is portable and each role can be replaced independently.

#### Acceptance Criteria

1. THE Monitor_Agent SHALL communicate detected anomalies to the Analyst_Agent using MCP Tool invocations or MCP Resource reads, and SHALL NOT use direct in-process function calls or shared module-level variables between roles.
2. THE Analyst_Agent SHALL communicate Diagnoses to the Remedy_Agent using MCP Tool invocations or MCP Resource reads, and SHALL NOT use direct in-process function calls or shared module-level variables between roles.
3. THE MCP_Server SHALL use `stdio` transport for all agent-to-server communication; no authentication is required for this demo.
4. THE system SHALL be designed so that each agent role (Monitor, Analyst, Remedy) can be replaced or upgraded independently without modifying the MCP_Server contract.
5. THE MCP_Server SHALL log all Tool invocations and Resource read events to stderr as structured JSON with `trace_id`, invoking role identity, and result status.
6. FOR complex multi-agent orchestration beyond MCP's scope, THE system design SHALL note that A2A (Agent-to-Agent) or ACP (Agent Communication Protocol) can complement MCP as a coordination layer.

> Production note: In production, Monitor, Analyst, and Remedy run as separate agent processes communicating via MCP. Demo uses stdio transport (no auth required); production requires OAuth 2.1 with PKCE.

---

### Requirement 9: MCP Prompt — opsbridge_incident_report

**User Story:** As the MCP Host, I want a pre-canned Prompt that guides the LLM through summarizing an incident, so that the demo shows MCP Prompts as a first-class primitive alongside Tools and Resources.

#### Acceptance Criteria

1. THE MCP_Server SHALL expose a Prompt named `opsbridge_incident_report`.
2. THE Prompt SHALL accept the following arguments: `service_name`, `error_pattern`, and `diagnosis_summary`.
3. WHEN the Prompt is invoked, THE MCP_Server SHALL return a structured message that instructs the LLM to produce an incident report covering: detected anomaly, system health assessment, recommended action, and approval status.
4. THE Prompt SHALL be usable by the Host to guide the LLM through the Monitor → Analyst → Remedy narrative in a single coherent response.
5. THE Prompt message SHALL reference the provided `service_name` and `error_pattern` arguments so the LLM output is scoped to the specific incident rather than a generic template.

---

## Production Roadmap

The following capabilities were omitted from this demo for simplicity. Each is the recommended production equivalent of a demo shortcut used above.

- **OAuth 2.1 + PKCE** — mandatory for all remote MCP servers per the March 2025 MCP specification; replaces the demo's unauthenticated stdio transport.
- **Redis-backed Session_Cache** — stateless, horizontally scalable session storage; replaces the demo's in-memory Mock_State dict.
- **OpenTelemetry tracing** — JSON-RPC span tracking with distributed trace context; replaces the demo's manual `trace_id` field in stderr logs.
- **Circuit breakers via pybreaker** — downstream resilience for all external API calls; omitted from demo as no real downstream services exist.
- **Redis token-bucket rate limiting** — per-agent request throttling; omitted from demo due to single-process stdio transport.
- **AWS Secrets Manager / Doppler** — secrets management for API keys and credentials; demo uses a mock key in environment variables.
- **Docker / AWS ECS container restart signal** — real remediation action sent to a container orchestrator; replaced in demo by `time.sleep(1)` + log print.
- **Separate agent processes with A2A coordination** — production Monitor, Analyst, and Remedy run as independent processes; demo collapses all three roles into one server script orchestrated by the Host via system prompt.
