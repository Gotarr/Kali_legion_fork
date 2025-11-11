# Legion v2.0 - Design-Prinzipien

**Version**: 2.0.0-alpha1  
**Datum**: 2025-11-11

---

## 🎯 Kern-Prinzipien

### 1. Pure Python (neueste Version) 🐍

**Ziel**: Maximale Portabilität und Wartbarkeit

#### Python Version
- **Minimum**: Python 3.10 (für Union types, match/case)
- **Empfohlen**: Python 3.12+ (neueste Features)
- **Testing**: Auf 3.10, 3.11, 3.12

#### Was das bedeutet
✅ **JA**:
- Pure Python-Implementierung
- Standard Library bevorzugen
- Type Hints überall (PEP 484)
- Async/Await (asyncio)
- Moderne Syntax (match/case, walrus operator, etc.)

❌ **NEIN**:
- Bash/Shell-Scripts
- Platform-spezifische Binaries (außer externe Tools)
- C-Extensions (außer in Dependencies)
- Legacy Python 2.x Kompatibilität

#### Beispiel
```python
# ✅ GUT: Pure Python, Type-Safe
from pathlib import Path
from typing import Optional

async def find_tool(name: str) -> Optional[Path]:
    """Find tool executable in system PATH."""
    for path in get_search_paths():
        exe = path / f"{name}.exe" if is_windows() else path / name
        if exe.exists():
            return exe
    return None

# ❌ SCHLECHT: Shell-Abhängig
def find_tool(name: str) -> str:
    return subprocess.check_output(f"which {name}", shell=True)
```

---

### 2. Schlanke GUI (Ressourcenschonend) 💻

**Ziel**: Schnell, effizient, nicht überladen

#### GUI-Framework
- **PyQt6** (neueste Version)
- **Minimal-Design**: Nur notwendige Widgets
- **Performance**: Async Operations, keine UI-Blocks

#### Design-Richtlinien

##### ✅ Erlaubt
- **Simple Layouts**: Grid, VBox, HBox
- **Standard Widgets**: Tables, Lists, Buttons, Input Fields
- **Dark/Light Mode**: System-Theme respektieren
- **Keyboard Shortcuts**: Für Power-User
- **Virtualized Views**: Für große Daten-Sets

##### ❌ Vermeiden
- Komplexe Animationen
- Unnötige Grafik-Effekte
- Zu viele verschachtelte Widgets
- Blocking Operations in UI-Thread
- Große Icons/Bilder laden

#### Beispiel UI-Struktur
```
┌─────────────────────────────────────────────────┐
│ Menu: File | Scan | Tools | Help                │
├─────────────────────────────────────────────────┤
│ Toolbar: [Quick Scan] [Add Host] [Settings]    │
├──────────────────┬──────────────────────────────┤
│ Hosts (Table)    │ Host Details                 │
│ IP | Hostname    │ ┌──────────────────────────┐ │
│ □ 192.168.1.1   │ │ Ports & Services         │ │
│ □ 192.168.1.2   │ │ [Port] [State] [Service] │ │
│ ...              │ │  22     open   ssh       │ │
│                  │ │  80     open   http      │ │
│                  │ └──────────────────────────┘ │
├──────────────────┴──────────────────────────────┤
│ Process Log: [Clear] [Export]                   │
│ [12:34:56] Started nmap scan...                 │
│ [12:35:12] Found 2 hosts                        │
└─────────────────────────────────────────────────┘
```

#### Performance-Tricks
```python
# ✅ Lazy Loading
def load_hosts(self):
    """Load only visible rows"""
    visible_range = self.table.visible_rows()
    return self.db.get_hosts(offset=visible_range.start, limit=100)

# ✅ Async Operations
async def scan_network(self):
    """Non-blocking scan"""
    self.progress_bar.show()
    try:
        result = await self.nmap.scan_async(target)
        self.update_table(result)
    finally:
        self.progress_bar.hide()

# ❌ Vermeiden: Blocking
def scan_network(self):
    result = subprocess.run(["nmap", ...])  # UI friert ein!
    self.update_table(result)
```

---

### 3. Third-Party Tools (OS-spezifisch) 🔧

**Ziel**: Native Tools nutzen, intelligente Fallbacks

#### Tool-Strategie

##### Primär: Native Tools
- **Beste Performance**: Direkte Binary-Ausführung
- **Vollständige Features**: Alle nmap/hydra Optionen
- **Community-Support**: Aktiv gepflegt

##### Fallback: Python-Wrapper
- **Wenn Tool nicht installiert**: python-nmap, etc.
- **Eingeschränkte Features**: Basis-Funktionalität
- **Langsamer**: Python-Overhead

#### OS-spezifische Tool-Pfade

##### Windows
```python
TOOL_PATHS = {
    "nmap": [
        r"C:\Program Files\Nmap\nmap.exe",
        r"C:\Program Files (x86)\Nmap\nmap.exe",
        r"C:\nmap\nmap.exe",  # Portable
    ],
    "hydra": [
        r"C:\hydra\hydra.exe",
        # WSL Fallback
        r"C:\Windows\System32\wsl.exe",  # -> wsl hydra
    ],
}
```

##### Linux
```python
TOOL_PATHS = {
    "nmap": [
        "/usr/bin/nmap",
        "/usr/local/bin/nmap",
        "/snap/bin/nmap",
    ],
    "hydra": [
        "/usr/bin/hydra",
        "/usr/local/bin/hydra",
    ],
}
```

