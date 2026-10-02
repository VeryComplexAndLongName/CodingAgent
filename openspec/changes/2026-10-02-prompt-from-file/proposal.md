## Why

`run`'s prompt is a single command-line argument. A longer task — a
checklist, a Markdown spec, anything that does not fit comfortably on one
shell line, or that a shell would mangle through its own quoting — has no
way in except being pasted as one unbroken argument.

## What Changes

- **`run --prompt-file <path>` reads the prompt from a file** instead of
  the positional argument — Markdown or plain text, read as-is, nothing
  stripped or interpreted. Exactly one of the positional argument or
  `--prompt-file` is required; giving both, or neither, is refused with
  the usage error naming which.
- Version 0.7.0.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `python-acp-coding-agent`: where `run`'s prompt text may come from.

## Impact

- `src/coding_agent/cli.py`: `--prompt-file` on `run`; `_resolve_prompt`.
- `tests/test_cli.py` (new).
- `docs/configuration.md`.
