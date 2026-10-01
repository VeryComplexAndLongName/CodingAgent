## Summary
Build a Python coding agent that speaks ACP-compatible JSON-RPC over stdio and uses an OpenAI-compatible Chat Completions backend. The agent executes built-in coding tools inside a constrained workspace and returns progress/events suitable for harness-style orchestration.

## Non-Goals
- Not implementing TLS in this change.
- Not implementing MCP server federation in this initial version.
- Not implementing repository-specific harness registry changes outside this workspace.

## Decisions
1. Chosen: ACP-like JSON-RPC over stdio for transport.
- Reason: matches harness and CLI orchestration workflows.
- Rejected alternative: HTTP server first.
- Rejection reason: increases deployment complexity for local runs and does not match default harness invocation style.

2. Chosen: OpenAI-compatible Chat Completions adapter with optional API key.
- Reason: broad compatibility with OpenAI, vLLM, LM Studio, llama.cpp servers, and private gateways.
- Rejected alternative: vendor-specific SDK lock-in.
- Rejection reason: conflicts with provider-agnostic requirement.

3. Chosen: built-in tools (filesystem/search/shell) managed by the agent core.
- Reason: deterministic baseline for coding tasks and simpler operational model.
- Rejected alternative: MCP-only tool model.
- Rejection reason: introduces hard dependency on external tool servers before baseline functionality exists.

4. Chosen: explicit runtime guardrails (max iterations, max tool calls, max seconds, command timeout).
- Reason: needed for safe and predictable harness execution.
- Rejected alternative: rely only on model behavior.
- Rejection reason: unsafe and non-deterministic.

## Risks / Trade-offs
- REST without TLS can expose traffic and bearer tokens if used on untrusted networks.
- OpenAI-compatible endpoints may differ in tool-calling behavior; adapter may require provider-specific compatibility adjustments.
- Shell tool increases power and risk; strict workspace cwd, timeout, and output truncation are required.

## Protocol Notes
Commands/events introduced in this change:
- RPC methods: initialize, session/new, session/prompt.
- Notifications: session/update for progress and final assistant message.
Backward compatibility:
- This is a new standalone agent implementation and does not alter existing adapter contracts in this repository.
