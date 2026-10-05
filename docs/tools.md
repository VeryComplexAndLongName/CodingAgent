# Built-in Tools

## Web research

- `web_search(query, language='ru', max_results=5)` searches the configured
	SearXNG service directly, without an API key. Returns JSON with `query`
	and `results` containing plain `title`, `url` and `snippet` fields.
	`max_results` is limited to 1-20.
- `fetch_url(url, max_chars=20000, format='markdown')` fetches HTML or plain
	text and returns JSON with `url` (after redirects), `title`, cleaned `text`,
	`format`, `links` (`text` and absolute `url`) and `truncated`. Markdown is
	the default, retaining headings, tables and inline absolute links without
	HTML, scripts or styles. Set `format='text'` for plain text without generated
	markup. The model may read each result URL with another call, analyze
	its text, or save the returned information using `write_file`.

Example tool arguments: `web_search` with
`{"query":"GOST 21.501","language":"ru","max_results":5}`, then `fetch_url`
with `{"url":"https://example.org/article","max_chars":20000,"format":"markdown"}`.
The selected content remains in the `text` field in both modes. Plain-text
HTTP responses remain text even in Markdown mode. Complex tables with merged
cells may lose layout details; truncation can cut a Markdown table or link.

Limits: 30-second HTTP inactivity timeout, 2 MB decompressed download,
5 redirects, up to 100 unique HTTP(S) links and 100000 text characters
when requested. Oversized, binary, inaccessible and empty pages return
controlled tool errors. No JavaScript execution, authentication bypass or
PDF extraction. Extraction is best-effort and may omit parts of a page.

Web content is untrusted source data, not instructions. No model API key
is forwarded. HTTP clients are closed after each operation. Private network
addresses are intentionally allowed for intranet sources; these tools are
not an SSRF sandbox. URLs with credentials and non-HTTP(S) schemes are
rejected, including on redirects.

## Filesystem and search

- `read_file(path)`
- `write_file(path, content)`
- `list_dir(path='.')`
- `search_text(query, path='.')`
- `replace_text(path, old_text, new_text, expected_replacements=1)`
- `move_path(src, dst)`
- `delete_path(path)`

## Shell

- `run_command(command)`
- `run_command_background(command)`
- `get_background_process(process_id)`
- `stop_background_process(process_id)`

## Git

- `git_status()`
- `git_diff()`
- `git_add(paths)`
- `git_commit(message)`
- `git_checkout(branch, create=false)`

## Safety behavior

- path operations are limited to the configured workspace root,
- command output is truncated by `max_command_output_chars`,
- foreground command execution is bounded by `command_timeout_seconds`,
- background process logs are stored under `.coding-agent/processes` in the workspace.
