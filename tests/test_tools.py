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


def test_list_dir_distinguishes_missing_from_a_file(tmp_path: Path) -> None:
    # Measured 2026-10-02: both cases raised the same "Not a directory",
    # so the model could not tell "not written yet" from "that is a file".
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=2, max_command_output_chars=1000)
    tools.write_file("a_file.txt", "hi")

    with pytest.raises(ToolError, match="No such file or directory"):
        tools.list_dir("missing")
    with pytest.raises(ToolError, match="Not a directory, it's a file"):
        tools.list_dir("a_file.txt")


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


def test_read_file_and_replace_text_on_a_binary_file_are_refused_cleanly(tmp_path: Path) -> None:
    # Measured 2026-10-02: a model reading an image it had just written
    # crashed with an unhandled UnicodeDecodeError, traceback and all.
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=2, max_command_output_chars=1000)
    (tmp_path / "image.png").write_bytes(bytes([0x89, 0x50, 0x4E, 0x47]))

    with pytest.raises(ToolError, match="Not a text file"):
        tools.read_file("image.png")
    with pytest.raises(ToolError, match="Not a text file"):
        tools.replace_text("image.png", "a", "b", expected_replacements=1)


def test_read_file_and_replace_text_distinguish_missing_from_a_directory(tmp_path: Path) -> None:
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=2, max_command_output_chars=1000)
    (tmp_path / "a_dir").mkdir()

    with pytest.raises(ToolError, match="No such file or directory"):
        tools.read_file("missing.txt")
    with pytest.raises(ToolError, match="Is a directory, not a file"):
        tools.read_file("a_dir")
    with pytest.raises(ToolError, match="No such file or directory"):
        tools.replace_text("missing.txt", "a", "b", expected_replacements=1)
    with pytest.raises(ToolError, match="Is a directory, not a file"):
        tools.replace_text("a_dir", "a", "b", expected_replacements=1)


def test_write_file_onto_a_directory_is_refused_cleanly(tmp_path: Path) -> None:
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=2, max_command_output_chars=1000)
    (tmp_path / "a_dir").mkdir()

    with pytest.raises(ToolError, match="Is a directory, not a file"):
        tools.write_file("a_dir", "hi")


def test_move_path_onto_an_existing_destination_is_refused_cleanly(tmp_path: Path) -> None:
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=2, max_command_output_chars=1000)
    tools.write_file("a.txt", "a")
    tools.write_file("b.txt", "b")

    with pytest.raises(ToolError, match="Destination already exists"):
        tools.move_path("a.txt", "b.txt")


def test_call_turns_any_os_error_into_a_clean_tool_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The structural fix, not a one-off: an OSError no specific method
    # above anticipated (here, a permission error `read_file`'s own
    # `except UnicodeDecodeError` does not catch) still comes out of
    # `call` as a `ToolError`, not a raw traceback.
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=2, max_command_output_chars=1000)
    tools.write_file("a.txt", "hi")

    def _raise_permission_error(self: Path, encoding: str | None = None) -> str:
        raise PermissionError("simulated: access denied")

    monkeypatch.setattr(Path, "read_text", _raise_permission_error)

    with pytest.raises(ToolError, match="PermissionError"):
        tools.call("read_file", {"path": "a.txt"})


def test_call_turns_invalid_arguments_into_a_clean_tool_error(tmp_path: Path) -> None:
    tools = BuiltinTools(workspace=tmp_path, command_timeout_seconds=2, max_command_output_chars=1000)

    with pytest.raises(ToolError, match="Invalid arguments"):
        tools.call("read_file", {"path": 123})


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

