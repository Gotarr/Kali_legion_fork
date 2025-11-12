# Legion Cross-Platform Migration Plan

**Ziel**: Legion vollständig plattformunabhängig machen (Windows & Linux)

**Status**: Phase 3 Complete  
**Startdatum**: 2025-11-11  
**Verantwortlich**: Gotarr

---

## 📋 Übersicht

Legion wird von einem Linux-spezifischen Tool zu einer vollständig plattformunabhängigen Pentesting-Suite (Windows & Linux) umgebaut. Die Migration erfolgt schrittweise, wobei der bestehende Code als Referenz erhalten bleibt.

---

## 🎯 Hauptziele

### Kern-Prinzipien
1. ✅ **Pure Python (neueste Version)**: Python 3.12+ bevorzugt, mindestens 3.10
   - Keine Bash/Shell-Scripts
   - Maximale Nutzung von Standard-Library
   - Type Hints & moderne Syntax
   
2. ✅ **Schlanke GUI**: Ressourcenschonende Oberfläche
   - PyQt6 mit minimalistischem Design
   - Keine unnötigen Animationen
   - Effiziente Table-Views
   - Optional: CLI-Mode für Server/Headless
   
3. ✅ **Intelligente Tool-Nutzung**: OS-spezifische Third-Party Tools
   - **Windows**: nmap.exe, hydra.exe, etc. (portable oder installiert)
   - **Linux**: Native Tools aus Paket-Manager (apt, yum, pacman)
   - Fallback: Python-Bibliotheken (python-nmap, etc.)

### Weitere Ziele
4. ✅ **Betriebssystem-Unabhängigkeit**: Windows & Linux Support
5. ✅ **Tool-Abstraktion**: Einheitliche APIs für externe Tools
6. ✅ **Bessere Testbarkeit**: Unit Tests, Integration Tests, CI/CD
7. ✅ **Verbesserte UX**: Plattformgerechte Installation & Konfiguration

---

## 📐 Neue Architektur

```
legion/
│
├── legacy/                      # Alter Code (Referenz, wird deprecated)
│   ├── app/
│   ├── ui/
│   ├── controller/
│   └── ...
│
├── src/                         # Neue plattformunabhängige Implementierung
│   └── legion/
│       ├── __init__.py
│       ├── __main__.py         # Entry point: python -m legion
│       │
│       ├── core/               # Kern-Logik (OS-unabhängig)
│       │   ├── __init__.py
│       │   ├── project.py      # Projekt-Management
│       │   ├── database.py     # DB-Abstraktion
│       │   ├── scanner.py      # Scan-Orchestrierung
│       │   └── models/         # Data Models
│       │       ├── host.py
│       │       ├── port.py
│       │       ├── service.py
│       │       └── vulnerability.py
│       │
│       ├── platform/           # OS-Abstraktion
│       │   ├── __init__.py
│       │   ├── detector.py     # OS/Platform Detection
│       │   ├── paths.py        # Plattformunabhängige Pfade
│       │   ├── privileges.py   # Root/Admin Checks
│       │   ├── process.py      # Prozess-Management
│       │   └── terminal.py     # Terminal-Abstraktion
│       │
│       ├── tools/              # Tool-Wrapper & Discovery
│       │   ├── __init__.py
│       │   ├── base.py         # Basis-Klasse für Tools
│       │   ├── discovery.py    # Tool-Pfad-Discovery
│       │   ├── nmap/
│       │   │   ├── __init__.py
│       │   │   ├── wrapper.py  # Nmap-Wrapper
│       │   │   ├── parser.py   # XML-Parser
│       │   │   └── commands.py # Command Builder
│       │   ├── hydra/
│       │   ├── nikto/
│       │   └── ...
│       │
│       ├── config/             # Konfiguration
│       │   ├── __init__.py
│       │   ├── manager.py      # Config-Management
│       │   ├── defaults.py     # Default-Settings
│       │   └── schema.py       # Config-Schema/Validation
│       │
│       ├── ui/                 # User Interface (PyQt6)
│       │   ├── __init__.py
│       │   ├── main_window.py
│       │   ├── widgets/
│       │   ├── dialogs/
│       │   └── resources/
│       │
│       ├── importers/          # Import-Module
│       │   ├── __init__.py
│       │   ├── nmap_xml.py
│       │   └── ...
│       │
│       └── utils/              # Hilfsfunktionen
│           ├── __init__.py
│           ├── logging.py
│           ├── validators.py
│           └── async_helpers.py
│
├── tests/                      # Tests (parallel zur src-Struktur)
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── docs/                       # Dokumentation
│   ├── architecture.md
│   ├── api/
│   └── user_guide/
│
├── scripts/                    # Utility-Scripts
│   ├── install_tools.py        # Tool-Installation Helper
│   └── setup_dev.py           # Dev-Environment Setup
│
├── pyproject.toml             # Moderne Package-Definition
├── setup.py                   # Backward-Kompatibilität
├── requirements.txt           # Dependencies
├── requirements-dev.txt       # Dev-Dependencies
├── .gitignore
├── README.md
└── MIGRATION_PLAN.md          # Dieses Dokument
```

