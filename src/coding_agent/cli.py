from __future__ import annotations

import argparse
import locale
import os
import sys
from io import TextIOWrapper
from pathlib import Path
from typing import cast

from loguru import logger

from coding_agent import __version__
from coding_agent.acp_server import ACPServer
from coding_agent.agent import CodingAgent
from coding_agent.config import AgentConfig, AgentLimits, from_env_defaults, no_proxy_from_env
from coding_agent.llm.openai_compatible import OpenAICompatibleProvider
from coding_agent.tools.builtin import BuiltinTools
from coding_agent.tools.registry import ToolRegistry


def _add_global_args(parser: argparse.ArgumentParser, *, suppress_defaults: bool) -> None:
    """Every option outside `run`'s own `prompt`. Added to the top-level
    parser with real defaults, and again to each subparser with defaults
    suppressed — so an option read before the subcommand survives unless
    the same option is given again after it, which is how a real ACP
    client (OpenSpec Workbench's `local-llm-acp` adapter) writes them:
    `acp --base-url <url> --model <model>`, not the other way around."""
    env_base_url, env_model, env_api_key = from_env_defaults()

    def default(value: object) -> object:
        return argparse.SUPPRESS if suppress_defaults else value

    parser.add_argument("--base-url", default=default(env_base_url))
    parser.add_argument("--model", default=default(env_model))
    parser.add_argument("--api-key", default=default(env_api_key))
    parser.add_argument(
        "--searxng-url",
        default=default(os.getenv("CODING_AGENT_SEARXNG_URL", "http://192.168.137.39:8888")),
        help="SearXNG base URL for web_search (connects directly)",
    )
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        default=default(no_proxy_from_env()),
        help="Reach the model endpoint directly, ignoring proxy settings in the environment",
    )
    parser.add_argument("--workspace", default=default("."))
    parser.add_argument("--max-iterations", type=int, default=default(20))
    parser.add_argument("--max-tool-calls", type=int, default=default(60))
    parser.add_argument("--max-seconds", type=int, default=default(300))
    parser.add_argument("--command-timeout-seconds", type=int, default=default(60))
    parser.add_argument("--max-command-output-chars", type=int, default=default(12000))
    parser.add_argument(
        "--request-timeout-seconds",
        type=int,
        default=default(120),
        help="HTTP timeout for one model request",
    )
    parser.add_argument("--max-prompt-tokens", type=int, default=default(None))
    parser.add_argument("--max-completion-tokens", type=int, default=default(None))
    parser.add_argument("--max-total-tokens", type=int, default=default(None))
    parser.add_argument("--max-context-used-tokens", type=int, default=default(None))
    parser.add_argument("--max-context-window-tokens", type=int, default=default(None))
    parser.add_argument("--max-context-share", type=float, default=default(None))
    parser.add_argument("--min-free-context-tokens", type=int, default=default(None))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="coding-agent")
    # Read by clients that detect the agent with `coding-agent --version`.
    parser.add_argument("--version", action="version", version=f"coding-agent {__version__}")
    _add_global_args(parser, suppress_defaults=False)

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Run one prompt from text or --prompt-file PATH and print assistant output",
    )
    _add_global_args(run_parser, suppress_defaults=True)
    run_parser.add_argument("prompt", nargs="?", default=None, help="The prompt text. Omit when using --prompt-file.")
    run_parser.add_argument(
        "--prompt-file",
        type=Path,
        default=None,
        help="Read the prompt from this file (Markdown or plain text) instead of the positional argument",
    )

    chat_parser = subparsers.add_parser("chat", help="Hold an interactive, multi-turn conversation over stdin/stdout")
    _add_global_args(chat_parser, suppress_defaults=True)

    acp_parser = subparsers.add_parser("acp", help="Run ACP-compatible stdio JSON-RPC server")
    _add_global_args(acp_parser, suppress_defaults=True)
    return parser


