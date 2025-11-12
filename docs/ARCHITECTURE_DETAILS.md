# Legion v2.0 - Architektur Details

Detaillierte Beschreibung der implementierten Features in Phase 1-4.

---

## 🚀 Phase 1: Platform Foundation

### 1️⃣ Platform Detection (`src/legion/platform/detector.py`)
```python
from legion.platform import detect_platform

info = detect_platform()
print(info)  # Windows 10 on x86_64 - Python 3.11.0

# Properties:
info.is_windows    # True/False
info.is_linux      # True/False  
info.is_wsl        # Windows Subsystem for Linux?
info.is_admin      # Running with privileges?
```

**Funktioniert auf**:
- ✅ Windows 10/11
- ✅ Linux (Ubuntu, Kali, Fedora, Debian, Arch, etc.)
- ✅ WSL (Windows Subsystem for Linux)

---

### 2️⃣ Path Management (`src/legion/platform/paths.py`)
```python
from legion.platform.paths import (
    get_data_dir,
    get_config_dir,
    get_log_dir,
    get_temp_dir,
    get_projects_dir,
)

# OS-spezifische Pfade automatisch:
data = get_data_dir()
# Windows: C:\Users\User\AppData\Local\GothamSecurity\legion
# Linux:   ~/.local/share/legion
```

**Features**:
- ✅ Automatische Verzeichnis-Erstellung
- ✅ Path Traversal Protection
- ✅ Plattformgerechte Locations
- ✅ Fallback wenn platformdirs nicht installiert

---

### 3️⃣ Privilege Management (`src/legion/platform/privileges.py`)
```python
from legion.platform.privileges import (
    is_admin,
    require_admin,
    request_elevation,
    check_raw_socket_capability,
)

# Admin-Check (plattformunabhängig)
if not is_admin():
    print("Brauche Admin-Rechte!")
    request_elevation()  # UAC auf Windows, sudo-Info auf Unix

# Raw Socket Check (wichtig für nmap)
if check_raw_socket_capability():
    print("Kann nmap verwenden!")
```

**Features**:
- ✅ Windows: UAC Elevation
- ✅ Linux: sudo Instructions
- ✅ Raw Socket Detection
- ✅ Detaillierter Privilege-Status

---

## 🚀 Phase 2: Tool Discovery System

### 4️⃣ Base Tool Class (`src/legion/tools/base.py`)
```python
from legion.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    @property
    def tool_name(self) -> str:
        return "mytool"
    
    async def parse_output(self, result: ToolResult) -> Any:
        # Parse tool output
        return parsed_data

# Usage
tool = MyTool("/path/to/tool")
result = await tool.run(["--arg1", "value"])
if result.success:
    print(result.stdout)
```

**Features**:
- ✅ Abstrakte Basisklasse für alle Tools
- ✅ Async Tool-Ausführung (nicht-blockierend)
- ✅ ToolResult mit exit_code, stdout, stderr
- ✅ Automatische Version-Detection
- ✅ Validation & Error Handling

---

### 5️⃣ Tool Discovery (`src/legion/tools/discovery.py`)
```python
from legion.tools.discovery import find_tool, discover_all_tools

# Find single tool
nmap_path = find_tool("nmap")
# Windows: C:\Program Files\Nmap\nmap.exe
# Linux:   /usr/bin/nmap

# Discover all common tools
tools = discover_all_tools()
for name, path in tools.items():
    print(f"{name}: {path}")
```

**Suchstrategie**:
1. ✅ Custom Paths (user-konfiguriert)
2. ✅ System PATH (shutil.which)
3. ✅ Common Locations (OS-spezifisch)
   - **Windows**: Program Files, C:\Tools
   - **Linux**: /usr/bin, /usr/local/bin, /opt, Kali-spezifisch
4. ✅ Windows Registry (nur Windows)

**Features**:
- ✅ Cross-Platform Tool Finding
- ✅ Automatic .exe Extension (Windows)
- ✅ WSL Support
- ✅ Common Tool Locations kennen

