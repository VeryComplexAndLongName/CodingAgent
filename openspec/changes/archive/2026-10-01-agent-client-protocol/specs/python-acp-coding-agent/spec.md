## ADDED Requirements

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
