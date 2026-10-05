## Why

The agent needs to search the internal SearXNG service and read web sources
as plain text with links, without delegating browsing to shell commands.

## What Changes

- Add `web_search(query, language, max_results)` using SearXNG JSON.
- Add `fetch_url(url, max_chars, format)` returning title, content and absolute
  links: Markdown by default, plain text when requested.
- Configure the SearXNG URL through CLI or environment; default to
  `http://192.168.137.39:8888`.
- Bound response sizes, redirects, output and HTTP timeouts; report failures
  as tool errors. Do not forward model credentials to web services.
- Version 0.10.0. See [ADR-0003](../../../docs/adr/0003-web-research-tools.md).

## Capabilities

### New Capabilities

- `web-research`: search and plain-text retrieval.

### Modified Capabilities

None.

## Impact

Tool dispatch, CLI configuration, extraction dependencies, focused tests
and tool documentation. No automatic crawling or JavaScript execution.