## 1. Argument parsing

- [x] 1.1 `src/coding_agent/cli.py`: a helper adds every global option
  (`--base-url`, `--model`, `--api-key`, `--no-proxy`, `--workspace` and
  the limit flags) to a given parser, each defaulting to
  `argparse.SUPPRESS` when told to. The top-level parser keeps its real
  defaults; `run` and `acp` get the same options with `SUPPRESS`, so an
  option given before the subcommand survives into the merged namespace
  unless the same option is given again after it.

## 2. Documents

- [x] 2.1 `docs/configuration.md`: a line stating every global option may
  come before or after `run`/`acp`.
- [x] 2.2 Version 0.5.0 in `pyproject.toml` and `__init__.py`.

## 3. Checks

- [x] 3.1 `tests/test_acp_stdio.py`: a process started as `coding-agent
  acp --base-url <url> --model <model>` — the exact argv OpenSpec
  Workbench's `local-llm-acp` adapter writes — completes a turn the same
  way the existing before-the-subcommand test does.
- [x] 3.2 `ruff`, `mypy`, `pytest`. 2026-10-01: `pytest` 25 passed in 5.67s
  (run with `NO_PROXY=127.0.0.1,localhost`: this machine's system proxy
  settings intercept loopback HTTP too under `trust_env=True`, a
  pre-existing environmental fact unrelated to this change — confirmed by
  reproducing the same interception against the reverted, pre-change
  `cli.py`). `ruff` and `mypy` show only the same findings present before
  this change, none in `cli.py` or the new test.
- [x] 3.3 **Live**: `coding-agent acp --base-url
  http://192.168.137.33:8000/v1 --model QuantTrio/Qwen3.6-35B-A3B-AWQ
  --no-proxy` — the exact argv `local-llm-acp`'s `buildInvocation` writes,
  plus `--no-proxy` for this machine's system proxy — answered
  `initialize` with `protocolVersion: 1` on 2026-10-01. Before this
  change, the same argv answered `unrecognized arguments: --base-url ...
  --model ...` and exited `2`.
