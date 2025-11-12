"""
Legion Feature Test Checklist

Run this after any major changes to verify functionality.

Author: Gotham Security
Date: 2025-11-12
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

print("=" * 60)
print("LEGION FEATURE TEST")
print("=" * 60)
print()

# Test 1: Imports
print("[1/7] Testing imports...")
try:
    from legion.ui.app import main
    from legion.core.database import SimpleDatabase
    from legion.core.scanner import ScanManager
    from legion.config import get_config, ConfigManager
    from legion.ui.mainwindow import MainWindow
    from legion.ui.models import HostsTableModel, PortsTableModel
    from legion.ui.dialogs import NewScanDialog, AboutDialog
    from legion.ui.settings import SettingsDialog
    print("      ✅ All imports successful")
except Exception as e:
    print(f"      ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Config
print("\n[2/7] Testing config system...")
try:
    config_manager = ConfigManager()
    config = config_manager.load()
    print(f"      ✅ Config loaded from: {config_manager.config_path}")
    print(f"      Theme: {config.ui.theme}")
    print(f"      Font: {config.ui.font_size}pt")
except Exception as e:
    print(f"      ❌ Config failed: {e}")
    sys.exit(1)

# Test 3: Database
print("\n[3/7] Testing database...")
try:
    db = SimpleDatabase()
    hosts = db.get_all_hosts()
    print(f"      ✅ Database initialized")
    print(f"      Hosts in DB: {len(hosts)}")
except Exception as e:
    print(f"      ❌ Database failed: {e}")
    sys.exit(1)

# Test 4: Scanner
print("\n[4/7] Testing scanner...")
try:
    import asyncio
    scanner = ScanManager()
    print(f"      ✅ Scanner initialized")
    print(f"      Max workers: {scanner.max_workers}")
except Exception as e:
    print(f"      ❌ Scanner failed: {e}")
    sys.exit(1)

# Test 5: Qt Models
print("\n[5/7] Testing Qt models...")
try:
    hosts_model = HostsTableModel(db)
    ports_model = PortsTableModel(db)
    print(f"      ✅ Models initialized")
    print(f"      Hosts model rows: {hosts_model.rowCount()}")
except Exception as e:
    print(f"      ❌ Models failed: {e}")
    sys.exit(1)

# Test 6: File Structure
print("\n[6/7] Testing file structure...")
try:
    required_files = [
        project_root / "legion.py",
        project_root / "src" / "legion" / "ui" / "app.py",
        project_root / "src" / "legion" / "ui" / "mainwindow.py",
        project_root / "src" / "legion" / "ui" / "settings.py",
        project_root / "src" / "legion" / "core" / "database.py",
        project_root / "src" / "legion" / "core" / "scanner.py",
        project_root / "src" / "legion" / "config" / "manager.py",
    ]
    
    missing = []
    for file_path in required_files:
        if not file_path.exists():
            missing.append(file_path)
    
    if missing:
        print(f"      ❌ Missing files:")
        for f in missing:
            print(f"         - {f}")
        sys.exit(1)
    else:
        print(f"      ✅ All required files present ({len(required_files)} files)")
except Exception as e:
    print(f"      ❌ File check failed: {e}")
    sys.exit(1)

# Test 7: Legacy cleanup
print("\n[7/7] Testing legacy cleanup...")
try:
    old_files = [
        project_root / "app",
        project_root / "ui",
        project_root / "controller",
        project_root / "db",
    ]
    
    found_legacy = []
    for old_path in old_files:
        if old_path.exists():
            found_legacy.append(old_path)
    
    if found_legacy:
        print(f"      ⚠️  Legacy files still present (should be in _old/):")
        for f in found_legacy:
            print(f"         - {f}")
    else:
        print(f"      ✅ Legacy files archived")
        
    # Check _old exists
    old_dir = project_root / "_old"
    if old_dir.exists():
        print(f"      ✅ Archive directory exists: _old/")
    else:
        print(f"      ⚠️  No archive directory (_old/ not found)")
        
except Exception as e:
    print(f"      ❌ Legacy check failed: {e}")

print()
print("=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print()
print("Legion is ready to use:")
print("  py legion.py")
print()
