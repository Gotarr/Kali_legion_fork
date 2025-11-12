"""
Simple JSON-based database for storing scan results.

This is a lightweight alternative to SQLAlchemy for Phase 3,
storing data as JSON files. Can be replaced with SQLAlchemy later.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    from legion.core.models import Host, Port, Service
    from legion.platform.paths import get_data_dir
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from legion.core.models import Host, Port, Service
    from legion.platform.paths import get_data_dir


def _datetime_serializer(obj: Any) -> Any:
    """JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class SimpleDatabase:
    """
    Simple JSON-based database for scan results.
    
    Stores hosts, ports, and services in JSON files for easy inspection
    and portability. Good for Phase 3 development and testing.
    
    Example:
        >>> db = SimpleDatabase("project1")
        >>> host = Host(ip="192.168.1.1", hostname="router")
        >>> db.save_host(host)
        >>> 
        >>> hosts = db.get_all_hosts()
        >>> for host in hosts:
        ...     print(host.ip)
    """
    
    def __init__(self, project_name: str = "default"):
        """
        Initialize database for a project.
        
        Args:
            project_name: Project name (creates subfolder).
        """
        self.project_name = project_name
        self.base_dir = get_data_dir() / "projects" / project_name
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.hosts_file = self.base_dir / "hosts.json"
        self.ports_file = self.base_dir / "ports.json"
        self.services_file = self.base_dir / "services.json"
        
        # In-memory cache
        self._hosts: dict[str, dict] = {}
        self._ports: dict[str, list[dict]] = {}  # Key: host_ip
        self._services: dict[str, dict] = {}
        
        # Load existing data
        self._load()
    
    def _load(self) -> None:
        """Load data from JSON files."""
        if self.hosts_file.exists():
            with open(self.hosts_file, 'r') as f:
                self._hosts = json.load(f)
        
        if self.ports_file.exists():
            with open(self.ports_file, 'r') as f:
                self._ports = json.load(f)
        
        if self.services_file.exists():
            with open(self.services_file, 'r') as f:
                self._services = json.load(f)
    
    def _save(self) -> None:
        """Save data to JSON files."""
        with open(self.hosts_file, 'w') as f:
            json.dump(self._hosts, f, indent=2, default=_datetime_serializer)
        
        with open(self.ports_file, 'w') as f:
            json.dump(self._ports, f, indent=2, default=_datetime_serializer)
        
        with open(self.services_file, 'w') as f:
            json.dump(self._services, f, indent=2, default=_datetime_serializer)
    
    def save_host(self, host: Host) -> None:
        """
        Save or update a host.
        
        Args:
            host: Host object to save.
        """
        host_dict = {
            "ip": host.ip,
            "hostname": host.hostname,
            "mac_address": host.mac_address,
            "vendor": host.vendor,
            "os_name": host.os_name,
            "os_family": host.os_family,
            "os_accuracy": host.os_accuracy,
            "state": host.state,
            "reason": host.reason,
            "distance": host.distance,
            "uptime": host.uptime,
            "last_boot": host.last_boot.isoformat() if host.last_boot else None,
            "discovered_at": host.discovered_at.isoformat() if host.discovered_at else None,
            "last_seen": host.last_seen.isoformat() if host.last_seen else None,
            "notes": host.notes,
        }
        
        self._hosts[host.ip] = host_dict
        self._save()
    
    def save_port(self, host_ip: str, port: Port) -> None:
        """
        Save or update a port for a host.
        
        Args:
            host_ip: IP address of the host.
            port: Port object to save.
        """
        # Check if port exists and track state changes
        port_key = f"{port.number}/{port.protocol}"
        if host_ip in self._ports:
            for existing_port in self._ports[host_ip]:
                if f"{existing_port['number']}/{existing_port['protocol']}" == port_key:
                    # Port exists - track state change
                    old_state = existing_port.get('state')
                    if old_state and old_state != port.state:
                        port.previous_state = old_state
                    break
        
        port_dict = {
            "number": port.number,
            "protocol": port.protocol,
            "state": port.state,
            "reason": port.reason,
            "service_name": port.service_name,
            "service_product": port.service_product,
            "service_version": port.service_version,
            "service_info": port.service_info,
            "service_os_type": port.service_os_type,
            "service_hostname": port.service_hostname,
            "service_method": port.service_method,
            "confidence": port.confidence,
            "discovered_at": port.discovered_at.isoformat() if port.discovered_at else None,
            "last_seen": port.last_seen.isoformat() if port.last_seen else None,
            "previous_state": port.previous_state,
            "notes": port.notes,
        }
        
        if host_ip not in self._ports:
            self._ports[host_ip] = []
        
        # Update existing or append new
        port_key = f"{port.number}/{port.protocol}"
        existing_idx = None
        for i, p in enumerate(self._ports[host_ip]):
            if f"{p['number']}/{p['protocol']}" == port_key:
                existing_idx = i
                break
        
        if existing_idx is not None:
            self._ports[host_ip][existing_idx] = port_dict
        else:
            self._ports[host_ip].append(port_dict)
        
        self._save()
    
    def get_host(self, ip: str) -> Optional[Host]:
        """
        Get host by IP address.
        
        Args:
            ip: IP address.
        
        Returns:
            Host object if found, None otherwise.
        """
        if ip not in self._hosts:
            return None
        
        data = self._hosts[ip]
        
        # Reconstruct Host object
        host = Host(
            ip=data["ip"],
            hostname=data.get("hostname"),
            mac_address=data.get("mac_address"),
            vendor=data.get("vendor"),
            os_name=data.get("os_name"),
            os_family=data.get("os_family"),
            os_accuracy=data.get("os_accuracy", 0),
            state=data.get("state", "unknown"),
            reason=data.get("reason"),
            distance=data.get("distance", 0),
            uptime=data.get("uptime"),
            notes=data.get("notes", ""),
        )
        
        # Parse datetime fields
        if data.get("last_boot"):
            host.last_boot = datetime.fromisoformat(data["last_boot"])
        if data.get("discovered_at"):
            host.discovered_at = datetime.fromisoformat(data["discovered_at"])
        if data.get("last_seen"):
            host.last_seen = datetime.fromisoformat(data["last_seen"])
        
        return host
    
    def get_all_hosts(self) -> list[Host]:
        """
        Get all hosts.
        
        Returns:
            List of all Host objects.
        """
        return [self.get_host(ip) for ip in self._hosts.keys()]
    
    def delete_host(self, ip: str) -> bool:
        """
        Delete a host and all associated ports/services.
        
        Args:
            ip: IP address of the host to delete.
        
        Returns:
            True if host was deleted, False if not found.
        """
        if ip not in self._hosts:
            return False
        
        # Delete host
        del self._hosts[ip]
        
        # Delete associated ports
        if ip in self._ports:
            del self._ports[ip]
        
        # Delete associated services
        services_to_delete = [
            svc_id for svc_id, svc in self._services.items()
            if svc.get("host_ip") == ip
        ]
        for svc_id in services_to_delete:
            del self._services[svc_id]
        
        # Save to disk
        self._save()
        
        return True
    
    def get_ports(self, host_ip: str) -> list[Port]:
        """
        Get all ports for a host.
        
        Args:
            host_ip: IP address of the host.
        
        Returns:
            List of Port objects.
        """
        if host_ip not in self._ports:
            return []
        
        ports = []
        for data in self._ports[host_ip]:
            port = Port(
                number=data["number"],
                protocol=data.get("protocol", "tcp"),
                state=data.get("state", "unknown"),
                reason=data.get("reason"),
                service_name=data.get("service_name"),
                service_product=data.get("service_product"),
                service_version=data.get("service_version"),
                service_info=data.get("service_info"),
                service_os_type=data.get("service_os_type"),
                service_hostname=data.get("service_hostname"),
                service_method=data.get("service_method", "table"),
                confidence=data.get("confidence", 0),
                previous_state=data.get("previous_state"),
                notes=data.get("notes", ""),
            )
            
            # Parse datetime fields
            if data.get("discovered_at"):
                port.discovered_at = datetime.fromisoformat(data["discovered_at"])
            if data.get("last_seen"):
                port.last_seen = datetime.fromisoformat(data["last_seen"])
            
            ports.append(port)
        
        return ports
    
    def get_open_ports(self, host_ip: str) -> list[Port]:
        """
        Get only open ports for a host.
        
        Args:
            host_ip: IP address of the host.
        
        Returns:
            List of open Port objects.
        """
        all_ports = self.get_ports(host_ip)
        return [p for p in all_ports if p.is_open]
    
    def get_up_hosts(self) -> list[Host]:
        """
        Get all hosts that are up.
        
        Returns:
            List of hosts with state='up'.
        """
        all_hosts = self.get_all_hosts()
        return [h for h in all_hosts if h.is_up]
    
    def get_stats(self) -> dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with counts of hosts, ports, etc.
        """
        total_hosts = len(self._hosts)
        up_hosts = len(self.get_up_hosts())
        total_ports = sum(len(ports) for ports in self._ports.values())
        
        return {
            "total_hosts": total_hosts,
            "up_hosts": up_hosts,
            "down_hosts": total_hosts - up_hosts,
            "total_ports": total_ports,
        }
    
    def find_hosts_by_service(self, service_name: str) -> list[Host]:
        """
        Find all hosts running a specific service.
        
        Args:
            service_name: Service name to search for (e.g., "ssh", "http").
        
        Returns:
            List of hosts with matching service.
        """
        matching_hosts = []
        
        for host_ip, ports in self._ports.items():
            for port_data in ports:
                if port_data.get("service_name", "").lower() == service_name.lower():
                    host = self.get_host(host_ip)
                    if host and host not in matching_hosts:
                        matching_hosts.append(host)
                    break
        
        return matching_hosts
    
    def clear(self) -> None:
        """Clear all data from database."""
        self._hosts.clear()
        self._ports.clear()
        self._services.clear()
        self._save()
    
    def __str__(self) -> str:
        """Human-readable representation."""
        stats = self.get_stats()
        return f"SimpleDatabase({self.project_name}): {stats['total_hosts']} hosts, {stats['total_ports']} ports"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"<SimpleDatabase project={self.project_name} dir={self.base_dir}>"


if __name__ == "__main__":
    # Demo / Testing
    print("Simple Database System")
    print("=" * 60)
    
    # Create test database
    db = SimpleDatabase("test_project")
    print(f"Database: {db}")
    print(f"Location: {db.base_dir}")
    print()
    
    # Clear any existing data
    db.clear()
    
    # Create test host
    host = Host(
        ip="192.168.1.1",
        hostname="router.local",
        mac_address="AA:BB:CC:DD:EE:FF",
        vendor="Cisco",
        os_name="Linux 3.2",
        os_family="Linux",
        os_accuracy=95,
        state="up",
        reason="echo-reply",
        distance=1,
    )
    
    print("Saving host...")
    db.save_host(host)
    
    # Create test ports
    ports = [
        Port(number=22, protocol="tcp", state="open", service_name="ssh", 
             service_product="OpenSSH", service_version="8.2p1"),
        Port(number=80, protocol="tcp", state="open", service_name="http",
             service_product="Apache", service_version="2.4"),
        Port(number=443, protocol="tcp", state="closed"),
    ]
    
    print("Saving ports...")
    for port in ports:
        db.save_port(host.ip, port)
    
    # Retrieve and display
    print("\n" + "=" * 60)
    print("Database Contents:")
    print("-" * 60)
    
    all_hosts = db.get_all_hosts()
    print(f"Hosts: {len(all_hosts)}")
    for h in all_hosts:
        print(f"  {h}")
        
        host_ports = db.get_ports(h.ip)
        print(f"  Ports: {len(host_ports)}")
        for p in host_ports:
            print(f"    {p}")
    
    print("\n" + "-" * 60)
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 60)
    print(f"Files created:")
    print(f"  {db.hosts_file}")
    print(f"  {db.ports_file}")
    print(f"  {db.services_file}")
