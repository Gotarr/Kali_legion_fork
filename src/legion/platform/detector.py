"""
Platform detection and information module.

Provides cross-platform OS detection and system information.
"""

import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class PlatformInfo:
    """Information about the current platform."""
    
    system: Literal["Windows", "Linux", "Darwin", "Unknown"]
    """Operating system name."""
    
    version: str
    """OS version string."""
    
    release: str
    """OS release string."""
    
    machine: str
    """Machine architecture (x86_64, arm64, etc.)."""
    
    is_wsl: bool
    """True if running under Windows Subsystem for Linux."""
    
    is_admin: bool
    """True if running with elevated privileges."""
    
    python_version: str
    """Python interpreter version."""
    
    def __str__(self) -> str:
        """Human-readable platform information."""
        wsl_info = " (WSL)" if self.is_wsl else ""
        admin_info = " [Admin]" if self.is_admin else ""
        return (
            f"{self.system} {self.version}{wsl_info}{admin_info} "
            f"on {self.machine} - Python {self.python_version}"
        )
    
    @property
    def is_windows(self) -> bool:
        """Check if running on Windows (native)."""
        return self.system == "Windows" and not self.is_wsl
    
    @property
    def is_linux(self) -> bool:
        """Check if running on Linux (including WSL)."""
        return self.system == "Linux" or self.is_wsl
    
    @property
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return self.system == "Darwin"
    
    @property
    def is_unix_like(self) -> bool:
        """Check if running on Unix-like system (Linux or macOS)."""
        return self.is_linux or self.is_macos


def _detect_wsl() -> bool:
    """
    Detect if running under Windows Subsystem for Linux.
    
    Returns:
        True if WSL is detected, False otherwise.
    """
    try:
        # Check for WSL-specific indicators
        with open("/proc/version", "r") as f:
            version_info = f.read().lower()
            return "microsoft" in version_info or "wsl" in version_info
    except (FileNotFoundError, PermissionError):
        return False


def _check_admin_privileges() -> bool:
    """
    Check if running with administrator/root privileges.
    
    Returns:
        True if running with elevated privileges.
    """
    system = platform.system()
    
    if system == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:  # Unix-like (Linux, macOS)
        try:
            import os
            return os.geteuid() == 0
        except AttributeError:
            # os.geteuid() not available (shouldn't happen on Unix)
            return False


def detect_platform() -> PlatformInfo:
    """
    Detect current platform and gather system information.
    
    Returns:
        PlatformInfo object with platform details.
    
    Example:
        >>> info = detect_platform()
        >>> print(info)
        Windows 10 on x86_64 - Python 3.11.0
        >>> if info.is_admin:
        ...     print("Running with admin privileges")
    """
    system = platform.system()
    
    # Normalize system name
    if system not in ("Windows", "Linux", "Darwin"):
        system = "Unknown"
    
    # Detect WSL
    is_wsl = False
    if system == "Linux":
        is_wsl = _detect_wsl()
    
    # Get version information
    version = platform.version()
    release = platform.release()
    machine = platform.machine()
    
    # Check admin privileges
    is_admin = _check_admin_privileges()
    
    # Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    return PlatformInfo(
        system=system,  # type: ignore
        version=version,
        release=release,
        machine=machine,
        is_wsl=is_wsl,
        is_admin=is_admin,
        python_version=python_version,
    )


def get_platform_name() -> str:
    """
    Get a simple platform name string.
    
    Returns:
        'windows', 'linux', 'macos', or 'unknown'
    """
    info = detect_platform()
    if info.is_windows:
        return "windows"
    elif info.is_linux:
        return "linux"
    elif info.is_macos:
        return "macos"
    else:
        return "unknown"


# Module-level platform info (cached)
_platform_info: PlatformInfo | None = None


def get_platform_info() -> PlatformInfo:
    """
    Get cached platform information.
    
    Returns:
        PlatformInfo object (cached after first call).
    """
    global _platform_info
    if _platform_info is None:
        _platform_info = detect_platform()
    return _platform_info


if __name__ == "__main__":
    # Demo / Testing
    info = detect_platform()
    print("Platform Detection Results:")
    print("=" * 60)
    print(info)
    print("=" * 60)
    print(f"System: {info.system}")
    print(f"Version: {info.version}")
    print(f"Release: {info.release}")
    print(f"Machine: {info.machine}")
    print(f"WSL: {info.is_wsl}")
    print(f"Admin: {info.is_admin}")
    print(f"Python: {info.python_version}")
    print()
    print(f"is_windows: {info.is_windows}")
    print(f"is_linux: {info.is_linux}")
    print(f"is_macos: {info.is_macos}")
    print(f"is_unix_like: {info.is_unix_like}")
