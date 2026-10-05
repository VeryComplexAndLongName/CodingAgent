from __future__ import annotations

import os
from pathlib import Path

from os import PathLike

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_iterations: int = Field(default=20, ge=1, le=10_000)
    max_tool_calls: int = Field(default=60, ge=1, le=100_000)
    max_seconds: int = Field(default=300, ge=1, le=86_400)
    command_timeout_seconds: int = Field(default=60, ge=1, le=86_400)
    max_command_output_chars: int = Field(default=12_000, ge=256, le=5_000_000)

    max_prompt_tokens: int | None = Field(default=None, ge=1)
    max_completion_tokens: int | None = Field(default=None, ge=1)
    max_total_tokens: int | None = Field(default=None, ge=1)

    max_context_used_tokens: int | None = Field(default=None, ge=1)
    max_context_window_tokens: int | None = Field(default=None, ge=1)
    max_context_share: float | None = Field(default=None, gt=0.0, le=1.0)
    min_free_context_tokens: int | None = Field(default=None, ge=0)

    def merged_with(self, override: AgentLimitsOverride | None) -> AgentLimits:
        if override is None:
            return self
        data = self.model_dump()
        data.update(override.model_dump(exclude_none=True))
        return AgentLimits.model_validate(data)


class AgentLimitsOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_iterations: int | None = Field(default=None, ge=1, le=10_000)
    max_tool_calls: int | None = Field(default=None, ge=1, le=100_000)
    max_seconds: int | None = Field(default=None, ge=1, le=86_400)
    command_timeout_seconds: int | None = Field(default=None, ge=1, le=86_400)
    max_command_output_chars: int | None = Field(default=None, ge=256, le=5_000_000)

    max_prompt_tokens: int | None = Field(default=None, ge=1)
    max_completion_tokens: int | None = Field(default=None, ge=1)
    max_total_tokens: int | None = Field(default=None, ge=1)

    max_context_used_tokens: int | None = Field(default=None, ge=1)
    max_context_window_tokens: int | None = Field(default=None, ge=1)
    max_context_share: float | None = Field(default=None, gt=0.0, le=1.0)
    min_free_context_tokens: int | None = Field(default=None, ge=0)


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_url: str
    model: str
    api_key: str | None
    workspace: Path
    limits: AgentLimits
    no_proxy: bool = False
    request_timeout_seconds: int = 120
    searxng_url: str = "http://192.168.137.39:8888"

    @field_validator("workspace", mode="before")
    @classmethod
    def normalize_workspace(cls, value: object) -> Path:
        if isinstance(value, Path):
            return value.resolve()
        if isinstance(value, (str, PathLike)):
            return Path(value).resolve()
        raise TypeError("workspace must be a path-like value")


DEFAULT_BASE_URL = "http://localhost:8000/v1"
DEFAULT_MODEL = "default"


def from_env_defaults() -> tuple[str, str, str | None]:
    base_url = os.getenv("CODING_AGENT_BASE_URL", DEFAULT_BASE_URL)
    model = os.getenv("CODING_AGENT_MODEL", DEFAULT_MODEL)
    api_key = os.getenv("CODING_AGENT_API_KEY")
    return base_url, model, api_key


def no_proxy_from_env() -> bool:
    value = os.getenv("CODING_AGENT_NO_PROXY")
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}
