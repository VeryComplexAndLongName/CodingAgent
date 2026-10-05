## Implementation

- [x] 1.4 Add `fetch_url` format selection: Markdown default and plain text opt-in.
	Preserve table structure and inline links; retain the JSON `text` field
	and report the selected format. Validate both modes through tool dispatch.
	70 tests passed, including both formats and invalid format rejection;
	new module and tests pass Ruff. Both modes smoke-tested on the HTML
	GOST page; Markdown retained formatting, with known complex-table limitations.

- [x] 1.1 Add bounded SearXNG search and HTML/plain-text fetching with links.
- [x] 1.2 Register tools and wire CLI/environment configuration in every mode.
- [x] 1.3 Document network trust, limitations and examples; bump to 0.10.0.

## Verification

- [x] 2.1 Test extraction, links, limits, redirects, errors and registration.
	Includes gzip, HTML charset, tables without generated markup and all CLI modes.
- [x] 2.2 Validate OpenSpec; run tests, lint and type checks.
	68 tests passed; new files pass Ruff; strict OpenSpec validation passed.
	Mypy reports only the two existing CLI `TextIO.reconfigure` errors.
- [x] 2.3 Smoke-test the internal SearXNG service and fetch a result.
	Query `GOST 21.501` in Russian at `192.168.137.39:8888` returned three
	selected results. The HTML result at
	`https://files.stroyinf.ru/Data2/1/4293732/4293732743.htm` returned
	20000 plain text characters, 24 links and `truncated: true`.
	The PDF result was refused by the download size limit, as expected.