---

## 🔄 Migrations-Phasen

### Phase 1: Foundation (Woche 1-2)
**Ziel**: Basis-Infrastruktur für plattformunabhängigen Code

- [x] Migrations-Plan erstellen
- [ ] Neue Verzeichnisstruktur anlegen
- [ ] `pyproject.toml` mit modernem Build-System
- [ ] Platform-Detection-Modul
- [ ] Pfad-Abstraktions-Modul
- [ ] Privilege-Check (Admin/Root)
- [ ] Logging-System konfigurieren
- [ ] Basis-Tests schreiben

**Deliverable**: Funktionsfähige Platform-Abstraktionsschicht

---

### Phase 2: Tool Discovery & Wrapper (Woche 3-4)
**Ziel**: Externe Tools plattformunabhängig einbinden

- [ ] Tool-Discovery-System (nmap, hydra, etc. finden)
- [ ] Basis-Tool-Wrapper-Klasse
- [ ] Nmap-Wrapper implementieren
  - [ ] Command-Builder
  - [ ] Prozess-Ausführung
  - [ ] XML-Parser (bestehend portieren)
- [ ] Nmap-Integration-Tests
- [ ] Hydra-Wrapper (Basis)

**Deliverable**: Nmap-Scans funktionieren plattformunabhängig

---

### Phase 3: Core Logic Migration (Woche 5-7) ✅ **ABGESCHLOSSEN**
**Ziel**: Geschäftslogik portieren

- [x] Data Models definieren (mit Type Hints) → `src/legion/core/models/`
- [x] Nmap XML Parser implementieren → `src/legion/tools/nmap/parser.py`
- [x] Datenbank-Abstraktion (SimpleDatabase) → `src/legion/core/database.py`
- [x] Scanner/Scheduler-Logik portieren → `src/legion/core/scanner.py`
- [x] End-to-End Integration Test → `src/legion/core/integration_test.py`
- [ ] Projekt-Management portieren (verschoben nach Phase 4)
- [ ] Screenshot-System plattformunabhängig (verschoben nach Phase 6)
- [ ] Core-Unit-Tests (verschoben nach Phase 7)

**Deliverable**: ✅ Core-Funktionalität funktioniert (Parser → Database)
**Details**: Siehe [docs/PHASE3_SUMMARY.md](docs/PHASE3_SUMMARY.md)

---

### Phase 4: Configuration System (Woche 8)
**Ziel**: Flexibles, plattformunabhängiges Config-System

- [ ] Config-Schema definieren (TOML/YAML)
- [ ] User-Config-Verzeichnisse (OS-spezifisch)
- [ ] Tool-Pfad-Konfiguration
- [ ] Wordlist-Pfad-Management
- [ ] Config-Migration von alter legion.conf
- [ ] Validation & Error-Handling

**Deliverable**: Konfiguration funktioniert auf allen Plattformen

---

### Phase 5: UI Migration (Woche 9-12)
**Ziel**: PyQt6-UI plattformunabhängig machen

- [ ] Main-Window portieren
- [ ] Host-Table-View
- [ ] Service-View
- [ ] Process-Management-View
- [ ] Screenshot-View
- [ ] Settings-Dialog
- [ ] Dialogs portieren
- [ ] UI-Tests

