from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

from coding_agent import __version__
from coding_agent.acp_server import ACPServer
from coding_agent.agent import CodingAgent
from coding_agent.config import AgentConfig, AgentLimits, from_env_defaults
from coding_agent.llm.openai_compatible import OpenAICompatibleProvider
from coding_agent.tools.builtin import BuiltinTools
from coding_agent.tools.registry import ToolRegistry


def build_parser() -> argparse.ArgumentParser:
    env_base_url, env_model, env_api_key = from_env_defaults()

    parser = argparse.ArgumentParser(prog="coding-agent")
    # Read by clients that detect the agent with `coding-agent --version`.
    parser.add_argument("--version", action="version", version=f"coding-agent {__version__}")
    parser.add_argument("--base-url", default=env_base_url)
    parser.add_argument("--model", default=env_model)
    parser.add_argument("--api-key", default=env_api_key)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--max-iterations", type=int, default=20)
    parser.add_argument("--max-tool-calls", type=int, default=60)
    parser.add_argument("--max-seconds", type=int, default=300)
    parser.add_argument("--command-timeout-seconds", type=int, default=60)
    parser.add_argument("--max-command-output-chars", type=int, default=12000)
    parser.add_argument("--max-prompt-tokens", type=int)
    parser.add_argument("--max-completion-tokens", type=int)
    parser.add_argument("--max-total-tokens", type=int)
    parser.add_argument("--max-context-used-tokens", type=int)
    parser.add_argument("--max-context-window-tokens", type=int)
    parser.add_argument("--max-context-share", type=float)
    parser.add_argument("--min-free-context-tokens", type=int)

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one prompt and print assistant output")
    run_parser.add_argument("prompt")

    subparsers.add_parser("acp", help="Run ACP-compatible stdio JSON-RPC server")
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
    )

    provider = OpenAICompatibleProvider(
        base_url=config.base_url,
        model=config.model,
        api_key=config.api_key,
    )
    tools = ToolRegistry(
        BuiltinTools(
            workspace=config.workspace,
            command_timeout_seconds=config.limits.command_timeout_seconds,
            max_command_output_chars=config.limits.max_command_output_chars,
        )
    )
    return CodingAgent(config=config, provider=provider, tools=tools)


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
        server.serve(sys.stdin)
        return 0

    logger.add(sys.stdout, format="{message}")
    agent = _build_agent(args)

    if args.command == "run":
        result = agent.run_prompt(prompt=args.prompt)
        logger.info(result.message)
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
