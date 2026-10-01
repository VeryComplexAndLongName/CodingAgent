"""An Agent Client Protocol server over stdio (protocol version 1).

One JSON-RPC message per line on stdin and on stdout, as the protocol's
stdio transport specifies. stdout carries protocol messages and nothing
else: logs go to stderr (see `cli.py`).

What is served:

- `initialize`: protocol version 1, no session loading, no authentication.
- `session/new`: a session whose tools work in the client's `cwd`.
- `session/prompt`: one agent turn. The agent's text arrives as
  `agent_message_chunk` updates, each tool call as a `tool_call` update and
  its result as a `tool_call_update`; the response carries the stop reason
  and the tokens the model reported.
- `session/cancel`: accepted and recorded. A turn already running is not
  interrupted from inside: this server reads one message at a time, and a
  client that must stop a turn ends the process, as every client of a
  stdio agent can.

Not served: permission requests (`session/request_permission`). The agent's
tools run without asking, within the session's working directory.
"""

from __future__ import annotations

import json
import sys
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, TextIO

from loguru import logger
from pydantic import ValidationError

from coding_agent.acp_models import (
    PROTOCOL_VERSION,
    InitializeParams,
    SessionCancelParams,
    SessionNewParams,
    SessionPromptParams,
    limits_from,
    prompt_text,
)
from coding_agent.agent import SYSTEM_PROMPT
from coding_agent.config import AgentLimitsOverride
from coding_agent.types import AgentResult

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# How much of a tool's output a `tool_call_update` carries. The model sees
# all of it; the client is shown what fits on a screen.
TOOL_OUTPUT_PREVIEW_CHARS = 4000

_TOOL_KINDS: dict[str, str] = {
    "read_file": "read",
    "list_dir": "read",
    "search_text": "search",
    "write_file": "edit",
    "replace_text": "edit",
    "delete_path": "delete",
    "move_path": "move",
}

# Stop reasons the protocol names, for each reason this agent stops. Every
# other reason is a limit on the turn's length: `max_turn_requests`.
_STOP_REASONS: dict[str, str] = {
    "completed": "end_turn",
    "max_prompt_tokens": "max_tokens",
    "max_completion_tokens": "max_tokens",
    "max_total_tokens": "max_tokens",
    "max_context_used_tokens": "max_tokens",
    "max_context_window_tokens": "max_tokens",
    "max_context_share": "max_tokens",
    "min_free_context_tokens": "max_tokens",
}


class PromptRunner(Protocol):
    def run_prompt(
        self,
        prompt: str,
        progress_callback: Callable[[dict[str, object]], None] | None = None,
        system_prompt: str = SYSTEM_PROMPT,
        limits_override: AgentLimitsOverride | None = None,
    ) -> AgentResult: ...


AgentFactory = Callable[[Path], PromptRunner]


class RpcError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class Session:
    def __init__(self, session_id: str, agent: PromptRunner, limits: AgentLimitsOverride | None) -> None:
        self.session_id = session_id
        self.agent = agent
        self.limits = limits
        self.cancel_requested = False


class ACPServer:
    def __init__(self, agent_factory: AgentFactory, output: TextIO | None = None) -> None:
        self._agent_factory = agent_factory
        self._output = output
        self.sessions: dict[str, Session] = {}

    # Transport -------------------------------------------------------------

    def serve(self, lines: TextIO) -> None:
        for raw_line in lines:
            line = raw_line.strip()
            if line:
                self.handle_line(line)

    def handle_line(self, line: str) -> None:
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            self._send_error(None, PARSE_ERROR, f"Parse error: {exc}")
            return
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            self._send_error(_id_of(message), INVALID_REQUEST, "Invalid request: not a JSON-RPC 2.0 message")
            return
        method = message.get("method")
        if not isinstance(method, str):
            # A response to a request this server never sends, or noise.
            return
        params = message.get("params") or {}
        if "id" not in message:
            self._handle_notification(method, params)
            return
        request_id = message["id"]
        try:
            result = self._handle_request(method, params)
        except RpcError as exc:
            self._send_error(request_id, exc.code, exc.message)
            return
        except ValidationError as exc:
            self._send_error(request_id, INVALID_PARAMS, f"Invalid params: {exc}")
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception("Request {} failed", method)
            self._send_error(request_id, INTERNAL_ERROR, f"{type(exc).__name__}: {exc}")
            return
        self._send({"jsonrpc": "2.0", "id": request_id, "result": result})

    # Methods ---------------------------------------------------------------

    def _handle_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "initialize":
            return self._initialize(InitializeParams.model_validate(params))
        if method == "session/new":
            return self._session_new(SessionNewParams.model_validate(params))
        if method == "session/prompt":
            return self._session_prompt(SessionPromptParams.model_validate(params))
        raise RpcError(METHOD_NOT_FOUND, f"Method not found: {method}")

    def _handle_notification(self, method: str, params: dict[str, Any]) -> None:
        if method == "session/cancel":
            try:
                session = self.sessions.get(SessionCancelParams.model_validate(params).sessionId)
            except ValidationError:
                return
            if session is not None:
                session.cancel_requested = True

    def _initialize(self, params: InitializeParams) -> dict[str, Any]:
        return {
            # The only version this server speaks; a client asking for a
            # later one is told so and decides whether to go on.
            "protocolVersion": min(params.protocolVersion, PROTOCOL_VERSION),
            "agentCapabilities": {
                "loadSession": False,
                "promptCapabilities": {"image": False, "audio": False, "embeddedContext": True},
            },
            "authMethods": [],
        }

    def _session_new(self, params: SessionNewParams) -> dict[str, Any]:
        cwd = Path(params.cwd)
        if not cwd.is_absolute():
            raise RpcError(INVALID_PARAMS, f"cwd must be an absolute path: {params.cwd}")
        if not cwd.is_dir():
            raise RpcError(INVALID_PARAMS, f"cwd is not a directory: {params.cwd}")
        if params.mcpServers:
            logger.warning("Ignoring {} MCP server(s): this agent connects to none", len(params.mcpServers))
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = Session(
            session_id=session_id,
            agent=self._agent_factory(cwd),
            limits=limits_from(params.limits, params.meta),
        )
        return {"sessionId": session_id}

    def _session_prompt(self, params: SessionPromptParams) -> dict[str, Any]:
        session = self.sessions.get(params.sessionId)
        if session is None:
            raise RpcError(INVALID_PARAMS, f"Unknown sessionId: {params.sessionId}")
        text = prompt_text(params.prompt)
        if not text.strip():
            raise RpcError(INVALID_PARAMS, "The prompt has no text")

        limits = session.limits
        prompt_limits = limits_from(params.limits, params.meta)
        if prompt_limits is not None:
            merged = limits.model_dump(exclude_none=True) if limits is not None else {}
            merged.update(prompt_limits.model_dump(exclude_none=True))
            limits = AgentLimitsOverride.model_validate(merged)

        session.cancel_requested = False
        turn = _Turn(self, session.session_id)
        result = session.agent.run_prompt(
            prompt=text,
            progress_callback=turn.on_progress,
            system_prompt=SYSTEM_PROMPT,
            limits_override=limits,
        )
        if result.stopped_reason != "completed" or not turn.said_anything:
            # A stop the model did not write is still said to the person.
            turn.message(result.message)

        response: dict[str, Any] = {
            "stopReason": _STOP_REASONS.get(result.stopped_reason, "max_turn_requests"),
            "_meta": {"codingAgent": {"stoppedReason": result.stopped_reason}},
        }
        usage = turn.usage()
        if usage is not None:
            response["usage"] = usage
        return response

    # Output ----------------------------------------------------------------

    def notify(self, session_id: str, update: dict[str, Any]) -> None:
        self._send(
            {
                "jsonrpc": "2.0",
                "method": "session/update",
                "params": {"sessionId": session_id, "update": update},
            }
        )

    def _send_error(self, request_id: Any, code: int, message: str) -> None:
        self._send({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})

    def _send(self, payload: dict[str, Any]) -> None:
        output = self._output if self._output is not None else sys.stdout
        # ASCII on the wire: JSON escapes the rest, and no console code page
        # can then garble a message.
        output.write(json.dumps(payload, ensure_ascii=True) + "\n")
        output.flush()


