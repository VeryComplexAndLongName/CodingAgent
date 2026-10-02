## ADDED Requirements

### Requirement: A `chat` command holds a multi-turn conversation

`coding-agent chat` SHALL read one line at a time from stdin, run it as a
turn sharing one conversation with every line before it in the same
process, and print each turn's message. A blank line SHALL be skipped.
`exit` or `quit` (trimmed, case-insensitive), end of input, or Ctrl-C
SHALL end the session.

#### Scenario: A second line refers to the first

- **WHEN** a session is given `My name is Alex.` and then `What is my
  name?`
- **THEN** the second turn's answer uses the first turn's conversation,
  not a fresh one

#### Scenario: Ending the session

- **WHEN** a line reads `exit`
- **THEN** the process ends without reading further input

#### Scenario: A turn fails

- **WHEN** a turn raises — a network error, a server's own rejection
- **THEN** the session keeps running: the failed line is dropped from the
  shared conversation, and the next line is read as a new turn
