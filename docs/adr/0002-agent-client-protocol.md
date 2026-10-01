# ADR-0002: Speak the Agent Client Protocol, not a dialect of it

## Status
Accepted (2026-10-01). Amends ADR-0001's "ACP-compatible JSON-RPC over stdio".

## Context
ADR-0001 chose "ACP-compatible" JSON-RPC over stdio so that harnesses
could drive the agent as a local process. What was built shared the
method names with the Agent Client Protocol and little else:

- `initialize` answered `protocolVersion: "0.1"`, a string; the protocol's
  version is an integer.
- `session/new` refused `cwd` and `mcpServers`, the two fields every ACP
  client sends, and the refusal carried `id: null`, so the client never
  got an answer to its request.
- `session/prompt` wanted the prompt as a string; the protocol sends a list
  of content blocks.
- Updates were `{event: "started" | "progress" | "completed"}`, not the
  protocol's `{update: {sessionUpdate: ...}}`, and the response had
  `stoppedReason` and no `stopReason`.
- The CLI wrote its logs to stdout, the protocol's channel.

Measured on 2026-09-30 with messages shaped as an ACP client sends them: no
session could be opened. OpenSpec Workbench's `local-llm-acp` adapter,
built against the protocol, could not run this agent at all.

## Decision
Serve the Agent Client Protocol, version 1, as published at
agentclientprotocol.com: `initialize`, `session/new` with the client's
`cwd`, `session/prompt` with content blocks, `session/update` notifications
(`agent_message_chunk`, `tool_call`, `tool_call_update`), a `stopReason`
the protocol names, and `session/cancel`. Logs go to stderr. Each session's
tools work in that session's `cwd`. This agent's limits travel in `_meta`,
the place the protocol gives to extensions.

## Alternatives Considered
1. Keep the dialect and give each client an adapter for it.
- Rejected: every client would carry a translation for one agent, and
  "ACP-compatible" would stay untrue.

2. Use an ACP SDK for Python.
- Rejected for now: the surface used is small, the protocol's schema
  is the contract either way, and a dependency for four methods is not
  worth its weight. Revisit if permission requests are served, which need
  concurrent reading of stdin.

## Consequences
- Positive: any ACP client drives the agent unchanged, including OpenSpec
  Workbench's `local-llm-acp`.
- Negative: the old dialect is gone. Nothing was known to speak it; its
  golden tests went with it.
- Open: permission requests (`session/request_permission`) are not sent.
  The tools run without asking, inside the session's `cwd`. A running turn
  is not stopped by `session/cancel`; a client ends the process.
