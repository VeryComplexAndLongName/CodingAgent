## 1. The protocol

- [x] 1.1 `src/coding_agent/acp_models.py`: the params of `initialize`,
  `session/new`, `session/prompt` and `session/cancel`, open to fields this
  agent does not use; `prompt_text` for content blocks; `limits_from` for
  `limits` and `_meta.codingAgent.limits`.
- [x] 1.2 `src/coding_agent/acp_server.py`: the four methods, errors that
  answer their request's id, `session/update` notifications from the
  agent's progress, the protocol's stop reasons and `usage`.
- [x] 1.3 `src/coding_agent/agent.py`: progress events `assistant_message`,
  `tool_result` and `usage`; `tool_call` carries its arguments.
- [x] 1.4 `src/coding_agent/cli.py`: in `acp` mode, logs to stderr, UTF-8
  stdin and stdout, and one agent per session in its `cwd`.
- [x] 1.5 `src/coding_agent/tools/builtin.py`: `.coding-agent/processes` is
  made when a background process first needs it.
- [x] 1.6 `src/coding_agent/llm/openai_compatible.py`: `"tool_calls": null`,
  `"usage": null` and null arguments read as none, as SGLang sends them;
  the first live turn against SGLang failed with "'NoneType' object is not
  iterable".
- [x] 1.7 `src/coding_agent/llm/openai_compatible.py`: `tool_calls_in_text`
  takes a call the model wrote as text, in Qwen3-Coder's
  `<function=...><parameter=...>` form or Hermes' JSON, each in
  `<tool_call>`, where the server's parser did not; only a call to an
  offered tool, and JSON only for array and object parameters. The second
  live turn ended at once: SGLang's `hermes` parser passed Qwen3.6's calls
  through as text.
- [x] 1.8 `src/coding_agent/cli.py`: `--version`.

## 2. Documents

- [x] 2.1 `docs/adr/0002-agent-client-protocol.md`.
- [x] 2.2 `docs/acp-protocol.md` describes the protocol as served.
- [x] 2.3 Version 0.3.0 in `pyproject.toml` and `__init__.py`.

## 3. Checks

- [x] 3.1 `tests/test_acp.py`: initialize, session in the client's `cwd`,
  a refused relative `cwd` answering its id, a turn's updates and
  response, a limit stop, limits merged from `_meta`, prompt text from
  blocks, unknown method and session, cancel as a notification.
- [x] 3.2 `tests/test_acp_stdio.py`: the real process against a stand-in
  OpenAI-compatible server; every stdout line is a protocol message, the
  file is written in the session's `cwd`, and no `.coding-agent` appears.
- [x] 3.3 `tests/test_openai_compatible.py`: null fields, a Qwen3-Coder and a
  Hermes call written as text, JSON-looking file content kept as text, a
  call to a tool not offered left as text. `pytest`: 23 passed on
  2026-10-01.
- [x] 3.4 **Delegated to local-llm-acp**: OpenSpec Workbench's
  `local-llm-acp` adapter runs this agent through its ACP driver against a
  real OpenAI-compatible model, and the run writes a file. Record the run
  id, the model endpoint, the events the driver produced, and the file.
  Record, 2026-10-01: run `live-local-llm-acp-1790853181423`, an `implement`
  run of OpenSpec Workbench's `local-llm-acp` runner (branch
  `fix-local-llm-acp`) on a scratch repository's change
  `greeting-takes-a-name`, against SGLang at `192.168.137.33:8000` serving
  `QuantTrio/Qwen3.6-35B-A3B-AWQ`. 70 s; the driver produced `started`, 21
  `tool_call` updates with their `tool_call_update`s (list_dir, read_file,
  replace_text, write_file, run_command `node --test`), the agent's
  summary as `agent_message_chunk`, `usageReported` (122745 in, 545 out)
  and `completed`. Afterwards `src/greet.js` takes a name,
  `src/greet.test.mjs` exists, `node --test` passes 5 of 5, and the
  change's four tasks are ticked; `git status` shows only `README.md`, the
  change's `tasks.md`, `src/greet.js` and `src/greet.test.mjs`.
