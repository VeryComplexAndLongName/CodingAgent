# Overview

The project provides a Python coding agent that:
- speaks ACP-compatible JSON-RPC over stdio,
- uses an OpenAI-compatible LLM endpoint,
- executes built-in coding tools,
- enforces hard runtime and usage limits.

## Architecture

- Agent core:
  - prompt/tool loop
  - stop conditions and guardrails
- ACP transport:
  - JSON-RPC methods and notifications over stdin/stdout
- LLM provider:
  - Chat Completions-compatible endpoint
- Tool subsystem:
  - filesystem/search/shell/git/background process controls

## Supported coding domains

The agent is intended for multi-language tasks, including:
- Python
- TypeScript
- JavaScript
- HTML
- CSS
- other text-based programming languages
