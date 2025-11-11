# Legion v2.0 - Cross-Platform Setup Anleitung

## ✅ Was wurde erstellt

### Phase 1: Foundation (ABGESCHLOSSEN)

Die Basis-Infrastruktur für plattformunabhängigen Code wurde erstellt:

#### 📁 Neue Struktur
```
src/legion/
├── __init__.py              ✅ Package initialization
├── __main__.py              ✅ Entry point
├── platform/                ✅ OS-Abstraktionsschicht
│   ├── __init__.py
│   ├── detector.py          ✅ Platform detection
│   ├── paths.py             ✅ Cross-platform paths
│   └── privileges.py        ✅ Admin/root handling
├── core/                    ✅ Business logic (vorbereitet)
├── tools/                   ✅ Tool wrappers (vorbereitet)
├── config/                  ✅ Configuration (vorbereitet)
└── utils/                   ✅ Utilities (vorbereitet)
```

#### 📄 Dokumentation
- ✅ `MIGRATION_PLAN.md` - Detaillierter 8-Phasen Migrations-Fahrplan
- ✅ `ARCHITECTURE.md` - Technische Architektur-Dokumentation
- ✅ `pyproject.toml` - Moderne Package-Definition mit Build-System
- ✅ `src/README.md` - Quick-Start Guide

---

## 🚀 Installation & Setup

### Voraussetzungen
- Python 3.10 oder höher
- pip (Python Package Manager)

### 1. Python-Umgebung einrichten

```powershell
# Virtual Environment erstellen (empfohlen)
py -m venv venv

# Aktivieren (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Aktivieren (Windows CMD)
venv\Scripts\activate.bat

# Aktivieren (Linux/Mac)
source venv/bin/activate
```

### 2. Dependencies installieren

```powershell
# Basis-Installation
pip install -r requirements.txt

# Oder: Development Mode (empfohlen für Entwicklung)
pip install -e .

# Mit allen Development-Tools
pip install -e ".[dev]"
```

**Hinweis**: Falls `platformdirs` nicht installiert ist, funktioniert der Code trotzdem durch die Fallback-Implementation.

---

## 🧪 Testen der neuen Platform-Layer

### Test 1: Platform Detection
```powershell
py src/legion/platform/detector.py
```

**Erwartete Ausgabe (Windows)**:
```
Platform Detection Results:
============================================================
Windows 10.0.19045 on AMD64 - Python 3.11.0
============================================================
System: Windows
Version: 10.0.19045
...
is_windows: True
is_linux: False
```

### Test 2: Path Management
```powershell
py src/legion/platform/paths.py
```

**Erwartete Ausgabe**:
```
Legion Directory Structure:
============================================================
Platform: Windows ...
Data Dir:       C:\Users\YourUser\AppData\Local\GothamSecurity\legion
Config Dir:     C:\Users\YourUser\AppData\Local\GothamSecurity\legion
...
```

### Test 3: Privilege Checking
```powershell
py src/legion/platform/privileges.py
```

**Erwartete Ausgabe**:
```
Privilege Status:
============================================================
is_admin            : False
can_raw_socket      : False
elevation_possible  : True

⚠️  Not running with administrator privileges
```

### Test 4: Haupt-Entry-Point
```powershell
py -m src.legion
```

**Erwartete Ausgabe**:
```
======================================================================
Legion - Cross-Platform Penetration Testing Framework
Version: 2.0.0-alpha1
======================================================================

Platform: Windows 10 on AMD64 - Python 3.11.0

Privilege Status:
  ✓ Is Admin: False
  ...

Directories:
  Data:   C:\Users\...\AppData\Local\GothamSecurity\legion
  ...

⚠️  WARNING: Not running with administrator privileges!
```

---

## 🎯 Was funktioniert bereits

### ✅ Plattform-Erkennung
- Windows, Linux, macOS Detection
- WSL (Windows Subsystem for Linux) Detection
- Architecture Detection (x64, arm64, etc.)
- Python Version Detection

