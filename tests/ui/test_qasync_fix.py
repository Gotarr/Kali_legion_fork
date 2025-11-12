"""
Fixed Test: Use qasync for Qt + asyncio integration

This is THE FIX for the UI refresh problem!

Problem: asyncio event loop and Qt event loop don't work together
Solution: Use qasync to integrate both event loops
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
import qasync
import asyncio

from legion.ui.mainwindow import MainWindow
from legion.core.database import SimpleDatabase
from legion.core.scanner import ScanManager
from legion.config.manager import ConfigManager

async def main_async():
    """Main async function."""
    print("=" * 70)
    print("FIXED TEST: Qt + asyncio with qasync")
    print("=" * 70)
    print()
    
    # Use fresh database
    db_name = "qasync_test"
    print(f"1. Creating database: {db_name}")
    db = SimpleDatabase(project_name=db_name)
    db._hosts.clear()
    db._ports.clear()
    print(f"   Checksum: Empty database ready")
    print()
    
    # Create scanner
    print("2. Creating scanner...")
    scanner = ScanManager(database=db)
    print(f"   Checksum: Scanner ready")
    print()
    
    # Create config
    config_mgr = ConfigManager()
    
    # Create main window
    print("3. Creating MainWindow...")
    window = MainWindow(
        database=db,
        scanner=scanner,
        config_manager=config_mgr
    )
    
    window.setWindowTitle("Legion UI - qasync Test")
    window.resize(1200, 800)
    window.show()
    print("   Checksum: UI shown")
    print()
    
    # Start scanner (asyncio workers)
    print("4. Starting scanner async workers...")
    await scanner.start()
    print("   Checksum: Scanner started")
    print()
    
    # Queue scan
    print("5. Queueing scan of 127.0.0.1...")
    job_id = await scanner.queue_scan("127.0.0.1", "quick")
    print(f"   Checksum: Scan queued: {job_id}")
    print()
    
    print("=" * 70)
    print("NOW WATCH FOR:")
    print("=" * 70)
    print("  [ScanManager] Scan finished")
    print("  [ScanManager] _notify_completion")
    print("  [MainWindow] _on_scan_completed_callback")
    print("  [MainWindow] _on_scan_completed_ui")
    print("  [MainWindow] refresh_data()")
    print("  [HostsTableModel] Loaded X hosts")
    print("=" * 70)
    print()

def main():
    """Entry point with qasync."""
    app = QApplication(sys.argv)
    
    # Create qasync event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    print("Using qasync event loop - Qt and asyncio integrated!")
    print()
    
    # Run main_async and keep Qt app running
    with loop:
        loop.run_until_complete(main_async())
        loop.run_forever()

if __name__ == "__main__":
    main()
