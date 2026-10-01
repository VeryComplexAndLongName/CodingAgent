# ADR-0001: Python ACP Coding Agent over OpenAI-Compatible API

## Status
Accepted

## Context
The workspace requires a coding-capable agent that can be used by harness workflows while connecting to privately hosted or third-party LLM endpoints through an OpenAI-compatible protocol. The agent must expose ACP-compatible behavior for orchestration and enforce hard runtime limits.

## Decision
Implement a standalone Python agent with:
- ACP-compatible JSON-RPC over stdio as the external interface.
- OpenAI-compatible Chat Completions backend with configurable base URL, model, and optional API key.
- Built-in coding tools (filesystem/search/shell) executed under workspace restrictions.
- Runtime guardrails: max iterations, max tool calls, max wall-clock seconds, command timeout, output truncation.

## Alternatives Considered
1. MCP-only architecture as the baseline.
- Rejected because baseline coding usability should not depend on external MCP server availability.

2. Vendor-specific SDK lock-in.
- Rejected because deployment target includes heterogeneous OpenAI-compatible infrastructure.

3. HTTP API as primary transport for harness integration.
- Rejected because harness-style execution commonly uses local stdio process boundaries.

## Consequences
- Positive:
  - Portable deployment across OpenAI-compatible providers.
  - Direct harness integration path through ACP-style process invocation.
  - Deterministic safety controls for autonomous coding sessions.
- Negative:
  - Compatibility quirks across providers may require adapter tuning.
  - No transport-level TLS in this phase; secure network perimeter remains operator responsibility.

## Security Notes
- API keys must be supplied via environment variables or command-line arguments and must never be logged.
- Shell execution is restricted to workspace cwd with bounded timeout and output size.
- Path handling must prevent writes outside the configured workspace root.
