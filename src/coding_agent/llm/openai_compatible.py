from __future__ import annotations

import json
import re
from typing import Any

import httpx

from coding_agent.types import AgentUsage, AssistantTurn, ToolCall


class OpenAICompatibleProvider:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None,
        timeout_seconds: int = 120,
        trust_env: bool = True,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        # False keeps a model on the local network out of a corporate proxy.
        self._trust_env = trust_env

    def _chat_completions_url(self) -> str:
        if self._base_url.endswith("/v1"):
            return f"{self._base_url}/chat/completions"
        return f"{self._base_url}/v1/chat/completions"

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        request_options: dict[str, Any] | None = None,
    ) -> AssistantTurn:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }
        if request_options:
            payload.update(request_options)

        with httpx.Client(timeout=self._timeout_seconds, trust_env=self._trust_env) as client:
            response = client.post(self._chat_completions_url(), headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]["message"]
        content = _normalize_content(choice.get("content", ""))

        tool_calls: list[ToolCall] = []
        # `or []`, not a default: servers such as SGLang send
        # `"tool_calls": null` on a turn that calls no tool.
        for raw_call in choice.get("tool_calls") or []:
            function_obj = raw_call.get("function") or {}
            raw_arguments = function_obj.get("arguments") or "{}"
            try:
                parsed_arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
            except json.JSONDecodeError:
                parsed_arguments = {}

            tool_calls.append(
                ToolCall(
                    call_id=raw_call.get("id", "unknown"),
                    name=function_obj.get("name", ""),
                    arguments=parsed_arguments if isinstance(parsed_arguments, dict) else {},
                )
            )

        if not tool_calls:
            tool_calls, content = tool_calls_in_text(content, _parameter_types(tools))

        usage_obj = data.get("usage") or {}
        usage = AgentUsage(
            prompt_tokens=usage_obj.get("prompt_tokens"),
            completion_tokens=usage_obj.get("completion_tokens"),
            total_tokens=usage_obj.get("total_tokens"),
            context_used_tokens=usage_obj.get("context_used_tokens"),
            context_window_tokens=usage_obj.get("context_window_tokens"),
        )
        usage.apply_defaults()

        return AssistantTurn(content=content, tool_calls=tool_calls, usage=usage)


_TOOL_CALL_BLOCK = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
_XML_FUNCTION = re.compile(r"<function=([^>\s]+)>(.*?)</function>", re.DOTALL)
_XML_PARAMETER = re.compile(r"<parameter=([^>\s]+)>(.*?)</parameter>", re.DOTALL)


ParameterTypes = dict[str, dict[str, str]]


def _parameter_types(tools: list[dict[str, Any]]) -> ParameterTypes:
    """Each offered tool's name, with the JSON type of each parameter."""
    types: ParameterTypes = {}
    for tool in tools:
        function = tool.get("function") or {}
        properties = (function.get("parameters") or {}).get("properties") or {}
        types[str(function.get("name", ""))] = {
            str(name): str(spec.get("type", "string")) for name, spec in properties.items() if isinstance(spec, dict)
        }
    return types


def tool_calls_in_text(content: str, known: ParameterTypes) -> tuple[list[ToolCall], str]:
    """Tool calls a model wrote into its text, for a server whose tool-call
    parser does not match the model's format and passes them through as
    text: Qwen3-Coder's `<function=name><parameter=p>value</parameter>`, or
    Hermes' `{"name": ..., "arguments": ...}`, each inside `<tool_call>`.
    Measured on 2026-10-01 against SGLang with `--tool-call-parser hermes`
    serving Qwen3.6, which writes the first.

    Only a call to a tool the request offered is taken; anything else stays
    text. Returns the calls and the text without them."""
    calls: list[ToolCall] = []
    taken: list[tuple[int, int]] = []
    for block in _TOOL_CALL_BLOCK.finditer(content):
        call = _parse_call(block.group(1), known, len(calls) + 1)
        if call is not None:
            calls.append(call)
            taken.append(block.span())
    if not calls:
        return [], content
    remaining = content
    for start, end in reversed(taken):
        remaining = remaining[:start] + remaining[end:]
    return calls, remaining.strip()


def _parse_call(body: str, known: ParameterTypes, index: int) -> ToolCall | None:
    function = _XML_FUNCTION.search(body)
    if function is not None:
        name = function.group(1)
        types = known.get(name, {})
        arguments: dict[str, Any] = {}
        for parameter in _XML_PARAMETER.finditer(function.group(2)):
            key = parameter.group(1)
            arguments[key] = _parameter_value(parameter.group(2), types.get(key, "string"))
    else:
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict) or not isinstance(parsed.get("name"), str):
            return None
        name = parsed["name"]
        raw_arguments = parsed.get("arguments") or {}
        if isinstance(raw_arguments, str):
            try:
                raw_arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                return None
        arguments = raw_arguments if isinstance(raw_arguments, dict) else {}
    if name not in known:
        return None
    return ToolCall(call_id=f"text-call-{index}", name=name, arguments=arguments)


def _parameter_value(raw: str, json_type: str) -> Any:
    """A parameter's text, without the newline the format puts around it.
    Read as JSON only where the tool declares an array or an object: a
    file's content that looks like JSON is still the text to write. Numbers
    and booleans stay text, which the tool's own validation reads."""
    value = raw[1:] if raw.startswith("\n") else raw
    value = value[:-1] if value.endswith("\n") else value
    if json_type in ("array", "object"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        return "\n".join(chunks)
    return ""
