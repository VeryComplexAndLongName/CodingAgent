from __future__ import annotations

import json
import time
from typing import Callable

from loguru import logger

from coding_agent.config import AgentConfig, AgentLimits, AgentLimitsOverride
from coding_agent.llm.openai_compatible import OpenAICompatibleProvider
from coding_agent.tools.builtin import ToolError
from coding_agent.tools.registry import ToolRegistry
from coding_agent.types import AgentResult, AgentUsage


ProgressCallback = Callable[[dict[str, object]], None]


SYSTEM_PROMPT = (
    "You are a coding agent. Solve tasks by using tools when needed. "
    "Write and edit code directly in files, run commands when useful, and provide concise final summaries. "
    "You can work across many languages including Python, TypeScript, JavaScript, HTML, and CSS."
)


class CodingAgent:
    def __init__(self, config: AgentConfig, provider: OpenAICompatibleProvider, tools: ToolRegistry) -> None:
        self.config = config
        self.provider = provider
        self.tools = tools

    def close(self) -> None:
        """Stops every background process a turn started, so none outlives
        this agent's own process."""
        self.tools.close()

    def run_prompt(
        self,
        prompt: str,
        progress_callback: ProgressCallback | None = None,
        system_prompt: str = SYSTEM_PROMPT,
        limits_override: AgentLimitsOverride | None = None,
        conversation: list[dict[str, object]] | None = None,
    ) -> AgentResult:
        started_at = time.monotonic()
        tool_calls_used = 0
        last_usage = AgentUsage()
        limits = self.config.limits.merged_with(limits_override)

        aggregated_prompt_tokens = 0
        aggregated_completion_tokens = 0
        aggregated_total_tokens = 0

        # `None` (every caller before `chat`): a fresh conversation, as
        # always. Given a list, only an empty one gets the system message
        # — a second call on the same list continues the first's turns.
        messages: list[dict[str, object]] = [] if conversation is None else conversation
        if not messages:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})


        for iteration in range(1, limits.max_iterations + 1):
            if self._timed_out(started_at, limits.max_seconds):
                return AgentResult(
                    message="Stopped by max_seconds limit.",
                    stopped_reason="max_seconds",
                    usage=last_usage,
                )

            if progress_callback:
                progress_callback({"type": "iteration", "value": iteration})

            request_options = self._build_request_options(limits)
            turn = self.provider.complete(messages=messages, tools=self.tools.schema(), request_options=request_options)
            turn.usage.apply_defaults()
            last_usage = turn.usage

            aggregated_prompt_tokens += turn.usage.prompt_tokens or 0
            aggregated_completion_tokens += turn.usage.completion_tokens or 0
            aggregated_total_tokens += turn.usage.total_tokens or 0

            assistant_message: dict[str, object] = {
                "role": "assistant",
                "content": turn.content,
            }

            if turn.tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tool_call.call_id,
                        "type": "function",
                        "function": {
                            "name": tool_call.name,
                            "arguments": json.dumps(tool_call.arguments),
                        },
                    }
                    for tool_call in turn.tool_calls
                ]

            messages.append(assistant_message)

            if progress_callback:
                progress_callback(
                    {
                        "type": "usage",
                        "prompt_tokens": turn.usage.prompt_tokens,
                        "completion_tokens": turn.usage.completion_tokens,
                        "total_tokens": turn.usage.total_tokens,
                    }
                )
                if turn.content.strip():
                    progress_callback({"type": "assistant_message", "text": turn.content})

            stop_reason = self._check_usage_limits(
                limits=limits,
                usage=turn.usage,
                aggregated_prompt_tokens=aggregated_prompt_tokens,
                aggregated_completion_tokens=aggregated_completion_tokens,
                aggregated_total_tokens=aggregated_total_tokens,
            )
            if stop_reason is not None:
                return AgentResult(
                    message=f"Stopped by {stop_reason} limit.",
                    stopped_reason=stop_reason,
                    usage=last_usage,
                )

            if not turn.tool_calls:
                content = turn.content.strip() or "Completed with empty assistant message."
                return AgentResult(message=content, stopped_reason="completed", usage=last_usage)

            for tool_call in turn.tool_calls:
                tool_calls_used += 1
                if tool_calls_used > limits.max_tool_calls:
                    return AgentResult(
                        message="Stopped by max_tool_calls limit.",
                        stopped_reason="max_tool_calls",
                        usage=last_usage,
                    )

                if progress_callback:
                    progress_callback(
                        {
                            "type": "tool_call",
                            "name": tool_call.name,
                            "call_id": tool_call.call_id,
                            "arguments": tool_call.arguments,
                        }
                    )

                failed = False
                try:
                    tool_output = self.tools.call(tool_call.name, tool_call.arguments)
                except ToolError as exc:
                    # The tool itself refused — a bad path, a missing
                    # argument: expected, and the model's to fix, not a
                    # traceback someone reading the log mistakes for a bug.
                    logger.warning("Tool call refused: {}", exc)
                    tool_output = f"Tool error: {exc}"
                    failed = True
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Tool call failed")
                    tool_output = f"Tool error: {exc}"
                    failed = True

                if progress_callback:
                    progress_callback(
                        {
                            "type": "tool_result",
                            "name": tool_call.name,
                            "call_id": tool_call.call_id,
                            "output": tool_output,
                            "failed": failed,
                        }
                    )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.call_id,
                        "content": tool_output,
                    }
                )

        return AgentResult(
            message="Stopped by max_iterations limit.",
            stopped_reason="max_iterations",
            usage=last_usage,
        )

    def _timed_out(self, started_at: float, max_seconds: int) -> bool:
        elapsed = time.monotonic() - started_at
        return elapsed > max_seconds

    def _build_request_options(self, limits: AgentLimits) -> dict[str, object]:
        options: dict[str, object] = {}
        if limits.max_completion_tokens is not None:
            options["max_tokens"] = limits.max_completion_tokens
        return options

    def _check_usage_limits(
        self,
        limits: AgentLimits,
        usage: AgentUsage,
        aggregated_prompt_tokens: int,
        aggregated_completion_tokens: int,
        aggregated_total_tokens: int,
    ) -> str | None:
        if limits.max_prompt_tokens is not None and aggregated_prompt_tokens > limits.max_prompt_tokens:
            return "max_prompt_tokens"
        if limits.max_completion_tokens is not None and aggregated_completion_tokens > limits.max_completion_tokens:
            return "max_completion_tokens"
        if limits.max_total_tokens is not None and aggregated_total_tokens > limits.max_total_tokens:
            return "max_total_tokens"

        if limits.max_context_used_tokens is not None and usage.context_used_tokens is not None:
            if usage.context_used_tokens > limits.max_context_used_tokens:
                return "max_context_used_tokens"

        if limits.max_context_window_tokens is not None and usage.context_window_tokens is not None:
            if usage.context_window_tokens > limits.max_context_window_tokens:
                return "max_context_window_tokens"

        if limits.max_context_share is not None and usage.context_share is not None:
            if usage.context_share > limits.max_context_share:
                return "max_context_share"

        if limits.min_free_context_tokens is not None and usage.free_context_tokens is not None:
            if usage.free_context_tokens < limits.min_free_context_tokens:
                return "min_free_context_tokens"

        return None
