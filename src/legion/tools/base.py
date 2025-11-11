"""
Base classes and interfaces for external tool wrappers.

This module provides the foundation for wrapping external pentesting tools
like nmap, hydra, nikto, etc. in a platform-agnostic way.
"""

import asyncio
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ToolResult:
    """Result from a tool execution."""
    
    success: bool
    """Whether the tool executed successfully."""
    
    exit_code: int
    """Process exit code."""
    
    stdout: str
    """Standard output from the tool."""
    
    stderr: str
    """Standard error from the tool."""
    
    command: list[str]
    """The command that was executed."""
    
    duration: float
    """Execution duration in seconds."""
    
    parsed_data: Any = None
    """Parsed output data (tool-specific)."""
    
    raw_output_path: Optional[Path] = None
    """Path to raw output file if saved."""
    
    def __str__(self) -> str:
        """Human-readable result summary."""
        status = "✓" if self.success else "✗"
        return (
            f"{status} Exit Code: {self.exit_code} | "
            f"Duration: {self.duration:.2f}s | "
            f"Command: {' '.join(self.command)}"
        )


@dataclass
class ToolInfo:
    """Information about an installed tool."""
    
    name: str
    """Tool name (e.g., 'nmap')."""
    
    path: Path
    """Full path to the executable."""
    
    version: str = "unknown"
    """Tool version string."""
    
    available: bool = True
    """Whether the tool is available and executable."""
    
    platform_specific: bool = False
    """Whether this tool is platform-specific."""
    
    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the tool."""
    
    def __str__(self) -> str:
        """Human-readable tool info."""
        status = "✓" if self.available else "✗"
        return f"{status} {self.name} v{self.version} @ {self.path}"


class BaseTool(ABC):
    """
    Abstract base class for external tool wrappers.
    
    All tool wrappers (nmap, hydra, nikto, etc.) should inherit from this
    class and implement the required abstract methods.
    
    Example:
        >>> class NmapTool(BaseTool):
        ...     @property
        ...     def tool_name(self) -> str:
        ...         return "nmap"
        ...     
        ...     async def parse_output(self, result: ToolResult) -> Any:
        ...         # Parse XML output
        ...         return parsed_data
    """
    
    def __init__(self, tool_path: Optional[Path] = None):
        """
        Initialize the tool wrapper.
        
        Args:
            tool_path: Optional explicit path to the tool executable.
                      If None, the tool will be discovered automatically.
        """
        self._tool_path = tool_path
        self._tool_info: Optional[ToolInfo] = None
    
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """
        Get the name of the tool.
        
        Returns:
            Tool name (e.g., "nmap", "hydra").
        """
        pass
    
    @property
    def tool_path(self) -> Optional[Path]:
        """
        Get the path to the tool executable.
        
        Returns:
            Path to executable, or None if not found.
        """
        return self._tool_path
    
    @tool_path.setter
    def tool_path(self, path: Path) -> None:
        """Set the tool path and invalidate cached info."""
        self._tool_path = path
        self._tool_info = None  # Invalidate cache
    
    async def validate(self) -> bool:
        """
        Validate that the tool is available and executable.
        
        Returns:
            True if tool is available and working.
        
        Example:
            >>> nmap = NmapTool()
            >>> if await nmap.validate():
            ...     print("nmap is ready")
        """
        if not self._tool_path:
            return False
        
        if not self._tool_path.exists():
            return False
        
        try:
            # Try running with --version or -h to verify it works
            result = await self.run(["--version"], timeout=5.0)
            return result.success or result.exit_code == 0
        except Exception:
            return False
    
    async def get_version(self) -> str:
        """
        Get the tool version string.
        
        Returns:
            Version string, or "unknown" if detection fails.
        """
        try:
            result = await self.run(["--version"], timeout=5.0)
            if result.success:
                # Most tools print version on first line
                version_line = result.stdout.split('\n')[0]
                return self._extract_version(version_line)
        except Exception:
            pass
        
        return "unknown"
    
    def _extract_version(self, version_output: str) -> str:
        """
        Extract version number from version output.
        
        Override this in subclasses for tool-specific version parsing.
        
        Args:
            version_output: Raw version output from the tool.
        
        Returns:
            Cleaned version string.
        """
        # Default: return first line, trimmed
        return version_output.strip().split('\n')[0]
    
    async def run(
        self,
        args: list[str],
        timeout: Optional[float] = None,
        input_data: Optional[str] = None,
        cwd: Optional[Path] = None,
    ) -> ToolResult:
        """
        Run the tool with specified arguments.
        
        Args:
            args: Command-line arguments for the tool.
            timeout: Optional timeout in seconds.
            input_data: Optional input to send to stdin.
            cwd: Optional working directory.
        
        Returns:
            ToolResult with execution details.
        
        Raises:
            FileNotFoundError: If tool executable not found.
            asyncio.TimeoutError: If execution exceeds timeout.
        
        Example:
            >>> result = await nmap.run(["-sV", "192.168.1.1"])
            >>> if result.success:
            ...     print(result.stdout)
        """
        if not self._tool_path:
            raise FileNotFoundError(f"{self.tool_name} executable not found")
        
        command = [str(self._tool_path)] + args
        
        import time
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                cwd=cwd,
            )
            
            # Communicate with timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(
                        input=input_data.encode() if input_data else None
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                # Kill the process on timeout
                process.kill()
                await process.wait()
                raise
            
            duration = time.time() - start_time
            
            return ToolResult(
                success=process.returncode == 0,
                exit_code=process.returncode or 0,
                stdout=stdout_bytes.decode('utf-8', errors='replace'),
                stderr=stderr_bytes.decode('utf-8', errors='replace'),
                command=command,
                duration=duration,
            )
        
        except FileNotFoundError:
            # Executable not found
            raise FileNotFoundError(
                f"{self.tool_name} executable not found at {self._tool_path}"
            )
        
        except Exception as e:
            # Other errors - return failed result
            duration = time.time() - start_time
            return ToolResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                command=command,
                duration=duration,
            )
    
    @abstractmethod
    async def parse_output(self, result: ToolResult) -> Any:
        """
        Parse the tool output into structured data.
        
        Args:
            result: ToolResult from execution.
        
        Returns:
            Parsed data structure (tool-specific).
        
        Example:
            >>> result = await nmap.run(["-sV", "192.168.1.1"])
            >>> parsed = await nmap.parse_output(result)
            >>> print(parsed.hosts)
        """
        pass
    
    async def execute(
        self,
        args: list[str],
        parse: bool = True,
        timeout: Optional[float] = None,
    ) -> ToolResult:
        """
        Execute the tool and optionally parse output.
        
        Convenience method that combines run() and parse_output().
        
        Args:
            args: Command-line arguments.
            parse: Whether to parse the output.
            timeout: Optional timeout in seconds.
        
        Returns:
            ToolResult with optional parsed_data field populated.
        """
        result = await self.run(args, timeout=timeout)
        
        if parse and result.success:
            try:
                result.parsed_data = await self.parse_output(result)
            except Exception as e:
                # Parsing failed - log but don't fail the whole execution
                result.stderr += f"\nParsing error: {e}"
        
        return result
    
    async def get_info(self) -> ToolInfo:
        """
        Get comprehensive information about this tool.
        
        Returns:
            ToolInfo with details about the tool installation.
        """
        if self._tool_info is not None:
            return self._tool_info
        
        # Detect version and availability
        available = await self.validate()
        version = await self.get_version() if available else "unknown"
        
        self._tool_info = ToolInfo(
            name=self.tool_name,
            path=self._tool_path or Path("not-found"),
            version=version,
            available=available,
        )
        
        return self._tool_info
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"<{self.__class__.__name__}(path={self._tool_path})>"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.tool_name} @ {self._tool_path or 'not found'}"


class ToolNotFoundError(Exception):
    """Raised when a required tool is not found on the system."""
    
    def __init__(self, tool_name: str, message: Optional[str] = None):
        """
        Initialize the exception.
        
        Args:
            tool_name: Name of the missing tool.
            message: Optional custom message.
        """
        self.tool_name = tool_name
        self.message = message or f"{tool_name} not found in system"
        super().__init__(self.message)


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""
    
    def __init__(
        self,
        tool_name: str,
        exit_code: int,
        stderr: str,
        message: Optional[str] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            tool_name: Name of the tool that failed.
            exit_code: Process exit code.
            stderr: Standard error output.
            message: Optional custom message.
        """
        self.tool_name = tool_name
        self.exit_code = exit_code
        self.stderr = stderr
        self.message = message or (
            f"{tool_name} execution failed with exit code {exit_code}"
        )
        super().__init__(self.message)
