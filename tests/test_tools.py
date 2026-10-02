from __future__ import annotations

import sys
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


def test_close_stops_a_running_background_process(tmp_path: Path) -> None:
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=2, max_command_output_chars=1000)
    result = tools.run_command_background(f'"{sys.executable}" -c "import time; time.sleep(30)"')
    process_id = result.split("process_id: ")[1].strip()

    tools.close()

    status = tools.get_background_process(process_id)
    assert "state: exited(" in status


def test_run_command_does_not_crash_on_output_the_locale_cannot_decode(tmp_path: Path) -> None:
    # Measured 2026-10-02 on a cp1251-locale machine: a lone 0x98 byte (an
    # emoji's UTF-8 lead byte, undefined in cp1251) crashed `subprocess`'s
    # own reader thread with `UnicodeDecodeError` before this tool ever
    # saw a result.
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=5, max_command_output_chars=1000)

    result = tools.run_command(f'"{sys.executable}" -c "import sys; sys.stdout.buffer.write(bytes([0x98]))"')

    assert "exit_code: 0" in result

