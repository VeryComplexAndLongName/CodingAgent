# Configuration

## CLI arguments

Global options:
- `--base-url`
- `--model`
- `--api-key`
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
- `acp`

## Environment variables

Fallback values:
- `CODING_AGENT_BASE_URL`
- `CODING_AGENT_MODEL`
- `CODING_AGENT_API_KEY`

## Typical configurations

Local model server without key:
```bash
coding-agent --base-url http://localhost:8000/v1 --model qwen2.5-coder acp
```

Hosted endpoint with key:
```bash
coding-agent --base-url https://example-llm.company/v1 --model deepseek-coder --api-key "$DEEPSEEK_API_KEY" acp
```
