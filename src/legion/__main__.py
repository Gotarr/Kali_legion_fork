"""
Legion - Cross-Platform Penetration Testing Framework

Entry point for running Legion as a module: python -m legion
"""

import sys
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def main() -> int:
    """
    Main entry point for Legion.
    
    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    from legion.platform.detector import detect_platform
    from legion.platform.privileges import is_admin, get_privilege_status
    from legion.platform.paths import (
        get_data_dir,
        get_config_dir,
        get_log_dir,
    )
    
    print("\n" + "=" * 70)
    print("Legion - Cross-Platform Penetration Testing Framework")
    print("Version: 2.0.0-alpha1")
    print("=" * 70)
    
    # Detect platform
    platform_info = detect_platform()
    print(f"\nPlatform: {platform_info}")
    
    # Check privileges
    privilege_status = get_privilege_status()
    print("\nPrivilege Status:")
    for key, value in privilege_status.items():
        status = "✓" if value else "✗"
        print(f"  {status} {key.replace('_', ' ').title()}: {value}")
    
    # Show directories
    print("\nDirectories:")
    print(f"  Data:   {get_data_dir()}")
    print(f"  Config: {get_config_dir()}")
    print(f"  Logs:   {get_log_dir()}")
    
    # Warning if not admin
    if not is_admin():
        print("\n⚠️  WARNING: Not running with administrator privileges!")
        print("   Some features (like nmap scanning) may not work correctly.")
        
        if platform_info.is_unix_like:
            print(f"\n   Please restart with: sudo {' '.join(sys.argv)}")
        elif platform_info.is_windows:
            print("\n   Please restart as Administrator.")
    
    print("\n" + "=" * 70)
    print("\nLegion v2.0 is under development.")
    print("The GUI will be available in a future release.")
    print("\nFor now, this demonstrates the cross-platform foundation:")
    print("  - Platform detection")
    print("  - Path management")
    print("  - Privilege checking")
    print("\nNext steps: Tool discovery, nmap wrapper, GUI migration")
    print("=" * 70 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
