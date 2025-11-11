"""
Tools package for external tool wrappers.

This package provides:
- Base classes for tool wrappers (base.py)
- Automatic tool discovery (discovery.py)
- Tool registry with caching (registry.py)
- Specific tool wrappers (nmap/, hydra/, etc.)
"""

from legion.tools.base import (
    BaseTool,
    ToolExecutionError,
    ToolInfo,
    ToolNotFoundError,
    ToolResult,
)
from legion.tools.discovery import (
    discover_all_tools,
    find_in_common_locations,
    find_in_path,
    find_tool,
    get_common_tool_locations,
)
from legion.tools.registry import (
    ToolRegistry,
    ToolRegistryEntry,
    get_registry,
)

__all__ = [
    # Base classes
    "BaseTool",
    "ToolInfo",
    "ToolResult",
    "ToolNotFoundError",
    "ToolExecutionError",
    # Discovery
    "find_tool",
    "find_in_path",
    "find_in_common_locations",
    "get_common_tool_locations",
    "discover_all_tools",
    # Registry
    "ToolRegistry",
    "ToolRegistryEntry",
    "get_registry",
]