### ✅ Pfad-Management
- OS-spezifische Verzeichnisse:
  - **Windows**: `%LOCALAPPDATA%\GothamSecurity\legion`
  - **Linux**: `~/.local/share/legion`
  - **macOS**: `~/Library/Application Support/legion`
- Automatische Verzeichnis-Erstellung
- Path Traversal Protection

### ✅ Privilege-Management
- Admin/Root Detection (plattformunabhängig)
- Raw Socket Capability Check
- UAC Elevation Request (Windows)
- Sudo Instructions (Unix)

---

## 📝 Nächste Schritte (Phase 2)

### Tool Discovery System
Als nächstes wird das automatische Finden von Tools implementiert:

```python
from legion.tools.discovery import find_tool

# Wird nmap finden auf:
# - Windows: C:\Program Files\Nmap\nmap.exe
# - Linux: /usr/bin/nmap
# - macOS: /usr/local/bin/nmap
nmap_path = find_tool("nmap")
```

### Nmap Wrapper
```python
from legion.tools.nmap import NmapWrapper

nmap = NmapWrapper()
result = await nmap.scan("192.168.1.0/24", ["-sV", "-sC"])
```

---

## 🔧 Troubleshooting

### Python nicht gefunden
```powershell
# Installiere Python von python.org oder Microsoft Store
# Dann verwende den Python Launcher:
py src/legion/platform/detector.py

# Version prüfen:
py --version
```

### Import-Fehler
```powershell
# Stelle sicher, dass du im Repository-Root bist
cd c:\Users\...\Kali_legion_fork

# Python-Pfad prüfen
py -c "import sys; print(sys.path)"
```

### platformdirs nicht gefunden
```powershell
# Installiere die dependency:
pip install platformdirs

# Oder nutze den eingebauten Fallback (funktioniert auch ohne)
```

---

## 📊 Projekt-Status

| Phase | Status | Beschreibung |
|-------|--------|--------------|
| **1. Foundation** | ✅ **Abgeschlossen** | Platform-Abstraktion, Pfade, Privileges |
| **2. Tool Discovery** | ⏳ In Planung | Automatisches Finden von Tools |
| **3. Core Logic** | 📋 Offen | Business Logic portieren |
| **4. Configuration** | 📋 Offen | Config-System |
| **5. UI Migration** | 📋 Offen | PyQt6 GUI portieren |
| **6. Additional Tools** | 📋 Offen | Weitere Tool-Wrapper |
| **7. Testing & Polish** | 📋 Offen | Produktionsreife |
| **8. Legacy Cleanup** | 📋 Offen | Alten Code entfernen |

---

## 🤝 Mitarbeit

Der Code folgt modernen Python-Standards:

- **Type Hints** überall (PEP 484)
- **Docstrings** (Google Style)
- **Black** Formatting
- **Ruff** Linting
- **pytest** für Tests

### Code-Qualität Tools (nach Installation)
```powershell
# Code formatieren
black src/

# Linting
ruff check src/

# Type-Checking
mypy src/

# Tests ausführen
pytest tests/
```

---

## 📚 Weitere Dokumentation

- **Migration Plan**: [MIGRATION_PLAN.md](MIGRATION_PLAN.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Original README**: [README.md](README.md)

---

## ✨ Highlights der neuen Architektur

1. **100% Python** - Keine Bash-Scripts mehr
2. **Type-Safe** - Volle Type-Hint-Unterstützung
3. **Testbar** - Dependency Injection, Mocking-freundlich
4. **Modern** - Async/Await, dataclasses, pathlib
5. **Sicher** - Input Validation, Path Traversal Protection
6. **Dokumentiert** - Umfassende Docstrings und Guides

---

**Stand**: 2025-11-11  
**Version**: 2.0.0-alpha1  
**Maintainer**: Gotarr