def _build_agent(args: argparse.Namespace, workspace: Path | None = None) -> CodingAgent:
    limits = AgentLimits(
        max_iterations=args.max_iterations,
        max_tool_calls=args.max_tool_calls,
        max_seconds=args.max_seconds,
        command_timeout_seconds=args.command_timeout_seconds,
        max_command_output_chars=args.max_command_output_chars,
        max_prompt_tokens=args.max_prompt_tokens,
        max_completion_tokens=args.max_completion_tokens,
        max_total_tokens=args.max_total_tokens,
        max_context_used_tokens=args.max_context_used_tokens,
        max_context_window_tokens=args.max_context_window_tokens,
        max_context_share=args.max_context_share,
        min_free_context_tokens=args.min_free_context_tokens,
    )

    config = AgentConfig(
        base_url=args.base_url,
        model=args.model,
        api_key=args.api_key,
        workspace=workspace if workspace is not None else args.workspace,
        limits=limits,
        no_proxy=args.no_proxy,
        request_timeout_seconds=args.request_timeout_seconds,
        searxng_url=args.searxng_url,
    )

    provider = OpenAICompatibleProvider(
        base_url=config.base_url,
        model=config.model,
        api_key=config.api_key,
        trust_env=not config.no_proxy,
        timeout_seconds=config.request_timeout_seconds,
    )
    tools = ToolRegistry(
        BuiltinTools(
            workspace=config.workspace,
            command_timeout_seconds=config.limits.command_timeout_seconds,
            max_command_output_chars=config.limits.max_command_output_chars,
            searxng_url=config.searxng_url,
            web_trust_env=not config.no_proxy,
        )
    )
    return CodingAgent(config=config, provider=provider, tools=tools)


def _run_chat(agent: CodingAgent) -> None:
    """One line of stdin per turn, every turn sharing one conversation,
    until `exit`/`quit`, end of input, or Ctrl-C. `run_prompt` itself
    turns a provider failure into a `provider_error`-stopped result, not
    an exception; the `try` here is a last resort, for whatever that
    does not cover, so one turn's bug still cannot end the session."""
    conversation: list[dict[str, object]] = []
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        prompt = line.strip()
        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit"}:
            return
        before = len(conversation)
        try:
            result = agent.run_prompt(prompt=prompt, conversation=conversation)
        except Exception as exc:  # noqa: BLE001
            del conversation[before:]
            logger.error("Turn failed: {}", exc)
            continue
        logger.info(result.message)


def _read_prompt_file(path: Path) -> str:
    """UTF-8, with or without a BOM; failing that, the system's own
    encoding — a file saved as "ANSI" on this machine is still a file
    someone meant to hand the agent."""
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding=locale.getpreferredencoding(False))


def _resolve_prompt(parser: argparse.ArgumentParser, args: argparse.Namespace) -> str:
    """`run`'s prompt text: the positional argument, or `--prompt-file`'s
    content — exactly one of the two, read as-is (Markdown or plain text,
    the file does not say which)."""
    prompt_file: Path | None = args.prompt_file
    prompt: str | None = args.prompt
    if prompt_file is not None:
        if prompt is not None:
            parser.error("argument prompt: not allowed with argument --prompt-file")
        try:
            return _read_prompt_file(prompt_file)
        except OSError as exc:
            parser.error(f"argument --prompt-file: could not read {prompt_file}: {exc}")
        except UnicodeDecodeError as exc:
            parser.error(
                f"argument --prompt-file: {prompt_file} is not valid UTF-8 or {locale.getpreferredencoding(False)} "
                f"text ({exc}); save the file as UTF-8"
            )
    if prompt is None:
        parser.error("one of the arguments prompt --prompt-file is required")
    return prompt


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logger.remove()
    if args.command == "acp":
        # stdout is the protocol's channel and carries nothing else; the
        # protocol is UTF-8 whatever the console's code page.
        logger.add(sys.stderr, format="{message}")
        cast(TextIOWrapper, sys.stdin).reconfigure(encoding="utf-8")
        cast(TextIOWrapper, sys.stdout).reconfigure(encoding="utf-8")
        server = ACPServer(agent_factory=lambda cwd: _build_agent(args, workspace=cwd))
        try:
            server.serve(sys.stdin)
        finally:
            # A session's background process does not outlive this one.
            for session in server.sessions.values():
                session.agent.close()
        return 0

    logger.add(sys.stdout, format="{message}")
    agent = _build_agent(args)

    try:
        if args.command == "run":
            result = agent.run_prompt(prompt=_resolve_prompt(parser, args))
            logger.info(result.message)
            return 0

        if args.command == "chat":
            _run_chat(agent)
            return 0
    finally:
        agent.close()

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
