from pathlib import Path
from typing import Any, Optional

from legion.tools.base import BaseTool, ToolResult
from legion.tools.registry import get_registry


class HydraTool(BaseTool):
    """
    Minimal Wrapper für THC-Hydra.

    Hinweis: Diese Klasse liefert ein Gerüst für Ausführung und spätere
    Ergebnisverarbeitung. Vollständiges Parsing folgt in weiteren Schritten.
    """

    def __init__(self, tool_path: Optional[Path] = None):
        if tool_path is None:
            # Versuche über Registry zu finden
            tool_path = get_registry().get_tool("hydra")
        super().__init__(tool_path=tool_path)

    @property
    def tool_name(self) -> str:
        return "hydra"

    async def parse_output(self, result: ToolResult) -> Any:
        """
        Hydra gibt standardmäßig Text auf stdout aus. Für das erste Inkrement
        geben wir die Rohzeilen zurück. Später kann hier strukturiertes Parsing
        (Erkennen von gefundenen Credentials etc.) ergänzt werden.
        """
        return {
            "lines": [line for line in result.stdout.splitlines()],
            "errors": [line for line in result.stderr.splitlines() if line],
        }
