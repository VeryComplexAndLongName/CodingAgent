"""The provider against answers shaped as real OpenAI-compatible servers
send them."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import httpx
import pytest

from coding_agent.llm.openai_compatible import OpenAICompatibleProvider, tool_calls_in_text

_KNOWN = {
    "read_file": {"path": "string"},
    "write_file": {"path": "string", "content": "string"},
    "git_add": {"paths": "array"},
}


def test_a_qwen3_coder_call_written_as_text_is_taken_as_a_call() -> None:
    # What Qwen3.6 wrote through SGLang's hermes parser on 2026-10-01.
    content = (
        "Let me look first.\n\n<tool_call>\n<function=read_file>\n<parameter=path>\nsrc/greet.js\n</parameter>\n"
        "</function>\n</tool_call>"
    )

    calls, rest = tool_calls_in_text(content, _KNOWN)

    assert [(call.name, call.arguments) for call in calls] == [("read_file", {"path": "src/greet.js"})]
    assert rest == "Let me look first."


def test_a_hermes_call_written_as_text_is_taken_as_a_call() -> None:
    content = '<tool_call>\n{"name": "git_add", "arguments": {"paths": ["a.txt"]}}\n</tool_call>'

    calls, rest = tool_calls_in_text(content, _KNOWN)

    assert [(call.name, call.arguments) for call in calls] == [("git_add", {"paths": ["a.txt"]})]
    assert rest == ""


def test_text_that_looks_like_json_stays_the_text_to_write() -> None:
    content = (
        "<tool_call>\n<function=write_file>\n<parameter=path>\na.json\n</parameter>\n"
        '<parameter=content>\n{"a": 1}\n</parameter>\n</function>\n</tool_call>'
    )

    [call], _ = tool_calls_in_text(content, _KNOWN)

    assert call.arguments == {"path": "a.json", "content": '{"a": 1}'}


def test_a_call_to_a_tool_not_offered_stays_text() -> None:
    content = "<tool_call>\n<function=format_disk>\n</function>\n</tool_call>"

    calls, rest = tool_calls_in_text(content, _KNOWN)

    assert calls == []
    assert rest == content


def _serve(answer: dict[str, Any]) -> HTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            body = json.dumps(answer).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: object) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_null_tool_calls_and_usage_read_as_none() -> None:
    # SGLang's answer to a turn that calls no tool, measured 2026-10-01:
    # `tool_calls` and `usage` present and null.
    server = _serve({"choices": [{"message": {"role": "assistant", "content": "Done.", "tool_calls": None}}], "usage": None})
    try:
        provider = OpenAICompatibleProvider(base_url=f"http://127.0.0.1:{server.server_address[1]}/v1", model="m", api_key=None)

        turn = provider.complete(messages=[{"role": "user", "content": "hi"}], tools=[])
    finally:
        server.shutdown()

    assert turn.content == "Done."
    assert turn.tool_calls == []
    assert turn.usage.total_tokens is None


def test_a_tool_call_with_null_arguments_reads_as_no_arguments() -> None:
    server = _serve(
        {
            "choices": [
                {"message": {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "git_status", "arguments": None}}]}}
            ]
        }
    )
    try:
        provider = OpenAICompatibleProvider(base_url=f"http://127.0.0.1:{server.server_address[1]}/v1", model="m", api_key=None)

        turn = provider.complete(messages=[{"role": "user", "content": "hi"}], tools=[])
    finally:
        server.shutdown()

    assert turn.content == ""
    assert [(call.name, call.arguments) for call in turn.tool_calls] == [("git_status", {})]


def test_the_environment_is_trusted_unless_the_provider_is_told_not_to(monkeypatch: pytest.MonkeyPatch) -> None:
    # A corporate proxy in the environment answered 502 for a model on the
    # local network, measured 2026-10-01.
    server = _serve({"choices": [{"message": {"role": "assistant", "content": "ok"}}]})
    seen: list[bool] = []
    real_client = httpx.Client

    def recording_client(*args: object, **kwargs: Any) -> httpx.Client:
        seen.append(kwargs["trust_env"])
        return real_client(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpx, "Client", recording_client)
    base_url = f"http://127.0.0.1:{server.server_address[1]}/v1"
    try:
        OpenAICompatibleProvider(base_url=base_url, model="m", api_key=None, trust_env=False).complete(
            messages=[{"role": "user", "content": "hi"}], tools=[]
        )
        OpenAICompatibleProvider(base_url=base_url, model="m", api_key=None).complete(
            messages=[{"role": "user", "content": "hi"}], tools=[]
        )
    finally:
        server.shutdown()

    assert seen == [False, True]
