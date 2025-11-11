"""
Platform-agnostic path management.

Provides cross-platform directory and file path utilities following
OS-specific conventions.
"""

from pathlib import Path
from typing import Optional

try:
    from platformdirs import (
        user_cache_dir,
        user_config_dir,
        user_data_dir,
        user_log_dir,
    )
except ImportError:
    # Fallback if platformdirs not installed
    import os
    from pathlib import Path
    
    def user_data_dir(appname: str, appauthor: str = None) -> str:
        if os.name == 'nt':  # Windows
            return os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), appauthor or appname, appname)
        elif os.name == 'posix':
            if 'darwin' in os.sys.platform:  # macOS
                return os.path.join(os.path.expanduser('~/Library/Application Support'), appname)
            else:  # Linux
                return os.path.join(os.path.expanduser('~/.local/share'), appname)
        return os.path.expanduser(f'~/.{appname}')
    
    def user_config_dir(appname: str, appauthor: str = None) -> str:
        if os.name == 'nt':  # Windows
            return user_data_dir(appname, appauthor)
        elif os.name == 'posix':
            if 'darwin' in os.sys.platform:  # macOS
                return os.path.join(os.path.expanduser('~/Library/Application Support'), appname)
            else:  # Linux
                return os.path.join(os.path.expanduser('~/.config'), appname)
        return os.path.expanduser(f'~/.{appname}')
    
    def user_cache_dir(appname: str, appauthor: str = None) -> str:
        if os.name == 'nt':  # Windows
            return os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), appauthor or appname, appname, 'Cache')
        elif os.name == 'posix':
            if 'darwin' in os.sys.platform:  # macOS
                return os.path.join(os.path.expanduser('~/Library/Caches'), appname)
            else:  # Linux
                return os.path.join(os.path.expanduser('~/.cache'), appname)
        return os.path.expanduser(f'~/.{appname}/cache')
    
    def user_log_dir(appname: str, appauthor: str = None) -> str:
        if os.name == 'nt':  # Windows
            return os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), appauthor or appname, appname, 'Logs')
        elif os.name == 'posix':
            if 'darwin' in os.sys.platform:  # macOS
                return os.path.join(os.path.expanduser('~/Library/Logs'), appname)
            else:  # Linux
                return os.path.join(os.path.expanduser('~/.local/state'), appname, 'log')
        return os.path.expanduser(f'~/.{appname}/logs')

try:
    from legion.platform.detector import get_platform_info
except ImportError:
    # For standalone testing
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from legion.platform.detector import get_platform_info

# Application name for directory creation
APP_NAME = "legion"
APP_AUTHOR = "GothamSecurity"


def get_data_dir() -> Path:
    """
    Get the user data directory for Legion.
    
    Platform-specific locations:
        - Windows: %LOCALAPPDATA%\\GothamSecurity\\legion
        - Linux: ~/.local/share/legion
        - macOS: ~/Library/Application Support/legion
    
    Returns:
        Path to user data directory (created if it doesn't exist).
    """
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_dir() -> Path:
    """
    Get the user configuration directory for Legion.
    
    Platform-specific locations:
        - Windows: %LOCALAPPDATA%\\GothamSecurity\\legion
        - Linux: ~/.config/legion
        - macOS: ~/Library/Application Support/legion
    
    Returns:
        Path to config directory (created if it doesn't exist).
    """
    path = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_cache_dir() -> Path:
    """
    Get the cache directory for Legion.
    
    Platform-specific locations:
        - Windows: %LOCALAPPDATA%\\GothamSecurity\\legion\\Cache
        - Linux: ~/.cache/legion
        - macOS: ~/Library/Caches/legion
    
    Returns:
        Path to cache directory (created if it doesn't exist).
    """
    path = Path(user_cache_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_log_dir() -> Path:
    """
    Get the log directory for Legion.
    
    Platform-specific locations:
        - Windows: %LOCALAPPDATA%\\GothamSecurity\\legion\\Logs
        - Linux: ~/.local/state/legion/log or ~/.cache/legion/log
        - macOS: ~/Library/Logs/legion
    
    Returns:
        Path to log directory (created if it doesn't exist).
    """
    path = Path(user_log_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_temp_dir() -> Path:
    """
    Get temporary directory for Legion.
    
    Uses the cache directory with a 'tmp' subdirectory.
    
    Returns:
        Path to temp directory (created if it doesn't exist).
    """
    path = get_cache_dir() / "tmp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_projects_dir() -> Path:
    """
    Get the default projects directory.
    
    Located in the user data directory under 'projects'.
    
    Returns:
        Path to projects directory (created if it doesn't exist).
    """
    path = get_data_dir() / "projects"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_wordlists_dir() -> Path:
    """
    Get the wordlists directory.
    
    Located in the user data directory under 'wordlists'.
    
    Returns:
        Path to wordlists directory (created if it doesn't exist).
    """
    path = get_data_dir() / "wordlists"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_tools_dir() -> Path:
    """
    Get directory for tool-related data (configs, scripts, etc.).
    
    Returns:
        Path to tools directory (created if it doesn't exist).
    """
    path = get_data_dir() / "tools"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_screenshots_dir(project_name: Optional[str] = None) -> Path:
    """
    Get screenshots directory.
    
    Args:
        project_name: Optional project name for project-specific screenshots.
    
    Returns:
        Path to screenshots directory (created if it doesn't exist).
    """
    if project_name:
        path = get_projects_dir() / project_name / "screenshots"
    else:
        path = get_data_dir() / "screenshots"
    
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_tool_output_dir(project_name: Optional[str] = None) -> Path:
    """
    Get tool output directory.
    
    Args:
        project_name: Optional project name for project-specific output.
    
    Returns:
        Path to tool output directory (created if it doesn't exist).
    """
    if project_name:
        path = get_projects_dir() / project_name / "tool-output"
    else:
        path = get_data_dir() / "tool-output"
    
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure.
    
    Returns:
        The path (now guaranteed to exist).
    
    Raises:
        OSError: If directory creation fails.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_home_dir() -> Path:
    """
    Get user's home directory.
    
    Returns:
        Path to home directory.
    """
    return Path.home()


def safe_path_join(base: Path, *parts: str) -> Path:
    """
    Safely join path components, preventing path traversal.
    
    Args:
        base: Base directory path.
        *parts: Path components to join.
    
    Returns:
        Joined path.
    
    Raises:
        ValueError: If resulting path is outside base directory.
    """
    result = base.joinpath(*parts).resolve()
    
    # Ensure result is within base directory
    try:
        result.relative_to(base.resolve())
    except ValueError:
        raise ValueError(f"Path traversal detected: {result} is outside {base}")
    
    return result


def normalize_path(path: str | Path) -> Path:
    """
    Normalize a path to a Path object with resolved symlinks.
    
    Args:
        path: String or Path to normalize.
    
    Returns:
        Normalized Path object.
    """
    return Path(path).expanduser().resolve()


if __name__ == "__main__":
    # Demo / Testing
    print("Legion Directory Structure:")
    print("=" * 60)
    print(f"Platform: {get_platform_info()}")
    print()
    print(f"Data Dir:       {get_data_dir()}")
    print(f"Config Dir:     {get_config_dir()}")
    print(f"Cache Dir:      {get_cache_dir()}")
    print(f"Log Dir:        {get_log_dir()}")
    print(f"Temp Dir:       {get_temp_dir()}")
    print(f"Projects Dir:   {get_projects_dir()}")
    print(f"Wordlists Dir:  {get_wordlists_dir()}")
    print(f"Tools Dir:      {get_tools_dir()}")
    print(f"Home Dir:       {get_home_dir()}")
