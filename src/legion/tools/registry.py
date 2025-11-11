"""
Tool registry for caching and managing discovered tools.

This module provides a central registry for all discovered external tools,
with caching to avoid repeated filesystem searches.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

try:
    from legion.platform.paths import get_cache_dir
    from legion.tools.base import ToolInfo
    from legion.tools.discovery import discover_all_tools, find_tool
except ImportError:
    # Standalone testing
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from legion.platform.paths import get_cache_dir
    from legion.tools.base import ToolInfo
    from legion.tools.discovery import discover_all_tools, find_tool


@dataclass
class ToolRegistryEntry:
    """Entry in the tool registry."""
    
    name: str
    """Tool name."""
    
    path: Optional[Path]
    """Path to executable (None if not found)."""
    
    available: bool
    """Whether the tool is currently available."""
    
    last_checked: float
    """Timestamp of last availability check."""
    
    version: str = "unknown"
    """Tool version string."""
    
    custom_path: bool = False
    """Whether this is a user-configured custom path."""


class ToolRegistry:
    """
    Central registry for managing external tool discovery and caching.
    
    The registry maintains a cache of discovered tools to avoid repeated
    filesystem searches. The cache is persisted to disk.
    
    Example:
        >>> registry = ToolRegistry()
        >>> nmap_path = registry.get_tool("nmap")
        >>> if nmap_path:
        ...     print(f"nmap found at: {nmap_path}")
        >>> 
        >>> # Discover all tools at once
        >>> registry.discover_all()
        >>> for tool in registry.get_all_tools():
        ...     print(f"{tool.name}: {tool.path}")
    """
    
    def __init__(self, cache_file: Optional[Path] = None):
        """
        Initialize the tool registry.
        
        Args:
            cache_file: Optional path to cache file. If None, uses default location.
        """
        if cache_file:
            self._cache_file = cache_file
        else:
            cache_dir = get_cache_dir()
            self._cache_file = cache_dir / "tool_registry.json"
        
        self._tools: dict[str, ToolRegistryEntry] = {}
        self._custom_paths: dict[str, list[Path]] = {}
        
        # Load cache
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cached tool information from disk."""
        if not self._cache_file.exists():
            return
        
        try:
            with open(self._cache_file, 'r') as f:
                data = json.load(f)
            
            # Restore tools
            for tool_data in data.get("tools", []):
                entry = ToolRegistryEntry(
                    name=tool_data["name"],
                    path=Path(tool_data["path"]) if tool_data.get("path") else None,
                    available=tool_data.get("available", False),
                    last_checked=tool_data.get("last_checked", 0.0),
                    version=tool_data.get("version", "unknown"),
                    custom_path=tool_data.get("custom_path", False),
                )
                self._tools[entry.name] = entry
            
            # Restore custom paths
            for tool_name, paths in data.get("custom_paths", {}).items():
                self._custom_paths[tool_name] = [Path(p) for p in paths]
        
        except Exception:
            # Cache corrupted or invalid - ignore and start fresh
            pass
    
    def _save_cache(self) -> None:
        """Save tool information to cache file."""
        try:
            # Prepare data for serialization
            data = {
                "tools": [
                    {
                        "name": entry.name,
                        "path": str(entry.path) if entry.path else None,
                        "available": entry.available,
                        "last_checked": entry.last_checked,
                        "version": entry.version,
                        "custom_path": entry.custom_path,
                    }
                    for entry in self._tools.values()
                ],
                "custom_paths": {
                    tool_name: [str(p) for p in paths]
                    for tool_name, paths in self._custom_paths.items()
                },
            }
            
            # Ensure cache directory exists
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write cache
            with open(self._cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception:
            # Failed to save cache - not critical
            pass
    
    def add_custom_path(self, tool_name: str, path: Path) -> None:
        """
        Add a custom search path for a specific tool.
        
        Args:
            tool_name: Name of the tool.
            path: Directory to search for the tool.
        """
        if tool_name not in self._custom_paths:
            self._custom_paths[tool_name] = []
        
        if path not in self._custom_paths[tool_name]:
            self._custom_paths[tool_name].append(path)
        
        # Invalidate cached tool entry
        if tool_name in self._tools:
            del self._tools[tool_name]
        
        self._save_cache()
    
    def set_tool_path(self, tool_name: str, path: Path) -> None:
        """
        Explicitly set the path for a tool.
        
        Args:
            tool_name: Name of the tool.
            path: Full path to the tool executable.
        """
        import time
        
        entry = ToolRegistryEntry(
            name=tool_name,
            path=path if path.exists() else None,
            available=path.exists(),
            last_checked=time.time(),
            version="unknown",
            custom_path=True,
        )
        
        self._tools[tool_name] = entry
        self._save_cache()
    
    def get_tool(self, tool_name: str, use_cache: bool = True) -> Optional[Path]:
        """
        Get the path to a tool executable.
        
        Args:
            tool_name: Name of the tool to find.
            use_cache: Whether to use cached results. If False, performs fresh search.
        
        Returns:
            Path to executable, or None if not found.
        """
        # Check cache first
        if use_cache and tool_name in self._tools:
            entry = self._tools[tool_name]
            if entry.available and entry.path and entry.path.exists():
                return entry.path
        
        # Not in cache or cache invalid - discover
        custom_paths = self._custom_paths.get(tool_name)
        path = find_tool(tool_name, custom_paths)
        
        # Update cache
        import time
        entry = ToolRegistryEntry(
            name=tool_name,
            path=path,
            available=path is not None,
            last_checked=time.time(),
            version="unknown",
            custom_path=False,
        )
        self._tools[tool_name] = entry
        self._save_cache()
        
        return path
    
    def discover_all(
        self,
        tool_names: Optional[list[str]] = None,
        force_refresh: bool = False,
    ) -> dict[str, Optional[Path]]:
        """
        Discover all tools and update cache.
        
        Args:
            tool_names: Optional list of tools to discover. If None, uses default list.
            force_refresh: If True, ignore cache and re-discover all tools.
        
        Returns:
            Dictionary mapping tool names to paths.
        """
        # Discover tools
        results = discover_all_tools(tool_names, self._custom_paths)
        
        # Update cache
        import time
        for tool_name, path in results.items():
            entry = ToolRegistryEntry(
                name=tool_name,
                path=path,
                available=path is not None,
                last_checked=time.time(),
                version="unknown",
                custom_path=False,
            )
            self._tools[tool_name] = entry
        
        self._save_cache()
        
        return results
    
    def get_all_tools(self) -> list[ToolRegistryEntry]:
        """
        Get all tools in the registry.
        
        Returns:
            List of all ToolRegistryEntry objects.
        """
        return list(self._tools.values())
    
    def get_available_tools(self) -> list[ToolRegistryEntry]:
        """
        Get only available (found) tools.
        
        Returns:
            List of available ToolRegistryEntry objects.
        """
        return [entry for entry in self._tools.values() if entry.available]
    
    def is_available(self, tool_name: str) -> bool:
        """
        Check if a tool is available.
        
        Args:
            tool_name: Name of the tool.
        
        Returns:
            True if tool is available, False otherwise.
        """
        return self.get_tool(tool_name) is not None
    
    def clear_cache(self) -> None:
        """Clear the tool registry cache."""
        self._tools.clear()
        self._save_cache()
    
    def invalidate_tool(self, tool_name: str) -> None:
        """
        Invalidate cache entry for a specific tool.
        
        Args:
            tool_name: Name of the tool to invalidate.
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            self._save_cache()
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolRegistryEntry]:
        """
        Get detailed information about a tool.
        
        Args:
            tool_name: Name of the tool.
        
        Returns:
            ToolRegistryEntry if found, None otherwise.
        """
        # Ensure tool is in cache
        self.get_tool(tool_name)
        
        return self._tools.get(tool_name)
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"<ToolRegistry(tools={len(self._tools)}, cache={self._cache_file})>"
    
    def __str__(self) -> str:
        """User-friendly string."""
        available = len(self.get_available_tools())
        total = len(self._tools)
        return f"ToolRegistry: {available}/{total} tools available"


# Global singleton registry
_global_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.
    
    Returns:
        Global ToolRegistry singleton.
    
    Example:
        >>> registry = get_registry()
        >>> nmap = registry.get_tool("nmap")
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = ToolRegistry()
    
    return _global_registry


if __name__ == "__main__":
    # Demo / Testing
    print("Tool Registry System")
    print("=" * 60)
    
    registry = ToolRegistry()
    print(f"Registry: {registry}")
    print()
    
    # Discover all tools
    print("Discovering tools...")
    results = registry.discover_all()
    print()
    
    # Show results
    print("Discovery Results:")
    print("-" * 60)
    
    for tool_name, path in results.items():
        if path:
            print(f"✓ {tool_name:15s} → {path}")
        else:
            print(f"✗ {tool_name:15s} → NOT FOUND")
    
    print("-" * 60)
    print()
    
    # Show registry status
    print(f"Registry Status: {registry}")
    print(f"Cache file: {registry._cache_file}")
    print()
    
    # Show available tools
    available = registry.get_available_tools()
    print(f"Available tools ({len(available)}):")
    for entry in available:
        print(f"  - {entry.name}: {entry.path}")
