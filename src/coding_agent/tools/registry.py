from __future__ import annotations

from typing import Any

from coding_agent.tools.builtin import BuiltinTools


class ToolRegistry:
    def __init__(self, builtin_tools: BuiltinTools) -> None:
        self._builtin_tools = builtin_tools

    def schema(self) -> list[dict[str, Any]]:
        return self._builtin_tools.schema()

    def call(self, name: str, arguments: dict[str, Any]) -> str:
        return self._builtin_tools.call(name, arguments)

    def close(self) -> None:
        self._builtin_tools.close()
