## ADDED Requirements

### Requirement: Search using SearXNG

The agent SHALL offer `web_search` using the configured SearXNG `/search`
endpoint with `format=json`, query and language. It SHALL return bounded
results with plain titles, snippets and HTTP(S) links, without API keys.

#### Scenario: Search internal service

- **WHEN** the tool searches a nonempty query in Russian
- **THEN** it returns up to the requested number of search results

### Requirement: Fetch plain text and links

The agent SHALL offer `fetch_url` for HTTP(S) HTML and plain text pages,
accepting `format="markdown"` (default) or `format="text"`, returning the
final URL, title, content in `text`, selected `format` and bounded absolute
links. Markdown SHALL preserve supported headings, tables and inline links;
text mode SHALL omit generated formatting. Unsupported formats SHALL be
rejected. It SHALL remove scripts, styles and HTML markup, close HTTP resources,
limit downloaded bytes and redirects, and report truncation explicitly.

#### Scenario: Read an article

- **WHEN** a page contains an article and relative links
- **THEN** the result contains cleaned Markdown and resolved HTTP(S) links

#### Scenario: Plain text requested

- **WHEN** a caller specifies `format="text"`
- **THEN** the result contains text without generated Markdown formatting

#### Scenario: Table and inline link

- **WHEN** an HTML article contains a simple table and a relative inline link
- **THEN** default output preserves a Markdown table and an absolute inline link

#### Scenario: Failed or unsupported retrieval

- **WHEN** a request times out, returns an HTTP error, exceeds the size
  limit or returns binary content
- **THEN** the tool returns a controlled error, not a raw traceback