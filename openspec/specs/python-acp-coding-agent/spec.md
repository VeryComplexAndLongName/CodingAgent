# python-acp-coding-agent Specification

## Purpose

Provides a Python coding agent over the Agent Client Protocol with configurable OpenAI-compatible models, tool execution, conversation state and resilient provider handling.

## Requirements

### Requirement: ACP-compatible coding process
The system MUST provide a Python executable that serves ACP-compatible JSON-RPC messages over stdio for coding workflows.

#### Scenario: Session lifecycle
- WHEN a client sends initialize, session/new, and session/prompt
- THEN the agent returns valid JSON-RPC responses
- AND emits progress/final updates through session/update notifications.

### Requirement: OpenAI-compatible LLM connectivity
The system MUST support OpenAI-compatible Chat Completions through a configurable base URL and model, with optional API key bearer authentication.

#### Scenario: API key optionality
- WHEN api_key is not configured
- THEN requests are sent without Authorization header
- AND completion still succeeds against endpoints that do not require authentication.

### Requirement: Built-in coding tools
The system MUST include built-in tools for filesystem operations, text search, and shell command execution.

#### Scenario: Workspace safety
- WHEN a tool receives a path outside workspace root
- THEN the call fails with a tool error
- AND no write/read occurs outside the workspace.

### Requirement: Runtime guardrails
The system MUST enforce upper bounds on iterations, tool calls, wall-clock runtime, and command execution behavior.

#### Scenario: Tool call cap
- WHEN tool call count exceeds configured max_tool_calls
- THEN the agent stops and reports max_tool_calls as stop reason.

### Requirement: ACP-configurable limits
The system MUST allow runtime limits to be supplied through ACP requests and applied per session and per prompt.

#### Scenario: Prompt-level override
- WHEN a client sets limits in `session/new` and sends a stricter override in `session/prompt`
- THEN the prompt run uses the merged effective limits with prompt values taking precedence.

### Requirement: Token and context stopping
The system MUST support stopping conditions based on token budgets and context pressure when usage data is available from the model response.

#### Scenario: Context share threshold
- WHEN usage reports context window and used context values
- AND used/window share exceeds configured `max_context_share`
- THEN the agent stops with stop reason `max_context_share`.

### Requirement: Extended coding tools
The system MUST provide patch-like file editing, git utilities, and background command lifecycle tools in addition to baseline filesystem and shell commands.

#### Scenario: Patch-like replace
- WHEN tool `replace_text` receives an expected replacement count that matches file content
- THEN the edit is applied atomically and reported with replacement count.

### Requirement: The stdio server speaks the Agent Client Protocol

The `acp` command SHALL serve the Agent Client Protocol, version 1, over
stdio, one JSON-RPC 2.0 message per line. It SHALL answer `initialize` with
an integer protocol version, SHALL open a session for `session/new` given
the client's absolute `cwd` and `mcpServers`, and SHALL take
`session/prompt`'s prompt as a list of content blocks. During a turn it
SHALL send `session/update` notifications: `agent_message_chunk` for the
model's text, `tool_call` when a tool starts and `tool_call_update` when it
ends. It SHALL answer the turn with a `stopReason` the protocol names and,
where the model reported tokens, `usage`. Every error SHALL carry the id of
the request it answers. stdout SHALL carry protocol messages only.

#### Scenario: A client opens a session and runs a turn

- **WHEN** a client sends `initialize` with `protocolVersion: 1`,
  `session/new` with an absolute `cwd` and an empty `mcpServers`, and
  `session/prompt` with a text block
- **THEN** each request is answered with its own id, the turn's text and
  tool calls arrive as `session/update` notifications, and the turn ends
  with `stopReason: "end_turn"`

#### Scenario: A limit ends the turn

- **WHEN** the agent stops on a limit of iterations, tool calls or time
- **THEN** the stop is said in an `agent_message_chunk`, and the turn ends
  with `stopReason: "max_turn_requests"`

#### Scenario: A request the server refuses

- **WHEN** `session/new` names a relative `cwd`
- **THEN** the error answers that request's id with code `-32602`

### Requirement: A session works in the client's directory

A session's tools SHALL read, write and run commands in the `cwd` its
`session/new` named, and SHALL leave nothing in it the turn did not write.

#### Scenario: A file written in a turn

- **WHEN** a turn writes `hello.txt`
- **THEN** it is in the session's `cwd`, and no `.coding-agent` directory
  appears there

### Requirement: A tool call is taken however the server returns it

The OpenAI-compatible provider SHALL read a null `tool_calls`, `usage` or
function arguments as none. Where an answer carries no structured tool
call, it SHALL take a call the model wrote in its text inside
`<tool_call>`, in Qwen3-Coder's `<function=...><parameter=...>` form or as
Hermes' JSON, provided the tool was offered, and SHALL remove it from the
text. A parameter SHALL be read as JSON only where the tool declares an
array or an object.

