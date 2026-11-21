## ADDED Requirements

### Requirement: Repository agent stages default to Codex ACP

The active repository Workbench configuration SHALL assign codex-cli-acp to migrated Claude assignments and to otherwise unassigned propose, review, apply and verify stages. A migrated assignment SHALL use a model supported by Codex or the model configured by Codex when no model is specified. Other explicit agent choices SHALL remain selectable.

#### Scenario: A Claude assignment is migrated

- **WHEN** a stage uses a Claude adapter or a Claude model
- **THEN** its replacement SHALL use codex-cli-acp without a Claude model identifier
- **AND** supported effort and repository-wide workflow settings SHALL be preserved

#### Scenario: Another agent is already selected

- **WHEN** a stage explicitly selects another supported agent
- **THEN** that selection SHALL remain in the configuration
