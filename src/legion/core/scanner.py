"""
Scanner orchestration and management.

This module provides the ScanManager class for orchestrating multiple
concurrent scans, managing scan queues, tracking progress, and coordinating
results storage.

Author: Gotham Security
Date: 2025-11-11
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Callable, Any
from uuid import uuid4

from legion.tools.nmap.wrapper import NmapTool
from legion.tools.nmap.parser import NmapXMLParser
from legion.core.database import SimpleDatabase
from legion.core.models.host import Host
from legion.core.models.port import Port

logger = logging.getLogger(__name__)


class ScanStatus(Enum):
    """Status of a scan job."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScanJob:
    """Represents a single scan job."""
    
    id: str
    target: str
    scan_type: str  # "quick", "full", "stealth", etc.
    options: Dict[str, Any] = field(default_factory=dict)
    status: ScanStatus = ScanStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result_file: Optional[Path] = None
    hosts_found: int = 0
    ports_found: int = 0
    
    @property
    def duration(self) -> Optional[float]:
        """Get scan duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_complete(self) -> bool:
        """Check if scan is complete (success or failure)."""
        return self.status in (ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED)


class ScanManager:
    """
    Manages scan operations and coordinates between tools, parsers, and database.
    
    Features:
    - Async scan queue management
    - Progress tracking and callbacks
    - Automatic result parsing and storage
    - Configurable concurrency limits
    """
    
    def __init__(
        self,
        database: SimpleDatabase,
        max_concurrent_scans: int = 3,
        result_dir: Optional[Path] = None
    ):
        """
        Initialize scan manager.
        
        Args:
            database: Database for storing scan results
            max_concurrent_scans: Maximum number of concurrent scans
            result_dir: Directory for storing scan output files
        """
        self.database = database
        self.max_concurrent_scans = max_concurrent_scans
        self.result_dir = result_dir or Path.cwd() / "scan_results"
        self.result_dir.mkdir(parents=True, exist_ok=True)
        
        # Scan log directory
        self.log_dir = Path.cwd() / "scan_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Scan tracking
        self._jobs: Dict[str, ScanJob] = {}
        self._queue: asyncio.Queue[ScanJob] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrent_scans)
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._running_tasks: Dict[str, asyncio.Task] = {}  # job_id -> task for cancellation
        
        # Tools
        self._nmap = NmapTool()
        self._parser = NmapXMLParser()
        
        # Callbacks
        self._progress_callbacks: List[Callable[[ScanJob], None]] = []
        self._completion_callbacks: List[Callable[[ScanJob], None]] = []
    
    def add_progress_callback(self, callback: Callable[[ScanJob], None]) -> None:
        """Add callback for scan progress updates."""
        self._progress_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable[[ScanJob], None]) -> None:
        """Add callback for scan completion."""
        self._completion_callbacks.append(callback)
    
    def _notify_progress(self, job: ScanJob) -> None:
        """Notify all progress callbacks."""
        for callback in self._progress_callbacks:
            try:
                callback(job)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    def _notify_completion(self, job: ScanJob) -> None:
        """Notify all completion callbacks."""
        logger.debug(f"Notifying {len(self._completion_callbacks)} completion callbacks for job {job.id}")
        for callback in self._completion_callbacks:
            try:
                callback(job)
            except Exception as e:
                logger.error(f"Error in completion callback: {e}")
    
    async def queue_scan(
        self,
        target: str,
        scan_type: str = "quick",
        **options: Any
    ) -> str:
        """
        Queue a new scan job.
        
        Args:
            target: Target IP, hostname, or CIDR range
            scan_type: Type of scan ("quick", "full", "stealth", etc.)
            **options: Additional scan options
        
        Returns:
            Job ID for tracking
        """
        job = ScanJob(
            id=str(uuid4()),
            target=target,
            scan_type=scan_type,
            options=options
        )
        
        self._jobs[job.id] = job
        await self._queue.put(job)
        self._notify_progress(job)
        
        # Log scan queued event
        self._log_scan_event(job, "queued")
        
        return job.id
    
    def get_job(self, job_id: str) -> Optional[ScanJob]:
        """Get scan job by ID."""
        return self._jobs.get(job_id)
    
    def get_all_jobs(self) -> List[ScanJob]:
        """Get all scan jobs."""
        return list(self._jobs.values())
    
    def get_active_jobs(self) -> List[ScanJob]:
        """Get currently running jobs."""
        return [job for job in self._jobs.values() if job.status == ScanStatus.RUNNING]
    
    def get_pending_jobs(self) -> List[ScanJob]:
        """Get queued jobs."""
        return [job for job in self._jobs.values() if job.status == ScanStatus.QUEUED]
    
    async def _process_scan_result(self, job: ScanJob, xml_path: Path) -> None:
        """
        Parse scan results and store in database.
        
        Args:
            job: Scan job
            xml_path: Path to XML result file
        """
        try:
            # Parse XML
            result = self._parser.parse_file(xml_path)
            
            # Store hosts and ports
            for host in result.hosts:
                self.database.save_host(host)
                job.hosts_found += 1
                
                # Get ports for this host from the ports dict
                host_ports = result.ports.get(host.ip, [])
                for port in host_ports:
                    self.database.save_port(host.ip, port)
                    job.ports_found += 1
            
            job.result_file = xml_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to process scan results: {e}")
    
    async def _execute_scan(self, job: ScanJob) -> None:
        """
        Execute a single scan job.
        
        Args:
            job: Scan job to execute
        """
        async with self._semaphore:
            try:
                # Check if already cancelled before starting
                if job.status == ScanStatus.CANCELLED:
                    logger.debug(f"Job {job.id} was cancelled before execution")
                    return
                
                # Update job status
                job.status = ScanStatus.RUNNING
                job.started_at = datetime.now()
                self._notify_progress(job)
                
                # Log scan started event
                self._log_scan_event(job, "started")
                
                # Prepare output file
                output_file = self.result_dir / f"{job.id}.xml"
                
                # Build nmap arguments based on scan type
                args = self._build_scan_args(job.scan_type, job.target, job.options)
                logger.debug(f"Starting nmap with args: {args}")
                args.extend(["-oX", str(output_file)])
                
                # Store current task for cancellation
                current_task = asyncio.current_task()
                if current_task:
                    self._running_tasks[job.id] = current_task
                
                try:
                    # Execute scan (args as list, not *args)
                    result = await self._nmap.run(args)
                    
                    # Check if cancelled during execution
                    if job.status == ScanStatus.CANCELLED:
                        logger.info(f"Scan {job.id} was cancelled during execution")
                        return
                    
                    if not result.success:
                        raise RuntimeError(f"Scan failed: {result.stderr}")
                    
                    # Process results
                    await self._process_scan_result(job, output_file)
                    
                    # Mark complete
                    job.status = ScanStatus.COMPLETED
                    job.completed_at = datetime.now()
                finally:
                    # Remove from running tasks
                    self._running_tasks.pop(job.id, None)
                
            except asyncio.CancelledError:
                # Task was cancelled
                job.status = ScanStatus.CANCELLED
                job.completed_at = datetime.now()
                job.error = "Scan cancelled by user"
                logger.info(f"Scan {job.id} cancelled")
                raise  # Re-raise to let asyncio handle it
            except Exception as e:
                job.status = ScanStatus.FAILED
                job.completed_at = datetime.now()
                job.error = str(e)
            
            finally:
                logger.info(f"Scan finished: {job.id} - {job.status.value}")
                self._notify_progress(job)
                self._notify_completion(job)
                
                # Log scan finished event (completed, failed, or cancelled)
                self._log_scan_event(job, "finished")
    
    def _build_scan_args(
        self,
        scan_type: str,
        target: str,
        options: Dict[str, Any]
    ) -> List[str]:
        """
        Build nmap arguments based on scan type.
        
        Args:
            scan_type: Type of scan
            target: Target to scan
            options: Additional options
        
        Returns:
            List of nmap arguments
        """
        # Base arguments for different scan types
        scan_profiles = {
            "quick": ["-T4", "-F"],  # Fast scan, top 100 ports
            "full": ["-T4", "-p-"],  # All ports
            "stealth": ["-sS", "-T2"],  # SYN scan, slower
            "version": ["-sV"],  # Service version detection
            "os": ["-O"],  # OS detection
            "aggressive": ["-A", "-T4"],  # Aggressive scan
        }
        
        args = scan_profiles.get(scan_type, ["-T4"])
        
        # Add custom options
        if "ports" in options:
            args.extend(["-p", options["ports"]])
        if options.get("version_detection"):
            args.append("-sV")
        if "timing" in options:
            args.append(f"-T{options['timing']}")
        if "scripts" in options:
            args.extend(["--script", options["scripts"]])
        
        # Add target
        args.append(target)
        
        return args
    
    async def _worker(self) -> None:
        """Worker coroutine for processing scan queue."""
        while self._running:
            try:
                # Get next job with timeout to allow checking _running flag
                job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                
                # Check if job was cancelled while in queue
                if job.status == ScanStatus.CANCELLED:
                    logger.debug(f"Skipping cancelled job: {job.target}")
                    self._queue.task_done()
                    continue
                
                await self._execute_scan(job)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                # Worker cancelled, exit gracefully
                break
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
    
    async def start(self, num_workers: Optional[int] = None) -> None:
        """
        Start scan workers.
        
        Args:
            num_workers: Number of worker tasks (defaults to max_concurrent_scans)
        """
        if self._running:
            return
        
        self._running = True
        num_workers = num_workers or self.max_concurrent_scans
        
        # Start worker tasks
        for _ in range(num_workers):
            worker = asyncio.create_task(self._worker())
            self._workers.append(worker)
    
    async def stop(self, wait: bool = True) -> None:
        """
        Stop scan workers.
        
        Args:
            wait: Wait for current scans to complete
        """
        self._running = False
        
        if wait:
            # Wait for queue to empty
            await self._queue.join()
        
        # Cancel workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
    
    async def wait_for_completion(self) -> None:
        """Wait for all queued scans to complete."""
        await self._queue.join()
    
    def cancel_scan(self, target: str) -> bool:
        """
        Cancel a specific scan by target.
        
        Args:
            target: Target IP/hostname to cancel
            
        Returns:
            True if scan was cancelled, False if not found or already completed
        """
        # Find job for this target
        for job in self._jobs.values():
            if job.target == target and not job.is_complete:
                if job.status == ScanStatus.QUEUED:
                    # Mark as cancelled (worker will skip it)
                    job.status = ScanStatus.CANCELLED
                    job.completed_at = datetime.now()
                    self._log_scan_event(job, "cancelled")
                    logger.info(f"Cancelled queued scan: {job.target}")
                    return True
                elif job.status == ScanStatus.RUNNING:
                    # Mark as cancelled and try to cancel the task
                    job.status = ScanStatus.CANCELLED
                    job.completed_at = datetime.now()
                    
                    # Kill the running nmap process immediately
                    killed = self._nmap.kill_current_process()
                    if killed:
                        logger.info(f"Killed nmap process for scan: {job.target}")
                    
                    # Try to cancel the running task
                    task = self._running_tasks.get(job.id)
                    if task and not task.done():
                        task.cancel()
                        logger.info(f"Cancelled running scan: {job.target}")
                    
                    self._log_scan_event(job, "cancelled")
                    return True
        return False
    
    def cancel_all_scans(self) -> int:
        """
        Cancel all pending and running scans.
        
        Returns:
            Number of scans cancelled
        """
        # First, kill the current nmap process if any
        self._nmap.kill_current_process()
        
        count = 0
        for job in list(self._jobs.values()):
            if not job.is_complete:
                job.status = ScanStatus.CANCELLED
                job.completed_at = datetime.now()
                
                # Try to cancel running task
                if job.id in self._running_tasks:
                    task = self._running_tasks[job.id]
                    if not task.done():
                        task.cancel()
                
                self._log_scan_event(job, "cancelled")
                count += 1
                logger.info(f"Cancelled scan: {job.target}")
        
        return count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scan statistics."""
        jobs = list(self._jobs.values())
        
        return {
            "total_jobs": len(jobs),
            "queued": sum(1 for j in jobs if j.status == ScanStatus.QUEUED),
            "running": sum(1 for j in jobs if j.status == ScanStatus.RUNNING),
            "completed": sum(1 for j in jobs if j.status == ScanStatus.COMPLETED),
            "failed": sum(1 for j in jobs if j.status == ScanStatus.FAILED),
            "cancelled": sum(1 for j in jobs if j.status == ScanStatus.CANCELLED),
            "total_hosts": sum(j.hosts_found for j in jobs),
            "total_ports": sum(j.ports_found for j in jobs),
        }
    
    def _log_scan_event(self, job: ScanJob, event: str) -> None:
        """
        Log scan event to JSON file.
        
        Args:
            job: Scan job
            event: Event type (queued, started, finished, cancelled)
        """
        try:
            log_file = self.log_dir / f"{job.id}.json"
            
            # Convert job to dict
            job_dict = {
                "id": job.id,
                "target": job.target,
                "scan_type": job.scan_type,
                "options": job.options,
                "status": job.status.value,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error": job.error,
                "hosts_found": job.hosts_found,
                "ports_found": job.ports_found,
                "duration": job.duration,
                "event": event,
                "timestamp": datetime.now().isoformat()
            }
            
            # Append to log file (each line is a JSON event - JSONL format)
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(job_dict) + '\n')
                
            logger.debug(f"Logged {event} event for scan {job.id}")
                
        except Exception as e:
            logger.error(f"Failed to log scan event: {e}")


