"""A conversation list shared across `run_prompt` calls builds on itself;
omitting one keeps every call's turns fresh."""

from __future__ import annotations

from pathlib import Path

from coding_agent.agent import CodingAgent
from coding_agent.config import AgentConfig, AgentLimits
from coding_agent.tools.builtin import BuiltinTools
from coding_agent.tools.registry import ToolRegistry
from coding_agent.types import AgentUsage, AssistantTurn


class RecordingProvider:
    """Answers with fixed turns and keeps every call's `messages`, so a
    test can see what the second call actually sent the model."""

    def __init__(self, turns: list[AssistantTurn]) -> None:
        self.turns = turns
        self.calls = 0
        self.seen_messages: list[list[dict[str, object]]] = []

    def complete(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]],
        request_options: dict[str, object] | None = None,
    ) -> AssistantTurn:
        self.seen_messages.append([dict(message) for message in messages])
        index = min(self.calls, len(self.turns) - 1)
        self.calls += 1
        return self.turns[index]


def _build_agent(tmp_path: Path, provider: RecordingProvider) -> CodingAgent:
    config = AgentConfig(
        base_url="http://localhost:8000/v1",
        model="test-model",
        api_key=None,
        workspace=tmp_path,
        limits=AgentLimits(max_iterations=1, max_tool_calls=2, max_seconds=120, command_timeout_seconds=2, max_command_output_chars=4000),
    )
    tools = ToolRegistry(BuiltinTools(tmp_path, command_timeout_seconds=2, max_command_output_chars=4000))
    return CodingAgent(config=config, provider=provider, tools=tools)


def test_a_shared_conversation_carries_the_first_turn_into_the_second(tmp_path: Path) -> None:
    provider = RecordingProvider(
        [
            AssistantTurn(content="Alex, got it.", tool_calls=[], usage=AgentUsage()),
            AssistantTurn(content="Your name is Alex.", tool_calls=[], usage=AgentUsage()),
        ]
    )
    agent = _build_agent(tmp_path, provider)
    conversation: list[dict[str, object]] = []

    first = agent.run_prompt("My name is Alex.", conversation=conversation)
    second = agent.run_prompt("What is my name?", conversation=conversation)

    assert first.message == "Alex, got it."
    assert second.message == "Your name is Alex."
    second_call_contents = [message["content"] for message in provider.seen_messages[1]]
    assert "My name is Alex." in second_call_contents
    assert "Alex, got it." in second_call_contents
    assert "What is my name?" in second_call_contents


def test_omitting_conversation_keeps_every_call_fresh(tmp_path: Path) -> None:
    provider = RecordingProvider(
        [
            AssistantTurn(content="first", tool_calls=[], usage=AgentUsage()),
            AssistantTurn(content="second", tool_calls=[], usage=AgentUsage()),
        ]
    )
    agent = _build_agent(tmp_path, provider)

    agent.run_prompt("one")
    agent.run_prompt("two")

    assert len(provider.seen_messages[0]) == 2
    assert len(provider.seen_messages[1]) == 2
