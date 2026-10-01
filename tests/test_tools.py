from __future__ import annotations

from pathlib import Path

import pytest

from coding_agent.tools.builtin import BuiltinTools, ToolError


def test_write_and_read_file_roundtrip(tmp_path: Path) -> None:
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=2, max_command_output_chars=1000)

    write_result = tools.write_file("src/example.py", "print('ok')\n")
    read_result = tools.read_file("src/example.py")

    assert "src/example.py" in write_result
    assert "print('ok')" in read_result


def test_workspace_escape_is_blocked(tmp_path: Path) -> None:
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=2, max_command_output_chars=1000)

    with pytest.raises(ToolError):
        tools.read_file("../outside.txt")


def test_replace_move_delete_file(tmp_path: Path) -> None:
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=2, max_command_output_chars=1000)
    tools.write_file("a.txt", "hello world")

    replace_result = tools.replace_text("a.txt", "world", "agent", expected_replacements=1)
    assert "Replaced text" in replace_result
    assert tools.read_file("a.txt") == "hello agent"

    move_result = tools.move_path("a.txt", "nested/b.txt")
    assert "nested/b.txt" in move_result
    assert tools.read_file("nested/b.txt") == "hello agent"

    delete_result = tools.delete_path("nested/b.txt")
    assert "Deleted nested/b.txt" == delete_result
