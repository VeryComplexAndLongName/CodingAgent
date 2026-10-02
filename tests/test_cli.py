"""`build_parser` and `_resolve_prompt`: argument parsing and the prompt
file option, without touching the network."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from coding_agent.cli import _resolve_prompt, build_parser


def test_prompt_from_the_positional_argument() -> None:
    parser = build_parser()
    args = parser.parse_args(["run", "hello"])

    assert _resolve_prompt(parser, args) == "hello"


def test_prompt_from_a_file(tmp_path: Path) -> None:
    prompt_path = tmp_path / "task.md"
    prompt_path.write_text("# Task\n\nDo the thing.\n", encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(["run", "--prompt-file", str(prompt_path)])

    assert _resolve_prompt(parser, args) == "# Task\n\nDo the thing.\n"


def test_both_the_positional_argument_and_prompt_file_is_rejected(tmp_path: Path) -> None:
    prompt_path = tmp_path / "task.md"
    prompt_path.write_text("hi", encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(["run", "hello", "--prompt-file", str(prompt_path)])

    with pytest.raises(SystemExit):
        _resolve_prompt(parser, args)


def test_neither_the_positional_argument_nor_prompt_file_is_rejected() -> None:
    parser = build_parser()
    args = parser.parse_args(["run"])

    with pytest.raises(SystemExit):
        _resolve_prompt(parser, args)


def test_a_missing_prompt_file_is_rejected(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args(["run", "--prompt-file", str(tmp_path / "missing.md")])

    with pytest.raises(SystemExit):
        _resolve_prompt(parser, args)


def test_a_prompt_file_in_the_systems_own_encoding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Measured 2026-10-02: a file saved as "ANSI" (cp1251 here) crashed
    # with an unhandled UnicodeDecodeError under plain UTF-8 reading.
    monkeypatch.setattr("coding_agent.cli.locale.getpreferredencoding", lambda do_setlocale=True: "cp1251")
    prompt_path = tmp_path / "task.txt"
    prompt_path.write_bytes("Задача".encode("cp1251"))
    parser = build_parser()
    args = parser.parse_args(["run", "--prompt-file", str(prompt_path)])

    assert _resolve_prompt(parser, args) == "Задача"


def test_a_prompt_file_decodable_by_neither_encoding_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("coding_agent.cli.locale.getpreferredencoding", lambda do_setlocale=True: "cp1251")
    prompt_path = tmp_path / "task.txt"
    # 0x98 is a continuation byte alone (invalid UTF-8) and undefined in cp1251.
    prompt_path.write_bytes(b"\x98")
    parser = build_parser()
    args = parser.parse_args(["run", "--prompt-file", str(prompt_path)])

    with pytest.raises(SystemExit):
        _resolve_prompt(parser, args)


def test_global_options_after_the_subcommand_still_work_with_prompt_file(tmp_path: Path) -> None:
    prompt_path = tmp_path / "task.md"
    prompt_path.write_text("hi", encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(["run", "--model", "m", "--prompt-file", str(prompt_path)])

    assert isinstance(args, argparse.Namespace)
    assert args.model == "m"
    assert _resolve_prompt(parser, args) == "hi"
