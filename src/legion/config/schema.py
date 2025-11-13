"""
Configuration schema for Legion.

Defines all configuration options with type hints and validation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal


@dataclass
class ScanningConfig:
    """Scanning-related configuration."""
    
    timeout: int = 300
    """Default scan timeout in seconds."""
    
    max_concurrent: int = 3
    """Maximum number of concurrent scans."""
    
    default_profile: str = "quick"
    """Default scan profile (quick, full, stealth, etc.)."""
    
    auto_parse: bool = True
    """Automatically parse scan results."""
    
    auto_save: bool = True
    """Automatically save scan results to database."""
    
    timing_template: Literal[0, 1, 2, 3, 4, 5] = 4
    """Nmap timing template (0=paranoid, 5=insane)."""
    
    verbose_output: bool = False
    """Enable verbose scan output."""
    
    screenshot_timeout: int = 15
    """Screenshot timeout in seconds (legacy feature)."""
    
    web_services: str = "http,https,ssl,soap"
    """Comma-separated list of services to treat as web services (legacy feature)."""
    
    enable_nse_scripts: bool = True
    """Enable Nmap NSE (Nmap Scripting Engine) scripts."""
    
    nse_script_path: Optional[str] = None
    """Custom path to NSE scripts directory (None = use Legion's scripts/nmap/)."""
    
    enable_vulners: bool = False
    """Automatically run Vulners NSE script for CVE detection."""
    
    vulners_min_cvss: float = 0.0
    """Minimum CVSS score for Vulners reporting (0.0 = all)."""
    
    shodan_api_key: str = ""
    """Shodan API key for shodan-api.nse script."""
    
    def validate(self) -> None:
        """Validate scanning configuration."""
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_concurrent <= 0:
            raise ValueError("max_concurrent must be positive")
        if self.default_profile not in ("quick", "full", "stealth", "version", "os", "aggressive"):
            raise ValueError(f"Invalid scan profile: {self.default_profile}")
        if self.screenshot_timeout <= 0:
            raise ValueError("screenshot_timeout must be positive")
        if self.vulners_min_cvss < 0.0 or self.vulners_min_cvss > 10.0:
            raise ValueError("vulners_min_cvss must be between 0.0 and 10.0")


@dataclass
class LoggingConfig:
    """Logging configuration."""
    
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    """Logging level."""
    
    file_enabled: bool = True
    """Enable logging to file."""
    
    file_path: Optional[str] = None
    """Custom log file path (None = auto)."""
    
    console_enabled: bool = True
    """Enable console logging."""
    
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    """Log message format."""
    
    max_file_size_mb: int = 10
    """Maximum log file size in MB."""
    
    backup_count: int = 5
    """Number of backup log files to keep."""
    
    def validate(self) -> None:
        """Validate logging configuration."""
        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        if self.backup_count < 0:
            raise ValueError("backup_count must be non-negative")


@dataclass
class ToolsConfig:
    """External tools configuration."""
    
    auto_discover: bool = True
    """Automatically discover tool paths."""
    
    nmap_path: Optional[str] = None
    """Custom nmap executable path."""
    
    hydra_path: Optional[str] = None
    """Custom hydra executable path."""
    
    nikto_path: Optional[str] = None
    """Custom nikto executable path."""
    
    searchsploit_path: Optional[str] = None
    """Custom searchsploit executable path."""
    
    custom_paths: dict[str, str] = field(default_factory=dict)
    """Custom paths for additional tools."""
    
    cache_enabled: bool = True
    """Enable tool path caching."""
    
    cache_ttl: int = 3600
    """Cache time-to-live in seconds."""
    
    def validate(self) -> None:
        """Validate tools configuration."""
        if self.cache_ttl < 0:
            raise ValueError("cache_ttl must be non-negative")
        
        # Validate custom paths exist if specified
        for tool, path_str in [
            ("nmap", self.nmap_path),
            ("hydra", self.hydra_path),
            ("nikto", self.nikto_path),
            ("searchsploit", self.searchsploit_path),
        ]:
            if path_str:
                path = Path(path_str)
                if not path.exists():
                    raise ValueError(f"{tool} path does not exist: {path_str}")


@dataclass
class UIConfig:
    """User interface configuration."""
    
    theme: Literal["light", "dark", "system"] = "system"
    """UI theme."""
    
    font_size: int = 10
    """Base font size in points."""
    
    show_toolbar: bool = True
    """Show main toolbar."""
    
    show_statusbar: bool = True
    """Show status bar."""
    
    remember_window_size: bool = True
    """Remember window size and position."""
    
    auto_refresh_interval: int = 5
    """Auto-refresh interval in seconds (0=disabled)."""
    
    max_table_rows: int = 1000
    """Maximum rows to display in tables."""
    
    confirm_deletions: bool = True
    """Confirm before deleting items."""
    
    default_terminal: str = "cmd"
    """Default terminal to use for external commands (legacy feature)."""
    """Confirm before deleting items."""
    
    def validate(self) -> None:
        """Validate UI configuration."""
        if self.font_size < 6 or self.font_size > 24:
            raise ValueError("font_size must be between 6 and 24")
        if self.auto_refresh_interval < 0:
            raise ValueError("auto_refresh_interval must be non-negative")
        if self.max_table_rows <= 0:
            raise ValueError("max_table_rows must be positive")


@dataclass
class DatabaseConfig:
    """Database configuration."""
    
    type: Literal["json", "sqlite"] = "json"
    """Database type."""
    
    path: Optional[str] = None
    """Custom database path (None = auto)."""
    
    auto_backup: bool = True
    """Automatically backup database."""
    
    backup_interval: int = 300
    """Backup interval in seconds."""
    
    compression: bool = False
    """Compress database files (SQLite only)."""
    
    def validate(self) -> None:
        """Validate database configuration."""
        if self.backup_interval < 0:
            raise ValueError("backup_interval must be non-negative")


@dataclass
class ProjectConfig:
    """Project-specific configuration."""
    
    name: str = "default"
    """Project name."""
    
    description: str = ""
    """Project description."""
    
    created_at: Optional[str] = None
    """Project creation timestamp (ISO format)."""
    
    scan_profile: str = "quick"
    """Default scan profile for this project."""
    
    auto_save_interval: int = 60
    """Auto-save interval in seconds."""
    
    def validate(self) -> None:
        """Validate project configuration."""
        if not self.name:
            raise ValueError("Project name cannot be empty")
        if self.auto_save_interval < 0:
            raise ValueError("auto_save_interval must be non-negative")


@dataclass
class LegionConfig:
    """Main Legion configuration."""
    
    scanning: ScanningConfig = field(default_factory=ScanningConfig)
    """Scanning configuration."""
    
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    """Logging configuration."""
    
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    """Tools configuration."""
    
    ui: UIConfig = field(default_factory=UIConfig)
    """UI configuration."""
    
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    """Database configuration."""
    
    project: ProjectConfig = field(default_factory=ProjectConfig)
    """Project configuration."""
    
    def validate(self) -> None:
        """Validate entire configuration."""
        self.scanning.validate()
        self.logging.validate()
        self.tools.validate()
        self.ui.validate()
        self.database.validate()
        self.project.validate()
    
    def __str__(self) -> str:
        """Human-readable configuration summary."""
        return (
            f"LegionConfig(\n"
            f"  Project: {self.project.name}\n"
            f"  Scan Profile: {self.scanning.default_profile}\n"
            f"  Max Concurrent: {self.scanning.max_concurrent}\n"
            f"  Log Level: {self.logging.level}\n"
            f"  Auto-discover Tools: {self.tools.auto_discover}\n"
            f"  UI Theme: {self.ui.theme}\n"
            f"  Database: {self.database.type}\n"
            f")"
        )


# Demo/Test
if __name__ == "__main__":
    print("Legion Configuration Schema")
    print("=" * 60)
    
    # Create default config
    config = LegionConfig()
    
    print("\nDefault Configuration:")
    print("-" * 60)
    print(config)
    
    print("\n" + "=" * 60)
    print("Scanning Config:")
    print(f"  Timeout: {config.scanning.timeout}s")
    print(f"  Max Concurrent: {config.scanning.max_concurrent}")
    print(f"  Profile: {config.scanning.default_profile}")
    print(f"  Timing: T{config.scanning.timing_template}")
    
    print("\nLogging Config:")
    print(f"  Level: {config.logging.level}")
    print(f"  File: {config.logging.file_enabled}")
    print(f"  Console: {config.logging.console_enabled}")
    
    print("\nTools Config:")
    print(f"  Auto-discover: {config.tools.auto_discover}")
    print(f"  Cache: {config.tools.cache_enabled}")
    
    print("\nUI Config:")
    print(f"  Theme: {config.ui.theme}")
    print(f"  Font Size: {config.ui.font_size}pt")
    
    print("\nDatabase Config:")
    print(f"  Type: {config.database.type}")
    print(f"  Auto-backup: {config.database.auto_backup}")
    
    # Validate
    print("\n" + "=" * 60)
    print("Validating configuration...")
    try:
        config.validate()
        print("✅ Configuration is valid!")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
    
    # Test invalid config
    print("\n" + "=" * 60)
    print("Testing invalid configuration...")
    invalid_config = LegionConfig()
    invalid_config.scanning.timeout = -10
    
    try:
        invalid_config.validate()
        print("❌ Should have failed!")
    except ValueError as e:
        print(f"✅ Caught error: {e}")
