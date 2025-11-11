"""
Configuration manager for Legion.

Handles loading, saving, and managing TOML-based configuration files.
"""

from typing import TYPE_CHECKING

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # Backport for Python 3.10

# Type checking: suppress warning for tomllib on Python 3.10
if TYPE_CHECKING:
    try:
        import tomllib  # type: ignore
    except ImportError:
        import tomli as tomllib  # type: ignore

import tomli_w  # For writing TOML
from pathlib import Path
from typing import Optional, Any
import logging
from dataclasses import asdict

from legion.config.schema import (
    LegionConfig,
    ScanningConfig,
    LoggingConfig,
    ToolsConfig,
    UIConfig,
    DatabaseConfig,
    ProjectConfig,
)
from legion.platform.paths import get_config_dir

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages Legion configuration files."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Custom config file path. If None, uses default user config.
        """
        if config_path is None:
            config_dir = get_config_dir()
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "legion.toml"
        
        self.config_path = Path(config_path)
        self._config: Optional[LegionConfig] = None
    
    def load(self) -> LegionConfig:
        """
        Load configuration from file.
        
        Returns:
            Loaded configuration (or default if file doesn't exist).
        """
        if not self.config_path.exists():
            logger.info(f"Config file not found: {self.config_path}, using defaults")
            self._config = LegionConfig()
            return self._config
        
        try:
            with open(self.config_path, "rb") as f:
                data = tomllib.load(f)
            
            logger.info(f"Loaded config from: {self.config_path}")
            self._config = self._dict_to_config(data)
            self._config.validate()
            return self._config
            
        except tomllib.TOMLDecodeError as e:
            logger.error(f"Invalid TOML in config file: {e}")
            raise ValueError(f"Failed to parse config file: {e}") from e
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def save(self, config: Optional[LegionConfig] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save. If None, saves current loaded config.
        """
        if config is None:
            if self._config is None:
                raise ValueError("No configuration to save")
            config = self._config
        
        # Validate before saving
        config.validate()
        
        # Convert to dict
        data = self._config_to_dict(config)
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write TOML
        try:
            with open(self.config_path, "wb") as f:
                tomli_w.dump(data, f)
            logger.info(f"Saved config to: {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def get(self) -> LegionConfig:
        """
        Get current configuration (loads if not already loaded).
        
        Returns:
            Current configuration.
        """
        if self._config is None:
            return self.load()
        return self._config
    
    def update(self, **kwargs: Any) -> None:
        """
        Update configuration values.
        
        Example:
            manager.update(scanning__timeout=600, logging__level="DEBUG")
        """
        config = self.get()
        
        for key, value in kwargs.items():
            parts = key.split("__")
            if len(parts) != 2:
                raise ValueError(f"Invalid key format: {key} (expected 'section__field')")
            
            section, field = parts
            
            if not hasattr(config, section):
                raise ValueError(f"Invalid section: {section}")
            
            section_obj = getattr(config, section)
            if not hasattr(section_obj, field):
                raise ValueError(f"Invalid field: {section}.{field}")
            
            setattr(section_obj, field, value)
        
        # Validate after update
        config.validate()
        self._config = config
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = LegionConfig()
        logger.info("Configuration reset to defaults")
    
    def _config_to_dict(self, config: LegionConfig) -> dict[str, Any]:
        """Convert LegionConfig to dictionary for TOML."""
        def filter_none(d: dict[str, Any]) -> dict[str, Any]:
            """Remove None values from dict (TOML doesn't support None)."""
            return {k: v for k, v in d.items() if v is not None}
        
        return {
            "scanning": filter_none(asdict(config.scanning)),
            "logging": filter_none(asdict(config.logging)),
            "tools": filter_none(asdict(config.tools)),
            "ui": filter_none(asdict(config.ui)),
            "database": filter_none(asdict(config.database)),
            "project": filter_none(asdict(config.project)),
        }
    
    def _dict_to_config(self, data: dict[str, Any]) -> LegionConfig:
        """Convert TOML dictionary to LegionConfig."""
        return LegionConfig(
            scanning=ScanningConfig(**data.get("scanning", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            tools=ToolsConfig(**data.get("tools", {})),
            ui=UIConfig(**data.get("ui", {})),
            database=DatabaseConfig(**data.get("database", {})),
            project=ProjectConfig(**data.get("project", {})),
        )


# Global config manager instance
_global_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[Path] = None) -> ConfigManager:
    """
    Get global configuration manager instance.
    
    Args:
        config_path: Custom config path (only used on first call).
    
    Returns:
        Global ConfigManager instance.
    """
    global _global_manager
    
    if _global_manager is None:
        _global_manager = ConfigManager(config_path)
    
    return _global_manager


def get_config() -> LegionConfig:
    """
    Get current configuration.
    
    Returns:
        Current LegionConfig instance.
    """
    return get_config_manager().get()


# Demo/Test
if __name__ == "__main__":
    import tempfile
    
    print("Legion Configuration Manager Test")
    print("=" * 60)
    
    # Create temp config file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Test 1: Create and save default config
        print("\n[TEST 1] Create and save default config")
        print("-" * 60)
        manager = ConfigManager(temp_path)
        config = manager.get()
        print(f"Default config: {config}")
        manager.save()
        print(f"[OK] Saved to: {temp_path}")
        
        # Test 2: Load saved config
        print("\n[TEST 2] Load saved config")
        print("-" * 60)
        manager2 = ConfigManager(temp_path)
        loaded = manager2.load()
        print(f"Loaded: {loaded}")
        print("[OK] Config loaded successfully")
        
        # Test 3: Update config
        print("\n[TEST 3] Update config values")
        print("-" * 60)
        manager2.update(
            scanning__timeout=600,
            logging__level="DEBUG",
            ui__theme="dark"
        )
        print(f"Updated timeout: {manager2.get().scanning.timeout}")
        print(f"Updated log level: {manager2.get().logging.level}")
        print(f"Updated theme: {manager2.get().ui.theme}")
        print("[OK] Config updated")
        
        # Test 4: Save updated config
        print("\n[TEST 4] Save updated config")
        print("-" * 60)
        manager2.save()
        
        # Read raw TOML to verify
        with open(temp_path, "r") as f:
            content = f.read()
        print("Saved TOML:")
        print(content[:300])
        print("[OK] Updated config saved")
        
        # Test 5: Global config manager
        print("\n[TEST 5] Global config manager")
        print("-" * 60)
        global_mgr = get_config_manager(temp_path)
        global_cfg = get_config()
        print(f"Global config: {global_cfg}")
        print("[OK] Global manager working")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        
    finally:
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
            print(f"\n[CLEANUP] Removed temp file: {temp_path}")
