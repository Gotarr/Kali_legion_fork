# Legion v2.0 - Cross-Platform Migration - Übersicht

## 🎉 Phase 1 - ABGESCHLOSSEN! ✅
## 🚀 Phase 2 - Tool Discovery System - ABGESCHLOSSEN! ✅

Die Foundation UND das Tool Discovery System für die plattformunabhängige Version von Legion wurden erfolgreich erstellt.

---

## 📊 Was wurde erreicht

### ✅ Neue Projekt-Struktur
```
Kali_legion_fork/
│
├── 📄 MIGRATION_PLAN.md          # 8-Phasen Migrations-Roadmap
├── 📄 ARCHITECTURE.md            # Technische Architektur
├── 📄 SETUP_GUIDE.md             # Installation & Test-Anleitung
├── 📄 pyproject.toml             # Modernes Build-System
│
├── 📁 src/legion/                # NEUE plattformunabhängige Implementation
│   ├── __init__.py
│   ├── __main__.py               # Entry Point: python -m legion
│   │
│   ├── 📁 platform/              # ✅ OS-Abstraktionsschicht (Phase 1 FERTIG)
│   │   ├── detector.py           # Platform-Erkennung
│   │   ├── paths.py              # Cross-Platform Pfade
│   │   └── privileges.py         # Admin/Root Handling
│   │
│   ├── 📁 tools/                 # ✅ Tool Discovery & Base (Phase 2 FERTIG)
│   │   ├── base.py               # BaseTool Klasse + ToolResult/ToolInfo
│   │   ├── discovery.py          # Tool Discovery (PATH, Registry, common dirs)
│   │   ├── registry.py           # Tool Registry mit Caching
│   │   └── nmap/                 # Nmap Wrapper (Beispiel)
│   │       ├── __init__.py
│   │       └── wrapper.py        # NmapTool Implementation
│   │
│   ├── 📁 core/                  # ⏳ Business Logic (vorbereitet)
│   ├── 📁 config/                # ⏳ Konfiguration (vorbereitet)
│   └── 📁 utils/                 # ⏳ Utilities (vorbereitet)
│
└── 📁 app/, ui/, controller/     # Legacy Code (bleibt als Referenz)
```

---

## 🚀 Kern-Features

### ✅ Phase 1: Platform Foundation (Implementiert)

#### 1️⃣ Platform Detection (`src/legion/platform/detector.py`)
```python
from legion.platform import detect_platform

info = detect_platform()
print(info)  # Windows 10 on x86_64 - Python 3.11.0

# Properties:
info.is_windows    # True/False
info.is_linux      # True/False  
info.is_macos      # True/False
info.is_wsl        # Windows Subsystem for Linux?
info.is_admin      # Running with privileges?
```

**Funktioniert auf**:
- ✅ Windows 10/11
- ✅ Linux (Ubuntu, Kali, Fedora, etc.)
- ✅ WSL (Windows Subsystem for Linux)
- ✅ macOS (nicht getestet, aber code-ready)

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
# macOS:   ~/Library/Application Support/legion
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
- ✅ Linux/Mac: sudo Instructions
- ✅ Raw Socket Detection
- ✅ Detaillierter Privilege-Status

---

### ✅ Phase 2: Tool Discovery System (Implementiert)

#### 4️⃣ Base Tool Class (`src/legion/tools/base.py`)
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

#### 5️⃣ Tool Discovery (`src/legion/tools/discovery.py`)
```python
from legion.tools.discovery import find_tool, discover_all_tools

# Find single tool
nmap_path = find_tool("nmap")
# Windows: C:\Program Files\Nmap\nmap.exe
# Linux:   /usr/bin/nmap
# macOS:   /usr/local/bin/nmap

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
   - **Linux**: /usr/bin, /usr/local/bin, /opt
   - **macOS**: Homebrew, MacPorts
4. ✅ Windows Registry (nur Windows)

**Features**:
- ✅ Cross-Platform Tool Finding
- ✅ Automatic .exe Extension (Windows)
- ✅ WSL Support
- ✅ Common Tool Locations kennen

---

#### 6️⃣ Tool Registry (`src/legion/tools/registry.py`)
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

#### 7️⃣ Nmap Wrapper (Beispiel-Implementation)
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
        # XML parsing kommt in Phase 3
```

**Features**:
- ✅ Platform-agnostisches Nmap Interface
- ✅ Async Scanning
- ✅ Auto-Discovery Integration
- ✅ Version Detection
- ⏳ XML Parsing (Phase 3)

---

## 📋 Migrations-Roadmap

| Phase | Status | Dauer | Nächste Schritte |
|-------|--------|-------|------------------|
| **1. Foundation** | ✅ **100%** | Woche 1-2 | *Abgeschlossen* |
| **2. Tool Discovery** | ✅ **100%** | Woche 3-4 | *Abgeschlossen* |
| **3. Core Logic** | 📋 **0%** | Woche 5-7 | Nmap XML Parser, Scanner, DB |
| **4. Configuration** | 📋 **0%** | Woche 8 | TOML Config-System |
| **5. UI Migration** | 📋 **0%** | Woche 9-12 | PyQt6 GUI portieren |
| **6. Additional Tools** | 📋 **0%** | Woche 13-14 | Weitere Tool-Wrapper |
| **7. Testing & Polish** | 📋 **0%** | Woche 15-16 | Produktionsreife |
| **8. Legacy Cleanup** | 📋 **0%** | Woche 17+ | Alten Code entfernen |

