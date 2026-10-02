## Why

Measured 2026-10-02: a `run` against a local 35B model, generating a long
turn over an accumulated multi-article conversation, answered past the
provider's hardcoded 120-second HTTP timeout. `httpx.ReadTimeout`
propagated out of `run_prompt`, out of `run`, as a raw traceback — the
process exited, and nothing the turn was about to write (it had already
written four articles across earlier turns) was lost, but the run itself
ended on an exception a person reading the log could not act on short of
reading the traceback for the word "timeout".

## What Changes

- **The model's own HTTP timeout is configurable**: `--request-timeout-seconds`
  (default 120, unchanged), read by `OpenAICompatibleProvider`.
- **A model request that fails ends the turn cleanly, not the process**:
  `run_prompt` catches a failure from the provider's own `complete()` and
  returns a `provider_error`-stopped `AgentResult` naming it, the same way
  a tool's own refusal already does, rather than letting it propagate.
  `run`'s single turn, `chat`'s session and `acp`'s session all inherit
  this without their own change.
- Version 0.8.0.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `python-acp-coding-agent`: the model request's timeout is configurable;
  a failed model request ends the turn, not the process.

## Impact

- `src/coding_agent/llm/openai_compatible.py`: unchanged signature,
  already accepts `timeout_seconds`.
- `src/coding_agent/config.py`: `request_timeout_seconds` on `AgentConfig`.
- `src/coding_agent/cli.py`: `--request-timeout-seconds`.
- `src/coding_agent/agent.py`: `run_prompt` catches the provider's
  failure.
- `tests/test_limits.py` or a new test module.
- `docs/configuration.md`.