##### macOS
```python
TOOL_PATHS = {
    "nmap": [
        "/usr/local/bin/nmap",  # Homebrew
        "/opt/homebrew/bin/nmap",  # M1/M2 Macs
    ],
    "hydra": [
        "/usr/local/bin/hydra",
        "/opt/homebrew/bin/hydra",
    ],
}
```

#### Discovery-Strategie
```python
async def find_tool(self, name: str) -> ToolInfo:
    """
    1. Check user config (custom path)
    2. Search in PATH
    3. Check OS-specific common locations
    4. Check Windows Registry (if Windows)
    5. Fallback to Python wrapper
    """
    # User config has priority
    if custom_path := self.config.get_tool_path(name):
        if Path(custom_path).exists():
            return ToolInfo(path=custom_path, type="native")
    
    # Search PATH
    if path := shutil.which(name):
        return ToolInfo(path=path, type="native")
    
    # OS-specific locations
    for location in self.get_common_paths(name):
        if location.exists():
            return ToolInfo(path=location, type="native")
    
    # Fallback
    if self.has_python_wrapper(name):
        return ToolInfo(path=None, type="python-wrapper")
    
    raise ToolNotFoundError(f"{name} not found. Install or configure path.")
```

#### Tool-Wrapper-Interface
```python
class ToolWrapper(Protocol):
    """Unified interface for all tools"""
    
    async def run(
        self,
        target: str,
        options: list[str],
        timeout: int = 300
    ) -> ToolResult:
        """Execute tool with options"""
        ...
    
    def is_available(self) -> bool:
        """Check if tool is installed"""
        ...
    
    def get_version(self) -> str:
        """Get tool version"""
        ...
```

---

## 📦 Dependency-Management

### Minimal-Dependencies-Prinzip

**Regel**: Nur Dependencies, die wirklich nötig sind.

#### Core Dependencies (immer installiert)
```toml
[project.dependencies]
PyQt6 = ">=6.6.0"          # GUI
SQLAlchemy = ">=2.0.0"     # Database
aiosqlite = ">=0.19.0"     # Async SQLite
pydantic = ">=2.5.0"       # Validation
platformdirs = ">=4.0.0"   # OS paths
psutil = ">=5.9.0"         # Process mgmt
```

#### Optional Dependencies (on-demand)
```toml
[project.optional-dependencies]
fallbacks = [
    "python-nmap>=0.7.1",  # Wenn nmap nicht installiert
]

dev = [
    "pytest>=7.4.0",
    "black>=23.12.0",
    "ruff>=0.1.0",
]
```

#### Installation-Modi
```bash
# Minimal (nur Core)
pip install legion

# Mit Fallbacks
pip install legion[fallbacks]

# Development
pip install legion[dev]

# Alles
pip install legion[fallbacks,dev]
```

---

## 🏗️ Architektur-Entscheidungen

### 1. Async-First
- Alle I/O-Operations async
- UI bleibt responsive
- Parallele Scans möglich

### 2. Type-Safe
- Type Hints überall
- mypy-konform
- Runtime-Validation mit Pydantic

### 3. Testbar
- Dependency Injection
- Interfaces (Protocols)
- Einfaches Mocking

### 4. Modular
- Klare Modul-Grenzen
- Austauschbare Komponenten
- Plugin-System (später)

---

## 📝 Code-Standards

### Type Hints
```python
# ✅ Vollständige Type Hints
def scan_port(
    host: str,
    port: int,
    timeout: float = 1.0
) -> Optional[ServiceInfo]:
    """Scan single port."""
    ...

# ❌ Keine Type Hints
def scan_port(host, port, timeout=1.0):
    ...
```

### Error Handling
```python
# ✅ Spezifische Exceptions
class ToolNotFoundError(LegionError):
    """Tool not found in system."""
    pass

try:
    nmap = await find_tool("nmap")
except ToolNotFoundError as e:
    logger.error(f"nmap not found: {e}")
    # Fallback to python-nmap
    nmap = PythonNmapWrapper()

# ❌ Generisches except
try:
    nmap = find_tool("nmap")
except:  # Zu breit!
    pass
```

### Docstrings
```python
# ✅ Google-Style Docstring
async def scan_network(
    self,
    target: str,
    ports: Optional[list[int]] = None
) -> ScanResult:
    """
    Scan network target for open ports.
    
    Args:
        target: IP address, hostname, or CIDR range.
        ports: List of ports to scan. None = common ports.
    
    Returns:
        ScanResult with discovered hosts and services.
    
    Raises:
        ToolNotFoundError: If nmap is not available.
        ScanTimeoutError: If scan exceeds timeout.
    
    Example:
        >>> result = await scanner.scan_network("192.168.1.0/24")
        >>> print(f"Found {len(result.hosts)} hosts")
    """
    ...
```

---

## ✅ Zusammenfassung

### Die 3 Säulen von Legion v2.0

1. **🐍 Pure Python**
   - Neueste Python-Version (3.12+)
   - Type-Safe, Modern, Wartbar

2. **💻 Schlanke GUI**
   - PyQt6, Minimalistisch
   - Schnell, Effizient, Optional CLI

3. **🔧 Smart Tool Integration**
   - Native Tools bevorzugen
   - OS-spezifische Pfade
   - Intelligente Fallbacks

### Diese Prinzipien führen zu:
- ✅ **Bessere Performance**: Native Tools + Async
- ✅ **Höhere Qualität**: Type Safety + Tests
- ✅ **Einfachere Wartung**: Pure Python, klare Struktur
- ✅ **Plattform-Unabhängigkeit**: Ein Code, alle OS

---

**Stand**: 2025-11-11  
**Status**: Design finalisiert  
**Nächster Schritt**: Phase 2 - Tool Discovery implementieren
