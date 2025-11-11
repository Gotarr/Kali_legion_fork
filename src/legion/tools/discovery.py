"""
Tool discovery system for finding external pentesting tools.

This module provides cross-platform tool discovery, searching in:
- System PATH
- Common installation directories (OS-specific)
- Windows Registry (on Windows)
- User-configured custom paths
"""

import os
import shutil
from pathlib import Path
from typing import Optional

try:
    from legion.platform.detector import get_platform_info
except ImportError:
    # Standalone testing
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from legion.platform.detector import get_platform_info


def find_in_path(tool_name: str) -> Optional[Path]:
    """
    Find a tool in the system PATH.
    
    Args:
        tool_name: Name of the tool (e.g., "nmap", "hydra").
    
    Returns:
        Path to executable if found, None otherwise.
    
    Example:
        >>> nmap_path = find_in_path("nmap")
        >>> if nmap_path:
        ...     print(f"Found: {nmap_path}")
    """
    # Use shutil.which for cross-platform PATH search
    result = shutil.which(tool_name)
    
    if result:
        return Path(result)
    
    # On Windows, also try with .exe extension
    platform = get_platform_info()
    if platform.is_windows and not tool_name.endswith('.exe'):
        result = shutil.which(f"{tool_name}.exe")
        if result:
            return Path(result)
    
    return None


def get_common_tool_locations() -> dict[str, list[Path]]:
    """
    Get common installation directories for tools by OS.
    
    Returns:
        Dictionary mapping OS type to list of common tool directories.
    
    Example:
        >>> locations = get_common_tool_locations()
        >>> windows_paths = locations.get("windows", [])
    """
    platform = get_platform_info()
    
    locations: dict[str, list[Path]] = {
        "windows": [],
        "linux": [],
        "macos": [],
    }
    
    # Windows common locations
    if platform.is_windows:
        program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")
        
        locations["windows"] = [
            # Nmap
            Path(program_files) / "Nmap",
            Path(program_files_x86) / "Nmap",
            
            # Wireshark (contains tshark)
            Path(program_files) / "Wireshark",
            Path(program_files_x86) / "Wireshark",
            
            # Metasploit
            Path(program_files) / "Metasploit",
            Path("C:\\metasploit"),
            
            # Hydra
            Path(program_files) / "Hydra",
            Path(program_files) / "THC-Hydra",
            
            # Common portable tools location
            Path("C:\\Tools"),
            Path("C:\\PentestTools"),
            
            # User-specific
            Path.home() / "Tools",
            Path.home() / "Desktop" / "Tools",
        ]
    
    # Linux common locations
    if platform.is_linux:
        locations["linux"] = [
            # Standard binary directories
            Path("/usr/bin"),
            Path("/usr/local/bin"),
            Path("/bin"),
            Path("/sbin"),
            Path("/usr/sbin"),
            Path("/usr/local/sbin"),
            
            # Kali-specific
            Path("/usr/share/nmap"),
            Path("/usr/share/metasploit-framework"),
            Path("/usr/share/wordlists"),
            
            # Snap packages
            Path("/snap/bin"),
            
            # User-installed
            Path.home() / ".local" / "bin",
            Path.home() / "bin",
            
            # Opt installations
            Path("/opt"),
        ]
    
    # macOS common locations
    if platform.is_macos:
        locations["macos"] = [
            # Homebrew (Intel)
            Path("/usr/local/bin"),
            Path("/usr/local/sbin"),
            Path("/usr/local/opt"),
            
            # Homebrew (Apple Silicon)
            Path("/opt/homebrew/bin"),
            Path("/opt/homebrew/sbin"),
            
            # MacPorts
            Path("/opt/local/bin"),
            Path("/opt/local/sbin"),
            
            # System
            Path("/usr/bin"),
            Path("/usr/sbin"),
            
            # User
            Path.home() / ".local" / "bin",
            Path.home() / "bin",
        ]
    
    return locations


def find_in_common_locations(tool_name: str) -> Optional[Path]:
    """
    Search for a tool in common installation directories.
    
    Args:
        tool_name: Name of the tool to find.
    
    Returns:
        Path to executable if found, None otherwise.
    """
    platform = get_platform_info()
    locations = get_common_tool_locations()
    
    # Get OS-specific locations
    if platform.is_windows:
        search_paths = locations["windows"]
        # Add .exe extension on Windows if not present
        if not tool_name.endswith('.exe'):
            exe_name = f"{tool_name}.exe"
        else:
            exe_name = tool_name
    elif platform.is_macos:
        search_paths = locations["macos"]
        exe_name = tool_name
    else:  # Linux
        search_paths = locations["linux"]
        exe_name = tool_name
    
    # Search each directory
    for directory in search_paths:
        if not directory.exists():
            continue
        
        # Direct match
        exe_path = directory / exe_name
        if exe_path.exists() and exe_path.is_file():
            return exe_path
        
        # Also try without .exe (in case of symlink or script)
        if platform.is_windows and exe_name.endswith('.exe'):
            alt_path = directory / tool_name
            if alt_path.exists() and alt_path.is_file():
                return alt_path
    
    return None


