## Why
Need a smoke test that proves a change can be prepared with a Python ACP coding agent assigned as executor across stages.

## Capabilities
- New:
  - Add a test-only OpenSpec change used to validate executor wiring and execution flow.
- Modified:
  - None.

## Scope
- Assign the Python ACP coding agent as stage executor in per-change harness config.
- Include one deterministic task that can be completed by the coding agent.
