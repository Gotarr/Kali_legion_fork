from pathlib import Path
from typing import Any, Optional

from legion.tools.base import BaseTool, ToolResult
from legion.tools.registry import get_registry


class SearchsploitTool(BaseTool):
    """
    Minimal Wrapper für searchsploit (Exploit-DB CLI).

    Standardmäßig gibt searchsploit Text aus. Optional besitzt es JSON-Output
    (-j). Für das erste Inkrement geben wir Rohdaten zurück.
    """

    def __init__(self, tool_path: Optional[Path] = None):
        if tool_path is None:
            tool_path = get_registry().get_tool("searchsploit")
        super().__init__(tool_path=tool_path)

    @property
    def tool_name(self) -> str:
        return "searchsploit"

    async def parse_output(self, result: ToolResult) -> Any:
        return {
            "lines": [line for line in result.stdout.splitlines()],
            "errors": [line for line in result.stderr.splitlines() if line],
        }
