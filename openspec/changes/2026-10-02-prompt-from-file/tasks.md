## 1. Reading the prompt from a file

- [x] 1.1 `src/coding_agent/cli.py`: `run`'s positional `prompt` becomes
  optional; `--prompt-file <path>` reads the file and uses its content as
  the prompt, unchanged. `_resolve_prompt(parser, args)` refuses,
  through `parser.error` (usage message, exit code 2), both given,
  neither given, and a `--prompt-file` that cannot be read.
- [x] 1.2 `src/coding_agent/cli.py`: `_read_prompt_file` reads UTF-8
  (`utf-8-sig`, so a BOM is not kept as text), falling back to
  `locale.getpreferredencoding(False)` on a `UnicodeDecodeError`. A file
  decodable by neither raises a `parser.error` naming the file, instead
  of an unhandled `UnicodeDecodeError` reaching the person as a
  traceback — found live on 2026-10-02 against a file saved as "ANSI".

## 2. Documents

- [x] 2.1 `docs/configuration.md`: `--prompt-file`, and that it is
  exclusive with the positional prompt.
- [x] 2.2 Version 0.7.1 in `pyproject.toml` and `__init__.py`.

## 3. Checks

- [x] 3.1 `tests/test_cli.py` (new): the positional argument; a file's
  content, including Markdown; both given; neither given; a missing
  file; a file in the system's own encoding (`cp1251`, via
  `monkeypatch`); a file decodable by neither; `--prompt-file` combined
  with a global option written after the subcommand
  (`2026-10-01-global-options-after-subcommand`).
- [x] 3.2 `ruff`, `mypy`, `pytest`. 2026-10-02: `pytest` 36 passed;
  `ruff` all checks passed on the touched files; `mypy` shows only the 2
  pre-existing `reconfigure` findings this change did not touch.
- [x] 3.3 **Live**: `coding-agent run --prompt-file` against SGLang at
  `192.168.137.33:8000` serving `QuantTrio/Qwen3.6-35B-A3B-AWQ`, the file
  a short Markdown task ("Reply with exactly one short sentence
  confirming you read this file..."), answered "I have read and
  acknowledged this file." on 2026-10-02. The encoding fallback itself
  was found and fixed from a live traceback the same day (a file saved
  as "ANSI" in `c:\temp\qwe.txt`), and is covered by the unit tests
  above rather than a second live run.
