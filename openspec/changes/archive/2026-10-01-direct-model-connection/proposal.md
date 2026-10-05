## Why

`httpx.Client` trusts the environment by default, so the provider sends
every model call through whatever `HTTP_PROXY`/`HTTPS_PROXY` names. On a
workstation behind a corporate proxy that breaks a model served on the
local network: measured on 2026-10-01 against SGLang at
`192.168.137.33:8000` serving `QuantTrio/Qwen3.6-35B-A3B-AWQ`, every turn
died with `httpx.HTTPStatusError: Server error '502 Bad Gateway'`, while
the same endpoint answered `200` once the host was excluded from the
proxy. The only workaround was `NO_PROXY`, which the agent neither
documents nor controls, and which a client launching the agent over ACP
cannot set per endpoint.

## What Changes

- **`--no-proxy` makes the agent connect directly**: the provider ignores
  the environment's proxy and certificate settings for model calls.
  `CODING_AGENT_NO_PROXY` is read as the fallback.
- Without the flag nothing changes: the environment is trusted as before.
- Version 0.4.0.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `python-acp-coding-agent`: how the provider reaches the model endpoint.

## Impact

- `src/coding_agent/llm/openai_compatible.py`: `trust_env` on the client.
- `src/coding_agent/config.py`: `no_proxy` on `AgentConfig`, and in
  `from_env_defaults`.
- `src/coding_agent/cli.py`: the `--no-proxy` flag, passed to the provider.
- `tests/test_openai_compatible.py`.
- `docs/configuration.md`.
