"""
Configuration management for Legion.

This module provides TOML-based configuration with:
- Type-safe settings via dataclasses
- User and project-level configuration
- Automatic validation
- Legacy config migration
- Hot-reload support (planned)
"""

from legion.config.schema import (
    LegionConfig,
    ScanningConfig,
    LoggingConfig,
    ToolsConfig,
    UIConfig,
    DatabaseConfig,
    ProjectConfig,
)
from legion.config.manager import ConfigManager, get_config_manager, get_config
from legion.config.defaults import (
    get_default_config,
    get_template_path,
    create_user_config,
    print_template,
)
from legion.config.init import (
    init_user_config,
    reset_user_config,
    find_legacy_config,
    migrate_legacy_config,
)

__all__ = [
    # Schema
    "LegionConfig",
    "ScanningConfig",
    "LoggingConfig",
    "ToolsConfig",
    "UIConfig",
    "DatabaseConfig",
    "ProjectConfig",
    # Manager
    "ConfigManager",
    "get_config_manager",
    "get_config",
    # Defaults
    "get_default_config",
    "get_template_path",
    "create_user_config",
    "print_template",
    # Init
    "init_user_config",
    "reset_user_config",
    "find_legacy_config",
    "migrate_legacy_config",
]
