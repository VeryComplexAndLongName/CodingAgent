## ADDED Requirements

### Requirement: Delegated FastAPI generation task
The change MUST define a delegated implementation task for `python-coding-agent-acp` that generates a FastAPI application under `C:/temp/acp-custom-llm`.

#### Scenario: Target project location
- WHEN delegated apply task runs
- THEN generated source files are created in `C:/temp/acp-custom-llm`
- AND not in the repository root.

### Requirement: API endpoint contract
The generated application MUST expose two endpoints with defined behavior.

#### Scenario: Version endpoint
- WHEN `GET /api/v1/version` is called
- THEN API returns a JSON payload containing service version.

#### Scenario: Sum endpoint
- WHEN `POST /api/v1/data` receives JSON `{ "a": 1, "b": 2 }`
- THEN API returns JSON with sum equal to `3`.

### Requirement: Secret handling for LLM execution
The change MUST avoid storing API key values in repository-tracked files.

#### Scenario: Runtime secret injection
- WHEN agent execution is configured
- THEN API key is provided via runtime environment variable
- AND tracked change artifacts contain no key value.
