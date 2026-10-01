## Summary
This change prepares a delegated coding task for the Python ACP coding agent to generate a FastAPI service in an external directory and validate core endpoint behavior.

## Non-Goals
- No implementation is performed in this change.
- No deployment automation is added.
- No archive action is performed.

## Decisions
1. Use delegated task execution by `python-coding-agent-acp`.
- Reason: the objective is to test the custom ACP coding agent flow.
- Rejected alternative: direct manual implementation in this repository.
- Rejection reason: would not validate the target agent workflow.

2. Keep API key out of tracked files.
- Reason: secret safety.
- Rejected alternative: store test key in `harness.json` or markdown.
- Rejection reason: secret leakage risk and poor practice even for test values.

3. Target external path `C:/temp/acp-custom-llm`.
- Reason: task requires generating project files outside this repository.
- Rejected alternative: generate files under repository root.
- Rejection reason: mismatches requested execution target.

## Risks / Trade-offs
- External path generation is less reproducible without workspace provisioning checks.
- LLM provider behavior may vary; strict endpoint acceptance criteria are required.
- Runtime connectivity to the specified LLM endpoint may fail due to network constraints.

## Protocol Notes
No new ACP methods are introduced in this change. The change uses existing agent execution flow and delegated task semantics.
