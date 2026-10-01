"""The real process, over stdio, against a stand-in OpenAI-compatible server:
the order of the command line, a stdout that carries nothing but protocol
messages, and a file written in the session's working directory."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any


class _FakeModel(BaseHTTPRequestHandler):
    calls = 0

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        type(self).calls += 1
        if type(self).calls == 1:
            message: dict[str, Any] = {
                "role": "assistant",
                "content": "Writing it.",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {"name": "write_file", "arguments": json.dumps({"path": "hello.txt", "content": "hi"})},
                    }
                ],
            }
        else:
            message = {"role": "assistant", "content": "Done: hello.txt written."}
        body = json.dumps(
            {"choices": [{"message": message}], "usage": {"prompt_tokens": 11, "completion_tokens": 3, "total_tokens": 14}}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        pass


def test_a_turn_over_stdio_writes_in_the_sessions_cwd(tmp_path: Path) -> None:
    _FakeModel.calls = 0
    server = HTTPServer(("127.0.0.1", 0), _FakeModel)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}/v1"
        # The global options come before the subcommand: argparse reads
        # them only there.
        process = subprocess.Popen(
            [sys.executable, "-m", "coding_agent.cli", "--base-url", base_url, "--model", "m", "--max-iterations", "5", "acp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        requests = [
            {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": 1, "clientCapabilities": {}}},
            {"jsonrpc": "2.0", "id": 1, "method": "session/new", "params": {"cwd": str(tmp_path), "mcpServers": []}},
        ]
        assert process.stdin is not None and process.stdout is not None
        for request in requests:
            process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()

        lines: list[dict[str, Any]] = []
        while len(lines) < 2:
            lines.append(json.loads(process.stdout.readline()))
        session_id = lines[1]["result"]["sessionId"]

        prompt = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/prompt",
            "params": {"sessionId": session_id, "prompt": [{"type": "text", "text": "write hello.txt"}]},
        }
        process.stdin.write(json.dumps(prompt) + "\n")
        process.stdin.flush()
        while True:
            # Every line is a protocol message; a log line would fail here.
            message = json.loads(process.stdout.readline())
            lines.append(message)
            if message.get("id") == 2:
                break
        process.stdin.close()
        process.wait(timeout=10)
    finally:
        server.shutdown()

    assert lines[0]["result"]["protocolVersion"] == 1
    kinds = [line["params"]["update"]["sessionUpdate"] for line in lines if line.get("method") == "session/update"]
    assert kinds == ["agent_message_chunk", "tool_call", "tool_call_update", "agent_message_chunk"]
    assert lines[-1]["result"]["stopReason"] == "end_turn"
    assert lines[-1]["result"]["usage"] == {"inputTokens": 22, "outputTokens": 6, "totalTokens": 28}
    assert (tmp_path / "hello.txt").read_text(encoding="utf-8") == "hi"
    assert not (tmp_path / ".coding-agent").exists()
