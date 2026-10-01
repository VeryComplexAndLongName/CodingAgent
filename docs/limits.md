# Limits and Stop Conditions

## Core execution limits

- `max_iterations`
- `max_tool_calls`
- `max_seconds`

## Command execution limits

- `command_timeout_seconds`
- `max_command_output_chars`

## Token limits

- `max_prompt_tokens`
- `max_completion_tokens`
- `max_total_tokens`

## Context limits

- `max_context_used_tokens`
- `max_context_window_tokens`
- `max_context_share`
- `min_free_context_tokens`

## Stop reasons

The runtime can stop with reasons including:
- `completed`
- `max_iterations`
- `max_tool_calls`
- `max_seconds`
- `max_prompt_tokens`
- `max_completion_tokens`
- `max_total_tokens`
- `max_context_used_tokens`
- `max_context_window_tokens`
- `max_context_share`
- `min_free_context_tokens`

## How ACP applies limits

- Default values come from process configuration.
- Session-level limits are set through `session/new` request `params.limits`.
- Prompt-level limits are set through `session/prompt` request `params.limits`.
- Prompt-level values override session-level values; session-level values override defaults.
