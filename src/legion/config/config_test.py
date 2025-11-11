"""
Integration tests for Legion configuration system.

Tests the complete config workflow:
- Schema validation
- TOML loading/saving
- Default config creation
- Legacy migration
- User config initialization
"""

import tempfile
import shutil
from pathlib import Path

from legion.config import (
    LegionConfig,
    ConfigManager,
    get_default_config,
    create_user_config,
    migrate_legacy_config,
)


def test_schema_validation() -> bool:
    """Test configuration schema and validation."""
    print("\n[TEST] Schema Validation")
    print("-" * 60)
    
    # Test 1: Default config is valid
    config = get_default_config()
    try:
        config.validate()
        print("[PASS] Default config is valid")
    except Exception as e:
        print(f"[FAIL] Default config invalid: {e}")
        return False
    
    # Test 2: Invalid timeout
    config.scanning.timeout = -10
    try:
        config.validate()
        print("[FAIL] Should have caught invalid timeout")
        return False
    except ValueError:
        print("[PASS] Invalid timeout caught")
    
    # Test 3: Invalid scan profile
    config2 = get_default_config()
    config2.scanning.default_profile = "invalid_profile"
    try:
        config2.validate()
        print("[FAIL] Should have caught invalid profile")
        return False
    except ValueError:
        print("[PASS] Invalid profile caught")
    
    return True


def test_config_manager() -> bool:
    """Test configuration manager load/save."""
    print("\n[TEST] Config Manager")
    print("-" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.toml"
        
        # Test 1: Create and save
        manager = ConfigManager(config_path)
        config = manager.get()
        config.scanning.timeout = 999
        config.logging.level = "DEBUG"
        manager.save()
        
        if not config_path.exists():
            print("[FAIL] Config file not created")
            return False
        print("[PASS] Config saved successfully")
        
        # Test 2: Load saved config
        manager2 = ConfigManager(config_path)
        loaded = manager2.load()
        
        if loaded.scanning.timeout != 999:
            print(f"[FAIL] Timeout not saved: {loaded.scanning.timeout}")
            return False
        if loaded.logging.level != "DEBUG":
            print(f"[FAIL] Log level not saved: {loaded.logging.level}")
            return False
        print("[PASS] Config loaded correctly")
        
        # Test 3: Update method
        manager2.update(
            scanning__max_concurrent=10,
            ui__theme="dark"
        )
        
        if manager2.get().scanning.max_concurrent != 10:
            print("[FAIL] Update failed")
            return False
        print("[PASS] Update method works")
        
        # Test 4: Save updated config
        manager2.save()
        manager3 = ConfigManager(config_path)
        reloaded = manager3.load()
        
        if reloaded.scanning.max_concurrent != 10:
            print("[FAIL] Updated value not persisted")
            return False
        print("[PASS] Updated config persisted")
    
    return True


def test_template_creation() -> bool:
    """Test user config template creation."""
    print("\n[TEST] Template Creation")
    print("-" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "legion.toml"
        
        # Test 1: Create from template
        created = create_user_config(config_path)
        
        if not created.exists():
            print("[FAIL] Template not created")
            return False
        print("[PASS] Template created")
        
        # Test 2: Verify content
        content = created.read_text(encoding="utf-8")
        if "Legion Configuration Template" not in content:
            print("[FAIL] Template content invalid")
            return False
        if "[scanning]" not in content:
            print("[FAIL] Missing scanning section")
            return False
        print("[PASS] Template content valid")
        
        # Test 3: Load template as config
        manager = ConfigManager(config_path)
        loaded = manager.load()
        loaded.validate()
        print("[PASS] Template is valid config")
    
    return True


def test_legacy_migration() -> bool:
    """Test legacy config migration."""
    print("\n[TEST] Legacy Migration")
    print("-" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        legacy_path = Path(tmpdir) / "legion.conf"
        
        # Create mock legacy config
        legacy_path.write_text("""[General]
max-fast-processes=7
screenshooter-timeout=800

[BruteSettings]
hydra-path=/custom/hydra
""")
        
        # Migrate
        migrated = migrate_legacy_config(legacy_path)
        
        # Verify migration
        if migrated.scanning.max_concurrent != 7:
            print(f"[FAIL] max_concurrent not migrated: {migrated.scanning.max_concurrent}")
            return False
        if migrated.scanning.timeout != 800:
            print(f"[FAIL] timeout not migrated: {migrated.scanning.timeout}")
            return False
        if migrated.tools.hydra_path != "/custom/hydra":
            print(f"[FAIL] hydra_path not migrated: {migrated.tools.hydra_path}")
            return False
        
        print("[PASS] Legacy config migrated correctly")
    
    return True


def test_full_workflow() -> bool:
    """Test complete configuration workflow."""
    print("\n[TEST] Full Workflow")
    print("-" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "legion.toml"
        
        # Step 1: Create default config
        create_user_config(config_path)
        print("[PASS] Step 1: Created default config")
        
        # Step 2: Load and modify
        manager = ConfigManager(config_path)
        config = manager.load()
        config.scanning.timeout = 777
        config.project.name = "test_project"
        manager.save()
        print("[PASS] Step 2: Modified and saved")
        
        # Step 3: Reload and verify
        manager2 = ConfigManager(config_path)
        reloaded = manager2.load()
        
        if reloaded.scanning.timeout != 777:
            print("[FAIL] Changes not persisted")
            return False
        if reloaded.project.name != "test_project":
            print("[FAIL] Project name not persisted")
            return False
        
        print("[PASS] Step 3: Changes persisted correctly")
        
        # Step 4: Update via manager
        manager2.update(ui__font_size=14)
        manager2.save()
        print("[PASS] Step 4: Updated via manager")
        
        # Step 5: Final verification
        manager3 = ConfigManager(config_path)
        final = manager3.load()
        
        if final.ui.font_size != 14:
            print("[FAIL] Manager update not persisted")
            return False
        if final.scanning.timeout != 777:
            print("[FAIL] Previous changes lost")
            return False
        
        print("[PASS] Step 5: All changes verified")
    
    return True


def run_all_tests() -> bool:
    """Run all integration tests."""
    print("=" * 60)
    print("LEGION CONFIGURATION SYSTEM - INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Schema Validation", test_schema_validation),
        ("Config Manager", test_config_manager),
        ("Template Creation", test_template_creation),
        ("Legacy Migration", test_legacy_migration),
        ("Full Workflow", test_full_workflow),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n[ERROR] Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