**Deliverable**: Vollständige UI funktioniert plattformunabhängig

---

### Phase 6: Additional Tools (Woche 13-14)
**Ziel**: Weitere Tool-Wrapper

- [ ] Hydra-Wrapper vervollständigen
- [ ] Nikto-Wrapper
- [ ] Weitere Tools nach Priorität
- [ ] Tool-Installation-Helper-Script
- [ ] Dokumentation für Tool-Setup

**Deliverable**: Alle wichtigen Tools integriert

---

### Phase 7: Testing & Polish (Woche 15-16)
**Ziel**: Produktionsreife herstellen

- [ ] Vollständige Test-Suite
- [ ] Integration-Tests auf allen Plattformen
- [ ] Performance-Optimierung
- [ ] Fehlerbehandlung verbessern
- [ ] User-Dokumentation
- [ ] Installation-Guides (Win/Mac/Linux)

**Deliverable**: Produktionsreifer Release-Kandidat

---

### Phase 8: Legacy Cleanup (Woche 17+)
**Ziel**: Alten Code entfernen

- [ ] Legacy-Code als deprecated markieren
- [ ] Migrations-Guide für User
- [ ] Legacy-Verzeichnis entfernen
- [ ] Final Release v1.0

**Deliverable**: Clean Codebase ohne Legacy

---

## 🔧 Technische Entscheidungen

### Build-System
- **pyproject.toml** mit setuptools/hatchling
- **PEP 517/518** konformes Build
- **Entry Points** für CLI: `legion` command
- **Python Version**: 3.12+ bevorzugt, mindestens 3.10

### Dependencies (Minimal-Prinzip)
```toml
[project]
name = "legion"
requires-python = ">=3.10"  # Minimum, 3.12+ empfohlen
dependencies = [
    # GUI (schlank konfiguriert)
    "PyQt6>=6.6.0",            # Neueste stabile Version
    
    # Database (async)
    "SQLAlchemy>=2.0.0",
    "aiosqlite>=0.19.0",
    
    # Async Operations
    "aiofiles>=23.0.0",
    
    # Configuration & Validation
    "pydantic>=2.5.0",         # Data validation
    "platformdirs>=4.0.0",     # OS-spezifische Pfade
    
    # Process Management
    "psutil>=5.9.0",           # Cross-platform process utilities
    
    # Tool Wrapper Fallbacks (optional)
    "python-nmap>=0.7.1",      # Fallback wenn nmap nicht installiert
]

[project.optional-dependencies]
# Nur für Development
dev = [
    "pytest>=7.4.0",
    "black>=23.12.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]
```

### GUI-Design-Prinzipien
1. **Minimalistisch**: Keine unnötigen Widgets
2. **Effizient**: Lazy Loading, virtualisierte Tables
3. **Responsive**: Async Operations, keine UI-Freezes
4. **Themeable**: Dark/Light Mode
5. **Optional CLI**: Alle Features auch über CLI verfügbar

### Code-Standards
- **Type Hints** überall (PEP 484)
- **Docstrings** (Google/NumPy Style)
- **Black** für Formatting
- **Ruff** für Linting
- **mypy** für Type-Checking
- **pytest** für Tests

### Plattform-Support
- **Windows 10/11** ✅
- **macOS 12+** ✅
- **Linux** (Ubuntu 20.04+, Kali, Fedora, Arch) ✅

---

## 📊 Kritische Bereiche

### 1. Prozess-Management
**Problem**: Aktuell mit `subprocess.Popen(shell=True)` - unsicher & platform-spezifisch

**Lösung**:
```python
# Vorher (legacy)
subprocess.Popen("nmap -sV 192.168.1.1", shell=True)

# Nachher (neu)
from legion.tools.nmap import NmapWrapper
nmap = NmapWrapper()
await nmap.run_scan("192.168.1.1", ["-sV"])
```

### 2. Pfad-Handling
**Problem**: Hardcoded `/usr/share/`, Linux-Pfade

**Lösung**:
```python
from legion.platform.paths import get_data_dir, get_config_dir
from pathlib import Path

# OS-spezifisch:
# Windows: C:\Users\user\AppData\Local\legion
# Linux: ~/.local/share/legion
# macOS: ~/Library/Application Support/legion
data_dir = get_data_dir()
```

