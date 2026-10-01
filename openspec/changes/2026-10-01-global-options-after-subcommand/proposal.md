## Why

A real ACP client was found that writes the global options after the
subcommand: OpenSpec Workbench's `local-llm-acp` adapter builds its
invocation as `acp --base-url <url> --model <model> ...limits`
(`packages/core/src/agents/local-llm-acp.ts`'s `buildInvocation`), not
`--base-url <url> --model <model> acp`. `argparse`'s subparsers read an
option only where it was declared — the top-level parser here, which
`add_subparsers` leaves unread past the subcommand token — so this order
fails outright.

Measured on 2026-10-01: running `coding-agent acp --base-url
http://192.168.137.33:8000/v1 --model QuantTrio/Qwen3.6-35B-A3B-AWQ`
directly, reproducing the adapter's exact argv, printed `coding-agent:
error: unrecognized arguments: --base-url ... --model ...` and exited `2`
before a single protocol message was written. Driven through Workbench,
the same failure reached the person running the harness as `failed: ACP
connection closed` — the ACP SDK's own message for a peer that closed its
stream, with nothing in it pointing at an argument order.

## What Changes

- **Every global option is read in either position**: before `run`/`acp`,
  as today, or after it, as this client writes it. Both at once is read
  as the later one.
- Nothing already working changes: a command line that already puts
  every option before the subcommand parses exactly as before.
- Version 0.5.0.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `python-acp-coding-agent`: where a global option may appear on the
  command line.

## Impact

- `src/coding_agent/cli.py`: the global options are added to `run` and
  `acp` themselves too, defaulting to `argparse.SUPPRESS` there so an
  omitted one does not overwrite what the top-level parser already read.
- `tests/test_acp_stdio.py`: the real process reads `--base-url`/`--model`
  written after `acp`.
- `docs/configuration.md`.
