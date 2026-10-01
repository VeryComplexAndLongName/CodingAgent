## ADDED Requirements

### Requirement: Executor assignment smoke test
The system MUST support a per-change harness configuration assigning a dedicated agent id for propose/review/apply/verify.

#### Scenario: Per-change stage assignment
- WHEN a change defines `stepAgents` entries for all stages
- THEN each stage has an explicit agent assignment in that change.

### Requirement: Deterministic execution proof
The delegated apply task MUST create a proof artifact file with exact expected content.

#### Scenario: Proof file created
- WHEN delegated task runs successfully
- THEN file `docs/test-agent-executor-proof.md` exists
- AND first line equals `Test change executed by python-coding-agent-acp.`
