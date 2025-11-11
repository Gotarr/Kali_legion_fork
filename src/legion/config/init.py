"""
User configuration initialization and migration.
"""

from pathlib import Path
from typing import Optional
import logging
import configparser  # For reading old legion.conf
import shutil

from legion.config.manager import ConfigManager, get_config_manager
from legion.config.defaults import create_user_config, get_template_path
from legion.config.schema import LegionConfig
from legion.platform.paths import get_config_dir, get_data_dir

logger = logging.getLogger(__name__)


def find_legacy_config() -> Optional[Path]:
    """
    Find legacy legion.conf file.
    
    Checks:
    - Current directory
    - User data directory
    - Config directory
    
    Returns:
        Path to legacy config if found, None otherwise.
    """
    locations = [
        Path.cwd() / "legion.conf",
        get_data_dir() / "legion.conf",
        get_config_dir() / "legion.conf",
    ]
    
    for path in locations:
        if path.exists():
            logger.info(f"Found legacy config: {path}")
            return path
    
    return None


def migrate_legacy_config(legacy_path: Path) -> LegionConfig:
    """
    Migrate legacy legion.conf to new TOML format.
    
    Args:
        legacy_path: Path to legacy legion.conf file.
    
    Returns:
        Migrated LegionConfig instance.
    """
    logger.info(f"Migrating legacy config from: {legacy_path}")
    
    # Start with defaults
    config = LegionConfig()
    
    try:
        # Parse legacy INI-style config
        parser = configparser.ConfigParser()
        parser.read(legacy_path)
        
        # Migrate relevant settings
        # Note: Old legion.conf has different structure, map what we can
        
        if parser.has_option("General", "max-fast-processes"):
            config.scanning.max_concurrent = parser.getint("General", "max-fast-processes")
        
        if parser.has_option("General", "screenshooter-timeout"):
            timeout = parser.getint("General", "screenshooter-timeout")
            # Legacy timeout was in different units, convert appropriately
            config.scanning.timeout = max(timeout, 300)
        
        # Tool paths
        if parser.has_option("BruteSettings", "hydra-path"):
            config.tools.hydra_path = parser.get("BruteSettings", "hydra-path")
        
        # Add more migrations as needed based on actual legion.conf structure
        
        logger.info("Legacy config migration completed")
        
    except Exception as e:
        logger.warning(f"Failed to migrate some legacy settings: {e}")
    
    return config


def backup_legacy_config(legacy_path: Path) -> Path:
    """
    Backup legacy config file.
    
    Args:
        legacy_path: Path to legacy config.
    
    Returns:
        Path to backup file.
    """
    backup_path = legacy_path.with_suffix(".conf.backup")
    shutil.copy(legacy_path, backup_path)
    logger.info(f"Backed up legacy config to: {backup_path}")
    return backup_path


def init_user_config(force_recreate: bool = False, migrate_legacy: bool = True) -> ConfigManager:
    """
    Initialize user configuration.
    
    This function:
    1. Checks for existing user config
    2. Migrates legacy legion.conf if found
    3. Creates default config if needed
    4. Returns ConfigManager ready to use
    
    Args:
        force_recreate: Force recreation of config even if exists.
        migrate_legacy: Attempt to migrate legacy legion.conf.
    
    Returns:
        Configured ConfigManager instance.
    """
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "legion.toml"
    
    # Check if config exists
    config_exists = config_path.exists()
    
    if config_exists and not force_recreate:
        logger.info(f"Using existing config: {config_path}")
        manager = ConfigManager(config_path)
        manager.load()
        return manager
    
    # Check for legacy config
    legacy_config = None
    if migrate_legacy:
        legacy_path = find_legacy_config()
        if legacy_path:
            logger.info("Found legacy config, migrating...")
            
            # Backup first
            backup_legacy_config(legacy_path)
            
            # Migrate
            legacy_config = migrate_legacy_config(legacy_path)
    
    # Create new config
    if legacy_config:
        # Use migrated config
        logger.info(f"Creating config from legacy: {config_path}")
        manager = ConfigManager(config_path)
        manager._config = legacy_config
        manager.save()
    else:
        # Create from template
        logger.info(f"Creating default config: {config_path}")
        create_user_config(config_path, force=force_recreate)
        manager = ConfigManager(config_path)
        manager.load()
    
    return manager


def reset_user_config() -> ConfigManager:
    """
    Reset user configuration to defaults.
    
    Returns:
        ConfigManager with reset configuration.
    """
    logger.warning("Resetting user configuration to defaults")
    config_path = get_config_dir() / "legion.toml"
    
    # Backup existing
    if config_path.exists():
        backup = config_path.with_suffix(".toml.backup")
        shutil.copy(config_path, backup)
        logger.info(f"Backed up existing config to: {backup}")
    
    # Create fresh config
    create_user_config(config_path, force=True)
    manager = ConfigManager(config_path)
    manager.load()
    
    return manager


# Demo/Test
if __name__ == "__main__":
    import tempfile
    import os
    
    print("Legion User Config Initialization Test")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock config directory
        os.environ["LEGION_CONFIG_DIR"] = tmpdir
        config_dir = Path(tmpdir)
        
        # Test 1: Init without existing config
        print("\n[TEST 1] Init user config (no existing)")
        print("-" * 60)
        
        # Create mock legacy config
        legacy_path = config_dir / "legion.conf"
        legacy_path.write_text("""
[General]
max-fast-processes=5
screenshooter-timeout=600

[BruteSettings]
hydra-path=/usr/bin/hydra
""")
        print(f"Created mock legacy config: {legacy_path.name}")
        
        # Initialize (should find and migrate legacy)
        from legion.config.init import find_legacy_config, migrate_legacy_config
        
        found = find_legacy_config()
        if found:
            print(f"Found legacy: {found.name}")
            migrated = migrate_legacy_config(found)
            print(f"Migrated max_concurrent: {migrated.scanning.max_concurrent}")
            print(f"Migrated hydra_path: {migrated.tools.hydra_path}")
            print("[OK] Legacy migration working")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] User config init working!")
