"""
Service data model.

Represents a service detected on a port with additional metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Service:
    """
    Represents a network service with detailed information.
    
    This is a more detailed representation than Port.service_*,
    used when we have extensive service fingerprinting data.
    
    Attributes:
        name: Service name (http, ssh, mysql, etc.).
        product: Product/software name.
        version: Product version.
        extra_info: Additional information.
        os_type: Operating system type.
        hostname: Hostname from service banner.
        device_type: Device type (router, printer, etc.).
        cpe: Common Platform Enumeration identifier.
        scripts: NSE script results (dict of script_name: output).
        fingerprint: Raw service fingerprint.
        confidence: Detection confidence (0-10).
        method: Detection method.
        discovered_at: Discovery timestamp.
        notes: Additional notes.
    """
    
    name: str
    """Service name."""
    
    product: Optional[str] = None
    """Product/software name."""
    
    version: Optional[str] = None
    """Product version."""
    
    extra_info: Optional[str] = None
    """Additional service information."""
    
    os_type: Optional[str] = None
    """Operating system type."""
    
    hostname: Optional[str] = None
    """Hostname from service banner."""
    
    device_type: Optional[str] = None
    """Device type (router, printer, firewall, etc.)."""
    
    cpe: list[str] = field(default_factory=list)
    """Common Platform Enumeration identifiers."""
    
    scripts: dict[str, str] = field(default_factory=dict)
    """NSE script results (script_name → output)."""
    
    fingerprint: Optional[str] = None
    """Raw service fingerprint."""
    
    confidence: int = 0
    """Detection confidence level (0-10)."""
    
    method: str = "table"
    """Detection method: table, probed, fingerprint."""
    
    discovered_at: datetime = field(default_factory=datetime.now)
    """Discovery timestamp."""
    
    notes: str = ""
    """Additional notes."""
    
    def __str__(self) -> str:
        """Human-readable representation."""
        parts = [self.name]
        
        if self.product:
            parts.append(self.product)
            if self.version:
                parts.append(self.version)
        
        if self.extra_info:
            parts.append(f"({self.extra_info})")
        
        return " ".join(parts)
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"<Service name={self.name} product={self.product} version={self.version}>"
    
    @property
    def full_name(self) -> str:
        """Get full service description."""
        parts = [self.name]
        
        if self.product:
            parts.append(f"({self.product}")
            if self.version:
                parts.append(self.version)
            parts.append(")")
        
        return " ".join(parts)
    
    def add_script_result(self, script_name: str, output: str) -> None:
        """
        Add NSE script result.
        
        Args:
            script_name: Name of the script.
            output: Script output.
        """
        self.scripts[script_name] = output
    
    def get_script_result(self, script_name: str) -> Optional[str]:
        """
        Get NSE script result.
        
        Args:
            script_name: Name of the script.
        
        Returns:
            Script output if available, None otherwise.
        """
        return self.scripts.get(script_name)
    
    def has_script_result(self, script_name: str) -> bool:
        """
        Check if script result exists.
        
        Args:
            script_name: Name of the script.
        
        Returns:
            True if script was run and has output.
        """
        return script_name in self.scripts