### 3. Root/Admin-Rechte
**Problem**: `os.geteuid()` nur auf Unix

**Lösung**:
```python
from legion.platform.privileges import is_admin, require_admin

if not is_admin():
    require_admin()  # Platform-specific elevation
```

### 4. Tool-Discovery
**Problem**: Tools werden an fixen Pfaden erwartet

**Lösung**:
```python
from legion.tools.discovery import find_tool

nmap_path = find_tool("nmap")
# Sucht in: PATH, common locations, Registry (Win), etc.
```

---

## 🧪 Test-Strategie

### Unit Tests
- Jedes Modul hat eigene Tests
- Mocking von externen Tools
- 80%+ Code Coverage

### Integration Tests
- End-to-End Scans
- Multi-Platform CI (GitHub Actions)
- Real-Tool-Tests wo möglich

### Platform-Tests
- Windows: GitHub Actions (windows-latest)
- Linux: GitHub Actions (ubuntu-latest)
- macOS: GitHub Actions (macos-latest)

---

## 📦 Distribution

### Installation
```bash
# Pip (alle Plattformen)
pip install legion-pentesting

# Portable (Windows)
legion-windows-portable.zip

# Homebrew (macOS)
brew install legion

# APT (Debian/Ubuntu)
sudo apt install legion
```

### Tool-Dependencies (OS-spezifisch)

#### Windows
```powershell
# Portable Versionen bevorzugt (keine Admin-Installation nötig)
- nmap (nmap.org/download)
- hydra (aus Kali-Ports oder WSL)
- Alternative: WSL mit Linux-Tools
```

#### Linux
```bash
# Native Paket-Manager
sudo apt install nmap hydra nikto  # Debian/Ubuntu/Kali
sudo dnf install nmap hydra nikto  # Fedora
sudo pacman -S nmap hydra nikto    # Arch
```

#### macOS
```bash
# Homebrew
brew install nmap hydra nikto
```

#### Fallback-Strategie
1. **Primär**: Native Tool-Installation (beste Performance)
2. **Fallback**: Python-Wrapper (python-nmap, etc.)
3. **Dokumentation**: Installations-Guides pro OS
4. **Helper-Script**: `legion install-tools` (interaktiv)

---

## 🚧 Risiken & Mitigation

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Nmap nicht verfügbar (Windows) | Hoch | Hoch | Python-nmap als Fallback, Installations-Guide |
| Performance-Probleme | Mittel | Mittel | Profiling, Async-Operations, Benchmarks |
| UI nicht portable | Niedrig | Hoch | PyQt6 ist cross-platform, frühe Tests |
| Tool-Output-Parsing | Hoch | Mittel | Umfangreiche Tests, Version-Detection |
| Breaking Changes | Mittel | Hoch | Semantic Versioning, Migrations-Guide |

---

## 📈 Success Metrics

- [ ] **Cross-Platform**: Läuft auf Win/Mac/Linux ohne Änderungen
- [ ] **Installation**: < 5 Minuten auf jeder Plattform
- [ ] **Tests**: >80% Coverage, alle Plattformen grün
- [ ] **Performance**: Keine Regression vs. Legacy
- [ ] **Dokumentation**: Vollständig für User & Developer
- [ ] **Community**: Positive Feedback, <10% kritische Bugs

---

## 🔗 Ressourcen

### Bibliotheken für Cross-Platform
- **platformdirs**: OS-spezifische Verzeichnisse
- **psutil**: Prozess-Management
- **pathlib**: Moderne Pfad-Verwaltung
- **python-nmap**: Nmap-Wrapper (Fallback)

### Referenzen
- [Packaging Python Projects](https://packaging.python.org/)
- [PyQt6 Cross-Platform](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Python Cross-Platform Best Practices](https://docs.python-guide.org/)

---

## 📝 Nächste Schritte

1. ✅ Diesen Plan reviewen und anpassen
2. ⏳ Phase 1 starten: Foundation aufbauen
3. ⏳ Erste Tests auf Windows durchführen
4. ⏳ Community-Feedback einholen

---

**Letzte Aktualisierung**: 2025-11-11  
**Nächstes Review**: Nach Phase 1
