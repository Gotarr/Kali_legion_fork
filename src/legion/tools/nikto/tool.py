from pathlib import Path
from typing import Any, Optional

from legion.tools.base import BaseTool, ToolResult
from legion.tools.registry import get_registry


class NiktoTool(BaseTool):
    """
    Minimal Wrapper für Nikto Webserver-Scanner.

    Hinweis: Dieses Grundgerüst führt nikto aus und gibt die Roh-Ausgaben zurück.
    Später können wir CSV/JSON-Ausgaben (falls aktiviert) strukturieren.
    """

    def __init__(self, tool_path: Optional[Path] = None):
        if tool_path is None:
            tool_path = get_registry().get_tool("nikto")
        super().__init__(tool_path=tool_path)

    @property
    def tool_name(self) -> str:
        return "nikto"

    async def parse_output(self, result: ToolResult) -> Any:
        return {
            "lines": [line for line in result.stdout.splitlines()],
            "errors": [line for line in result.stderr.splitlines() if line],
        }
