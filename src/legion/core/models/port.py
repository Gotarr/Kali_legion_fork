"""
Port data model.

Represents a network port on a host.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Port:
    """
    Represents a network port on a host.
    
    Attributes:
        number: Port number (1-65535).
        protocol: Protocol (tcp, udp, sctp).
        state: Port state (open, closed, filtered, etc.).
        reason: Reason for state determination.
        service_name: Service name (http, ssh, etc.).
        service_product: Product name (Apache, OpenSSH, etc.).
        service_version: Product version.
        service_info: Additional service info.
        service_os_type: OS type from service detection.
        service_hostname: Hostname from service.
        service_method: Detection method (probed, table).
        confidence: Detection confidence (0-10).
        discovered_at: When this port was first discovered.
        last_seen: When this port was last seen.
        notes: Additional notes.
    """
    
    number: int
    """Port number (1-65535)."""
    
    protocol: str = "tcp"
    """Protocol: tcp, udp, sctp."""
    
    state: str = "unknown"
    """Port state: open, closed, filtered, unfiltered, open|filtered, closed|filtered."""
    
    reason: Optional[str] = None
    """Reason for state: syn-ack, reset, etc."""
    
    service_name: Optional[str] = None
    """Service name (http, ssh, ftp, etc.)."""
    
    service_product: Optional[str] = None
    """Product/software name (Apache httpd, OpenSSH, etc.)."""
    
    service_version: Optional[str] = None
    """Product version."""
    
    service_info: Optional[str] = None
    """Additional service information."""
    
    service_os_type: Optional[str] = None
    """OS type from service banner."""
    
    service_hostname: Optional[str] = None
    """Hostname from service."""
    
    service_method: str = "table"
    """Detection method: table, probed."""
    
    confidence: int = 0
    """Service detection confidence (0-10)."""
    
    discovered_at: datetime = field(default_factory=datetime.now)
    """First discovery timestamp."""
    
    last_seen: datetime = field(default_factory=datetime.now)
    """Last seen timestamp."""
    
    notes: str = ""
    """Additional notes."""
    
    def __str__(self) -> str:
        """Human-readable representation."""
        parts = [f"{self.number}/{self.protocol}"]
        
        if self.state:
            parts.append(self.state)
        
        if self.service_name:
            service_info = self.service_name
            if self.service_product:
                service_info += f" ({self.service_product}"
                if self.service_version:
                    service_info += f" {self.service_version}"
                service_info += ")"
            parts.append(service_info)
        
        return " ".join(parts)
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"<Port {self.number}/{self.protocol} state={self.state} service={self.service_name}>"
    
    @property
    def is_open(self) -> bool:
        """Check if port is open."""
        return self.state.lower() == "open"
    
    @property
    def is_closed(self) -> bool:
        """Check if port is closed."""
        return self.state.lower() == "closed"
    
    @property
    def is_filtered(self) -> bool:
        """Check if port is filtered."""
        return "filtered" in self.state.lower()
    
    @property
    def full_service_name(self) -> str:
        """Get full service description."""
        if not self.service_name:
            return "unknown"
        
        parts = [self.service_name]
        
        if self.service_product:
            parts.append(self.service_product)
            if self.service_version:
                parts.append(self.service_version)
        
        return " ".join(parts)
    
    def update_last_seen(self) -> None:
        """Update last seen timestamp to now."""
        self.last_seen = datetime.now()
