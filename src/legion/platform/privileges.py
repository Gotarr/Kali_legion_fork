"""
Privilege management for cross-platform admin/root access.
"""

import sys
from pathlib import Path
from typing import NoReturn

# Handle both package import and standalone execution
try:
    from legion.platform.detector import get_platform_info
except ImportError:
    # For standalone testing
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from legion.platform.detector import get_platform_info


def is_admin() -> bool:
    """
    Check if the current process has administrator/root privileges.
    
    Returns:
        True if running with elevated privileges, False otherwise.
    
    Example:
        >>> if not is_admin():
        ...     print("This tool requires administrator privileges")
    """
    return get_platform_info().is_admin


def require_admin(message: str = "This operation requires administrator privileges") -> None:
    """
    Require administrator privileges, raising an exception if not available.
    
    Args:
        message: Custom error message.
    
    Raises:
        PermissionError: If not running with admin privileges.
    
    Example:
        >>> require_admin("Nmap requires root access for raw socket operations")
    """
    if not is_admin():
        raise PermissionError(message)


def request_elevation() -> NoReturn:
    """
    Request privilege elevation and restart the application.
    
    Platform-specific behavior:
        - Windows: Attempts to restart with UAC elevation
        - Linux/macOS: Prints instructions to run with sudo
    
    Note:
        This function does not return - it either restarts the app or exits.
    
    Raises:
        SystemExit: After printing instructions or attempting elevation.
    """
    platform_info = get_platform_info()
    
    if platform_info.is_windows:
        _elevate_windows()
    else:  # Unix-like
        _elevate_unix()


def _elevate_windows() -> NoReturn:
    """
    Attempt UAC elevation on Windows.
    
    Uses ctypes to call ShellExecuteW with 'runas' verb.
    """
    import ctypes
    import sys
    
    print("Requesting administrator privileges...")
    
    try:
        # Parameters for ShellExecuteW
        script = sys.executable
        params = " ".join(sys.argv)
        
        # Call ShellExecuteW with 'runas' to trigger UAC
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,      # hwnd
            "runas",   # operation
            script,    # file
            params,    # parameters
            None,      # directory
            1          # show command (SW_SHOWNORMAL)
        )
        
        if ret > 32:  # Success
            print("Restarting with administrator privileges...")
            sys.exit(0)
        else:
            print("Failed to elevate privileges.")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error during elevation: {e}")
        sys.exit(1)


def _elevate_unix() -> NoReturn:
    """
    Print instructions for Unix elevation and exit.
    
    On Unix systems, we can't programmatically elevate - the user
    must restart with sudo.
    """
    import sys
    
    print("\n" + "=" * 60)
    print("ADMINISTRATOR PRIVILEGES REQUIRED")
    print("=" * 60)
    print("\nLegion requires root privileges for raw socket operations")
    print("(needed by nmap and other scanning tools).")
    print("\nPlease restart Legion using sudo:")
    print(f"\n    sudo {' '.join(sys.argv)}")
    print("\n" + "=" * 60 + "\n")
    
    sys.exit(1)


def check_raw_socket_capability() -> bool:
    """
    Check if raw socket operations are available.
    
    This is a key requirement for tools like nmap.
    
    Returns:
        True if raw sockets can be created, False otherwise.
    """
    if is_admin():
        return True
    
    # On some Linux systems, raw sockets might be available
    # even without root via capabilities
    if get_platform_info().is_unix_like:
        try:
            import socket
            # Try to create a raw socket
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            s.close()
            return True
        except PermissionError:
            return False
        except Exception:
            # Other errors might indicate missing support, not permissions
            return False
    
    return False


def get_privilege_status() -> dict[str, bool]:
    """
    Get detailed privilege status.
    
    Returns:
        Dictionary with privilege information:
            - is_admin: Admin/root status
            - can_raw_socket: Raw socket capability
            - elevation_possible: Can request elevation
    """
    platform_info = get_platform_info()
    
    return {
        "is_admin": platform_info.is_admin,
        "can_raw_socket": check_raw_socket_capability(),
        "elevation_possible": platform_info.is_windows or platform_info.is_unix_like,
    }


if __name__ == "__main__":
    # Demo / Testing
    print("Privilege Status:")
    print("=" * 60)
    
    status = get_privilege_status()
    for key, value in status.items():
        print(f"{key:20s}: {value}")
    
    print()
    
    if not is_admin():
        print("⚠️  Not running with administrator privileges")
        print("\nSome features may not work correctly.")
        print("\nTo request elevation, uncomment the line below:")
        print("# request_elevation()")
    else:
        print("✓ Running with administrator privileges")
