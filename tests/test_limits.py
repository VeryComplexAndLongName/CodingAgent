from __future__ import annotations

from pathlib import Path

from coding_agent.agent import CodingAgent
from coding_agent.config import AgentConfig, AgentLimits
from coding_agent.tools.builtin import BuiltinTools
from coding_agent.tools.registry import ToolRegistry
from coding_agent.types import AgentUsage, AssistantTurn, ToolCall


class DummyProvider:
    def __init__(self, turns: list[AssistantTurn]) -> None:
        self.turns = turns
        self.calls = 0

    def complete(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        request_options: dict[str, object] | None = None,
    ) -> AssistantTurn:
        index = min(self.calls, len(self.turns) - 1)
        self.calls += 1
        return self.turns[index]


def _build_agent(tmp_path: Path, provider: DummyProvider, max_iterations: int = 2) -> CodingAgent:
    config = AgentConfig(
        base_url="http://localhost:8000/v1",
        model="test-model",
        api_key=None,
        workspace=tmp_path,
        limits=AgentLimits(
            max_iterations=max_iterations,
            max_tool_calls=2,
            max_seconds=120,
            command_timeout_seconds=2,
            max_command_output_chars=4000,
        ),
    )
    tools = ToolRegistry(BuiltinTools(tmp_path, command_timeout_seconds=2, max_command_output_chars=4000))
    return CodingAgent(config=config, provider=provider, tools=tools)


def test_completed_without_tool_calls(tmp_path: Path) -> None:
    provider = DummyProvider(
        [
            AssistantTurn(content="done", tool_calls=[], usage=AgentUsage()),
        ]
    )
    agent = _build_agent(tmp_path, provider, max_iterations=1)

    result = agent.run_prompt("do something")

    assert result.stopped_reason == "completed"


def test_max_tool_calls_limit(tmp_path: Path) -> None:
    provider = DummyProvider(
        [
            AssistantTurn(
                content="",
                tool_calls=[
                    ToolCall(call_id="1", name="list_dir", arguments={"path": "."}),
                    ToolCall(call_id="2", name="list_dir", arguments={"path": "."}),
                    ToolCall(call_id="3", name="list_dir", arguments={"path": "."}),
                ],
                usage=AgentUsage(),
            )
        ]
    )
    agent = _build_agent(tmp_path, provider, max_iterations=2)

    result = agent.run_prompt("list")

    assert result.stopped_reason == "max_tool_calls"


def test_max_total_tokens_limit(tmp_path: Path) -> None:
    provider = DummyProvider(
        [
            AssistantTurn(
                content="",
                tool_calls=[ToolCall(call_id="1", name="list_dir", arguments={"path": "."})],
                usage=AgentUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
            )
        ]
    )
    config = AgentConfig(
        base_url="http://localhost:8000/v1",
        model="test-model",
        api_key=None,
        workspace=tmp_path,
        limits=AgentLimits(
            max_iterations=5,
            max_tool_calls=10,
            max_seconds=120,
            max_total_tokens=5,
        ),
    )
    tools = ToolRegistry(BuiltinTools(tmp_path, command_timeout_seconds=2, max_command_output_chars=4000))
    agent = CodingAgent(config=config, provider=provider, tools=tools)

    result = agent.run_prompt("limit")

    assert result.stopped_reason == "max_total_tokens"


def test_max_context_share_limit(tmp_path: Path) -> None:
    provider = DummyProvider(
        [
            AssistantTurn(
                content="",
                tool_calls=[ToolCall(call_id="1", name="list_dir", arguments={"path": "."})],
                usage=AgentUsage(
                    prompt_tokens=1,
                    completion_tokens=1,
                    total_tokens=2,
                    context_used_tokens=90,
                    context_window_tokens=100,
                ),
            )
        ]
    )
    config = AgentConfig(
        base_url="http://localhost:8000/v1",
        model="test-model",
        api_key=None,
        workspace=tmp_path,
        limits=AgentLimits(
            max_iterations=5,
            max_tool_calls=10,
            max_seconds=120,
            max_context_share=0.5,
        ),
    )
    tools = ToolRegistry(BuiltinTools(tmp_path, command_timeout_seconds=2, max_command_output_chars=4000))
    agent = CodingAgent(config=config, provider=provider, tools=tools)

    result = agent.run_prompt("limit context")

    assert result.stopped_reason == "max_context_share"
