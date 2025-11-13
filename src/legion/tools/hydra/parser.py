"""
Hydra output parser for extracting credentials and attack results.

This module parses THC-Hydra text output and extracts:
- Found credentials (login:password pairs)
- Attack statistics (attempts, success rate, duration)
- Error messages and warnings
- Service-specific information

Author: Gotham Security
Date: 2025-11-13
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class HydraCredential:
    """A single discovered credential."""
    
    host: str
    """Target host/IP."""
    
    port: int
    """Target port."""
    
    service: str
    """Service name (ssh, ftp, http-post-form, etc.)."""
    
    login: str
    """Username/login."""
    
    password: str
    """Password."""
    
    def __str__(self) -> str:
        """Human-readable credential string."""
        return f"{self.login}:{self.password} @ {self.service}://{self.host}:{self.port}"


@dataclass
class HydraStatistics:
    """Attack statistics from Hydra run."""
    
    total_attempts: int = 0
    """Total login attempts made."""
    
    successful_attempts: int = 0
    """Number of successful logins."""
    
    duration_seconds: float = 0.0
    """Total attack duration in seconds."""
    
    attempts_per_second: float = 0.0
    """Average attempts per second."""
    
    tasks: int = 0
    """Number of parallel tasks used."""
    
    def __str__(self) -> str:
        """Human-readable statistics."""
        return (
            f"Attempts: {self.successful_attempts}/{self.total_attempts} | "
            f"Speed: {self.attempts_per_second:.1f}/s | "
            f"Duration: {self.duration_seconds:.1f}s"
        )


@dataclass
class HydraResult:
    """Complete Hydra attack result."""
    
    credentials: List[HydraCredential] = field(default_factory=list)
    """List of discovered credentials."""
    
    statistics: HydraStatistics = field(default_factory=HydraStatistics)
    """Attack statistics."""
    
    target: str = ""
    """Target host/IP."""
    
    service: str = ""
    """Target service."""
    
    errors: List[str] = field(default_factory=list)
    """Error messages encountered."""
    
    warnings: List[str] = field(default_factory=list)
    """Warning messages."""
    
    raw_output: str = ""
    """Raw Hydra output."""
    
    @property
    def success(self) -> bool:
        """Check if any credentials were found."""
        return len(self.credentials) > 0
    
    @property
    def credential_count(self) -> int:
        """Number of credentials found."""
        return len(self.credentials)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "credentials": [
                {
                    "host": c.host,
                    "port": c.port,
                    "service": c.service,
                    "login": c.login,
                    "password": c.password,
                }
                for c in self.credentials
            ],
            "statistics": {
                "total_attempts": self.statistics.total_attempts,
                "successful_attempts": self.statistics.successful_attempts,
                "duration_seconds": self.statistics.duration_seconds,
                "attempts_per_second": self.statistics.attempts_per_second,
                "tasks": self.statistics.tasks,
            },
            "target": self.target,
            "service": self.service,
            "errors": self.errors,
            "warnings": self.warnings,
        }
    
    def __str__(self) -> str:
        """Human-readable result summary."""
        if self.success:
            return f"✓ Found {self.credential_count} credential(s) | {self.statistics}"
        else:
            return f"✗ No credentials found | {self.statistics}"


class HydraOutputParser:
    """
    Parser for Hydra text output.
    
    Hydra output format examples:
    
    Success:
        [22][ssh] host: 192.168.1.1   login: admin   password: password123
        [21][ftp] host: 192.168.1.2   login: user   password: pass
    
    Statistics:
        1 of 1 target successfully completed, 2 valid passwords found
        Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2025-11-13 10:30:15
    """
    
    # Regex patterns for parsing
    CREDENTIAL_PATTERN = re.compile(
        r'\[(\d+)\]\[([^\]]+)\]\s+host:\s*(\S+)\s+login:\s*(\S+)\s+password:\s*(.+?)(?:\s*$|\s+\[)'
    )
    
    STATISTICS_PATTERN = re.compile(
        r'(\d+)\s+of\s+(\d+)\s+target[s]?\s+.*completed.*?(\d+)\s+valid\s+password[s]?\s+found'
    )
    
    DURATION_PATTERN = re.compile(
        r'finished\s+at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
    )
    
    STARTED_PATTERN = re.compile(
        r'starting\s+at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
    )
    
    TASKS_PATTERN = re.compile(
        r'\[DATA\].*?max\s+(\d+)\s+tasks'
    )
    
    ATTEMPTS_PATTERN = re.compile(
        r'\[DATA\].*?(\d+)\s+login\s+tries.*?\(l:(\d+)/p:(\d+)\)'
    )
    
    ERROR_PATTERN = re.compile(
        r'\[ERROR\](.+)', re.IGNORECASE
    )
    
    WARNING_PATTERN = re.compile(
        r'\[WARNING\](.+)', re.IGNORECASE
    )
    
    def parse(self, output: str) -> HydraResult:
        """
        Parse Hydra output text.
        
        Args:
            output: Raw Hydra stdout/stderr text.
        
        Returns:
            HydraResult with parsed credentials and statistics.
        
        Example:
            >>> parser = HydraOutputParser()
            >>> result = parser.parse(hydra_output)
            >>> print(f"Found {len(result.credentials)} credentials")
        """
        result = HydraResult(raw_output=output)
        
        lines = output.splitlines()
        
        # Parse credentials
        for line in lines:
            cred = self._parse_credential(line)
            if cred:
                result.credentials.append(cred)
                # Extract target/service from first credential
                if not result.target:
                    result.target = cred.host
                if not result.service:
                    result.service = cred.service
        
        # Parse statistics
        result.statistics = self._parse_statistics(output)
        result.statistics.successful_attempts = len(result.credentials)
        
        # Parse errors and warnings
        for line in lines:
            error = self._parse_error(line)
            if error:
                result.errors.append(error)
            
            warning = self._parse_warning(line)
            if warning:
                result.warnings.append(warning)
        
        return result
    
    def _parse_credential(self, line: str) -> Optional[HydraCredential]:
        """
        Parse a single credential line.
        
        Format: [22][ssh] host: 192.168.1.1   login: admin   password: password123
        """
        match = self.CREDENTIAL_PATTERN.search(line)
        if not match:
            return None
        
        port_str, service, host, login, password = match.groups()
        
        return HydraCredential(
            host=host.strip(),
            port=int(port_str),
            service=service.strip(),
            login=login.strip(),
            password=password.strip(),
        )
    
    def _parse_statistics(self, output: str) -> HydraStatistics:
        """Parse attack statistics from output."""
        stats = HydraStatistics()
        
        # Extract tasks
        tasks_match = self.TASKS_PATTERN.search(output)
        if tasks_match:
            stats.tasks = int(tasks_match.group(1))
        
        # Extract attempts
        attempts_match = self.ATTEMPTS_PATTERN.search(output)
        if attempts_match:
            total_tries = int(attempts_match.group(1))
            logins = int(attempts_match.group(2))
            passwords = int(attempts_match.group(3))
            stats.total_attempts = logins * passwords
        
        # Extract duration
        started_match = self.STARTED_PATTERN.search(output)
        finished_match = self.DURATION_PATTERN.search(output)
        
        if started_match and finished_match:
            from datetime import datetime
            try:
                started = datetime.strptime(started_match.group(1), "%Y-%m-%d %H:%M:%S")
                finished = datetime.strptime(finished_match.group(1), "%Y-%m-%d %H:%M:%S")
                stats.duration_seconds = (finished - started).total_seconds()
                
                # Calculate attempts per second
                if stats.duration_seconds > 0 and stats.total_attempts > 0:
                    stats.attempts_per_second = stats.total_attempts / stats.duration_seconds
            except ValueError:
                pass
        
        # Extract completion statistics
        stats_match = self.STATISTICS_PATTERN.search(output)
        if stats_match:
            completed = int(stats_match.group(1))
            total_targets = int(stats_match.group(2))
            found_passwords = int(stats_match.group(3))
            stats.successful_attempts = found_passwords
        
        return stats
    
    def _parse_error(self, line: str) -> Optional[str]:
        """Parse error message from line."""
        match = self.ERROR_PATTERN.search(line)
        if match:
            return match.group(1).strip()
        return None
    
    def _parse_warning(self, line: str) -> Optional[str]:
        """Parse warning message from line."""
        match = self.WARNING_PATTERN.search(line)
        if match:
            return match.group(1).strip()
        return None


if __name__ == "__main__":
    # Demo / Testing
    sample_output = """
Hydra v9.6 (c) 2023 by van Hauser/THC & David Maciejak - Please do not use in military or secret service organizations, or for illegal purposes (this is non-binding, these *** ignore laws and ethics anyway).

Hydra (https://github.com/vanhauser-thc/thc-hydra) starting at 2025-11-13 10:30:00
[DATA] max 16 tasks per 1 server, overall 16 tasks, 100 login tries (l:10/p:10), ~7 tries per task
[DATA] attacking ssh://192.168.1.1:22/
[22][ssh] host: 192.168.1.1   login: admin   password: admin123
[22][ssh] host: 192.168.1.1   login: root   password: toor
1 of 1 target successfully completed, 2 valid passwords found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2025-11-13 10:30:15
"""
    
    print("Hydra Output Parser Demo")
    print("=" * 80)
    print()
    
    parser = HydraOutputParser()
    result = parser.parse(sample_output)
    
    print(f"Result: {result}")
    print()
    print("Credentials found:")
    for cred in result.credentials:
        print(f"  • {cred}")
    print()
    print(f"Statistics: {result.statistics}")
    print()
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
