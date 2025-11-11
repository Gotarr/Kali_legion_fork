#!/usr/bin/env python3
"""
Test script for MainWindow with sample data.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from legion.config.manager import get_config_manager
from legion.core.database import SimpleDatabase
from legion.core.models import Host, Port
from legion.core.scanner import ScanManager
from legion.ui import MainWindow


def create_sample_data(db: SimpleDatabase) -> None:
    """Create sample hosts and ports for testing."""
    print("Creating sample data...")
    
    # Sample hosts
    hosts = [
        Host(ip="192.168.1.1", hostname="router.local", state="up", 
             os_name="Linux 3.x"),
        Host(ip="192.168.1.10", hostname="web-server", state="up",
             os_name="Ubuntu 20.04", os_family="Linux"),
        Host(ip="192.168.1.20", hostname="db-server", state="up",
             os_name="Windows Server 2019", os_family="Windows"),
        Host(ip="192.168.1.50", hostname="workstation", state="down",
             os_name="Windows 10", os_family="Windows"),
        Host(ip="192.168.1.100", hostname="nas.local", state="up",
             os_name="FreeNAS"),
    ]
    
    for host in hosts:
        db.save_host(host)
    
    # Ports for router
    router_ports = [
        Port(number=22, protocol="tcp", state="open", 
             service_name="ssh", service_product="OpenSSH", service_version="8.2p1"),
        Port(number=53, protocol="udp", state="open",
             service_name="domain", service_product="dnsmasq"),
        Port(number=80, protocol="tcp", state="open",
             service_name="http", service_product="lighttpd", service_version="1.4.55"),
    ]
    for port in router_ports:
        db.save_port("192.168.1.1", port)
    
    # Ports for web-server
    web_ports = [
        Port(number=22, protocol="tcp", state="open",
             service_name="ssh", service_product="OpenSSH", service_version="8.2p1"),
        Port(number=80, protocol="tcp", state="open",
             service_name="http", service_product="Apache", service_version="2.4.41"),
        Port(number=443, protocol="tcp", state="open",
             service_name="https", service_product="Apache", service_version="2.4.41"),
        Port(number=3306, protocol="tcp", state="open",
             service_name="mysql", service_product="MySQL", service_version="8.0.23"),
    ]
    for port in web_ports:
        db.save_port("192.168.1.10", port)
    
    # Ports for db-server
    db_ports = [
        Port(number=3389, protocol="tcp", state="open",
             service_name="ms-wbt-server", service_product="Microsoft RDP"),
        Port(number=1433, protocol="tcp", state="open",
             service_name="ms-sql-s", service_product="Microsoft SQL Server", service_version="2019"),
        Port(number=445, protocol="tcp", state="open",
             service_name="microsoft-ds", service_product="SMB"),
    ]
    for port in db_ports:
        db.save_port("192.168.1.20", port)
    
    # Ports for NAS
    nas_ports = [
        Port(number=21, protocol="tcp", state="open",
             service_name="ftp", service_product="vsftpd"),
        Port(number=139, protocol="tcp", state="open",
             service_name="netbios-ssn", service_product="Samba"),
        Port(number=445, protocol="tcp", state="open",
             service_name="microsoft-ds", service_product="Samba", service_version="4.13"),
        Port(number=80, protocol="tcp", state="open",
             service_name="http", service_product="nginx", service_version="1.18.0"),
    ]
    for port in nas_ports:
        db.save_port("192.168.1.100", port)
    
    print(f"[OK] Created {len(hosts)} hosts with various ports")


def main():
    """Run the MainWindow with sample data."""
    print("=" * 60)
    print("Legion MainWindow Test")
    print("=" * 60)
    
    # Initialize config
    print("\n[1/5] Initializing config...")
    config_manager = get_config_manager()
    config = config_manager.get()
    print(f"      Config loaded from: {config_manager.config_path}")
    
    # Create database with sample data
    print("\n[2/5] Creating database...")
    db = SimpleDatabase(project_name="test_ui")
    
    # Only create sample data if database is empty
    existing_hosts = db.get_all_hosts()
    if len(existing_hosts) == 0:
        print("      Database is empty - creating sample data...")
        create_sample_data(db)
        print(f"      [OK] Created {len(db.get_all_hosts())} sample hosts")
    else:
        print(f"      Database already has {len(existing_hosts)} hosts - keeping them")
    
    print(f"      Database ready with {len(db.get_all_hosts())} hosts")
    
    # Create scanner (needs database)
    print("\n[3/5] Creating scanner...")
    scanner = ScanManager(database=db)
    print("      ScanManager ready")
    
    # Create Qt application
    print("\n[4/5] Creating Qt application...")
    app = QApplication(sys.argv)
    print("      QApplication created")
    
    # Create main window
    print("\n[5/5] Creating MainWindow...")
    window = MainWindow(
        database=db,
        scanner=scanner,
        config_manager=config_manager
    )
    
    print("\n" + "=" * 60)
    print("UI FEATURES:")
    print("  - Hosts table: 5 hosts with different states")
    print("  - Click a host to see its ports/services")
    print("  - Color coding: Green = up, Red = down")
    print("  - Tooltips: Hover over IP addresses")
    print("  - Auto-refresh: Every 10 seconds")
    print("=" * 60)
    
    print("\nShowing window...")
    window.show()
    window.raise_()  # Bring to front
    window.activateWindow()
    
    print("Window displayed! Check your screen.")
    print("Close the window to exit.\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
