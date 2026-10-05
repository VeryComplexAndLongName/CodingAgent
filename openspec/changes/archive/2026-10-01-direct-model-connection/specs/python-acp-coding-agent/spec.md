## ADDED Requirements

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
