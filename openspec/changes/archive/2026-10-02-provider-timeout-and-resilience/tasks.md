## 1. A configurable timeout

- [x] 1.1 `src/coding_agent/config.py`: `request_timeout_seconds: int =
  120` on `AgentConfig`.
- [x] 1.2 `src/coding_agent/cli.py`: `--request-timeout-seconds`, default
  `120`, added through `_add_global_args` (so it parses before or after
  the subcommand like every other global option); passed to
  `OpenAICompatibleProvider(timeout_seconds=...)`.

## 2. A failed model request ends the turn, not the process

- [x] 2.1 `src/coding_agent/agent.py`: `run_prompt` wraps
  `self.provider.complete(...)` in a `try`/`except Exception`; on failure
  it logs a `WARNING` (no traceback — a network failure is not a bug) and
  returns immediately with `stopped_reason="provider_error"` and a
  message naming the exception, leaving `messages`/`conversation`
  exactly as it stood (ending on the last tool result or the user's own
  message, same shape as a turn awaiting its answer).

## 3. Documents

- [x] 3.1 `docs/configuration.md`: `--request-timeout-seconds`, and that
  a failed model request ends the turn rather than the process.
- [x] 3.2 Version 0.8.0 in `pyproject.toml` and `__init__.py`.

## 4. Checks

- [x] 4.1 A new test: a provider whose `complete()` raises is given to
  `CodingAgent.run_prompt`, and the call returns (does not raise) with
  `stopped_reason == "provider_error"`.
- [x] 4.2 `ruff`, `mypy`, `pytest`. 2026-10-02: `pytest` 40 passed in
  9.58s; `ruff` shows only pre-existing findings this change did not
  touch; `mypy` shows only the 2 pre-existing `reconfigure` findings.
- [x] 4.3 **Live**: `coding-agent --request-timeout-seconds 1 run "..."`
  against SGLang at `192.168.137.33:8000` serving
  `QuantTrio/Qwen3.6-35B-A3B-AWQ` printed `Model request failed: timed
  out` then `Stopped by a provider error: timed out`, exit code 0, no
  traceback — reproducing, and fixing, the live crash this change was
  written for (a 120s timeout during a long multi-article `run`).
