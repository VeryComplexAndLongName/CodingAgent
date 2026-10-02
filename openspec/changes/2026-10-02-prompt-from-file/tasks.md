## 1. Reading the prompt from a file

- [x] 1.1 `src/coding_agent/cli.py`: `run`'s positional `prompt` becomes
  optional; `--prompt-file <path>` reads the file as UTF-8 text and uses
  it as the prompt, unchanged. `_resolve_prompt(parser, args)` refuses,
  through `parser.error` (usage message, exit code 2), both given,
  neither given, and a `--prompt-file` that cannot be read.

## 2. Documents

- [x] 2.1 `docs/configuration.md`: `--prompt-file`, and that it is
  exclusive with the positional prompt.
- [x] 2.2 Version 0.7.0 in `pyproject.toml` and `__init__.py`.

## 3. Checks

- [x] 3.1 `tests/test_cli.py` (new): the positional argument; a file's
  content, including Markdown; both given; neither given; a missing
  file; `--prompt-file` combined with a global option written after the
  subcommand (`2026-10-01-global-options-after-subcommand`).
- [x] 3.2 `ruff`, `mypy`, `pytest`. 2026-10-02: `pytest` 34 passed in
  7.83s; `ruff` all checks passed on the touched files; `mypy` shows only
  the 2 pre-existing `reconfigure` findings this change did not touch.
- [x] 3.3 **Live**: `coding-agent run --prompt-file` against SGLang at
  `192.168.137.33:8000` serving `QuantTrio/Qwen3.6-35B-A3B-AWQ`, the file
  a short Markdown task ("Reply with exactly one short sentence
  confirming you read this file..."), answered "I have read and
  acknowledged this file." on 2026-10-02.