---

### 6️⃣ Tool Registry (`src/legion/tools/registry.py`)
```python
from legion.tools.registry import get_registry

registry = get_registry()

# Get tool (mit Caching)
nmap = registry.get_tool("nmap")

# Discover all tools
registry.discover_all()

# Custom path hinzufügen
registry.add_custom_path("nmap", Path("C:/CustomTools"))

# Cache wird automatisch gespeichert in:
# Windows: %LOCALAPPDATA%\GothamSecurity\legion\Cache\tool_registry.json
# Linux:   ~/.cache/legion/tool_registry.json
```

**Features**:
- ✅ Zentrales Tool-Management
- ✅ Persistent Caching (JSON)
- ✅ Custom Path Support
- ✅ Cache Invalidation
- ✅ Singleton Pattern

---

### 7️⃣ Nmap Wrapper (Beispiel-Implementation)
```python
from legion.tools.nmap import NmapTool

nmap = NmapTool()  # Auto-discovery via Registry

if await nmap.validate():
    # Scan durchführen
    result = await nmap.scan(
        target="192.168.1.0/24",
        args=["-sV", "-T4"],
        timeout=300.0
    )
    
    if result.success:
        print(result.stdout)
        # XML parsing in Phase 3
```

**Features**:
- ✅ Platform-agnostisches Nmap Interface
- ✅ Async Scanning
- ✅ Auto-Discovery Integration
- ✅ Version Detection

---

## 🚀 Phase 3: Core Logic

### 8️⃣ Data Models (`src/legion/core/models/`)
```python
from legion.core.models import Host, Port, Service

# Host model with full nmap data
host = Host(
    ip="192.168.1.1",
    hostname="router.local",
    mac_address="00:11:22:33:44:55",
    vendor="Cisco Systems",
    os_name="Linux 3.2 - 4.9",
    os_accuracy=95,
    state="up",
    distance=1,
    uptime=864000  # 10 days
)

# Port model with service details
port = Port(
    number=22,
    protocol="tcp",
    state="open",
    service_name="ssh",
    service_product="OpenSSH",
    service_version="8.2p1",
    confidence=10
)
```

**Features**:
- ✅ Type-safe dataclasses
- ✅ Full nmap attribute support
- ✅ OS detection (name, family, accuracy)
- ✅ Service versioning (product, version, CPE)
- ✅ Timestamps (discovered_at, last_seen, last_boot)

---

### 9️⃣ Nmap XML Parser (`src/legion/tools/nmap/parser.py`)
```python
from legion.tools.nmap.parser import NmapXMLParser

parser = NmapXMLParser()

# Parse from file
result = parser.parse_file("scan.xml")

# Parse from string
result = parser.parse_string(xml_content)

# Access structured data
for host in result.hosts:
    print(f"Host: {host.ip} ({host.hostname})")
    print(f"OS: {host.os_name} ({host.os_accuracy}%)")
    
    # Get ports for this host
    for port in result.ports.get(host.ip, []):
        print(f"  {port.number}/{port.protocol}: {port.service_name}")
```

**Features**:
- ✅ Complete XML parsing
- ✅ Host attributes (IP, hostname, MAC, vendor)
- ✅ OS detection (name, family, accuracy, CPE)
- ✅ Port/Service details (state, product, version)
- ✅ NSE script results
- ✅ Uptime & distance parsing
- ✅ Scan metadata (args, version, timestamps)

---

### 🔟 Simple Database (`src/legion/core/database.py`)
```python
from legion.core.database import SimpleDatabase

db = SimpleDatabase(project_name="pentest_2025")

# Save hosts
db.save_host(host)

# Save ports
db.save_port(host.ip, port)

# Query data
all_hosts = db.get_all_hosts()
up_hosts = db.get_up_hosts()
ports = db.get_ports("192.168.1.1")

# Search by service
ssh_hosts = db.find_hosts_by_service("ssh")

# Statistics
stats = db.get_stats()
# {'total_hosts': 10, 'up_hosts': 8, 'down_hosts': 2, 'total_ports': 42}
```

