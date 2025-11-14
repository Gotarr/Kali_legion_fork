"""
THC-Hydra wrapper for brute-force authentication attacks.

This module provides a Python wrapper around the Hydra command-line tool,
handling cross-platform execution and structured credential parsing.

Author: Gotham Security
Date: 2025-11-13
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

from legion.tools.base import BaseTool, ToolResult
from legion.tools.registry import get_registry
from legion.tools.hydra.parser import HydraOutputParser, HydraResult


class HydraTool(BaseTool):
    """
    THC-Hydra brute-force authentication wrapper.
    
    Provides platform-agnostic access to Hydra functionality with
    automatic tool discovery and structured credential parsing.
    
    Supported services: SSH, FTP, HTTP(S), SMB, RDP, MySQL, PostgreSQL,
    SMTP, POP3, IMAP, Telnet, VNC, and 50+ others.
    
    Example:
        >>> hydra = HydraTool()
        >>> if await hydra.validate():
        ...     result = await hydra.attack(
        ...         target="192.168.1.1",
        ...         service="ssh",
        ...         login_list=["admin", "root"],
        ...         password_list=["password", "123456"]
        ...     )
        ...     for cred in result.parsed_data.credentials:
        ...         print(f"Found: {cred}")
    """

    def __init__(self, tool_path: Optional[Path] = None):
        """
        Initialize Hydra wrapper.
        
        Args:
            tool_path: Optional explicit path to hydra executable.
                      If None, will be auto-discovered.
        """
        if tool_path is None:
            # Try to discover hydra via registry
            registry = get_registry()
            discovered_path = registry.get_tool("hydra")
            if discovered_path:
                tool_path = discovered_path
        
        super().__init__(tool_path=tool_path)

    @property
    def tool_name(self) -> str:
        """Get tool name."""
        return "hydra"
    
    async def validate(self) -> bool:
        """
        Validate that Hydra is available and executable.
        
        Overrides BaseTool.validate() because Hydra uses -h instead of --version.
        
        Returns:
            True if Hydra is available and working.
        """
        if not self._tool_path:
            return False
        
        if not self._tool_path.exists():
            return False
        
        try:
            # Hydra uses -h, not --version
            result = await self.run(["-h"], timeout=5.0)
            # Hydra -h returns exit code 255, but outputs help
            return "Hydra" in result.stdout or result.success
        except Exception:
            return False
    
    async def get_version(self) -> str:
        """
        Get Hydra version using -h flag instead of --version.
        
        Hydra doesn't support --version, so we parse from -h output.
        The first line contains: "Hydra v9.1 (c) 2020 by van Hauser..."
        
        Returns:
            Version string (e.g., "9.1") or "unknown".
        """
        try:
            result = await self.run(["-h"], timeout=5.0)
            if "Hydra" in result.stdout:
                # Use existing _extract_version() method
                first_line = result.stdout.split('\n')[0]
                return self._extract_version(first_line)
        except Exception:
            pass
        
        return "unknown"

    async def attack(
        self,
        target: str,
        service: str,
        login: Optional[str] = None,
        password: Optional[str] = None,
        login_list: Optional[List[str]] = None,
        password_list: Optional[List[str]] = None,
        login_file: Optional[Path] = None,
        password_file: Optional[Path] = None,
        combo_file: Optional[Path] = None,
        port: Optional[int] = None,
        tasks: int = 16,
        timeout: Optional[float] = None,
        additional_args: Optional[List[str]] = None,
    ) -> ToolResult:
        """
        Perform a Hydra brute-force attack.
        
        You must provide either:
        - login/password (single credentials)
        - login_list/password_list
        - login_file/password_file
        - combo_file (colon-separated user:pass file)
        
        Args:
            target: Target IP, hostname, or CIDR range.
            service: Service to attack (ssh, ftp, http-post-form, etc.).
            login: Single username to try.
            password: Single password to try.
            login_list: List of usernames to try.
            password_list: List of passwords to try.
            login_file: Path to file with usernames (one per line).
            password_file: Path to file with passwords (one per line).
            combo_file: Path to colon-separated user:pass file.
            port: Optional port (overrides default service port).
            tasks: Number of parallel tasks (default: 16).
            timeout: Optional timeout in seconds.
            additional_args: Optional additional Hydra arguments.
        
        Returns:
            ToolResult with attack output and parsed credentials.
        
        Example:
            >>> # Attack with single credentials
            >>> result = await hydra.attack(
            ...     target="192.168.1.1",
            ...     service="ssh",
            ...     login="admin",
            ...     password="password123"
            ... )
            
            >>> # Attack SSH with username/password lists
            >>> result = await hydra.attack(
            ...     target="192.168.1.1",
            ...     service="ssh",
            ...     login_list=["admin", "root"],
            ...     password_list=["password", "123456"],
            ...     tasks=4
            ... )
            
            >>> # Attack FTP with files
            >>> result = await hydra.attack(
            ...     target="ftp.example.com",
            ...     service="ftp",
            ...     login_file=Path("users.txt"),
            ...     password_file=Path("passwords.txt")
            ... )
        """
        args = []
        
        # Add login/password sources
        if combo_file:
            args.extend(["-C", str(combo_file)])
        else:
            # Login source
            if login:
                args.extend(["-l", login])
            elif login_list:
                for login_item in login_list:
                    args.extend(["-l", login_item])
            elif login_file:
                args.extend(["-L", str(login_file)])
            else:
                raise ValueError("Must provide login, login_list, or login_file")
            
            # Password source
            if password:
                args.extend(["-p", password])
            elif password_list:
                for password_item in password_list:
                    args.extend(["-p", password_item])
            elif password_file:
                args.extend(["-P", str(password_file)])
            else:
                raise ValueError("Must provide password, password_list, or password_file")
        
        # Add parallel tasks
        args.extend(["-t", str(tasks)])
        
        # Add port if specified
        if port:
            args.extend(["-s", str(port)])
        
        # Add additional arguments
        if additional_args:
            args.extend(additional_args)
        
        # Add target and service
        # Format: hydra [options] target service
        args.append(target)
        args.append(service)
        
        # Execute attack
        result = await self.run(args, timeout=timeout)
        
        # Parse output automatically
        if result.success or result.stdout:
            try:
                parser = HydraOutputParser()
                result.parsed_data = parser.parse(result.stdout + "\n" + result.stderr)
            except Exception as e:
                # Parsing failed - attach error but don't fail
                result.stderr += f"\nParsing error: {e}"
        
        return result

    async def parse_output(self, result: ToolResult) -> HydraResult:
        """
        Parse Hydra output to extract credentials and statistics.
        
        Args:
            result: ToolResult from Hydra execution.
        
        Returns:
            HydraResult with parsed credentials and attack statistics.
        """
        parser = HydraOutputParser()
        return parser.parse(result.stdout + "\n" + result.stderr)

    def _extract_version(self, version_output: str) -> str:
        """
        Extract Hydra version from --version output.
        
        Args:
            version_output: Raw version output.
        
        Returns:
            Version string.
        """
        # Hydra version output format:
        # "Hydra v9.6 (c) 2023 by van Hauser/THC"
        if "Hydra v" in version_output:
            import re
            match = re.search(r'Hydra v([\d.]+)', version_output)
            if match:
                return match.group(1)
        
        return version_output.strip().split('\n')[0]


if __name__ == "__main__":
    # Demo / Testing
    import asyncio
    
    async def main():
        print("Hydra Tool Wrapper Demo")
        print("=" * 80)
        print()
        
        hydra = HydraTool()
        print(f"Tool: {hydra}")
        print(f"Path: {hydra.tool_path}")
        print()
        
        # Validate tool
        print("Validating Hydra installation...")
        if await hydra.validate():
            print("✓ Hydra is available")
            
            # Get version
            version = await hydra.get_version()
            print(f"  Version: {version}")
            
            # Get full info
            info = await hydra.get_info()
            print(f"  Info: {info}")
        else:
            print("✗ Hydra not found or not executable")
            print("\nInstallation instructions:")
            print("  Windows: Download from https://github.com/maaaaz/thc-hydra-windows")
            print("  Linux:   sudo apt install hydra")
            print("  macOS:   brew install hydra")
    
    asyncio.run(main())
