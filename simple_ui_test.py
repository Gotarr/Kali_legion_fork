"""Simplified UI test to debug issues."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 60)
print("SIMPLE UI TEST")
print("=" * 60)

try:
    print("\n[1] Importing PyQt6...")
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
    from PyQt6.QtCore import Qt
    print("    OK")
    
    print("\n[2] Importing Legion modules...")
    from legion.config.manager import get_config_manager
    from legion.core.database import SimpleDatabase  
    from legion.core.scanner import ScanManager
    from legion.core.models import Host
    print("    OK")
    
    print("\n[3] Creating QApplication...")
    app = QApplication(sys.argv)
    print("    OK")
    
    print("\n[4] Creating test database...")
    db = SimpleDatabase(project_name="simple_test")
    db.save_host(Host(ip="192.168.1.1", hostname="test", state="up"))
    print(f"    OK - {len(db.get_all_hosts())} host(s)")
    
    print("\n[5] Creating ScanManager...")
    scanner = ScanManager(database=db)
    print("    OK")
    
    print("\n[6] Creating ConfigManager...")
    config_mgr = get_config_manager()
    print("    OK")
    
    print("\n[7] Importing MainWindow...")
    from legion.ui import MainWindow
    print("    OK")
    
    print("\n[8] Creating MainWindow instance...")
    window = MainWindow(
        database=db,
        scanner=scanner,
        config_manager=config_mgr
    )
    print("    OK")
    
    print("\n[9] Showing window...")
    window.setWindowTitle("Legion UI Test - SIMPLE")
    window.resize(1200, 800)
    window.show()
    window.raise_()
    print("    OK - Window should be visible!")
    
    print("\n" + "=" * 60)
    print("SUCCESS! Check for the Legion window.")
    print("Close the window to exit.")
    print("=" * 60 + "\n")
    
    sys.exit(app.exec())
    
except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
