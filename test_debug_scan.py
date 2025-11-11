#!/usr/bin/env python3
"""
Debug scanner integration with extensive logging.
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(name)s: %(message)s'
)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from legion.config.manager import get_config_manager
from legion.core.database import SimpleDatabase
from legion.core.scanner import ScanManager
from legion.ui import MainWindow

def main():
    print("=" * 60)
    print("DEBUG: Scanner Integration Test")
    print("=" * 60)
    
    # Create components
    config_manager = get_config_manager()
    db = SimpleDatabase(project_name="debug_scan")
    scanner = ScanManager(database=db)
    
    print(f"\nDatabase: {len(db.get_all_hosts())} hosts initially")
    
    # Create Qt app
    app = QApplication(sys.argv)
    
    # Create window
    window = MainWindow(
        database=db,
        scanner=scanner,
        config_manager=config_manager
    )
    
    # Add debug hooks
    def debug_progress(job):
        print(f"\n[DEBUG CALLBACK] Progress: {job.target} - {job.status.value}")
    
    def debug_complete(job):
        print(f"\n[DEBUG CALLBACK] Complete: {job.target} - {job.status.value}")
        print(f"  Hosts found: {job.hosts_found}")
        print(f"  Ports found: {job.ports_found}")
        
        # Check database
        hosts = db.get_all_hosts()
        print(f"  Database now has: {len(hosts)} hosts")
        for h in hosts:
            ports = db.get_ports(h.ip)
            print(f"    - {h.ip}: {len(ports)} ports")
    
    scanner.add_progress_callback(debug_progress)
    scanner.add_completion_callback(debug_complete)
    
    print("\n" + "=" * 60)
    print("INSTRUCTIONS:")
    print("1. Hosts table should be empty")
    print("2. Go to: Scan -> New Scan")
    print("3. Target: 127.0.0.1")
    print("4. Click OK")
    print("\nWatch the console output for debug messages!")
    print("=" * 60 + "\n")
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
