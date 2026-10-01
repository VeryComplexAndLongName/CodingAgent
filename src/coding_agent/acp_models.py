"""Payloads of the Agent Client Protocol (https://agentclientprotocol.com),
protocol version 1, as far as this agent reads and writes them.

Incoming params allow fields this agent does not use: the protocol lets a
client send `_meta` and later additions, and refusing them would refuse a
conforming client. Outgoing payloads are built as plain dicts in
`acp_server.py`, in the shapes the protocol's schema names.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from coding_agent.config import AgentLimitsOverride

PROTOCOL_VERSION = 1


class InitializeParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    protocolVersion: int = Field(ge=0, le=65535)


class SessionNewParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    cwd: str
    mcpServers: list[dict[str, Any]] = Field(default_factory=list)
    # Not part of the protocol: this agent's own extension, also accepted
    # under `_meta.codingAgent.limits`.
    limits: AgentLimitsOverride | None = None
    meta: dict[str, Any] | None = Field(default=None, alias="_meta")


class SessionPromptParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    sessionId: str
    prompt: list[dict[str, Any]]
    limits: AgentLimitsOverride | None = None
    meta: dict[str, Any] | None = Field(default=None, alias="_meta")


class SessionCancelParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    sessionId: str


def limits_from(
    limits: AgentLimitsOverride | None, meta: dict[str, Any] | None
) -> AgentLimitsOverride | None:
    """The limits a request asked for: its `limits` field, else
    `_meta.codingAgent.limits`, else none."""
    if limits is not None:
        return limits
    extension = (meta or {}).get("codingAgent")
    if isinstance(extension, dict) and isinstance(extension.get("limits"), dict):
        return AgentLimitsOverride.model_validate(extension["limits"])
    return None


def prompt_text(blocks: list[dict[str, Any]]) -> str:
    """The text of a prompt's content blocks, in order. Text blocks are
    taken as they are; an embedded text resource contributes its text, and
    a resource link its name and URI. Other blocks (images, audio) are not
    readable by a text model and are left out."""
    parts: list[str] = []
    for block in blocks:
        kind = block.get("type")
        if kind == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
        elif kind == "resource":
            resource = block.get("resource")
            if isinstance(resource, dict) and isinstance(resource.get("text"), str):
                parts.append(resource["text"])
        elif kind == "resource_link":
            name = block.get("name") or block.get("uri") or ""
            parts.append(f"[{name}]({block.get('uri', '')})")
    return "\n\n".join(part for part in parts if part)
