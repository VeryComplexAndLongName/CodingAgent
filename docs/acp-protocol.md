# ACP Protocol Surface

`coding-agent ... acp` serves the [Agent Client Protocol](https://agentclientprotocol.com),
protocol version 1, over stdio: one JSON-RPC 2.0 message per line on stdin
and on stdout. stdout carries protocol messages only; logs go to stderr.
Any ACP client (Zed, the ACP SDKs, OpenSpec Workbench's `local-llm-acp`)
can drive it. See [ADR 0002](adr/0002-agent-client-protocol.md) for why it
speaks the protocol rather than a dialect of its own.

The global options come before the subcommand, because that is where
`argparse` reads them:

```bash
coding-agent --base-url http://localhost:8000/v1 --model qwen2.5-coder --max-iterations 25 acp
```

## Methods

### initialize

```json
{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":1,"clientCapabilities":{}}}
```

The answer is protocol version 1, no session loading, prompts of text and
embedded text resources, and no authentication methods.

### session/new

```json
{"jsonrpc":"2.0","id":1,"method":"session/new","params":{"cwd":"/abs/path/to/repo","mcpServers":[]}}
```

`cwd` must be an absolute directory: the session's tools read, write and
run commands there and nowhere else. MCP servers are not connected; a
non-empty list is logged and ignored. The answer is `{"sessionId": "<uuid>"}`.

### session/prompt

```json
{"jsonrpc":"2.0","id":2,"method":"session/prompt","params":{"sessionId":"<uuid>","prompt":[{"type":"text","text":"Add a test for greet()"}]}}
```

Text blocks and embedded text resources make up the prompt; a resource link
contributes its name and URI; images and audio are left out. While the turn
runs, the agent sends `session/update` notifications:

- `agent_message_chunk` for each piece of text the model writes, and for a
  stop the model did not write (a limit reached);
- `tool_call`, with `status: "in_progress"`, the tool's `kind` and its
  arguments as `rawInput`, when a tool starts;
- `tool_call_update`, with `status: "completed"` or `"failed"` and the first
  4000 characters of the output, when it ends.

The answer carries `stopReason`:

| The agent stopped because | `stopReason` |
| --- | --- |
| the model ended its turn | `end_turn` |
| a token or context limit | `max_tokens` |
| any other limit (iterations, tool calls, time) | `max_turn_requests` |

and `usage` (`inputTokens`, `outputTokens`, `totalTokens`) summed over the
turn's model calls, where the model reported any. The agent's own reason is
in `_meta.codingAgent.stoppedReason`.

### session/cancel

A notification. It is recorded; a turn already running finishes or is
ended by the client closing the process.

Not served: `session/load`, `session/set_mode`, and permission requests.
The tools run without asking, inside the session's `cwd`.

## Limits through ACP

Limits are this agent's extension, not part of the protocol. They are read
from `_meta.codingAgent.limits` (or a top-level `limits` field) on
`session/new`, and on `session/prompt`, whose values are laid over the
session's:

```json
{"_meta":{"codingAgent":{"limits":{"max_iterations":30,"max_seconds":600,"max_context_share":0.8}}}}
```

Accepted fields:

- `max_iterations`
- `max_tool_calls`
- `max_seconds`
- `command_timeout_seconds`
- `max_command_output_chars`
- `max_prompt_tokens`
- `max_completion_tokens`
- `max_total_tokens`
- `max_context_used_tokens`
- `max_context_window_tokens`
- `max_context_share`
- `min_free_context_tokens`

The same limits are also command-line options, which apply to every
session the process serves.
