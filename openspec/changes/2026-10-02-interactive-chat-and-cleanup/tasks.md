## 1. A conversation across turns

- [x] 1.1 `src/coding_agent/agent.py`: `run_prompt` takes an optional
  `conversation: list[dict[str, object]] | None`. `None` (every existing
  caller) builds a fresh `[system, user]` list exactly as today. Given a
  list, a fresh one appends only the system message when the list is
  empty, then every call appends the new user message and every message
  the turn produced — so a second call on the same list continues the
  first's conversation.

## 2. The `chat` command

- [ ] 2.1 `src/coding_agent/cli.py`: `chat` takes no positional argument.
  It reads one line at a time from stdin; a blank line is skipped; `exit`
  or `quit` (case-insensitive, trimmed) ends the loop; end of input or
  Ctrl-C ends it too. Each line runs through `run_prompt` sharing one
  `conversation` list, and its `message` is printed. A turn that raises
  drops that line from the shared conversation and reports the error
  without ending the session.

## 3. Nothing outlives the agent's own process

- [x] 3.1 `src/coding_agent/tools/builtin.py`: `BuiltinTools.close()`
  terminates every background process still running (`popen.poll() is
  None`), waits briefly, and kills what does not stop.
- [x] 3.2 `src/coding_agent/tools/registry.py`: `ToolRegistry.close()`
  calls the same on its `BuiltinTools`.
- [x] 3.3 `src/coding_agent/cli.py`: `run` and `chat` close the agent's
  tools before returning, success or not.
- [x] 3.4 `src/coding_agent/acp_server.py`: once `serve()`'s loop ends
  (stdin closed), every session's tools are closed.

## 4. Documents

- [x] 4.1 `docs/configuration.md`: the `chat` command, and that a
  background process never outlives the agent's own.
- [x] 4.2 Version 0.6.0 in `pyproject.toml` and `__init__.py`.

## 5. Checks

- [x] 5.1 `tests/test_agent.py` (new): a second `run_prompt` call sharing
  a `conversation` list sees the first call's turns; a fresh call without
  one does not.
- [x] 5.2 `tests/test_tools.py`: `close()` terminates a background
  process `run_command_background` started, and reports it exited.
- [x] 5.3 `ruff`, `mypy`, `pytest`. 2026-10-02: `pytest` 28 passed in
  5.50s (run with `NO_PROXY=127.0.0.1,localhost`: this machine's system
  proxy intercepts loopback HTTP under `trust_env=True`, unrelated
  pre-existing fact, see `2026-10-01-global-options-after-subcommand`).
  `ruff`/`mypy` on the touched files show none of their own; the
  pre-existing findings elsewhere are untouched.
- [x] 5.4 **Live**: `coding-agent chat` against SGLang at
  `192.168.137.33:8000` serving `QuantTrio/Qwen3.6-35B-A3B-AWQ`, with
  `--no-proxy`. "My name is Alex. ..." answered "Nice to meet you,
  Alex!"; "What is my name? ..." answered "Alex" — the second turn used
  the first's conversation. `exit` ended the process cleanly (no
  background process had been started in this exchange, so none needed
  stopping).
