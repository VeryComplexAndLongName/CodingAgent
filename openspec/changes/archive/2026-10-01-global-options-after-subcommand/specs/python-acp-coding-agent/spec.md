## ADDED Requirements

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
