## ADDED Requirements

### Requirement: ACP-compatible coding process
The system MUST provide a Python executable that serves ACP-compatible JSON-RPC messages over stdio for coding workflows.

#### Scenario: Session lifecycle
- WHEN a client sends initialize, session/new, and session/prompt
- THEN the agent returns valid JSON-RPC responses
- AND emits progress/final updates through session/update notifications.

### Requirement: OpenAI-compatible LLM connectivity
The system MUST support OpenAI-compatible Chat Completions through a configurable base URL and model, with optional API key bearer authentication.

#### Scenario: API key optionality
- WHEN api_key is not configured
- THEN requests are sent without Authorization header
- AND completion still succeeds against endpoints that do not require authentication.

### Requirement: Built-in coding tools
The system MUST include built-in tools for filesystem operations, text search, and shell command execution.

#### Scenario: Workspace safety
- WHEN a tool receives a path outside workspace root
- THEN the call fails with a tool error
- AND no write/read occurs outside the workspace.

### Requirement: Runtime guardrails
The system MUST enforce upper bounds on iterations, tool calls, wall-clock runtime, and command execution behavior.

#### Scenario: Tool call cap
- WHEN tool call count exceeds configured max_tool_calls
- THEN the agent stops and reports max_tool_calls as stop reason.

### Requirement: ACP-configurable limits
The system MUST allow runtime limits to be supplied through ACP requests and applied per session and per prompt.

#### Scenario: Prompt-level override
- WHEN a client sets limits in `session/new` and sends a stricter override in `session/prompt`
- THEN the prompt run uses the merged effective limits with prompt values taking precedence.

### Requirement: Token and context stopping
The system MUST support stopping conditions based on token budgets and context pressure when usage data is available from the model response.

#### Scenario: Context share threshold
- WHEN usage reports context window and used context values
- AND used/window share exceeds configured `max_context_share`
- THEN the agent stops with stop reason `max_context_share`.

### Requirement: Extended coding tools
The system MUST provide patch-like file editing, git utilities, and background command lifecycle tools in addition to baseline filesystem and shell commands.

#### Scenario: Patch-like replace
- WHEN tool `replace_text` receives an expected replacement count that matches file content
- THEN the edit is applied atomically and reported with replacement count.