**Aktueller Stand**: Phase 2 ✅ → Start Phase 3 📋

---

## 🔧 Technologie-Stack

### Basis
- **Python**: 3.10+ (Type Hints, dataclasses)
- **Build System**: pyproject.toml + setuptools
- **Package Structure**: src-layout (modern best practice)

### Dependencies
```toml
# Kern-Dependencies
PyQt6              # GUI Framework (cross-platform)
SQLAlchemy         # Database (async support)
platformdirs       # OS-spezifische Pfade
psutil             # Prozess-Management
pathlib            # Moderne Pfad-Operationen (stdlib)

# Development
pytest             # Testing
black              # Code Formatting
ruff               # Linting
mypy               # Type Checking
```

---

## 🎯 Design-Prinzipien

### 1. **Platform-Agnostic**
```python
# ❌ VORHER (Linux-only)
subprocess.Popen("nmap -sV 192.168.1.1", shell=True)
os.system('cp -r "' + source + '" "' + dest + '"')

# ✅ NACHHER (Cross-Platform)
from legion.tools.nmap import NmapWrapper
nmap = NmapWrapper()
await nmap.scan("192.168.1.1", ["-sV"])
```

### 2. **Type-Safe**
```python
# Vollständige Type Hints überall
def detect_platform() -> PlatformInfo:
    """Type-safe platform detection."""
    ...

@dataclass
class PlatformInfo:
    system: Literal["Windows", "Linux", "Darwin"]
    version: str
    is_admin: bool
```

### 3. **Testable**
```python
# Dependency Injection für einfaches Mocking
class ScanManager:
    def __init__(self, nmap: NmapWrapper, db: Database):
        self.nmap = nmap  # Easily mockable
        self.db = db
```

### 4. **Secure**
```python
# Path Traversal Protection
def safe_path_join(base: Path, *parts: str) -> Path:
    result = base.joinpath(*parts).resolve()
    if not result.is_relative_to(base):
        raise ValueError("Path traversal detected!")
    return result

# Keine shell=True mehr
subprocess.Popen(["nmap", "-sV", ip])  # Sicher!
```

---

## 🧪 Wie testen?

### Phase 1 & 2 Tests

#### Voraussetzung: Python installieren
```powershell
# Windows: Download von python.org
# Oder: Microsoft Store

# Prüfen:
py --version  # Sollte 3.10+ sein
```

### Installation
```powershell
# 1. Repository klonen (bereits erledigt ✓)
# 2. Virtual Environment (optional aber empfohlen)
py -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Dependencies installieren
pip install -r requirements.txt
# oder direkt:
pip install platformdirs
```

### Tests ausführen
```powershell
# === PHASE 1 TESTS ===

# Test 1: Platform Detection
py src/legion/platform/detector.py

# Test 2: Path Management  
py src/legion/platform/paths.py

# Test 3: Privilege Checking
py src/legion/platform/privileges.py

# Test 4: Main Entry Point
cd src; py -m legion; cd ..

# === PHASE 2 TESTS ===

# Test 5: Tool Discovery
py src\legion\tools\discovery.py

# Test 6: Tool Registry
py src\legion\tools\registry.py

# Test 7: Nmap Wrapper (wenn nmap installiert)
py src\legion\tools\nmap\wrapper.py
```

### Erwartete Ausgabe
```
======================================================================
Legion - Cross-Platform Penetration Testing Framework
Version: 2.0.0-alpha1
======================================================================

Platform: Windows 10.0.19045 on AMD64 - Python 3.11.0

Privilege Status:
  ✓ Is Admin: False
  ✗ Can Raw Socket: False
  ✓ Elevation Possible: True

Directories:
  Data:   C:\Users\...\AppData\Local\GothamSecurity\legion
  Config: C:\Users\...\AppData\Local\GothamSecurity\legion
  Logs:   C:\Users\...\AppData\Local\GothamSecurity\legion\Logs

⚠️  WARNING: Not running with administrator privileges!
   Some features (like nmap scanning) may not work correctly.

======================================================================
Legion v2.0 is under development.
...
```

---

## 📈 Nächste Schritte (Phase 3)

### Core Logic Implementation

**Ziel**: Kern-Logik für Scanning, Database, Project Management

#### 3.1 Nmap XML Parser
```python
# src/legion/tools/nmap/parser.py (geplant)

from legion.tools.nmap.parser import NmapXMLParser

parser = NmapXMLParser()
scan_data = parser.parse_file("scan_results.xml")

# Structured data:
for host in scan_data.hosts:
    print(f"Host: {host.ip} ({host.hostname})")
    for port in host.ports:
        print(f"  {port.number}/{port.protocol}: {port.service}")
```

