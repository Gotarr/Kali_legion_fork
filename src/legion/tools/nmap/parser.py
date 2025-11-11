"""
Nmap XML output parser.

Parses nmap XML output files into structured Host/Port/Service objects.
Supports all common nmap output elements including OS detection, service
versioning, and NSE script results.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from legion.core.models import Host, Port, Service
except ImportError:
    # Standalone testing
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from legion.core.models import Host, Port, Service


@dataclass
class NmapScanResult:
    """
    Complete nmap scan results.
    
    Attributes:
        hosts: List of discovered hosts.
        ports: Dictionary mapping host IP to list of ports.
        scan_info: Scan metadata (command, start time, etc.).
        stats: Scan statistics (total hosts, up hosts, etc.).
        args: Nmap command-line arguments.
        version: Nmap version.
        start_time: Scan start timestamp.
        end_time: Scan end timestamp.
        xml_file: Path to source XML file.
    """
    
    hosts: list[Host] = field(default_factory=list)
    """List of discovered hosts."""
    
    ports: dict[str, list[Port]] = field(default_factory=dict)
    """Port lists by host IP."""
    
    scan_info: dict[str, str] = field(default_factory=dict)
    """Scan metadata."""
    
    stats: dict[str, int] = field(default_factory=dict)
    """Scan statistics."""
    
    args: str = ""
    """Nmap command arguments."""
    
    version: str = ""
    """Nmap version."""
    
    start_time: Optional[datetime] = None
    """Scan start time."""
    
    end_time: Optional[datetime] = None
    """Scan end time."""
    
    xml_file: Optional[Path] = None
    """Source XML file path."""
    
    def __str__(self) -> str:
        """Human-readable representation."""
        total = len(self.hosts)
        up = len([h for h in self.hosts if h.is_up])
        return f"NmapScanResult: {up}/{total} hosts up"
    
    @property
    def up_hosts(self) -> list[Host]:
        """Get list of hosts that are up."""
        return [h for h in self.hosts if h.is_up]
    
    @property
    def duration(self) -> Optional[float]:
        """Get scan duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class NmapXMLParser:
    """
    Parser for nmap XML output files.
    
    Parses XML output from nmap and converts it into structured Python objects.
    
    Example:
        >>> parser = NmapXMLParser()
        >>> result = parser.parse_file("scan.xml")
        >>> for host in result.hosts:
        ...     print(f"{host.ip}: {host.state}")
        ...     for port in host.ports:
        ...         print(f"  {port.number}/{port.protocol}: {port.state}")
    """
    
    def parse_file(self, xml_file: Path | str) -> NmapScanResult:
        """
        Parse nmap XML file.
        
        Args:
            xml_file: Path to XML file.
        
        Returns:
            NmapScanResult with all discovered hosts.
        
        Raises:
            FileNotFoundError: If XML file doesn't exist.
            ET.ParseError: If XML is malformed.
        """
        xml_path = Path(xml_file)
        if not xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {xml_path}")
        
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        result = NmapScanResult(xml_file=xml_path)
        
        # Parse root attributes
        result.args = root.get("args", "")
        result.version = root.get("version", "")
        
        start_str = root.get("start")
        if start_str:
            result.start_time = datetime.fromtimestamp(int(start_str))
        
        # Parse scan info
        scaninfo = root.find("scaninfo")
        if scaninfo is not None:
            result.scan_info = dict(scaninfo.attrib)
        
        # Parse hosts
        for host_elem in root.findall("host"):
            host, ports = self._parse_host(host_elem)
            result.hosts.append(host)
            if ports:
                result.ports[host.ip] = ports
        
        # Parse run stats
        runstats = root.find("runstats")
        if runstats is not None:
            finished = runstats.find("finished")
            if finished is not None:
                end_str = finished.get("time")
                if end_str:
                    result.end_time = datetime.fromtimestamp(int(end_str))
            
            hosts_elem = runstats.find("hosts")
            if hosts_elem is not None:
                result.stats = {
                    "total": int(hosts_elem.get("total", 0)),
                    "up": int(hosts_elem.get("up", 0)),
                    "down": int(hosts_elem.get("down", 0)),
                }
        
        return result
    
    def parse_string(self, xml_string: str) -> NmapScanResult:
        """
        Parse nmap XML from string.
        
        Args:
            xml_string: XML content as string.
        
        Returns:
            NmapScanResult with all discovered hosts.
        
        Raises:
            ET.ParseError: If XML is malformed.
        """
        root = ET.fromstring(xml_string)
        
        result = NmapScanResult()
        result.args = root.get("args", "")
        result.version = root.get("version", "")
        
        # Parse hosts
        for host_elem in root.findall("host"):
            host, ports = self._parse_host(host_elem)
            result.hosts.append(host)
            if ports:
                result.ports[host.ip] = ports
        
        return result
    
    def _parse_host(self, host_elem: ET.Element) -> tuple[Host, list[Port]]:
        """
        Parse host element.
        
        Args:
            host_elem: XML host element.
        
        Returns:
            Tuple of (Host object, list of Port objects).
        """
        host = Host(ip="")
        
        # Parse status
        status = host_elem.find("status")
        if status is not None:
            host.state = status.get("state", "unknown")
            host.reason = status.get("reason")
        
        # Parse addresses
        for addr_elem in host_elem.findall("address"):
            addr_type = addr_elem.get("addrtype")
            addr = addr_elem.get("addr")
            
            if addr_type == "ipv4" or addr_type == "ipv6":
                host.ip = addr or ""
            elif addr_type == "mac":
                host.mac_address = addr
                host.vendor = addr_elem.get("vendor")
        
        # Parse hostnames
        hostnames_elem = host_elem.find("hostnames")
        if hostnames_elem is not None:
            hostname_elem = hostnames_elem.find("hostname")
            if hostname_elem is not None:
                host.hostname = hostname_elem.get("name")
        
        # Parse OS detection
        os_elem = host_elem.find("os")
        if os_elem is not None:
            osmatch = os_elem.find("osmatch")
            if osmatch is not None:
                host.os_name = osmatch.get("name")
                accuracy_str = osmatch.get("accuracy")
                if accuracy_str:
                    host.os_accuracy = int(accuracy_str)
                
                # Get OS class for family
                osclass = osmatch.find("osclass")
                if osclass is not None:
                    host.os_family = osclass.get("osfamily")
        
        # Parse distance
        distance_elem = host_elem.find("distance")
        if distance_elem is not None:
            value_str = distance_elem.get("value")
            if value_str:
                host.distance = int(value_str)
        
        # Parse uptime
        uptime_elem = host_elem.find("uptime")
        if uptime_elem is not None:
            seconds_str = uptime_elem.get("seconds")
            if seconds_str:
                host.uptime = int(seconds_str)
                # Calculate last boot
                if host.discovered_at:
                    from datetime import timedelta
                    host.last_boot = host.discovered_at - timedelta(seconds=host.uptime)
        
        # Parse ports (link to host)
        ports_elem = host_elem.find("ports")
        if ports_elem is not None:
            ports = self._parse_ports(ports_elem)
            return host, ports
        
        return host, []
    
    def _parse_ports(self, ports_elem: ET.Element) -> list[Port]:
        """
        Parse ports element.
        
        Args:
            ports_elem: XML ports element.
        
        Returns:
            List of Port objects.
        """
        ports = []
        
        for port_elem in ports_elem.findall("port"):
            port = self._parse_port(port_elem)
            ports.append(port)
        
        return ports
    
    def _parse_port(self, port_elem: ET.Element) -> Port:
        """
        Parse port element.
        
        Args:
            port_elem: XML port element.
        
        Returns:
            Port object.
        """
        port_num = int(port_elem.get("portid", "0"))
        protocol = port_elem.get("protocol", "tcp")
        
        port = Port(number=port_num, protocol=protocol)
        
        # Parse state
        state_elem = port_elem.find("state")
        if state_elem is not None:
            port.state = state_elem.get("state", "unknown")
            port.reason = state_elem.get("reason")
        
        # Parse service
        service_elem = port_elem.find("service")
        if service_elem is not None:
            port.service_name = service_elem.get("name")
            port.service_product = service_elem.get("product")
            port.service_version = service_elem.get("version")
            port.service_info = service_elem.get("extrainfo")
            port.service_os_type = service_elem.get("ostype")
            port.service_hostname = service_elem.get("hostname")
            port.service_method = service_elem.get("method", "table")
            
            conf_str = service_elem.get("conf")
            if conf_str:
                port.confidence = int(conf_str)
        
        # Parse scripts (NSE)
        for script_elem in port_elem.findall("script"):
            script_id = script_elem.get("id", "")
            script_output = script_elem.get("output", "")
            if script_id and script_output:
                port.notes += f"\n[{script_id}]\n{script_output}\n"
        
        return port
    
    def parse_host_from_xml(self, xml_file: Path | str, target_ip: str) -> Optional[Host]:
        """
        Parse specific host from XML file.
        
        Args:
            xml_file: Path to XML file.
            target_ip: IP address to find.
        
        Returns:
            Host object if found, None otherwise.
        """
        result = self.parse_file(xml_file)
        
        for host in result.hosts:
            if host.ip == target_ip:
                return host
        
        return None


