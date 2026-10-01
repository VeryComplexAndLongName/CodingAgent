# Built-in Tools

## Filesystem and search

- `read_file(path)`
- `write_file(path, content)`
- `list_dir(path='.')`
- `search_text(query, path='.')`
- `replace_text(path, old_text, new_text, expected_replacements=1)`
- `move_path(src, dst)`
- `delete_path(path)`

## Shell

- `run_command(command)`
- `run_command_background(command)`
- `get_background_process(process_id)`
- `stop_background_process(process_id)`

## Git

- `git_status()`
- `git_diff()`
- `git_add(paths)`
- `git_commit(message)`
- `git_checkout(branch, create=false)`

## Safety behavior

- path operations are limited to the configured workspace root,
- command output is truncated by `max_command_output_chars`,
- foreground command execution is bounded by `command_timeout_seconds`,
- background process logs are stored under `.coding-agent/processes` in the workspace.
