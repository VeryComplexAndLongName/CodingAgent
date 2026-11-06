## Why

`run`'s prompt is a single command-line argument. A longer task — a
checklist, a Markdown spec, anything that does not fit comfortably on one
shell line, or that a shell would mangle through its own quoting — has no
way in except being pasted as one unbroken argument.

## What Changes

- **`run --prompt-file <path>` reads the prompt from a file** instead of
  the positional argument — Markdown or plain text, read as-is, nothing
  stripped or interpreted. UTF-8 (with or without a BOM) first; a file
  that is not falls back to the system's own encoding (`cp1251` on a
  Russian-locale Windows, for one), rather than crashing with a raw
  `UnicodeDecodeError` — found live on 2026-10-02 against a file saved as
  "ANSI". Exactly one of the positional argument or `--prompt-file` is
  required; giving both, or neither, is refused with the usage error
  naming which.
- Version 0.7.1.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `python-acp-coding-agent`: where `run`'s prompt text may come from.

## Impact

- `src/coding_agent/cli.py`: `--prompt-file` on `run`; `_resolve_prompt`.
- `tests/test_cli.py` (new).
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