**Features**:
- ✅ JSON-based storage (easy inspection)
- ✅ In-memory caching
- ✅ Host/Port/Service management
- ✅ Search by service
- ✅ Statistics & filtering
- ✅ Datetime serialization
- ✅ Project-based organization
- ⏳ SQLAlchemy migration (Phase 6)

---

### 1️⃣1️⃣ Scanner Manager (`src/legion/core/scanner.py`)
```python
from legion.core.scanner import ScanManager

scanner = ScanManager(
    database=db,
    max_concurrent_scans=3,
    result_dir=Path("./scans")
)

# Add callbacks
scanner.add_progress_callback(lambda job: print(f"Status: {job.status}"))
scanner.add_completion_callback(lambda job: print(f"Done: {job.hosts_found} hosts"))

# Start workers
await scanner.start()

# Queue scans
job_id1 = await scanner.queue_scan("192.168.1.0/24", "quick")
job_id2 = await scanner.queue_scan("192.168.1.1", "full", ports="1-65535")

# Wait for completion
await scanner.wait_for_completion()

# Get results
job = scanner.get_job(job_id1)
print(f"Found {job.hosts_found} hosts, {job.ports_found} ports")
print(f"Duration: {job.duration}s")
```

**Features**:
- ✅ Async scan queue management
- ✅ Configurable worker pool
- ✅ Progress tracking & callbacks
- ✅ Automatic result parsing
- ✅ Database integration
- ✅ Scan profiles (quick, full, stealth, aggressive)
- ✅ Timeout & error handling
- ✅ Statistics & job tracking

**Scan Profiles**:
- `quick`: Fast scan, top 100 ports (-T4 -F)
- `full`: All 65535 ports (-T4 -p-)
- `stealth`: SYN scan, slower (-sS -T2)
- `version`: Service version detection (-sV)
- `os`: OS detection (-O)
- `aggressive`: Full scan with scripts (-A -T4)

---

## 🚀 Phase 4: Configuration System

### 1️⃣3️⃣ Config Schema (`src/legion/config/schema.py`)
```python
from legion.config import LegionConfig, get_default_config

# Get default configuration
config = get_default_config()

# Access settings
print(f"Scan Timeout: {config.scanning.timeout}s")
print(f"Max Concurrent: {config.scanning.max_concurrent}")
print(f"Log Level: {config.logging.level}")
print(f"UI Theme: {config.ui.theme}")

# Modify settings
config.scanning.timeout = 600
config.logging.level = "DEBUG"
config.ui.theme = "dark"

# Validate
config.validate()  # Raises ValueError if invalid
```

**Config Sections**:
- ✅ **Scanning**: timeout, max_concurrent, profiles, timing
- ✅ **Logging**: level, file/console, rotation
- ✅ **Tools**: auto-discovery, custom paths, caching
- ✅ **UI**: theme, font size, auto-refresh
- ✅ **Database**: type (json/sqlite), backup
- ✅ **Project**: name, description, scan profile

---

### 1️⃣4️⃣ Config Manager (`src/legion/config/manager.py`)
```python
from legion.config import ConfigManager, get_config

# Load config (auto-creates if not exists)
config = get_config()

# Or use manager directly
manager = ConfigManager()
config = manager.load()

# Update via manager
manager.update(
    scanning__timeout=900,
    logging__level="INFO",
    ui__theme="dark"
)

# Save changes
manager.save()

# Reset to defaults
manager.reset()
```

**Features**:
- ✅ TOML-based (human-readable)
- ✅ Automatic file creation
- ✅ Type-safe loading/saving
- ✅ Batch updates
- ✅ Global singleton instance
- ✅ None-value filtering (TOML compatible)

**Config Locations**:
- Windows: `%APPDATA%\legion\legion.toml`
- Linux: `~/.config/legion/legion.toml`

---

**Letztes Update**: 12. November 2025