# Demo/Test code
if __name__ == "__main__":
    import tempfile
    
    def progress_callback(job: ScanJob) -> None:
        """Progress update callback."""
        print(f"[{job.status.value.upper()}] {job.target} (ID: {job.id[:8]})")
        if job.status == ScanStatus.COMPLETED:
            print(f"  → Found {job.hosts_found} hosts, {job.ports_found} ports")
            print(f"  → Duration: {job.duration:.2f}s")
        elif job.status == ScanStatus.FAILED:
            print(f"  → Error: {job.error}")
    
    async def main():
        print("Scanner Manager Test")
        print("=" * 60)
        
        # Create temp database
        with tempfile.TemporaryDirectory() as tmpdir:
            db = SimpleDatabase(project_name="scanner_test")
            
            # Create scanner
            scanner = ScanManager(
                database=db,
                max_concurrent_scans=2,
                result_dir=Path(tmpdir) / "scans"
            )
            
            # Add callback
            scanner.add_progress_callback(progress_callback)
            scanner.add_completion_callback(
                lambda job: print(f"Scan {job.id[:8]} completed!\n")
            )
            
            # Start workers
            await scanner.start()
            
            print("\nQueuing scans (mock mode - will fail without nmap)...\n")
            
            # Queue some scans
            job1 = await scanner.queue_scan("192.168.1.1", "quick")
            job2 = await scanner.queue_scan("192.168.1.0/24", "full", ports="22,80,443")
            job3 = await scanner.queue_scan("scanme.nmap.org", "version")
            
            print(f"Queued 3 scans:")
            print(f"  - {job1[:8]}: 192.168.1.1 (quick)")
            print(f"  - {job2[:8]}: 192.168.1.0/24 (full)")
            print(f"  - {job3[:8]}: scanme.nmap.org (version)")
            print()
            
            # Wait for completion (will fail quickly without nmap)
            await asyncio.sleep(2)
            
            # Stop scanner
            await scanner.stop(wait=False)
            
            # Show statistics
            print("\n" + "=" * 60)
            print("Statistics:")
            stats = scanner.get_statistics()
            for key, value in stats.items():
                print(f"  {key}: {value}")
            
            print("\n" + "=" * 60)
            print("Note: Scans will fail without nmap installed.")
            print("This test demonstrates the queue/worker architecture.")
    
    asyncio.run(main())
