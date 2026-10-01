from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from coding_agent.acp_server import ACPServer
from coding_agent.config import AgentLimitsOverride
from coding_agent.types import AgentResult, AgentUsage


class FakeAgent:
    """Plays one turn: says something, calls a tool, reports usage."""

    def __init__(self, result: AgentResult | None = None) -> None:
        self.last_prompt: str | None = None
        self.last_limits: AgentLimitsOverride | None = None
        self.result = result or AgentResult(message="done", stopped_reason="completed", usage=AgentUsage())

    def run_prompt(
        self,
        prompt: str,
        progress_callback: Any = None,
        system_prompt: str = "",
        limits_override: AgentLimitsOverride | None = None,
    ) -> AgentResult:
        self.last_prompt = prompt
        self.last_limits = limits_override
        if progress_callback is not None:
            progress_callback({"type": "iteration", "value": 1})
            progress_callback({"type": "usage", "prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
            progress_callback({"type": "assistant_message", "text": "Writing the file."})
            progress_callback(
                {"type": "tool_call", "name": "write_file", "call_id": "c1", "arguments": {"path": "a.txt", "content": "x"}}
            )
            progress_callback(
                {"type": "tool_result", "name": "write_file", "call_id": "c1", "output": "Wrote a.txt", "failed": False}
            )
            progress_callback({"type": "usage", "prompt_tokens": 20, "completion_tokens": 7, "total_tokens": 27})
            if self.result.stopped_reason == "completed":
                progress_callback({"type": "assistant_message", "text": self.result.message})
        return self.result


class Harness:
    def __init__(self, agent: FakeAgent | None = None) -> None:
        self.agent = agent or FakeAgent()
        self.workspaces: list[Path] = []
        self.output = io.StringIO()
        self.server = ACPServer(agent_factory=self._factory, output=self.output)
        self._read = 0

    def _factory(self, cwd: Path) -> FakeAgent:
        self.workspaces.append(cwd)
        return self.agent

    def send(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        self.server.handle_line(json.dumps(message))
        lines = self.output.getvalue().splitlines()[self._read :]
        self._read += len(lines)
        return [json.loads(line) for line in lines]

    def open_session(self, cwd: Path, **extra: Any) -> str:
        self.send({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": 1}})
        [response] = self.send(
            {"jsonrpc": "2.0", "id": 1, "method": "session/new", "params": {"cwd": str(cwd), "mcpServers": [], **extra}}
        )
        return str(response["result"]["sessionId"])


def test_initialize_answers_protocol_version_1() -> None:
    [response] = Harness().send(
        {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": 1, "clientCapabilities": {}}}
    )

    assert response["id"] == 0
    assert response["result"]["protocolVersion"] == 1
    assert response["result"]["agentCapabilities"]["loadSession"] is False
    assert response["result"]["authMethods"] == []


def test_session_new_takes_the_clients_cwd(tmp_path: Path) -> None:
    harness = Harness()

    session_id = harness.open_session(tmp_path)

    assert session_id
    assert harness.workspaces == [tmp_path]


def test_session_new_refuses_a_relative_cwd_with_the_requests_id() -> None:
    [response] = Harness().send(
        {"jsonrpc": "2.0", "id": 7, "method": "session/new", "params": {"cwd": "relative", "mcpServers": []}}
    )

    assert response["id"] == 7
    assert response["error"]["code"] == -32602


def test_a_prompt_turn_streams_updates_and_ends_with_a_stop_reason(tmp_path: Path) -> None:
    harness = Harness()
    session_id = harness.open_session(tmp_path)

    messages = harness.send(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/prompt",
            "params": {"sessionId": session_id, "prompt": [{"type": "text", "text": "make a.txt"}]},
        }
    )

    updates = [message["params"]["update"] for message in messages if message.get("method") == "session/update"]
    assert [update["sessionUpdate"] for update in updates] == [
        "agent_message_chunk",
        "tool_call",
        "tool_call_update",
        "agent_message_chunk",
    ]
    assert updates[0]["content"] == {"type": "text", "text": "Writing the file."}
    assert updates[1] == {
        "sessionUpdate": "tool_call",
        "toolCallId": "c1",
        "title": "write_file a.txt",
        "kind": "edit",
        "status": "in_progress",
        "rawInput": {"path": "a.txt", "content": "x"},
    }
    assert updates[2]["status"] == "completed"
    assert updates[2]["content"] == [{"type": "content", "content": {"type": "text", "text": "Wrote a.txt"}}]
    assert all(message["params"]["sessionId"] == session_id for message in messages if "method" in message)

    response = messages[-1]
    assert response["id"] == 2
    assert response["result"]["stopReason"] == "end_turn"
    assert response["result"]["usage"] == {"inputTokens": 30, "outputTokens": 12, "totalTokens": 42}
    assert harness.agent.last_prompt == "make a.txt"


def test_a_limit_stop_is_said_and_maps_to_a_protocol_stop_reason(tmp_path: Path) -> None:
    agent = FakeAgent(AgentResult(message="Stopped by max_iterations limit.", stopped_reason="max_iterations"))
    harness = Harness(agent)
    session_id = harness.open_session(tmp_path)

    messages = harness.send(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "session/prompt",
            "params": {"sessionId": session_id, "prompt": [{"type": "text", "text": "go"}]},
        }
    )

    last_update = [message for message in messages if message.get("method") == "session/update"][-1]
    assert last_update["params"]["update"]["content"]["text"] == "Stopped by max_iterations limit."
    assert messages[-1]["result"]["stopReason"] == "max_turn_requests"
    assert messages[-1]["result"]["_meta"] == {"codingAgent": {"stoppedReason": "max_iterations"}}


def test_session_limits_merge_with_prompt_limits(tmp_path: Path) -> None:
    harness = Harness()
    session_id = harness.open_session(tmp_path, _meta={"codingAgent": {"limits": {"max_iterations": 2, "max_seconds": 60}}})

    harness.send(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [{"type": "text", "text": "go"}],
                "_meta": {"codingAgent": {"limits": {"max_iterations": 1}}},
            },
        }
    )

    assert harness.agent.last_limits is not None
    assert harness.agent.last_limits.max_iterations == 1
    assert harness.agent.last_limits.max_seconds == 60


def test_prompt_text_reads_text_and_embedded_resources(tmp_path: Path) -> None:
    harness = Harness()
    session_id = harness.open_session(tmp_path)

    harness.send(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "session/prompt",
            "params": {
                "sessionId": session_id,
                "prompt": [
                    {"type": "text", "text": "first"},
                    {"type": "resource", "resource": {"uri": "file:///x", "text": "second"}},
                    {"type": "image", "data": "", "mimeType": "image/png"},
                ],
            },
        }
    )

    assert harness.agent.last_prompt == "first\n\nsecond"


def test_unknown_method_and_unknown_session_answer_with_errors(tmp_path: Path) -> None:
    harness = Harness()

    [unknown] = harness.send({"jsonrpc": "2.0", "id": 8, "method": "session/load", "params": {}})
    [no_session] = harness.send(
        {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "session/prompt",
            "params": {"sessionId": "nope", "prompt": [{"type": "text", "text": "x"}]},
        }
    )

    assert unknown == {"jsonrpc": "2.0", "id": 8, "error": {"code": -32601, "message": "Method not found: session/load"}}
    assert no_session["id"] == 9 and no_session["error"]["code"] == -32602


def test_cancel_is_a_notification_and_gets_no_answer(tmp_path: Path) -> None:
    harness = Harness()
    session_id = harness.open_session(tmp_path)

    assert harness.send({"jsonrpc": "2.0", "method": "session/cancel", "params": {"sessionId": session_id}}) == []
    assert harness.server.sessions[session_id].cancel_requested is True
