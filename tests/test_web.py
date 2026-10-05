from __future__ import annotations

import gzip
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from coding_agent.cli import _build_agent, build_parser
from coding_agent.tools.builtin import BuiltinTools, ToolError
from coding_agent.tools.web import WebError, WebTools


def _client(
    monkeypatch: pytest.MonkeyPatch, handler: Callable[[httpx.Request], httpx.Response]
) -> None:
    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kwargs: real_client(**kwargs, transport=httpx.MockTransport(handler)),
    )


def test_fetch_clean_text_and_links(monkeypatch: pytest.MonkeyPatch) -> None:
    page = '<html><head><title>Example</title><style>hidden style</style></head><body><nav>Menu</nav><main><h1>Article</h1><p>Useful content &amp; details.</p><a href="/next">Next</a><a href="/next#part">Again</a><a href="javascript:alert(1)">Bad</a><script>secret script</script></main></body></html>'
    _client(monkeypatch, lambda request: httpx.Response(200, text=page, headers={"content-type": "text/html"}))
    result = json.loads(WebTools().fetch("https://example.org/article", format="text"))
    assert "Useful content & details." in result["text"]
    assert "secret script" not in result["text"]
    assert "hidden style" not in result["text"]
    assert "<" not in result["text"]
    assert result["links"] == [{"text": "Next", "url": "https://example.org/next"}]


def test_search_json_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search"
        assert request.url.params["q"] == "test query"
        assert request.url.params["format"] == "json"
        assert request.url.params["language"] == "ru"
        assert "authorization" not in request.headers
        return httpx.Response(200, json={"results": [{"title": "<b>Title</b>", "url": "https://example.org", "content": "Snippet &amp; text"}] * 3})
    _client(monkeypatch, handler)
    result = json.loads(WebTools().search("test query", max_results=1))
    assert result["results"] == [{"title": "Title", "url": "https://example.org", "snippet": "Snippet & text"}]


@pytest.mark.parametrize("url", ["file:///secret", "ftp://example.org", "http://user:pass@example.org"])
def test_invalid_url(url: str) -> None:
    with pytest.raises(WebError, match="Invalid URL"):
        WebTools().fetch(url)


def test_plain_text_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    _client(monkeypatch, lambda request: httpx.Response(200, text="abcdefgh", headers={"content-type": "text/plain"}))
    result = json.loads(WebTools().fetch("https://example.org", max_chars=4))
    assert result["text"] == "abcd"
    assert result["truncated"] is True


def test_download_bound(monkeypatch: pytest.MonkeyPatch) -> None:
    _client(monkeypatch, lambda request: httpx.Response(200, content=b"x" * 20))
    with pytest.raises(WebError, match="size limit"):
        WebTools(max_response_bytes=10).fetch("https://example.org")


@pytest.mark.parametrize("status", [403, 500])
def test_http_errors(monkeypatch: pytest.MonkeyPatch, status: int) -> None:
    _client(monkeypatch, lambda request: httpx.Response(status))
    with pytest.raises(WebError, match="Web request failed"):
        WebTools().fetch("https://example.org")


def test_binary_content_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    _client(monkeypatch, lambda request: httpx.Response(200, content=b"PNG", headers={"content-type": "image/png"}))
    with pytest.raises(WebError, match="Unsupported content"):
        WebTools().fetch("https://example.org/image")


def test_invalid_search_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _client(monkeypatch, lambda request: httpx.Response(200, text="not JSON"))
    with pytest.raises(WebError, match="Invalid SearXNG"):
        WebTools().search("test")


def test_redirect_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    _client(monkeypatch, lambda request: httpx.Response(302, headers={"location": "file:///secret"}))
    with pytest.raises(WebError, match="Invalid URL"):
        WebTools().fetch("https://example.org")


def test_timeout_is_controlled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("test timeout", request=request)
    _client(monkeypatch, handler)
    tools = BuiltinTools(tmp_path, 2, 1000)
    with pytest.raises(ToolError, match="ReadTimeout"):
        tools.call("fetch_url", {"url": "https://example.org"})


