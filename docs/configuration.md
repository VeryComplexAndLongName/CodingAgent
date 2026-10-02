# Configuration

## CLI arguments

Global options:
- `--base-url`
- `--model`
- `--api-key`
- `--no-proxy`
- `--workspace`
- `--max-iterations`
- `--max-tool-calls`
- `--max-seconds`
- `--command-timeout-seconds`
- `--max-command-output-chars`
- `--max-prompt-tokens`
- `--max-completion-tokens`
- `--max-total-tokens`
- `--max-context-used-tokens`
- `--max-context-window-tokens`
- `--max-context-share`
- `--min-free-context-tokens`

Commands:
- `run <prompt>`
- `chat`
- `acp`

Every global option may come before `run`/`acp` or after it — a real ACP
client such as OpenSpec Workbench's `local-llm-acp` adapter writes them
after (`acp --base-url ... --model ...`). Where the same option is
written in both places, the one after the subcommand is used.

### `chat`

An interactive, multi-turn conversation over stdin/stdout: each line is a
turn, and every turn shares one conversation with every line before it
in the same process. A blank line is skipped. `exit`, `quit`, end of
input (Ctrl-D) or Ctrl-C ends the session.

```bash
coding-agent --base-url http://localhost:8000/v1 --model qwen2.5-coder chat
```

A background process `run_command_background` started during the
session, if still running, is stopped when the session ends — the same
is true of `run` and `acp` — so nothing a turn started outlives the
agent's own process.

## Environment variables

Fallback values:
- `CODING_AGENT_BASE_URL`
- `CODING_AGENT_MODEL`
- `CODING_AGENT_API_KEY`
- `CODING_AGENT_NO_PROXY` (`1`/`true`/`yes`/`on`)

## Proxies

Model calls follow `HTTP_PROXY`, `HTTPS_PROXY` and `NO_PROXY` from the
environment. Behind a corporate proxy that cannot reach a model served on
the local network, the proxy answers `502 Bad Gateway`; `--no-proxy` makes
the agent connect to the endpoint directly instead.

```bash
coding-agent --no-proxy --base-url http://192.168.137.33:8000/v1 --model qwen3 run "..."
```

## Typical configurations

Local model server without key:
```bash
coding-agent --base-url http://localhost:8000/v1 --model qwen2.5-coder acp
```

Hosted endpoint with key:
```bash
coding-agent --base-url https://example-llm.company/v1 --model deepseek-coder --api-key "$DEEPSEEK_API_KEY" acp
```