#### 3.2 Database Layer
```python
# src/legion/core/database.py (geplant)

from legion.core.database import Database
from legion.core.models import Host, Port, Service

async with Database("project.db") as db:
    # Store scan results
    host = Host(ip="192.168.1.1", hostname="router.local")
    await db.save(host)
    
    # Query
    hosts = await db.query(Host).filter(status="up").all()
```

#### 3.3 Scanner Orchestration
```python
# src/legion/core/scanner.py (geplant)

from legion.core.scanner import ScanManager

scanner = ScanManager()

# Queue scans
await scanner.queue_scan("192.168.1.0/24", scan_type="discovery")
await scanner.queue_scan("192.168.1.1", scan_type="version")

# Execute all queued scans
await scanner.execute_all()
```

---

## 💡 Neue Features in Phase 2

| Feature | Beschreibung | Status |
|---------|--------------|--------|
| **BaseTool** | Abstrakte Klasse für alle Tools | ✅ |
| **Async Execution** | Nicht-blockierende Tool-Ausführung | ✅ |
| **Tool Discovery** | Automatisches Finden auf allen OS | ✅ |
| **PATH Search** | shutil.which Integration | ✅ |
| **Common Locations** | OS-spezifische Tool-Pfade | ✅ |
| **Registry Search** | Windows Registry Integration | ✅ |
| **Tool Caching** | Persistent Tool Registry | ✅ |
| **Custom Paths** | User-definierte Tool-Pfade | ✅ |
| **Nmap Wrapper** | Beispiel-Implementation | ✅ |
| **Version Detection** | Automatische Tool-Version | ✅ |

---

## 📈 Frühere Schritte (Phase 2) - ERLEDIGT ✅

### Tool Discovery System

**Status**: ✅ **ABGESCHLOSSEN**

Automatisches Finden von Tools auf allen Betriebssystemen implementiert:

**Implementiert**:
- ✅ `src/legion/tools/base.py` - BaseTool Klasse
- ✅ `src/legion/tools/discovery.py` - Tool Discovery
- ✅ `src/legion/tools/registry.py` - Tool Registry mit Caching
- ✅ `src/legion/tools/nmap/wrapper.py` - Nmap Wrapper

**Suchstrategie funktioniert**:
1. Custom Paths (user-configured)
2. System PATH
3. Common Install Locations
4. Windows Registry

**Getestet auf Windows 10**:
- ✅ Discovery findet Tools in PATH
- ✅ Common Locations korrekt für Windows
- ✅ Registry-Search funktioniert
- ✅ Caching in AppData\Local

---

## 💡 Vorteile der neuen Architektur

| Aspekt | Alt (Legacy) | Neu (v2.0) |
|--------|-------------|------------|
| **Plattform** | Nur Linux | Windows, Linux, macOS |
| **Shell-Scripts** | Viele .sh Files | Pure Python |
| **Type Safety** | Minimal | 100% Type Hints |
| **Testing** | Schwierig | Dependency Injection |
| **Security** | shell=True | Keine Shell-Execution |
| **Pfade** | Hardcoded | OS-spezifisch |
| **Docs** | Veraltet | Umfassend |
| **Build** | setup.py | pyproject.toml |

---

## 📚 Dokumentation

Alle Details in:

- **[MIGRATION_PLAN.md](MIGRATION_PLAN.md)**: Kompletter 8-Phasen Plan
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Technische Details
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)**: Installation & Testing
- **[src/README.md](src/README.md)**: Quick-Start für neue Struktur

---

## 🤝 Beitragen

Der Code ist jetzt viel besser strukturiert für Contributions:

1. **Type Hints** → Bessere IDE-Unterstützung
2. **Klare Modules** → Einfach zu navigieren
3. **Docs** → Jede Funktion dokumentiert
4. **Tests** → pytest-ready

### Code-Standards
```python
# Type Hints überall
def get_data_dir() -> Path:
    """Get user data directory."""
    ...

# Docstrings (Google Style)
def find_tool(name: str) -> Optional[Path]:
    """
    Find executable for a tool.
    
    Args:
        name: Tool name (e.g., 'nmap').
    
    Returns:
        Path to executable, or None if not found.
    """
```

---

## ✨ Zusammenfassung

**Phase 1 ist abgeschlossen!** Die Foundation steht:

✅ Platform Detection  
✅ Path Management  
✅ Privilege Handling  
✅ Dokumentation  
✅ Projekt-Struktur  

**Bereit für Phase 2**: Tool Discovery & Nmap-Wrapper

---

**Stand**: 2025-11-11  
**Version**: 2.0.0-alpha1  
**Status**: Phase 1 Complete ✅  
**Maintainer**: Gotarr

---

## 🎯 Vision

**Endziel**: Ein vollständig plattformunabhängiges, modernes Pentesting-Framework in Pure Python, das auf Windows, Linux und macOS gleichermaßen läuft - ohne Bash-Scripts, mit voller Type-Safety und erstklassiger Developer Experience.

**Wir sind auf dem besten Weg! 🚀**
