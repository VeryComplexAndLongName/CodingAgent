from __future__ import annotations

import json
from typing import Any, Literal
from urllib.parse import urldefrag, urljoin, urlsplit

import httpx
import trafilatura
from lxml import etree, html


class WebError(RuntimeError):
    pass


def _http_url(url: str) -> str:
    try:
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError("HTTP(S) URL required")
        if parts.username is not None or parts.password is not None:
            raise ValueError("URL credentials are not allowed")
        port = parts.port
        if port is not None and port < 1:
            raise ValueError("Invalid port")
    except ValueError as exc:
        raise WebError(f"Invalid URL: {exc}") from exc
    return url


class WebTools:
    def __init__(
        self,
        search_url: str = "http://192.168.137.39:8888",
        trust_env: bool = True,
        timeout_seconds: int = 30,
        max_response_bytes: int = 2_000_000,
    ) -> None:
        self.search_url = search_url.rstrip("/")
        self.trust_env = trust_env
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes

    def _get(
        self, url: str, *, params: dict[str, str] | None = None, direct: bool = False
    ) -> httpx.Response:
        current = _http_url(url)
        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                trust_env=False if direct else self.trust_env,
                headers={"User-Agent": "CodingAgent/0.10 web-research"},
            ) as client:
                for redirect_count in range(6):
                    with client.stream("GET", current, params=params) as response:
                        if response.is_redirect:
                            if redirect_count == 5 or "location" not in response.headers:
                                raise WebError("Too many redirects or missing redirect location")
                            current = _http_url(urljoin(str(response.url), response.headers["location"]))
                            params = None
                            continue
                        response.raise_for_status()
                        body = bytearray()
                        for chunk in response.iter_bytes(chunk_size=65_536):
                            body.extend(chunk)
                            if len(body) > self.max_response_bytes:
                                raise WebError("Response exceeds download size limit")
                        return httpx.Response(
                            response.status_code,
                            headers={
                                key: value for key, value in response.headers.items()
                                if key not in {"content-encoding", "content-length"}
                            },
                            content=bytes(body),
                            request=response.request,
                        )
        except httpx.HTTPError as exc:
            raise WebError(f"Web request failed ({type(exc).__name__}): {exc}") from exc
        raise WebError("No response")

    def search(self, query: str, language: str = "ru", max_results: int = 5) -> str:
        if not query.strip() or not 1 <= max_results <= 20:
            raise WebError("Nonempty query and max_results between 1 and 20 required")
        endpoint = self.search_url if self.search_url.endswith("/search") else self.search_url + "/search"
        response = self._get(
            endpoint, params={"q": query, "format": "json", "language": language}, direct=True
        )
        try:
            data = response.json()
            if not isinstance(data, dict) or not isinstance(data.get("results"), list):
                raise WebError("Invalid SearXNG response: expected a results array")
            results = []
            for item in data["results"]:
                if not isinstance(item, dict) or not isinstance(item.get("url"), str):
                    continue
                try:
                    url = _http_url(item["url"])
                except WebError:
                    continue
                results.append({
                    "title": _plain(str(item.get("title") or ""))[:500],
                    "url": url[:8192],
                    "snippet": _plain(str(item.get("content") or ""))[:2000],
                })
                if len(results) >= max_results:
                    break
            return json.dumps({"query": query, "results": results}, ensure_ascii=False)
        except (ValueError, etree.ParserError) as exc:
            raise WebError(f"Invalid SearXNG response: {exc}") from exc

    def fetch(
        self, url: str, max_chars: int = 20_000,
        format: Literal["markdown", "text"] = "markdown",
    ) -> str:
        if format not in {"markdown", "text"}:
            raise WebError("format must be markdown or text")
        if not 1 <= max_chars <= 100_000:
            raise WebError("max_chars must be between 1 and 100000")
        response = self._get(url)
        media_type = response.headers.get("content-type", "").split(";", 1)[0].lower().strip()
        final_url = str(response.url)
        links: list[dict[str, str]] = []
        title = ""
        if media_type == "text/plain":
            text = response.text
        elif media_type in {"text/html", "application/xhtml+xml"}:
            try:
                declared_encoding = response.charset_encoding
                parser = html.HTMLParser(encoding=declared_encoding, no_network=True)
                document = html.fromstring(response.content, parser=parser)
                title = " ".join(document.xpath("string(//title)").split())[:500]
                for element in document.xpath("//script|//style|//noscript|//template"):
                    element.drop_tree()
                base_url = final_url
                base_values = document.xpath("//base/@href")
                if base_values:
                    base_url = urljoin(final_url, str(base_values[0]))
                seen: set[str] = set()
                for anchor in document.xpath("//a[@href]"):
                    href = str(anchor.get("href", "")).strip()
                    if not href or href.startswith("#"):
                        continue
                    absolute_url = urljoin(base_url, href)
                    destination = urldefrag(absolute_url)[0]
                    try:
                        _http_url(destination)
                    except WebError:
                        anchor.attrib.pop("href", None)
                        continue
                    anchor.set("href", absolute_url)
                    if destination in seen:
                        continue
                    seen.add(destination)
                    if len(links) < 100:
                        links.append({"text": " ".join(anchor.text_content().split())[:500], "url": destination[:8192]})
                cleaned = html.tostring(document, encoding="unicode")
                extracted = trafilatura.extract(
                    cleaned, output_format="markdown" if format == "markdown" else "xml",
                    include_comments=False, include_tables=True,
                    include_links=format == "markdown", include_formatting=format == "markdown",
                    url=final_url,
                )
                if extracted and format == "text":
                    text = "\n".join(etree.fromstring(extracted.encode("utf-8")).itertext())
                else:
                    text = extracted or ""
                if format == "markdown" and text:
                    headings = document.xpath("//h1")
                    if headings:
                        heading = " ".join(headings[0].text_content().split())
                        if heading and not any(line.lstrip("# ") == heading for line in text.splitlines()):
                            text = f"# {heading}\n\n{text}"
                if not text:
                    for element in document.xpath("//nav|//header|//footer|//aside"):
                        element.drop_tree()
                    candidates = document.xpath("//main|//article")
                    root = candidates[0] if candidates else document
                    text = root.text_content()
            except (etree.ParserError, ValueError) as exc:
                raise WebError(f"Cannot parse HTML: {exc}") from exc
        else:
            raise WebError(f"Unsupported content type: {media_type or 'missing'}; HTML or plain text required")
        if format == "text":
            text = "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())
        else:
            text = text.strip()
        if not text:
            raise WebError("No readable text found; the page may require JavaScript or authentication")
        return json.dumps({
            "url": final_url, "title": title, "text": text[:max_chars], "format": format,
            "links": links, "truncated": len(text) > max_chars,
        }, ensure_ascii=False)


def _plain(value: str) -> str:
    if not value.strip():
        return ""
    document: Any = html.fragment_fromstring(value, create_parent="div")
    for element in document.xpath("//script|//style"):
        element.drop_tree()
    return " ".join(document.text_content().split())