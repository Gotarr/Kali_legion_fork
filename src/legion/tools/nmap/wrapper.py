"""
Nmap wrapper for cross-platform network scanning.

This module provides a Python wrapper around the nmap command-line tool,
handling platform-specific differences and providing structured output parsing.
"""

from pathlib import Path
from typing import Any, Optional

try:
    from legion.tools.base import BaseTool, ToolResult
    from legion.tools.registry import get_registry
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from legion.tools.base import BaseTool, ToolResult
    from legion.tools.registry import get_registry


class NmapTool(BaseTool):
    """
    Nmap scanner wrapper.
    
    Provides platform-agnostic access to nmap scanning functionality
    with automatic tool discovery and structured output parsing.
    
    Example:
        >>> nmap = NmapTool()
        >>> if await nmap.validate():
        ...     result = await nmap.scan("192.168.1.1", ["-sV"])
        ...     print(result.stdout)
    """
    
    def __init__(self, tool_path: Optional[Path] = None):
        """
        Initialize Nmap wrapper.
        
        Args:
            tool_path: Optional explicit path to nmap executable.
                      If None, will be auto-discovered.
        """
        # Try to discover nmap if not provided
        if tool_path is None:
            registry = get_registry()
            discovered_path = registry.get_tool("nmap")
            if discovered_path:
                tool_path = discovered_path
        
        super().__init__(tool_path)
    
    @property
    def tool_name(self) -> str:
        """Get tool name."""
        return "nmap"
    
    async def scan(
        self,
        target: str,
        args: Optional[list[str]] = None,
        output_file: Optional[Path] = None,
        timeout: Optional[float] = None,
    ) -> ToolResult:
        """
        Perform an nmap scan.
        
        Args:
            target: Target IP, hostname, or CIDR range.
            args: Optional additional nmap arguments.
            output_file: Optional path to save XML output.
            timeout: Optional timeout in seconds.
        
        Returns:
            ToolResult with scan output.
        
        Example:
            >>> result = await nmap.scan("192.168.1.0/24", ["-sV", "-T4"])
        """
        scan_args = args or []
        
        # Add XML output if requested
        if output_file:
            scan_args.extend(["-oX", str(output_file)])
        
        # Add target
        scan_args.append(target)
        
        # Execute scan
        return await self.run(scan_args, timeout=timeout)
    
    async def parse_output(self, result: ToolResult) -> Any:
        """
        Parse nmap XML output.
        
        Args:
            result: ToolResult from nmap execution.
        
        Returns:
            Parsed scan data (placeholder for now).
        
        Note:
            Full XML parsing will be implemented in Phase 3.
            For now, this is a placeholder.
        """
        # TODO: Implement XML parsing in Phase 3
        # Will parse nmap XML output into structured Host/Port objects
        return {
            "raw_output": result.stdout,
            "parsed": False,
            "note": "XML parsing not yet implemented - coming in Phase 3",
        }
    
    def _extract_version(self, version_output: str) -> str:
        """
        Extract nmap version from --version output.
        
        Args:
            version_output: Raw version output.
        
        Returns:
            Version string.
        """
        # Nmap version output format:
        # "Nmap version 7.94 ( https://nmap.org )"
        if "Nmap version" in version_output:
            parts = version_output.split()
            for i, part in enumerate(parts):
                if part == "version" and i + 1 < len(parts):
                    return parts[i + 1]
        
        return version_output.strip().split('\n')[0]


if __name__ == "__main__":
    # Demo / Testing
    import asyncio
    
    async def main():
        print("Nmap Tool Wrapper")
        print("=" * 60)
        
        nmap = NmapTool()
        print(f"Tool: {nmap}")
        print(f"Path: {nmap.tool_path}")
        print()
        
        # Validate
        print("Validating nmap installation...")
        is_valid = await nmap.validate()
        
        if is_valid:
            print("✓ Nmap is available and working")
            
            # Get version
            version = await nmap.get_version()
            print(f"Version: {version}")
            
            # Get tool info
            info = await nmap.get_info()
            print(f"Info: {info}")
        else:
            print("✗ Nmap not found or not working")
            print("\nTo install nmap:")
            print("  Windows: Download from https://nmap.org/download.html")
            print("  Linux:   sudo apt install nmap")
            print("  macOS:   brew install nmap")
    
    asyncio.run(main())
