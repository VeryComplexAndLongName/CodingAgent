# ADR-0003: SearXNG and plain-text web retrieval

## Status

Accepted.

## Decision

Use the operator's internal SearXNG JSON service for search, trafilatura
for article extraction and lxml for HTML links and fallback text. Keep
network logic separate from builtin dispatch. Do not scrape search engines
directly or add a browser runtime for static pages.

## Consequences

No search API secret is needed. Private destinations are allowed because
the operator explicitly uses an intranet server. These tools are for a
trusted operator, not an SSRF isolation boundary. They do not send the LLM
API key, execute JavaScript, bypass authentication or follow links without
a separate tool call. Results are untrusted source material.

Downloads, output, redirects and timeouts are bounded. Closing a client
releases local connections, not server-side model caches. Extraction can
omit content; links may include navigation. Anti-bot pages and paywalls
are not bypassed.