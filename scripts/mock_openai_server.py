from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {"/v1/chat/completions", "/chat/completions"}:
            self.send_response(404)
            self.end_headers()
            return

        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        request = json.loads(raw.decode("utf-8"))
        messages = request.get("messages", [])

        has_tool_response = any(msg.get("role") == "tool" for msg in messages)

        if not has_tool_response:
            self._send(
                {
                    "id": "chatcmpl-1",
                    "object": "chat.completion",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "call_1",
                                        "type": "function",
                                        "function": {
                                            "name": "write_file",
                                            "arguments": json.dumps(
                                                {
                                                    "path": "docs/test-agent-executor-proof.md",
                                                    "content": "Test change executed by python-coding-agent-acp.\n",
                                                }
                                            ),
                                        },
                                    }
                                ],
                            },
                            "finish_reason": "tool_calls",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 50,
                        "completion_tokens": 10,
                        "total_tokens": 60,
                        "context_used_tokens": 60,
                        "context_window_tokens": 1000,
                    },
                }
            )
            return

        self._send(
            {
                "id": "chatcmpl-2",
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Task completed. The proof file was created with the expected content.",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 70,
                    "completion_tokens": 12,
                    "total_tokens": 82,
                    "context_used_tokens": 82,
                    "context_window_tokens": 1000,
                },
            }
        )


def main() -> None:
    server = HTTPServer(("127.0.0.1", 18080), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
