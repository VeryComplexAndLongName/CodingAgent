## Decisions

Keep HTTP/extraction in `tools/web.py`, called by the existing builtin
dispatcher. Use trafilatura for article extraction and lxml for safe HTML
parsing and links, not regular expressions. Results are JSON strings with
Markdown content by default, or plain text with `format="text"`, allowing
the model to pass them to `write_file`. Content remains in the `text`
field, and `format` identifies its representation. Use trafilatura's
Markdown renderer to retain tables and formatting; do not collapse its
whitespace or paragraph breaks. Plain-text HTTP responses remain text.

SearXNG connects directly to the configured internal server. Page fetching
honors the existing `--no-proxy` switch. HTTP clients close per operation.
Private network destinations are intentionally supported, not an SSRF
sandbox. Only HTTP(S) without URL credentials is allowed. See ADR-0003.

No global model cache flush, LLM credentials, browser session or autonomous
crawler is involved. JavaScript-only, authenticated and binary pages are
not supported. External content is untrusted data, not instructions.