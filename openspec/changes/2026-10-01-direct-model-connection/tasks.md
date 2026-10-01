## 1. The connection

- [x] 1.1 `src/coding_agent/llm/openai_compatible.py`: `trust_env` on the
  provider, given to `httpx.Client`.
- [x] 1.2 `src/coding_agent/config.py`: `no_proxy` on `AgentConfig`;
  `from_env_defaults` reads `CODING_AGENT_NO_PROXY`.
- [x] 1.3 `src/coding_agent/cli.py`: `--no-proxy`, defaulting to the
  environment, passed to the provider as `trust_env=not no_proxy`.

## 2. Documents

- [x] 2.1 `docs/configuration.md`: the flag, the environment variable and
  the proxy case it answers.
- [x] 2.2 Version 0.4.0 in `pyproject.toml` and `__init__.py`.

## 3. Checks

- [x] 3.1 `tests/test_openai_compatible.py`: the client is built with
  `trust_env` false when the provider is told not to use a proxy, and true
  otherwise.
- [x] 3.2 `ruff`, `mypy`, `pytest`. 2026-10-01: 25 passed; the 13 `ruff`
  findings and the 2 `mypy` errors are the ones this change did not touch.
- [x] 3.3 **Live**: with `HTTP_PROXY=http://127.0.0.1:9` and no
  `NO_PROXY`, `coding-agent --no-proxy --base-url
  http://192.168.137.33:8000/v1 --model QuantTrio/Qwen3.6-35B-A3B-AWQ run`
  answered "готово" on 2026-10-01; the same run without the flag died with
  `httpx.ConnectError` against the proxy.
