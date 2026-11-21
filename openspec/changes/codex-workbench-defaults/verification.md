# Verification

Date: 2026-11-21

- Parsed the repository configuration through the current Workbench reader.
- Verified the global configuration and resolved active changes.
- Verified both Claude adapters still expose their model and custom-agent settings.
- Removed Claude model IDs only from the assignments migrated to Codex ACP.
- Preserved supported effort and repository-level autonomy, review and run limits.

Strict repository OpenSpec validation passed for 6 items.

Existing unchanged per-change configuration errors
- 2026-09-28-fastapi-sum-api-agent-task: InvalidHarnessConfigError: stepAgents.propose references unknown agent id "python-coding-agent-acp"
The same errors were reproduced using the server's previous per-change files. Global configuration validation passed.
