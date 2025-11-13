"""
Credential data model.

Represents discovered credentials from brute force attacks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Credential:
    """
    Represents a discovered credential (username/password).
    
    Attributes:
        host: Target host IP/hostname.
        port: Target port number.
        service: Service type (ssh, ftp, http, etc.).
        username: Login/username.
        password: Password.
        source: Discovery source (hydra, manual, etc.).
        discovered_at: When this credential was discovered.
        verified: Whether credential has been verified.
        notes: Additional notes.
    """
    
    host: str
    """Target host (IP or hostname)."""
    
    port: int
    """Target port number."""
    
    service: str
    """Service type (ssh, ftp, http-post-form, etc.)."""
    
    username: str
    """Login/username."""
    
    password: str
    """Password."""
    
    source: str = "unknown"
    """Discovery source (hydra, nikto, manual, etc.)."""
    
    discovered_at: datetime = field(default_factory=datetime.now)
    """Discovery timestamp."""
    
    verified: bool = True
    """Whether credential has been verified to work."""
    
    notes: str = ""
    """Additional notes."""
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.username}:{self.password} @ {self.service}://{self.host}:{self.port}"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"<Credential {self.username}@{self.host}:{self.port}/{self.service} "
            f"source={self.source}>"
        )
    
    @property
    def target(self) -> str:
        """Get full target string."""
        return f"{self.service}://{self.host}:{self.port}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "host": self.host,
            "port": self.port,
            "service": self.service,
            "username": self.username,
            "password": self.password,
            "source": self.source,
            "discovered_at": self.discovered_at.isoformat(),
            "verified": self.verified,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Credential":
        """Create Credential from dictionary."""
        # Convert ISO timestamp back to datetime
        if isinstance(data.get("discovered_at"), str):
            data["discovered_at"] = datetime.fromisoformat(data["discovered_at"])
        
        return cls(**data)
