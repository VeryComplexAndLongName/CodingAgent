from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentUsage(BaseModel):
    model_config = ConfigDict(extra="allow")

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    context_used_tokens: int | None = None
    context_window_tokens: int | None = None

    def apply_defaults(self) -> AgentUsage:
        if self.total_tokens is None and self.prompt_tokens is not None and self.completion_tokens is not None:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        if self.context_used_tokens is None and self.total_tokens is not None:
            self.context_used_tokens = self.total_tokens
        return self

    @property
    def free_context_tokens(self) -> int | None:
        if self.context_used_tokens is None or self.context_window_tokens is None:
            return None
        return max(self.context_window_tokens - self.context_used_tokens, 0)

    @property
    def context_share(self) -> float | None:
        if self.context_used_tokens is None or self.context_window_tokens is None:
            return None
        if self.context_window_tokens <= 0:
            return None
        return float(self.context_used_tokens) / float(self.context_window_tokens)


class AgentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    stopped_reason: str
    usage: AgentUsage = Field(default_factory=AgentUsage)


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_id: str
    name: str
    arguments: dict[str, Any]


class AssistantTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    tool_calls: list[ToolCall]
    usage: AgentUsage
