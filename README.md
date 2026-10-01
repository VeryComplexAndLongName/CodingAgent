# Python ACP Coding Agent

Standalone coding agent implemented in Python with:
- ACP-compatible JSON-RPC over stdio for orchestration,
- OpenAI-compatible model backend,
- built-in coding tools for repository work,
- configurable hard limits for execution, tokens, and context pressure.

## Documentation index

- Project overview: [docs/overview.md](docs/overview.md)
- Configuration and runtime options: [docs/configuration.md](docs/configuration.md)
- ACP protocol surface: [docs/acp-protocol.md](docs/acp-protocol.md)
- Built-in tools: [docs/tools.md](docs/tools.md)
- Limits and stop reasons: [docs/limits.md](docs/limits.md)
- Usage examples: [docs/examples.md](docs/examples.md)
- Security guidance: [docs/security.md](docs/security.md)

## Quick start

Install:
```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
```

One-shot mode:
```bash
coding-agent \
  --base-url http://localhost:8000/v1 \
  --model qwen2.5-coder \
  --workspace . \
  run "Create a TypeScript utility and tests"
```

ACP mode:
```bash
coding-agent \
  --base-url http://localhost:8000/v1 \
  --model qwen2.5-coder \
  --workspace . \
  acp
```

## Limits at a glance

Execution:
- `max_iterations`
- `max_tool_calls`
- `max_seconds`

Token budgets:
- `max_prompt_tokens`
- `max_completion_tokens`
- `max_total_tokens`

Context controls:
- `max_context_used_tokens`
- `max_context_window_tokens`
- `max_context_share`
- `min_free_context_tokens`

ACP-level control:
- limits can be provided in `session/new` and overridden in `session/prompt`.

## Harness integration note

The executable is intended to be launched as a local ACP process. Register this command in your harness agent registry and point stage configuration to that agent id.
