## Why
This change follows architecture decision [ADR-0001](../../../docs/adr/0001-python-acp-coding-agent.md): the workspace needs a provider-agnostic coding agent that can run with privately hosted LLM infrastructure via an OpenAI-compatible API and be exposed as an ACP-compatible endpoint for harness workflows.

## Capabilities
- New:
  - Introduce a Python ACP-compatible coding agent executable for multi-language coding tasks.
  - Add configurable OpenAI-compatible LLM connectivity (base URL, model, optional API key).
  - Add built-in coding tools (filesystem, search, shell) with execution limits.
- Modified:
  - Repository now contains runnable agent source code, packaging metadata, and usage documentation.

## Scope
- Add Python source under src layout.
- Add a minimal ACP stdio JSON-RPC interface.
- Add runtime limits for iteration count, tool calls, and wall-clock time.
- Add docs with harness usage guidance.

## Out of Scope
- Full replacement of existing harness agent registry internals in other repositories.
- TLS termination and certificate lifecycle management.
