## MODIFIED Requirements

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