def test_redirect_resolves_relative_links(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/old":
            return httpx.Response(302, headers={"location": "/new/"})
        return httpx.Response(200, text='<main>Text <a href="next">Next</a></main>', headers={"content-type": "text/html"})
    _client(monkeypatch, handler)
    result = json.loads(WebTools().fetch("https://example.org/old"))
    assert result["url"] == "https://example.org/new/"
    assert result["links"][0]["url"] == "https://example.org/new/next"


def test_redirect_loop_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    _client(monkeypatch, lambda request: httpx.Response(302, headers={"location": "/loop"}))
    with pytest.raises(WebError, match="Too many redirects"):
        WebTools().fetch("https://example.org")


def test_registration_and_argument_validation(tmp_path: Path) -> None:
    tools = BuiltinTools(tmp_path, 2, 1000)
    names = {item["function"]["name"] for item in tools.schema()}
    assert {"web_search", "fetch_url"} <= names
    for name, arguments in [("web_search", {"query": "", "max_results": 30}), ("fetch_url", {"url": "http://example.org", "max_chars": 0})]:
        with pytest.raises(ToolError, match="Invalid arguments"):
            tools.call(name, arguments)


@pytest.mark.parametrize("command", ["run", "chat", "acp"])
def test_cli_wiring(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, command: str) -> None:
    monkeypatch.setenv("CODING_AGENT_SEARXNG_URL", "http://search.internal:8888")
    parser = build_parser()
    argv = [command, "--workspace", str(tmp_path), "--no-proxy"]
    if command == "run":
        argv.append("test")
    agent = _build_agent(parser.parse_args(argv))
    assert agent.config.searxng_url == "http://search.internal:8888"
    assert agent.tools._builtin_tools._web.trust_env is False
    args = parser.parse_args(["--searxng-url", "http://first", command, "--searxng-url", "http://last"] + (["test"] if command == "run" else []))
    assert args.searxng_url == "http://last"


def test_compressed_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _client(monkeypatch, lambda request: httpx.Response(
        200, content=gzip.compress(b"Readable text"),
        headers={"content-type": "text/plain", "content-encoding": "gzip"},
    ))
    assert json.loads(WebTools().fetch("https://example.org"))["text"] == "Readable text"


def test_html_meta_encoding(monkeypatch: pytest.MonkeyPatch) -> None:
    text = "\u0422\u0435\u043a\u0441\u0442 \u0441\u0442\u0430\u0442\u044c\u0438"
    page = '<html><head><meta charset="windows-1251"></head><body><main>' + text + '</main></body></html>'
    _client(monkeypatch, lambda request: httpx.Response(
        200, content=page.encode("cp1251"), headers={"content-type": "text/html"},
    ))
    assert text in json.loads(WebTools().fetch("https://example.org"))["text"]


def test_table_text_has_no_generated_markup(monkeypatch: pytest.MonkeyPatch) -> None:
    page = '<article><h1>Table</h1><p>Article content.</p><table><tr><td>Value one</td><td>Value two</td></tr></table></article>'
    _client(monkeypatch, lambda request: httpx.Response(200, text=page, headers={"content-type": "text/html"}))
    text = json.loads(WebTools().fetch("https://example.org", format="text"))["text"]
    assert "Value one" in text
    assert "Value two" in text
    assert "|" not in text
    assert "<" not in text


def test_markdown_default_keeps_heading_links_and_table(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    page = '<article><h1>Heading</h1><p>A paragraph with <a href="/source">a source</a>.</p><table><tr><th>Name</th><th>Value</th></tr><tr><td>One</td><td>Two</td></tr></table><script>hidden</script></article>'
    _client(monkeypatch, lambda request: httpx.Response(200, text=page, headers={"content-type": "text/html"}))
    tools = BuiltinTools(tmp_path, 2, 1000)
    result = json.loads(tools.call("fetch_url", {"url": "https://example.org/article"}))
    assert result["format"] == "markdown"
    assert "# Heading" in result["text"]
    assert "[a source](https://example.org/source)" in result["text"]
    assert "| Name | Value |" in result["text"]
    assert "| One | Two |" in result["text"]
    assert "hidden" not in result["text"]
    assert "<table" not in result["text"]
    plain = json.loads(tools.call("fetch_url", {"url": "https://example.org/article", "format": "text"}))
    assert plain["format"] == "text"
    assert "|" not in plain["text"]
    assert "[a source]" not in plain["text"]


def test_invalid_fetch_format_is_refused(tmp_path: Path) -> None:
    tools = BuiltinTools(tmp_path, 2, 1000)
    with pytest.raises(ToolError, match="Invalid arguments"):
        tools.call("fetch_url", {"url": "https://example.org", "format": "html"})
    with pytest.raises(WebError, match="format must"):
        WebTools().fetch("https://example.org", format="html")