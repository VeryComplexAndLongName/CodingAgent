# Archive design record

This record documents the archive audit of the existing implementation.


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
