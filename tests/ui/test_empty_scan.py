#!/usr/bin/env python3
"""
Test MainWindow with EMPTY database for real scanning.

Uses qasync for proper Qt + asyncio integration.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
import qasync

from legion.config.manager import get_config_manager
from legion.core.database import SimpleDatabase
from legion.core.scanner import ScanManager
from legion.ui import MainWindow


def main():
    """Run the MainWindow with empty database for real scans."""
    print("=" * 60)
    print("Legion MainWindow - Real Scanning Test")
    print("=" * 60)
    
    # Initialize config
    print("\n[1/4] Initializing config...")
    config_manager = get_config_manager()
    config = config_manager.get()
    print(f"      Config loaded from: {config_manager.config_path}")
    
    # Create EMPTY database
    print("\n[2/4] Creating EMPTY database...")
    db = SimpleDatabase(project_name="scan_test_empty")
    
    # Clear any existing data
    for host in db.get_all_hosts():
        # SimpleDatabase doesn't have delete, so we start fresh
        pass
    
    print(f"      Database ready: {len(db.get_all_hosts())} hosts (should be 0)")
    
    # Create scanner (needs database)
    print("\n[3/4] Creating scanner...")
    scanner = ScanManager(database=db)
    print("      ScanManager ready")
    
    # Create Qt application with qasync
    print("\n[4/4] Creating Qt application...")
    app = QApplication(sys.argv)
    
    # Setup qasync event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    print("      QApplication created with qasync event loop")
    
    # Start scanner workers
    async def start_scanner():
        await scanner.start()
    
    loop.run_until_complete(start_scanner())
    print("      Scanner workers started")
    
    # Create main window
    print("\nCreating MainWindow...")
    window = MainWindow(
        database=db,
        scanner=scanner,
        config_manager=config_manager
    )
    
    print("\n" + "=" * 60)
    print("REAL SCANNING TEST (with qasync)")
    print("=" * 60)
    print("\n1. The hosts table should be EMPTY initially")
    print("2. Go to: Scan -> New Scan")
    print("3. Enter target: 127.0.0.1 or 192.168.x.x")
    print("4. Select: Quick Scan")
    print("5. Click OK")
    print("\nAfter scan:")
    print("  - Watch status bar for progress")
    print("  - When complete, host should appear in hosts table")
    print("  - Click on it to see discovered ports")
    print("  - Scanner callbacks now work properly!")
    print("\n" + "=" * 60)
    
    window.show()
    window.raise_()
    window.activateWindow()
    
    print("\nWindow displayed! Start scanning.")
    
    # Run with qasync event loop
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
