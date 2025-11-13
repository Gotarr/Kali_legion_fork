"""
Nmap wrapper for cross-platform network scanning.

This module provides a Python wrapper around the nmap command-line tool,
handling platform-specific differences and providing structured output parsing.
"""

from pathlib import Path
from typing import Any, Optional

try:
    from legion.tools.base import BaseTool, ToolResult
    from legion.tools.nmap.parser import NmapXMLParser, NmapScanResult
    from legion.tools.registry import get_registry
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from legion.tools.base import BaseTool, ToolResult
    from legion.tools.nmap.parser import NmapXMLParser, NmapScanResult
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
        script: Optional[str] = None,
        script_args: Optional[dict[str, str]] = None,
    ) -> ToolResult:
        """
        Perform an nmap scan.
        
        Args:
            target: Target IP, hostname, or CIDR range.
            args: Optional additional nmap arguments.
            output_file: Optional path to save XML output.
            timeout: Optional timeout in seconds.
            script: NSE script name (e.g., 'vulners', 'shodan-api').
            script_args: Script arguments as key-value pairs.
        
        Returns:
            ToolResult with scan output and optional XML path.
        
        Example:
            >>> # Basic scan
            >>> result = await nmap.scan("192.168.1.0/24", ["-sV", "-T4"])
            >>> 
            >>> # With NSE script
            >>> result = await nmap.scan(
            ...     "192.168.1.1",
            ...     ["-sV"],
            ...     script="vulners",
            ...     script_args={"mincvss": "5.0"}
            ... )
        """
        scan_args = args or []
        
        # Add NSE script if specified
        if script:
            scan_args.extend(["--script", script])
            
            # Add script arguments
            if script_args:
                script_arg_str = ",".join(
                    f"{key}={value}" for key, value in script_args.items()
                )
                scan_args.extend(["--script-args", script_arg_str])
        
        # Add XML output if requested
        if output_file:
            scan_args.extend(["-oX", str(output_file)])
        
        # Add target
        scan_args.append(target)
        
        # Execute scan
        result = await self.run(scan_args, timeout=timeout)
        
        # Store XML file path in result
        if output_file and output_file.exists():
            result.raw_output_path = output_file
        
        return result
    
    async def scan_with_vulners(
        self,
        target: str,
        min_cvss: float = 0.0,
        output_file: Optional[Path] = None,
        timeout: Optional[float] = None,
    ) -> ToolResult:
        """
        Scan with Vulners NSE script for CVE detection.
        
        Args:
            target: Target IP, hostname, or CIDR range.
            min_cvss: Minimum CVSS score to report (default: 0.0).
            output_file: Optional path to save XML output.
            timeout: Optional timeout in seconds.
        
        Returns:
            ToolResult with CVE/vulnerability information.
        
        Example:
            >>> # Find vulnerabilities with CVSS >= 7.0
            >>> result = await nmap.scan_with_vulners("192.168.1.1", min_cvss=7.0)
        """
        return await self.scan(
            target=target,
            args=["-sV"],
            output_file=output_file,
            timeout=timeout,
            script="vulners",
            script_args={"mincvss": str(min_cvss)} if min_cvss > 0 else None,
        )
    
    async def scan_with_shodan(
        self,
        target: str,
        api_key: str,
        output_file: Optional[Path] = None,
        timeout: Optional[float] = None,
    ) -> ToolResult:
        """
        Scan with Shodan NSE script for additional host information.
        
        Args:
            target: Target IP, hostname, or CIDR range.
            api_key: Shodan API key.
            output_file: Optional path to save XML output.
            timeout: Optional timeout in seconds.
        
        Returns:
            ToolResult with Shodan enrichment data.
        
        Example:
            >>> result = await nmap.scan_with_shodan(
            ...     "192.168.1.1",
            ...     api_key="YOUR_SHODAN_KEY"
            ... )
        """
        return await self.scan(
            target=target,
            args=["-sn"],  # Host discovery only
            output_file=output_file,
            timeout=timeout,
            script="shodan-api",
            script_args={"shodan-api.apikey": api_key},
        )
    
    def get_nse_script_path(self) -> Optional[Path]:
        """
        Get path to Legion's NSE scripts directory.
        
        Returns:
            Path to scripts/nmap/ if it exists, None otherwise.
        """
        # Assume scripts are relative to repository root
        repo_root = Path(__file__).parent.parent.parent.parent.parent
        nse_dir = repo_root / "scripts" / "nmap"
        
        if nse_dir.exists():
            return nse_dir
        
        return None
    
    def get_nmap_script_path(self) -> Optional[Path]:
        """
        Get path to nmap's built-in NSE scripts directory.
        
        Returns:
            Path to nmap's scripts/ directory if found, None otherwise.
        """
        if not self.tool_path:
            return None
        
        # Nmap scripts are typically in same directory as nmap executable
        nmap_dir = self.tool_path.parent
        scripts_dir = nmap_dir / "scripts"
        
        if scripts_dir.exists():
            return scripts_dir
        
        return None
    
    async def list_nse_scripts(self) -> list[str]:
        """
        List available NSE scripts in Legion's scripts/nmap/ directory.
        
        Returns:
            List of script names (without .nse extension).
        """
        scripts = []
        nse_path = self.get_nse_script_path()
        
        if nse_path and nse_path.exists():
            for script_file in nse_path.glob("*.nse"):
                scripts.append(script_file.stem)
        
        return scripts
    
    async def scan_with_custom_scripts(
        self,
        target: str,
        use_legion_scripts: bool = True,
        output_file: Optional[Path] = None,
        timeout: Optional[float] = None,
    ) -> ToolResult:
        """
        Scan using Legion's custom NSE scripts from scripts/nmap/.
        
        Args:
            target: Target IP, hostname, or CIDR range.
            use_legion_scripts: If True, prepend Legion's script path to nmap's search.
            output_file: Optional path to save XML output.
            timeout: Optional timeout in seconds.
        
        Returns:
            ToolResult with scan output using custom scripts.
        
        Example:
            >>> # Use Legion's NSE scripts
            >>> result = await nmap.scan_with_custom_scripts("192.168.1.1")
        """
        args = ["-sV"]
        
        if use_legion_scripts:
            legion_scripts = self.get_nse_script_path()
            if legion_scripts:
                # Add Legion's scripts to nmap's search path
                args.extend(["--script-path", str(legion_scripts)])
        
        return await self.scan(
            target=target,
            args=args,
            output_file=output_file,
            timeout=timeout,
        )
    
    async def parse_output(self, result: ToolResult) -> NmapScanResult:
        """
        Parse nmap XML output.
        
        Args:
            result: ToolResult from nmap execution.
        
        Returns:
            NmapScanResult with parsed scan data.
        
        Raises:
            ValueError: If XML output file not found or invalid.
        """
        # Check if we have XML output file
        if not result.raw_output_path:
            raise ValueError("No XML output file available. Use output_file parameter in scan().")
        
        # Parse the XML file
        parser = NmapXMLParser()
        return parser.parse_file(result.raw_output_path)
    
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
