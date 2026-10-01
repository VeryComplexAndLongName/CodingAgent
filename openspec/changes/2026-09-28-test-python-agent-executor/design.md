## Summary
This is a test-only change to verify executor assignment and execution with the local Python ACP coding agent.

## Non-Goals
- No production behavior change.
- No archive of this test change in this run.

## Decisions
1. Use per-change harness override to assign a dedicated agent id across propose/review/apply/verify.
2. Use a deterministic task (create one markdown file) to validate execution.

## Risks / Trade-offs
- The selected agent id must also exist in harness runtime registry to run fully automated chains.
- If no OpenAI-compatible endpoint is available, execution requires a temporary local mock endpoint.

## Protocol Notes
No command/event contract is changed in this test change.
