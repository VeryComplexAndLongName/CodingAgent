# Security Notes

## API keys

- Prefer environment variables or external secret stores.
- Avoid passing keys in shell history where possible.
- The implementation does not intentionally log API keys.

## Network

- Plain HTTP is acceptable only on trusted private networks.
- For untrusted networks, use TLS termination or tunnel traffic.

## Tool execution

- File operations are constrained to workspace root.
- Shell commands can modify repository state; use bounded timeouts and review outputs.
- Background process support should be monitored and terminated when no longer needed.

## Git operations

- Git tools are intentionally low-level and can change repository history if misused.
- Prefer protected workflows and review before commit operations.
