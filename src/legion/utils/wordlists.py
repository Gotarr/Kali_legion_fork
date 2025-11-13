"""
Wordlist utilities for Legion.

Provides helper functions to locate and manage wordlists from scripts/wordlists/
"""

from pathlib import Path
from typing import Optional, List


def get_wordlists_dir() -> Path:
    """
    Get the wordlists directory path.
    
    Returns:
        Path to scripts/wordlists/ directory.
    """
    # From src/legion/utils/wordlists.py -> scripts/wordlists/
    base = Path(__file__).parent.parent.parent.parent / "scripts" / "wordlists"
    return base


def get_service_wordlists(service: str) -> tuple[Optional[Path], Optional[Path]]:
    """
    Get default username and password wordlists for a service.
    
    Args:
        service: Service name (ssh, ftp, mysql, etc.)
    
    Returns:
        Tuple of (username_wordlist, password_wordlist) paths.
        Either may be None if not found.
    """
    wordlist_dir = get_wordlists_dir()
    
    if not wordlist_dir.exists():
        return None, None
    
    # Service-specific password lists
    service_password_files = {
        'ssh': 'ssh-betterdefaultpasslist.txt',
        'ftp': 'ftp-betterdefaultpasslist.txt',
        'mysql': 'mysql-betterdefaultpasslist.txt',
        'mssql': 'mssql-betterdefaultpasslist.txt',
        'postgres': 'postgres-betterdefaultpasslist.txt',
        'oracle': 'oracle-betterdefaultpasslist.txt',
        'telnet': 'telnet-betterdefaultpasslist.txt',
        'vnc': 'vnc-betterdefaultpasslist.txt',
        'db2': 'db2-betterdefaultpasslist.txt',
        'tomcat': 'tomcat-betterdefaultpasslist.txt',
        'windows': 'windows-betterdefaultpasslist.txt',
        'smb': 'windows-betterdefaultpasslist.txt',
        'rdp': 'windows-betterdefaultpasslist.txt',
    }
    
    # Get service-specific password file
    password_file = service_password_files.get(service.lower())
    password_path = None
    
    if password_file:
        password_path = wordlist_dir / password_file
        if not password_path.exists():
            password_path = None
    
    # Fallback to generic password list
    if not password_path:
        generic_passwords = [
            'ssh-password.txt',
            'ssh-betterdefaultpasslist.txt',
            'root-userpass.txt'
        ]
        for filename in generic_passwords:
            candidate = wordlist_dir / filename
            if candidate.exists():
                password_path = candidate
                break
    
    # Username wordlists
    username_path = None
    username_candidates = [
        'ssh-user.txt',
        'root-userpass.txt',
        'routers-userpass.txt'
    ]
    
    for filename in username_candidates:
        candidate = wordlist_dir / filename
        if candidate.exists():
            username_path = candidate
            break
    
    return username_path, password_path


def list_all_wordlists() -> List[Path]:
    """
    List all available wordlists.
    
    Returns:
        List of wordlist file paths.
    """
    wordlist_dir = get_wordlists_dir()
    
    if not wordlist_dir.exists():
        return []
    
    return sorted([f for f in wordlist_dir.glob("*.txt")])


def get_wordlist_info(wordlist_path: Path) -> dict:
    """
    Get information about a wordlist file.
    
    Args:
        wordlist_path: Path to wordlist file.
    
    Returns:
        Dictionary with wordlist info (name, size, line_count).
    """
    if not wordlist_path.exists():
        return {"error": "File not found"}
    
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        return {
            "name": wordlist_path.name,
            "path": str(wordlist_path),
            "size_bytes": wordlist_path.stat().st_size,
            "line_count": len(lines),
            "first_lines": [line.strip() for line in lines[:5] if line.strip()]
        }
    except Exception as e:
        return {"error": str(e)}


def export_credentials_to_wordlist(
    credentials: List,
    output_file: Path,
    mode: str = "passwords",
    append: bool = False
) -> int:
    """
    Export credentials to a wordlist file.
    
    Args:
        credentials: List of Credential objects.
        output_file: Output file path.
        mode: Export mode - "passwords", "usernames", or "combo" (user:pass).
        append: If True, append to existing file and avoid duplicates.
    
    Returns:
        Number of NEW lines written.
    """
    lines = set()  # Use set to avoid duplicates within new credentials
    
    for cred in credentials:
        if mode == "passwords":
            lines.add(cred.password)
        elif mode == "usernames":
            lines.add(cred.username)
        elif mode == "combo":
            lines.add(f"{cred.username}:{cred.password}")
    
    # If appending, read existing lines to avoid duplicates
    existing_lines = set()
    if append and output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_lines = {line.strip() for line in f if line.strip()}
        except Exception:
            pass  # If read fails, just overwrite
    
    # Filter out duplicates
    lines_to_write = lines - existing_lines
    
    # Write to file
    write_mode = 'a' if append else 'w'
    with open(output_file, write_mode, encoding='utf-8') as f:
        for line in sorted(lines_to_write):
            f.write(f"{line}\n")
    
    return len(lines_to_write)


def import_wordlist(
    wordlist_path: Path,
    format: str = "auto"
) -> List[tuple]:
    """
    Import wordlist and parse it.
    
    Args:
        wordlist_path: Path to wordlist file.
        format: Format - "auto", "passwords", "usernames", "combo" (user:pass).
    
    Returns:
        List of tuples: [(username, password), ...] or [(None, password), ...]
    """
    if not wordlist_path.exists():
        raise FileNotFoundError(f"Wordlist not found: {wordlist_path}")
    
    entries = []
    
    with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Auto-detect format
            if format == "auto" or format == "combo":
                if ':' in line:
                    parts = line.split(':', 1)
                    username = parts[0].strip()
                    password = parts[1].strip() if len(parts) > 1 else ""
                    entries.append((username, password))
                else:
                    # Just password
                    entries.append((None, line))
            elif format == "passwords":
                entries.append((None, line))
            elif format == "usernames":
                entries.append((line, None))
    
    return entries


if __name__ == "__main__":
    # Demo
    print("=== Wordlist Utilities Demo ===\n")
    
    print(f"Wordlists directory: {get_wordlists_dir()}\n")
    
    # List all wordlists
    print("Available wordlists:")
    for wl in list_all_wordlists():
        info = get_wordlist_info(wl)
        if "error" not in info:
            print(f"  - {info['name']}: {info['line_count']} entries, {info['size_bytes']} bytes")
    
    print("\nService-specific wordlists:")
    for service in ['ssh', 'ftp', 'mysql', 'vnc']:
        user_wl, pass_wl = get_service_wordlists(service)
        print(f"  {service}:")
        print(f"    Usernames: {user_wl.name if user_wl else 'N/A'}")
        print(f"    Passwords: {pass_wl.name if pass_wl else 'N/A'}")
