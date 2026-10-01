## Why

ADR-0001 promised "ACP-compatible JSON-RPC over stdio", and the server
built shared method names with the Agent Client Protocol and little else.
Measured on 2026-09-30 with messages shaped as an ACP client sends them:
`session/new` refused `cwd` and `mcpServers` and answered with `id: null`,
`session/prompt` refused a list of content blocks, and the CLI logged to
stdout. No ACP client could open a session. OpenSpec Workbench's
`local-llm-acp` adapter, written to the protocol, could not run this agent.
See [ADR-0002](../../../docs/adr/0002-agent-client-protocol.md).

## What Changes

- **The stdio server speaks ACP version 1**: `initialize` with an integer
  version, `session/new` taking the client's `cwd`, `session/prompt` taking
  content blocks, `session/update` notifications of the protocol's kinds,
  a `stopReason` the protocol names and `usage` in its fields, and
  `session/cancel` as a notification. **BREAKING** for anything that spoke
  the old dialect; nothing known did.
- **Each session works in its own `cwd`**: its tools are built for that
  directory.
- **stdout carries protocol messages only** in `acp` mode; logs go to
  stderr, and stdin and stdout are UTF-8.
- **The agent reports what it does**: each turn's text, each tool's start
  and its result, and each model call's tokens reach the server as
  progress events.
- **Limits move to `_meta.codingAgent.limits`**, the protocol's place for
  extensions; a top-level `limits` field is still read.
- **No `.coding-agent/` directory appears in a workspace** until a
  background process needs one.
- **The provider reads what SGLang sends**: null `tool_calls`, `usage` and
  arguments are none, and a tool call the model wrote as text, which a
  server whose parser does not match the model passes through, is taken as
  a call. Both were found by the first live runs against SGLang serving
  Qwen3.6.
- `coding-agent --version`.
- Version 0.3.0.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `python-acp-coding-agent`: the stdio protocol, the session's working
  directory, and where limits travel.

## Impact

- `src/coding_agent/acp_server.py`, `acp_models.py`: rewritten.
- `src/coding_agent/agent.py`: progress events `assistant_message`,
  `tool_result` and `usage`; `tool_call` carries its arguments.
- `src/coding_agent/cli.py`: logs to stderr and UTF-8 streams in `acp`
  mode; one agent per session.
- `src/coding_agent/tools/builtin.py`: the process directory is made when
  first needed.
- `src/coding_agent/llm/openai_compatible.py`: null fields and calls
  written as text; `tests/test_openai_compatible.py`.
- `tests/test_acp.py`, `tests/test_acp_stdio.py`; `tests/test_acp_golden.py`
  and `tests/golden/` removed.
- `docs/acp-protocol.md`, `docs/adr/0002-agent-client-protocol.md`.
