## MODIFIED Requirements

### Requirement: A background process never outlives the agent's own

A background process `run_command_background` started SHALL be stopped
when the agent's own process ends, whether or not a turn stopped it
itself first.

#### Scenario: A background process still running when the process ends

- **WHEN** a turn starts a background process and `run`, `chat` ends, or
  `acp`'s stdin closes, without a turn stopping it first
- **THEN** the process is terminated before the agent's own process exits
