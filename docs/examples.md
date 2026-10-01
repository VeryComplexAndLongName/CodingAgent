# Examples

## One-shot run mode

```bash
coding-agent \
  --base-url http://localhost:8000/v1 \
  --model qwen2.5-coder \
  --workspace . \
  --max-iterations 25 \
  --max-tool-calls 80 \
  --max-seconds 900 \
  --max-total-tokens 200000 \
  run "Create a Python module and unit tests for slug generation"
```

## ACP mode with conservative limits

```bash
coding-agent \
  --base-url http://localhost:8000/v1 \
  --model qwen2.5-coder \
  --workspace . \
  --max-iterations 15 \
  --max-tool-calls 40 \
  --max-seconds 300 \
  --max-context-share 0.75 \
  acp
```

## Prompt-level ACP override example

`session/new`:
```json
{"jsonrpc":"2.0","id":1,"method":"session/new","params":{"limits":{"max_iterations":20}}}
```

`session/prompt` with stronger limits:
```json
{
  "jsonrpc":"2.0",
  "id":2,
  "method":"session/prompt",
  "params":{
    "sessionId":"<uuid>",
    "prompt":"Refactor JS utility and add tests",
    "limits":{
      "max_tool_calls":25,
      "max_completion_tokens":2500,
      "max_seconds":180
    }
  }
}
```
