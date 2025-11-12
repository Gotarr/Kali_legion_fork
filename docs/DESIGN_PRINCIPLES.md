# Legion v2.0 - Design Principles

Grundlegende Design-Prinzipien und Vorteile der neuen Architektur.

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
    system: Literal["Windows", "Linux"]
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

## 💡 Vorteile der neuen Architektur

| Aspekt | Alt (Legacy) | Neu (v2.0) |
|--------|-------------|------------|
| **Plattform** | Nur Linux | Windows & Linux |
| **Shell-Scripts** | Viele .sh Files | Pure Python |
| **Type Safety** | Minimal | 100% Type Hints |
| **Testing** | Schwierig | Dependency Injection |
| **Security** | shell=True | Keine Shell-Execution |
| **Pfade** | Hardcoded | OS-spezifisch |
| **Docs** | Veraltet | Umfassend |
| **Build** | setup.py | pyproject.toml |

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
tomli              # TOML parser (Python 3.10, stdlib in 3.11+)
tomli-w            # TOML writer

# Development
pytest             # Testing
black              # Code Formatting
ruff               # Linting
mypy               # Type Checking
```

---

## 🤝 Code-Standards

### Type Hints überall
```python
def get_data_dir() -> Path:
    """Get user data directory."""
    ...
```

### Docstrings (Google Style)
```python
def find_tool(name: str) -> Optional[Path]:
    """
    Find executable for a tool.
    
    Args:
        name: Tool name (e.g., 'nmap').
    
    Returns:
        Path to executable, or None if not found.
    """
```

### Dependency Injection
```python
class MainWindow:
    def __init__(
        self,
        database: SimpleDatabase,
        scanner: ScanManager,
        config_manager: ConfigManager
    ):
        self.db = database
        self.scanner = scanner
        self.config = config_manager
```

---

## 🎯 Vision

**Endziel**: Ein vollständig plattformunabhängiges, modernes Pentesting-Framework in Pure Python, das auf Windows und Linux gleichermaßen läuft - ohne Bash-Scripts, mit voller Type-Safety und erstklassiger Developer Experience.

---

**Letztes Update**: 12. November 2025
