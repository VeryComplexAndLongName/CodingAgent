## MODIFIED Requirements

### Requirement: `run`'s prompt comes from the positional argument or a file

`coding-agent run` SHALL accept the prompt either as its positional
argument or, given `--prompt-file <path>`, as that file's content read
as-is (UTF-8 text, Markdown or plain, nothing stripped or interpreted).
Exactly one of the two SHALL be given; giving both, or neither, SHALL be
refused with a usage error.

#### Scenario: A Markdown file as the prompt

- **WHEN** `coding-agent run --prompt-file task.md` is run and `task.md`
  holds a Markdown checklist
- **THEN** the file's content is sent as the turn's prompt, unchanged

#### Scenario: Both given

- **WHEN** `coding-agent run "hi" --prompt-file task.md` is run
- **THEN** the process exits with a usage error naming both

#### Scenario: Neither given

- **WHEN** `coding-agent run` is run with no positional argument and no
  `--prompt-file`
- **THEN** the process exits with a usage error
