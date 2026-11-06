## Why

Every client this agent has so far (`run`, `acp`) is one-shot or driven by
another program; nobody can simply talk to it from a terminal. Someone
running it against a shared model server also found no way to be certain
that stopping the agent left nothing behind on that server or in the
workspace — a background process `run_command_background` started had no
code path that ever stopped it again except the model asking to, and nothing
stopped it when the agent's own process ended.

## What Changes

- **A `chat` command holds a conversation**: it reads one line from stdin
  at a time, answers each with the agent's turn, and keeps every prior
  turn — the model's and the tools' — for the next one, until `exit`,
  `quit`, end of input, or Ctrl-C.
- **`run_prompt` takes a conversation to extend**: an optional list of
  prior messages it appends the new turn's to, so `chat`'s turns build on
  each other the way `run`'s and `acp`'s single turn never needed to.
  Omitting it keeps today's behavior exactly: a fresh system and user
  message, nothing carried from a prior call.
- **Every background process started during a run is stopped when the
  agent's own process ends**: `run`, `chat` and `acp` each stop every
  process `run_command_background` started before exiting, whether the
  turn that started it ever stopped it itself.
- Version 0.6.0.

## Capabilities

### New Capabilities

- `interactive-chat`: a `chat` command that holds a multi-turn
  conversation over stdin/stdout.

### Modified Capabilities

- `python-acp-coding-agent`: a background process never outlives the
  agent's own process.

## Impact

- `src/coding_agent/agent.py`: `run_prompt`'s new `conversation` parameter.
- `src/coding_agent/cli.py`: the `chat` subcommand and its REPL; every
  command closes its tools before returning.
- `src/coding_agent/tools/builtin.py`, `registry.py`: `close()`, stopping
  every background process still running.
- `src/coding_agent/acp_server.py`: closes every session's tools once
  `serve()` returns.
- `tests/test_agent.py` (new), `tests/test_tools.py`.
- `docs/configuration.md`.


## Archive contract evidence, 2026-11-06

This Python repository has no webui/server adapter contract for these changes.
The actual contracts were checked instead: `tests/test_cli.py` covers positional
and file prompts, BOM/system encoding and usage errors; `tests/test_agent.py`
covers shared history and provider-error handling; `tests/test_tools.py` covers
background-process termination. The complete suite passed **71 tests** on the
unchanged main source. A fresh interactive CLI probe also passed blank input,
trimmed case-insensitive exit/quit, EOF/Ctrl-C, shared conversation and failed-turn
rollback. `docs/test-agent-executor-proof.md` retains the exact executor receipt.
The original live SGLang observations remain in the relevant tasks.

See `tasks.md` and `audit-verification.md` for task-specific acceptance. No new
runtime change or protocol change is introduced by archival. Original provider
availability/host-environment limitations remain; this audit does not promise
today's model service availability. A legacy MODIFIED delta whose requirement
never reached the main spec is classified as ADDED, preserving its verified
contract rather than dropping it or bypassing validation.