if __name__ == "__main__":
    # Demo / Testing
    print("Nmap XML Parser")
    print("=" * 60)
    
    # Create sample XML for testing
    sample_xml = """<?xml version="1.0"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -sV 192.168.1.1" start="1699718400" version="7.94">
<scaninfo type="syn" protocol="tcp" numservices="1000" services="1-1000"/>
<host>
    <status state="up" reason="echo-reply"/>
    <address addr="192.168.1.1" addrtype="ipv4"/>
    <address addr="AA:BB:CC:DD:EE:FF" addrtype="mac" vendor="Cisco"/>
    <hostnames>
        <hostname name="router.local" type="PTR"/>
    </hostnames>
    <ports>
        <port protocol="tcp" portid="22">
            <state state="open" reason="syn-ack"/>
            <service name="ssh" product="OpenSSH" version="8.2p1" method="probed" conf="10"/>
        </port>
        <port protocol="tcp" portid="80">
            <state state="open" reason="syn-ack"/>
            <service name="http" product="Apache httpd" version="2.4.41" method="probed" conf="10"/>
        </port>
    </ports>
    <os>
        <osmatch name="Linux 3.2 - 4.9" accuracy="95">
            <osclass type="general purpose" vendor="Linux" osfamily="Linux" accuracy="95"/>
        </osmatch>
    </os>
    <distance value="1"/>
    <uptime seconds="864000"/>
</host>
<runstats>
    <finished time="1699718500"/>
    <hosts up="1" down="0" total="1"/>
</runstats>
</nmaprun>"""
    
    parser = NmapXMLParser()
    result = parser.parse_string(sample_xml)
    
    print(f"Scan Result: {result}")
    print(f"Nmap Version: {result.version}")
    print(f"Arguments: {result.args}")
    print()
    
    print(f"Hosts Found: {len(result.hosts)}")
    print("-" * 60)
    
    for host in result.hosts:
        print(f"\nHost: {host}")
        print(f"  IP: {host.ip}")
        print(f"  Hostname: {host.hostname}")
        print(f"  MAC: {host.mac_address} ({host.vendor})")
        print(f"  State: {host.state} ({host.reason})")
        print(f"  OS: {host.os_name} ({host.os_accuracy}% accuracy)")
        print(f"  OS Family: {host.os_family}")
        print(f"  Distance: {host.distance} hops")
        print(f"  Uptime: {host.uptime} seconds")
        if host.last_boot:
            print(f"  Last Boot: {host.last_boot}")
    
    print("\n" + "=" * 60)
    print("Parser test completed successfully!")
