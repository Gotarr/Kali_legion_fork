"""
Default configuration values and template generation.
"""

from pathlib import Path
from typing import Optional
import shutil

from legion.config.schema import LegionConfig
from legion.platform.paths import get_config_dir


def get_default_config() -> LegionConfig:
    """
    Get default Legion configuration.
    
    Returns:
        Default LegionConfig instance with sensible defaults.
    """
    return LegionConfig()


def get_template_path() -> Path:
    """
    Get path to the config template file.
    
    Returns:
        Path to template.toml in the legion.config package.
    """
    return Path(__file__).parent / "template.toml"


def create_user_config(target_path: Optional[Path] = None, force: bool = False) -> Path:
    """
    Create user config file from template.
    
    Args:
        target_path: Where to create the config (None = default user config dir).
        force: Overwrite existing config file if True.
    
    Returns:
        Path to created config file.
    
    Raises:
        FileExistsError: If config exists and force=False.
    """
    if target_path is None:
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        target_path = config_dir / "legion.toml"
    
    target_path = Path(target_path)
    
    # Check if already exists
    if target_path.exists() and not force:
        raise FileExistsError(f"Config file already exists: {target_path}")
    
    # Copy template
    template = get_template_path()
    if not template.exists():
        raise FileNotFoundError(f"Template file not found: {template}")
    
    shutil.copy(template, target_path)
    return target_path


def print_template() -> None:
    """Print config template to stdout."""
    template = get_template_path()
    if template.exists():
        print(template.read_text(encoding="utf-8"))
    else:
        print(f"[ERROR] Template not found: {template}")


# Demo/Test
if __name__ == "__main__":
    import tempfile
    
    print("Legion Default Config & Template")
    print("=" * 60)
    
    # Test 1: Get default config
    print("\n[TEST 1] Get default config")
    print("-" * 60)
    config = get_default_config()
    print(f"Default config: {config}")
    print("[OK]")
    
    # Test 2: Get template path
    print("\n[TEST 2] Get template path")
    print("-" * 60)
    template_path = get_template_path()
    print(f"Template path: {template_path}")
    print(f"Exists: {template_path.exists()}")
    if template_path.exists():
        lines = template_path.read_text(encoding="utf-8").splitlines()
        print(f"Lines: {len(lines)}")
        print(f"First line: {lines[0]}")
        print("[OK]")
    else:
        print("[FAIL] Template not found!")
    
    # Test 3: Create user config in temp location
    print("\n[TEST 3] Create user config")
    print("-" * 60)
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config = Path(tmpdir) / "legion.toml"
        created = create_user_config(temp_config)
        print(f"Created: {created}")
        print(f"Exists: {created.exists()}")
        
        # Verify content
        content = created.read_text(encoding="utf-8")
        print(f"Size: {len(content)} bytes")
        print(f"First 100 chars: {content[:100]}")
        print("[OK]")
        
        # Test overwrite protection
        print("\n[TEST 4] Test overwrite protection")
        print("-" * 60)
        try:
            create_user_config(temp_config, force=False)
            print("[FAIL] Should have raised FileExistsError")
        except FileExistsError as e:
            print(f"[OK] Caught expected error: {e}")
        
        # Test force overwrite
        print("\n[TEST 5] Test force overwrite")
        print("-" * 60)
        created2 = create_user_config(temp_config, force=True)
        print(f"Overwritten: {created2}")
        print("[OK]")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All tests passed!")
