"""Test real nmap scan integration."""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from legion.core.database import SimpleDatabase
from legion.core.scanner import ScanManager

print("=" * 60)
print("NMAP SCAN TEST")
print("=" * 60)

async def test_scan():
    # Create database
    db = SimpleDatabase(project_name="scan_test")
    
    # Create scanner
    scanner = ScanManager(database=db, max_concurrent_scans=1)
    
    # Progress callback
    def on_progress(job):
        print(f"[PROGRESS] {job.target}: {job.status.value}")
    
    # Completion callback
    def on_complete(job):
        print(f"[COMPLETE] {job.target}: {job.status.value}")
        if job.status.value == "completed":
            print(f"  Found: {job.hosts_found} hosts, {job.ports_found} ports")
        elif job.status.value == "failed":
            print(f"  Error: {job.error}")
    
    scanner.add_progress_callback(on_progress)
    scanner.add_completion_callback(on_complete)
    
    # Queue a localhost scan (safe and fast)
    print("\n[1] Queuing scan of localhost...")
    job_id = await scanner.queue_scan("127.0.0.1", "quick")
    print(f"    Job ID: {job_id}")
    
    # Start scanner
    print("\n[2] Starting scanner...")
    await scanner.start()
    
    # Wait a bit for scan to complete
    print("\n[3] Waiting for scan to complete...")
    await asyncio.sleep(10)
    
    # Check results
    print("\n[4] Checking results...")
    hosts = db.get_all_hosts()
    print(f"    Hosts in database: {len(hosts)}")
    
    for host in hosts:
        ports = db.get_ports(host.ip)
        print(f"    - {host.ip}: {len(ports)} ports")
    
    # Stop scanner
    print("\n[5] Stopping scanner...")
    await scanner.stop()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_scan())