#### Scenario: A server whose parser does not match the model

- **WHEN** an answer's text holds `<tool_call><function=read_file><parameter=path>src/greet.js</parameter></function></tool_call>`
  and no structured tool call
- **THEN** the turn calls `read_file` with path `src/greet.js`

#### Scenario: A tool that was not offered

- **WHEN** the text names a tool the request did not offer
- **THEN** no call is made and the text is left as it is

### Requirement: Limits travel as an extension

Limits SHALL be read from `_meta.codingAgent.limits`, or a top-level
`limits` field, on `session/new` and on `session/prompt`; a prompt's values
SHALL be laid over its session's.

#### Scenario: A prompt narrows its session's limits

- **WHEN** `session/new` sets `max_iterations: 2` and `max_seconds: 60`, and
  a `session/prompt` sets `max_iterations: 1`
- **THEN** the turn runs with `max_iterations: 1` and `max_seconds: 60`

### Requirement: The model endpoint can be reached without a proxy

The agent SHALL offer `--no-proxy`, falling back to
`CODING_AGENT_NO_PROXY`, which makes the OpenAI-compatible provider ignore
the environment's proxy settings for model calls. Without it the provider
SHALL keep trusting the environment.

#### Scenario: A model on the local network behind a corporate proxy

- **WHEN** `HTTP_PROXY` names a proxy that cannot reach the model's host,
  and the agent is run with `--no-proxy`
- **THEN** the model call goes to the endpoint directly and the turn
  succeeds

#### Scenario: The flag is not given

- **WHEN** the agent is run without `--no-proxy` and without
  `CODING_AGENT_NO_PROXY`
- **THEN** the provider uses the environment's proxy settings as before

### Requirement: A global option is read before or after the subcommand

Every option `coding-agent` accepts outside `run`'s own `prompt`
positional SHALL be read whether it is written before `run`/`acp` or
after it. Where the same option is written in both places, the one
written after the subcommand SHALL be used.

#### Scenario: Options written after the subcommand, as a real ACP client writes them

- **WHEN** `coding-agent acp --base-url <url> --model <model>` is run
- **THEN** the server uses that base URL and model, exactly as
  `coding-agent --base-url <url> --model <model> acp` would

#### Scenario: The same option in both places

- **WHEN** `coding-agent --model a run --model b "hi"` is run
- **THEN** the turn uses model `b`

### Requirement: `run`'s prompt comes from the positional argument or a file

`coding-agent run` SHALL accept the prompt either as its positional
argument or, given `--prompt-file <path>`, as that file's content read
as-is (Markdown or plain, nothing stripped or interpreted) — UTF-8 (with
or without a BOM), falling back to the system's own encoding where it is
not. Exactly one of the two SHALL be given; giving both, or neither,
SHALL be refused with a usage error. A file decodable by neither SHALL be
refused with a usage error naming the file.

#### Scenario: A Markdown file as the prompt

- **WHEN** `coding-agent run --prompt-file task.md` is run and `task.md`
  holds a Markdown checklist
- **THEN** the file's content is sent as the turn's prompt, unchanged

#### Scenario: A file in the system's own encoding

- **WHEN** `task.txt` is saved in the system's own encoding rather than
  UTF-8
- **THEN** its content is still read correctly, rather than raising an
  unhandled `UnicodeDecodeError`

#### Scenario: Both given

- **WHEN** `coding-agent run "hi" --prompt-file task.md` is run
- **THEN** the process exits with a usage error naming both

#### Scenario: Neither given

- **WHEN** `coding-agent run` is run with no positional argument and no
  `--prompt-file`
- **THEN** the process exits with a usage error

### Requirement: The model request's timeout is configurable

`--request-timeout-seconds` (default 120) SHALL set the HTTP timeout the
provider gives each model request.

#### Scenario: A slower model given more time

- **WHEN** `coding-agent --request-timeout-seconds 300 ...` is run
- **THEN** a model request is allowed up to 300 seconds before the
  provider gives up on it

### Requirement: A failed model request ends the turn, not the process

A turn whose model request fails (a timeout, a connection error) SHALL
end with `stopped_reason: "provider_error"` and a message naming the
failure, rather than raising out of `run_prompt`.

#### Scenario: A request timing out

- **WHEN** a model request exceeds `--request-timeout-seconds`
- **THEN** the turn ends with `stopped_reason: "provider_error"`; `run`
  prints the message and exits; `chat`'s session and `acp`'s session
  continue

### Requirement: A background process never outlives the agent's own

A background process `run_command_background` started SHALL be stopped
when the agent's own process ends, whether or not a turn stopped it
itself first.

#### Scenario: A background process still running when the process ends

- **WHEN** a turn starts a background process and `run`, `chat` ends, or
  `acp`'s stdin closes, without a turn stopping it first
- **THEN** the process is terminated before the agent's own process exits
