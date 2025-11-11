"""
Host data model.

Represents a discovered host (IP/hostname) with its properties.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Host:
    """
    Represents a network host discovered during scanning.
    
    Attributes:
        ip: IP address of the host.
        hostname: DNS hostname (if resolved).
        mac_address: MAC address (if available).
        vendor: Network card vendor (from MAC).
        os_name: Operating system name.
        os_family: OS family (Linux, Windows, etc.).
        os_accuracy: OS detection accuracy (0-100).
        state: Host state (up, down, unknown).
        reason: Reason for state determination.
        distance: Network distance (hops).
        uptime: System uptime in seconds.
        last_boot: Last boot timestamp.
        discovered_at: When this host was first discovered.
        last_seen: When this host was last seen.
        ports: List of open/closed ports (set externally).
        notes: Additional notes about the host.
    """
    
    ip: str
    """IP address (IPv4 or IPv6)."""
    
    hostname: Optional[str] = None
    """DNS hostname."""
    
    mac_address: Optional[str] = None
    """MAC address (format: XX:XX:XX:XX:XX:XX)."""
    
    vendor: Optional[str] = None
    """Network interface vendor."""
    
    os_name: Optional[str] = None
    """Operating system name."""
    
    os_family: Optional[str] = None
    """OS family (Windows, Linux, Unix, etc.)."""
    
    os_accuracy: int = 0
    """OS detection accuracy percentage (0-100)."""
    
    state: str = "unknown"
    """Host state: up, down, unknown."""
    
    reason: Optional[str] = None
    """Reason for state (echo-reply, reset, etc.)."""
    
    distance: int = 0
    """Network distance in hops."""
    
    uptime: Optional[int] = None
    """System uptime in seconds."""
    
    last_boot: Optional[datetime] = None
    """Estimated last boot time."""
    
    discovered_at: datetime = field(default_factory=datetime.now)
    """First discovery timestamp."""
    
    last_seen: datetime = field(default_factory=datetime.now)
    """Last seen timestamp."""
    
    notes: str = ""
    """Additional notes."""
    
    def __str__(self) -> str:
        """Human-readable representation."""
        parts = [self.ip]
        if self.hostname:
            parts.append(f"({self.hostname})")
        if self.os_name:
            parts.append(f"- {self.os_name}")
        return " ".join(parts)
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"<Host ip={self.ip} hostname={self.hostname} state={self.state}>"
    
    @property
    def is_up(self) -> bool:
        """Check if host is up."""
        return self.state.lower() == "up"
    
    @property
    def display_name(self) -> str:
        """Get display name (hostname or IP)."""
        return self.hostname if self.hostname else self.ip
    
    def update_last_seen(self) -> None:
        """Update last seen timestamp to now."""
        self.last_seen = datetime.now()