def find_in_windows_registry(tool_name: str) -> Optional[Path]:
    """
    Search Windows Registry for tool installation paths.
    
    Only works on Windows. Checks common registry keys where tools
    register their installation paths.
    
    Args:
        tool_name: Name of the tool.
    
    Returns:
        Path to executable if found in registry, None otherwise.
    """
    platform = get_platform_info()
    if not platform.is_windows:
        return None
    
    try:
        import winreg
    except ImportError:
        return None
    
    # Common registry paths to check
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    
    # Tool-specific registry keys
    tool_registry_keys = {
        "nmap": [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Nmap"),
        ],
        "wireshark": [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wireshark"),
        ],
    }
    
    # Check tool-specific keys first
    if tool_name.lower() in tool_registry_keys:
        for hkey, subkey in tool_registry_keys[tool_name.lower()]:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                    exe_path = Path(install_path) / f"{tool_name}.exe"
                    if exe_path.exists():
                        return exe_path
            except (FileNotFoundError, OSError):
                continue
    
    # Search uninstall keys for any mention of the tool
    for hkey, base_path in registry_paths:
        try:
            with winreg.OpenKey(hkey, base_path) as base_key:
                # Enumerate all subkeys
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(base_key, i)
                        i += 1
                        
                        # Open the subkey
                        try:
                            with winreg.OpenKey(base_key, subkey_name) as subkey:
                                # Check DisplayName
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    if tool_name.lower() in display_name.lower():
                                        # Found a match - try to get install location
                                        try:
                                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                            exe_path = Path(install_location) / f"{tool_name}.exe"
                                            if exe_path.exists():
                                                return exe_path
                                        except (FileNotFoundError, OSError):
                                            pass
                                except (FileNotFoundError, OSError):
                                    pass
                        except (FileNotFoundError, OSError):
                            continue
                    
                    except OSError:
                        break
        except (FileNotFoundError, OSError):
            continue
    
    return None


def find_tool(tool_name: str, custom_paths: Optional[list[Path]] = None) -> Optional[Path]:
    """
    Comprehensive tool search using multiple strategies.
    
    Search order:
    1. Custom paths (if provided)
    2. System PATH
    3. Common installation directories
    4. Windows Registry (Windows only)
    
    Args:
        tool_name: Name of the tool to find.
        custom_paths: Optional list of custom directories to search first.
    
    Returns:
        Path to executable if found, None otherwise.
    
    Example:
        >>> nmap = find_tool("nmap")
        >>> if nmap:
        ...     print(f"Found nmap at: {nmap}")
        >>> else:
        ...     print("nmap not found")
    """
    # 1. Check custom paths first
    if custom_paths:
        platform = get_platform_info()
        exe_name = f"{tool_name}.exe" if platform.is_windows else tool_name
        
        for custom_dir in custom_paths:
            if not custom_dir.exists():
                continue
            
            exe_path = custom_dir / exe_name
            if exe_path.exists() and exe_path.is_file():
                return exe_path
    
    # 2. Check system PATH
    path_result = find_in_path(tool_name)
    if path_result:
        return path_result
    
    # 3. Check common installation directories
    common_result = find_in_common_locations(tool_name)
    if common_result:
        return common_result
    
    # 4. Check Windows Registry (Windows only)
    platform = get_platform_info()
    if platform.is_windows:
        registry_result = find_in_windows_registry(tool_name)
        if registry_result:
            return registry_result
    
    # Not found
    return None


def discover_all_tools(
    tool_names: Optional[list[str]] = None,
    custom_paths: Optional[dict[str, list[Path]]] = None,
) -> dict[str, Optional[Path]]:
    """
    Discover multiple tools at once.
    
    Args:
        tool_names: List of tool names to discover. If None, uses default list.
        custom_paths: Optional dict mapping tool names to custom search paths.
    
    Returns:
        Dictionary mapping tool names to their paths (or None if not found).
    
    Example:
        >>> tools = discover_all_tools(["nmap", "hydra", "nikto"])
        >>> for name, path in tools.items():
        ...     if path:
        ...         print(f"{name}: {path}")
        ...     else:
        ...         print(f"{name}: NOT FOUND")
    """
    # Default common pentesting tools
    if tool_names is None:
        tool_names = [
            "nmap",
            "hydra",
            "nikto",
            "sqlmap",
            "dirb",
            "gobuster",
            "wpscan",
            "enum4linux",
            "smbclient",
            "metasploit",
            "msfconsole",
        ]
    
    results: dict[str, Optional[Path]] = {}
    
    for tool_name in tool_names:
        # Get custom paths for this tool if provided
        tool_custom_paths = None
        if custom_paths and tool_name in custom_paths:
            tool_custom_paths = custom_paths[tool_name]
        
        # Discover the tool
        results[tool_name] = find_tool(tool_name, tool_custom_paths)
    
    return results


if __name__ == "__main__":
    # Demo / Testing
    print("Tool Discovery System")
    print("=" * 60)
    
    platform = get_platform_info()
    print(f"Platform: {platform}")
    print()
    
    # Discover common tools
    print("Discovering common pentesting tools...")
    print("-" * 60)
    
    tools = discover_all_tools()
    
    found = 0
    not_found = 0
    
    for tool_name, tool_path in tools.items():
        if tool_path:
            print(f"✓ {tool_name:15s} → {tool_path}")
            found += 1
        else:
            print(f"✗ {tool_name:15s} → NOT FOUND")
            not_found += 1
    
    print("-" * 60)
    print(f"Summary: {found} found, {not_found} not found")
    print()
    
    # Show common locations for this OS
    print("Common tool locations for this OS:")
    print("-" * 60)
    locations = get_common_tool_locations()
    
    if platform.is_windows:
        os_locations = locations["windows"]
    elif platform.is_macos:
        os_locations = locations["macos"]
    else:
        os_locations = locations["linux"]
    
    for location in os_locations:
        exists = "✓" if location.exists() else "✗"
        print(f"{exists} {location}")
