## Why
A test change is needed to evaluate end-to-end execution by the Python ACP coding agent against a real OpenAI-compatible LLM endpoint.

## Capabilities
- New:
  - Define a delegated implementation task for generating a FastAPI service in an external workspace.
- Modified:
  - None.

## Scope
- Create a coding task in `C:/temp/acp-custom-llm`.
- Require implementation of a small REST API service with two endpoints.
- Define explicit verification evidence and agent assignment.

## Target API
- `GET /api/v1/version`: returns service version.
- `POST /api/v1/data`: accepts JSON body `{ "a": 1, "b": 2 }` and returns the sum.

## LLM Runtime Configuration
- Base URL: `http://192.168.137.33:8000/v1`
- Model: `QuantTrio/Qwen3.6-35B-A3B-AWQ`
- API key must be provided at runtime through environment variable (do not commit key values to repository files).
