from __future__ import annotations

import argparse
import sys
from pathlib import Path

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

    run_parser = subparsers.add_parser("run", help="Run one prompt and print assistant output")
    _add_global_args(run_parser, suppress_defaults=True)
    run_parser.add_argument("prompt")

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
    )

    provider = OpenAICompatibleProvider(
        base_url=config.base_url,
        model=config.model,
        api_key=config.api_key,
        trust_env=not config.no_proxy,
    )
    tools = ToolRegistry(
        BuiltinTools(
            workspace=config.workspace,
            command_timeout_seconds=config.limits.command_timeout_seconds,
            max_command_output_chars=config.limits.max_command_output_chars,
        )
    )
    return CodingAgent(config=config, provider=provider, tools=tools)


def _run_chat(agent: CodingAgent) -> None:
    """One line of stdin per turn, every turn sharing one conversation,
    until `exit`/`quit`, end of input, or Ctrl-C. A turn that raises (a
    network error, a limit the provider itself rejects) ends that turn,
    not the session: the line it failed on is dropped from the shared
    conversation, and the next line is read as normal."""
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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logger.remove()
    if args.command == "acp":
        # stdout is the protocol's channel and carries nothing else; the
        # protocol is UTF-8 whatever the console's code page.
        logger.add(sys.stderr, format="{message}")
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
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
            result = agent.run_prompt(prompt=args.prompt)
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