class _Turn:
    """Turns the agent's progress events into `session/update`
    notifications, and keeps the token counts for the response."""

    def __init__(self, server: ACPServer, session_id: str) -> None:
        self._server = server
        self._session_id = session_id
        self.said_anything = False
        self._input_tokens = 0
        self._output_tokens = 0
        self._total_tokens = 0
        self._counted = False

    def message(self, text: str) -> None:
        self.said_anything = True
        self._server.notify(
            self._session_id,
            {"sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": text}},
        )

    def on_progress(self, event: dict[str, object]) -> None:
        kind = event.get("type")
        if kind == "assistant_message":
            self.message(str(event.get("text", "")))
        elif kind == "tool_call":
            name = str(event.get("name", ""))
            arguments = event.get("arguments")
            self._server.notify(
                self._session_id,
                {
                    "sessionUpdate": "tool_call",
                    "toolCallId": str(event.get("call_id", "")),
                    "title": _tool_title(name, arguments),
                    "kind": _TOOL_KINDS.get(name, "execute" if name.startswith(("run_", "git_")) else "other"),
                    "status": "in_progress",
                    "rawInput": arguments if isinstance(arguments, dict) else {},
                },
            )
        elif kind == "tool_result":
            output = str(event.get("output", ""))
            if len(output) > TOOL_OUTPUT_PREVIEW_CHARS:
                hidden = len(output) - TOOL_OUTPUT_PREVIEW_CHARS
                output = output[:TOOL_OUTPUT_PREVIEW_CHARS] + f"\n... ({hidden} more characters)"
            self._server.notify(
                self._session_id,
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": str(event.get("call_id", "")),
                    "status": "failed" if event.get("failed") else "completed",
                    "content": [{"type": "content", "content": {"type": "text", "text": output}}],
                },
            )
        elif kind == "usage":
            prompt_tokens = event.get("prompt_tokens")
            completion_tokens = event.get("completion_tokens")
            total_tokens = event.get("total_tokens")
            if isinstance(prompt_tokens, int):
                self._input_tokens += prompt_tokens
                self._counted = True
            if isinstance(completion_tokens, int):
                self._output_tokens += completion_tokens
                self._counted = True
            if isinstance(total_tokens, int):
                self._total_tokens += total_tokens

    def usage(self) -> dict[str, int] | None:
        """The tokens of every model call in the turn, where the model
        reported any. None where it reported none: zero would say the turn
        cost nothing."""
        if not self._counted:
            return None
        total = self._total_tokens or self._input_tokens + self._output_tokens
        return {"inputTokens": self._input_tokens, "outputTokens": self._output_tokens, "totalTokens": total}


def _tool_title(name: str, arguments: object) -> str:
    if not isinstance(arguments, dict):
        return name
    for key in ("path", "command", "query", "src", "branch", "process_id", "message"):
        value = arguments.get(key)
        if isinstance(value, str) and value:
            shown = value if len(value) <= 80 else value[:77] + "..."
            return f"{name} {shown}"
    return name


def _id_of(message: object) -> Any:
    return message.get("id") if isinstance(message, dict) else None
