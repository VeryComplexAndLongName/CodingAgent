from __future__ import annotations

import subprocess
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolError(RuntimeError):
    """Raised when tool execution fails."""


class ReadFileArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str


class WriteFileArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    content: str


class ListDirArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = "."


class SearchTextArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str
    path: str = "."


class RunCommandArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    command: str


class ReplaceTextArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    old_text: str
    new_text: str
    expected_replacements: int = Field(default=1, ge=1)


class DeletePathArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str


class MovePathArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    src: str
    dst: str


class GitAddArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paths: list[str]


class GitCommitArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str


class GitCheckoutArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    branch: str
    create: bool = False


class BackgroundStartArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    command: str


class BackgroundGetArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    process_id: str


class BackgroundStopArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    process_id: str


class BackgroundProcess:
    def __init__(self, process_id: str, command: str, popen: subprocess.Popen[str], log_path: Path) -> None:
        self.process_id = process_id
        self.command = command
        self.popen = popen
        self.log_path = log_path


class BuiltinTools:
    def __init__(
        self,
        workspace: Path,
        command_timeout_seconds: int,
        max_command_output_chars: int,
    ) -> None:
        self.workspace = workspace.resolve()
        self.command_timeout_seconds = command_timeout_seconds
        self.max_command_output_chars = max_command_output_chars
        self._background: dict[str, BackgroundProcess] = {}
        # Made when a background process first needs it: a session that runs
        # none leaves nothing behind in the workspace.
        self._process_dir = self.workspace / ".coding-agent" / "processes"

    def schema(self) -> list[dict[str, Any]]:
        return [
            _tool_schema("read_file", "Read a UTF-8 text file.", {"path": {"type": "string"}}, ["path"]),
            _tool_schema(
                "write_file",
                "Write UTF-8 text to a file. Parent directories are created.",
                {"path": {"type": "string"}, "content": {"type": "string"}},
                ["path", "content"],
            ),
            _tool_schema("list_dir", "List directory entries.", {"path": {"type": "string"}}, ["path"]),
            _tool_schema(
                "search_text",
                "Search substring in workspace files.",
                {"query": {"type": "string"}, "path": {"type": "string"}},
                ["query"],
            ),
            _tool_schema(
                "run_command",
                "Run a shell command in workspace cwd with timeout.",
                {"command": {"type": "string"}},
                ["command"],
            ),
            _tool_schema(
                "replace_text",
                "Replace exact text in a UTF-8 file (patch-like edit).",
                {
                    "path": {"type": "string"},
                    "old_text": {"type": "string"},
                    "new_text": {"type": "string"},
                    "expected_replacements": {"type": "integer", "minimum": 1},
                },
                ["path", "old_text", "new_text"],
            ),
            _tool_schema("delete_path", "Delete a file inside workspace.", {"path": {"type": "string"}}, ["path"]),
            _tool_schema(
                "move_path",
                "Move or rename a file inside workspace.",
                {"src": {"type": "string"}, "dst": {"type": "string"}},
                ["src", "dst"],
            ),
            _tool_schema("git_status", "Run git status --short --branch.", {}, []),
            _tool_schema("git_diff", "Run git diff.", {}, []),
            _tool_schema(
                "git_add",
                "Run git add for selected paths.",
                {"paths": {"type": "array", "items": {"type": "string"}}},
                ["paths"],
            ),
            _tool_schema(
                "git_commit",
                "Run git commit with a message.",
                {"message": {"type": "string"}},
                ["message"],
            ),
            _tool_schema(
                "git_checkout",
                "Run git checkout branch (optionally create).",
                {"branch": {"type": "string"}, "create": {"type": "boolean"}},
                ["branch"],
            ),
            _tool_schema(
                "run_command_background",
                "Start a background command in workspace cwd.",
                {"command": {"type": "string"}},
                ["command"],
            ),
            _tool_schema(
                "get_background_process",
                "Get status and logs from a background process.",
                {"process_id": {"type": "string"}},
                ["process_id"],
            ),
            _tool_schema(
                "stop_background_process",
                "Stop a background process.",
                {"process_id": {"type": "string"}},
                ["process_id"],
            ),
        ]

    def call(self, name: str, arguments: dict[str, Any]) -> str:
        if name == "read_file":
            read_args = ReadFileArgs.model_validate(arguments)
            return self.read_file(read_args.path)
        if name == "write_file":
            write_args = WriteFileArgs.model_validate(arguments)
            return self.write_file(write_args.path, write_args.content)
        if name == "list_dir":
            list_args = ListDirArgs.model_validate(arguments)
            return self.list_dir(list_args.path)
        if name == "search_text":
            search_args = SearchTextArgs.model_validate(arguments)
            return self.search_text(search_args.query, search_args.path)
        if name == "run_command":
            command_args = RunCommandArgs.model_validate(arguments)
            return self.run_command(command_args.command)
        if name == "replace_text":
            replace_args = ReplaceTextArgs.model_validate(arguments)
            return self.replace_text(
                replace_args.path,
                replace_args.old_text,
                replace_args.new_text,
                replace_args.expected_replacements,
            )
        if name == "delete_path":
            delete_args = DeletePathArgs.model_validate(arguments)
            return self.delete_path(delete_args.path)
        if name == "move_path":
            move_args = MovePathArgs.model_validate(arguments)
            return self.move_path(move_args.src, move_args.dst)
        if name == "git_status":
            return self.git_status()
        if name == "git_diff":
            return self.git_diff()
        if name == "git_add":
            git_add_args = GitAddArgs.model_validate(arguments)
            return self.git_add(git_add_args.paths)
        if name == "git_commit":
            git_commit_args = GitCommitArgs.model_validate(arguments)
            return self.git_commit(git_commit_args.message)
        if name == "git_checkout":
            git_checkout_args = GitCheckoutArgs.model_validate(arguments)
            return self.git_checkout(git_checkout_args.branch, git_checkout_args.create)
        if name == "run_command_background":
            background_start_args = BackgroundStartArgs.model_validate(arguments)
            return self.run_command_background(background_start_args.command)
        if name == "get_background_process":
            background_get_args = BackgroundGetArgs.model_validate(arguments)
            return self.get_background_process(background_get_args.process_id)
        if name == "stop_background_process":
            background_stop_args = BackgroundStopArgs.model_validate(arguments)
            return self.stop_background_process(background_stop_args.process_id)
        raise ToolError(f"Unknown tool: {name}")

    def read_file(self, path: str) -> str:
        target = self._resolve_within_workspace(path)
        return target.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> str:
        target = self._resolve_within_workspace(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        rel = target.relative_to(self.workspace).as_posix()
        return f"Wrote {rel}"

    def list_dir(self, path: str) -> str:
        target = self._resolve_within_workspace(path)
        if not target.is_dir():
            raise ToolError(f"Not a directory: {path}")
        lines = []
        for child in sorted(target.iterdir(), key=lambda p: p.name.lower()):
            suffix = "/" if child.is_dir() else ""
            lines.append(f"{child.name}{suffix}")
        return "\n".join(lines)

    def search_text(self, query: str, path: str = ".") -> str:
        if not query:
            raise ToolError("query cannot be empty")
        root = self._resolve_within_workspace(path)
        if not root.exists():
            raise ToolError(f"Path does not exist: {path}")

        if root.is_file():
            return self._search_file(root, query)

        matches: list[str] = []
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".exe"}:
                continue
            result = self._search_file(file_path, query)
            if result:
                matches.append(result)
            if len(matches) >= 200:
                break
        return "\n".join(matches)

    def run_command(self, command: str) -> str:
        if not command.strip():
            raise ToolError("command cannot be empty")
        completed = self._run_subprocess(command=command, timeout_seconds=self.command_timeout_seconds)
        output = self._format_process_output(completed.returncode, completed.stdout, completed.stderr)
        if len(output) > self.max_command_output_chars:
            output = output[: self.max_command_output_chars] + "\n[truncated]"
        return output

    def replace_text(self, path: str, old_text: str, new_text: str, expected_replacements: int) -> str:
        target = self._resolve_within_workspace(path)
        original = target.read_text(encoding="utf-8")
        count = original.count(old_text)
        if count != expected_replacements:
            raise ToolError(f"Expected {expected_replacements} replacements but found {count}")
        updated = original.replace(old_text, new_text)
        target.write_text(updated, encoding="utf-8")
        rel = target.relative_to(self.workspace).as_posix()
        return f"Replaced text in {rel} ({count} occurrence(s))"

    def delete_path(self, path: str) -> str:
        target = self._resolve_within_workspace(path)
        if target.is_dir():
            raise ToolError("delete_path supports files only")
        if not target.exists():
            raise ToolError(f"Path does not exist: {path}")
        target.unlink()
        rel = target.relative_to(self.workspace).as_posix()
        return f"Deleted {rel}"

    def move_path(self, src: str, dst: str) -> str:
        source = self._resolve_within_workspace(src)
        target = self._resolve_within_workspace(dst)
        if not source.exists():
            raise ToolError(f"Source does not exist: {src}")
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
        src_rel = source.relative_to(self.workspace).as_posix()
        dst_rel = target.relative_to(self.workspace).as_posix()
        return f"Moved {src_rel} -> {dst_rel}"

    def git_status(self) -> str:
        completed = self._run_subprocess("git status --short --branch", self.command_timeout_seconds)
        return self._format_process_output(completed.returncode, completed.stdout, completed.stderr)

    def git_diff(self) -> str:
        completed = self._run_subprocess("git diff", self.command_timeout_seconds)
        return self._format_process_output(completed.returncode, completed.stdout, completed.stderr)

    def git_add(self, paths: list[str]) -> str:
        if not paths:
            raise ToolError("paths cannot be empty")
        normalized: list[str] = []
        for path in paths:
            self._resolve_within_workspace(path)
            normalized.append(path)
        command = "git add " + " ".join(_quote_arg(path) for path in normalized)
        completed = self._run_subprocess(command, self.command_timeout_seconds)
        return self._format_process_output(completed.returncode, completed.stdout, completed.stderr)

    def git_commit(self, message: str) -> str:
        if not message.strip():
            raise ToolError("message cannot be empty")
        command = f"git commit -m {_quote_arg(message)}"
        completed = self._run_subprocess(command, self.command_timeout_seconds)
        return self._format_process_output(completed.returncode, completed.stdout, completed.stderr)

    def git_checkout(self, branch: str, create: bool) -> str:
        if not branch.strip():
            raise ToolError("branch cannot be empty")
        cmd = f"git checkout {'-b ' if create else ''}{_quote_arg(branch)}"
        completed = self._run_subprocess(cmd, self.command_timeout_seconds)
        return self._format_process_output(completed.returncode, completed.stdout, completed.stderr)

    def run_command_background(self, command: str) -> str:
        if not command.strip():
            raise ToolError("command cannot be empty")

        process_id = str(uuid.uuid4())
        self._process_dir.mkdir(parents=True, exist_ok=True)
        log_path = self._process_dir / f"{process_id}.log"
        log_file = log_path.open("w", encoding="utf-8")
        popen = subprocess.Popen(
            command,
            cwd=self.workspace,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
        )
        self._background[process_id] = BackgroundProcess(
            process_id=process_id,
            command=command,
            popen=popen,
            log_path=log_path,
        )
        return f"process_id: {process_id}"

    def get_background_process(self, process_id: str) -> str:
        process = self._background.get(process_id)
        if process is None:
            raise ToolError(f"Unknown process_id: {process_id}")

        exit_code = process.popen.poll()
        state = "running" if exit_code is None else f"exited({exit_code})"
        output = ""
        if process.log_path.exists():
            output = process.log_path.read_text(encoding="utf-8", errors="ignore")
        if len(output) > self.max_command_output_chars:
            output = output[: self.max_command_output_chars] + "\n[truncated]"
        return f"state: {state}\ncommand: {process.command}\nlog:\n{output}"

    def stop_background_process(self, process_id: str) -> str:
        process = self._background.get(process_id)
        if process is None:
            raise ToolError(f"Unknown process_id: {process_id}")
        if process.popen.poll() is None:
            process.popen.terminate()
        return self.get_background_process(process_id)

    def close(self) -> None:
        """Stops every background process still running, so none outlives
        the agent's own process."""
        for process in self._background.values():
            if process.popen.poll() is None:
                process.popen.terminate()
                try:
                    process.popen.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.popen.kill()

    def _resolve_within_workspace(self, path: str) -> Path:
        candidate = (self.workspace / path).resolve()
        if not self._is_within_workspace(candidate):
            raise ToolError(f"Path escapes workspace: {path}")
        return candidate

    def _is_within_workspace(self, path: Path) -> bool:
        try:
            path.relative_to(self.workspace)
            return True
        except ValueError:
            return False

    def _search_file(self, file_path: Path, query: str) -> str:
        try:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return ""
        found: list[str] = []
        for index, line in enumerate(lines, start=1):
            if query.lower() in line.lower():
                rel = file_path.relative_to(self.workspace).as_posix()
                found.append(f"{rel}:{index}:{line.strip()}")
        return "\n".join(found)

    def _run_subprocess(self, command: str, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                command,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                shell=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise ToolError(f"Command timed out after {timeout_seconds}s") from exc

    def _format_process_output(self, exit_code: int, stdout: str, stderr: str) -> str:
        output = f"exit_code: {exit_code}\nstdout:\n{stdout}\nstderr:\n{stderr}"
        if len(output) > self.max_command_output_chars:
            return output[: self.max_command_output_chars] + "\n[truncated]"
        return output


def _tool_schema(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


def _quote_arg(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'
