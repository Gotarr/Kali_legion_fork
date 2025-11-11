# Phase 4 Summary: Configuration System

**Status**: ✅ **COMPLETE**  
**Datum**: 2025-01-21  
**Dauer**: ~2 Stunden  
**Zeilen Code**: ~900 (produktiv) + ~300 (tests)

---

## Übersicht

Phase 4 implementiert ein vollständiges TOML-basiertes Konfigurationssystem für Legion mit:
- Type-safe Configuration Schema
- TOML Loader/Saver
- User Config Management
- Legacy Config Migration
- Umfassende Tests

---

## Implementierte Komponenten

### 1. Configuration Schema (`schema.py`)
**312 Zeilen**

Dataclass-basierte Konfiguration mit 6 Sektionen:

```python
@dataclass
class LegionConfig:
    scanning: ScanningConfig
    logging: LoggingConfig
    tools: ToolsConfig
    ui: UIConfig
    database: DatabaseConfig
    project: ProjectConfig
```

**Features**:
- Vollständige Type Hints
- Validierung für alle Felder
- Sensible Defaults
- Human-readable `__str__()`

**Scanning Config**:
- `timeout`: Scan timeout (300s)
- `max_concurrent`: Max concurrent scans (3)
- `default_profile`: "quick", "full", "stealth", etc.
- `timing_template`: Nmap T0-T5 (default: T4)

**Logging Config**:
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `file_enabled`: Log to file (True)
- `max_file_size_mb`: Rotation size (10 MB)
- `backup_count`: Backup files (5)

**Tools Config**:
- `auto_discover`: Automatische Tool-Erkennung (True)
- `nmap_path`, `hydra_path`, `nikto_path`, etc.
- `custom_paths`: Dict für weitere Tools
- `cache_enabled`: Tool-Path-Cache (True)

**UI Config**:
- `theme`: "light", "dark", "system"
- `font_size`: 6-24 pt (default: 10)
- `auto_refresh_interval`: 5s
- `confirm_deletions`: True

**Database Config**:
- `type`: "json" oder "sqlite"
- `auto_backup`: True
- `backup_interval`: 300s

**Project Config**:
- `name`: Projekt-Name
- `description`: Beschreibung
- `scan_profile`: Default Scan Profile
- `auto_save_interval`: 60s

---

### 2. Configuration Manager (`manager.py`)
**235 Zeilen**

Verwaltet Config-Dateien mit TOML-Support:

```python
manager = ConfigManager("/path/to/legion.toml")
config = manager.load()
config.scanning.timeout = 600
manager.save()
```

**Features**:
- `load()`: TOML laden mit Fehlerbehandlung
- `save()`: Config als TOML speichern
- `update(**kwargs)`: Felder via `section__field=value` updaten
- `reset()`: Zurück zu Defaults
- `_config_to_dict()`: Dataclass → TOML Dict (filtert `None`)
- `_dict_to_config()`: TOML Dict → Dataclass

**Global Manager**:
```python
from legion.config import get_config, get_config_manager

config = get_config()  # Globale Config
manager = get_config_manager()  # Globaler Manager
```

**TOML Libraries**:
- `tomllib` (Python 3.11+) oder `tomli` (3.10 backport)
- `tomli_w` für TOML-Writing

---

### 3. Default Settings & Template (`defaults.py` + `template.toml`)
**130 Zeilen + 180 Zeilen Template**

**defaults.py**:
```python
# Default Config
config = get_default_config()

# Template Path
template = get_template_path()

# Create User Config
path = create_user_config()  # ~/.config/legion/legion.toml
```

**template.toml**:
- 180 Zeilen vollständig kommentiertes Template
- Alle Config-Optionen erklärt
- Beispiele für Custom Tool Paths
- Platform-spezifische Pfad-Hinweise (Windows/Linux)

Beispiel:
```toml
[scanning]
# Scan timeout in seconds (default: 300 = 5 minutes)
timeout = 300

# Maximum number of concurrent scans (default: 3)
max_concurrent = 3

# Default scan profile
# Options: "quick", "full", "stealth", "version", "os", "aggressive"
default_profile = "quick"
```

---

### 4. User Config Initialization (`init.py`)
**175 Zeilen**

Verwaltet User-Config mit Legacy-Migration:

```python
# Init User Config (mit Legacy-Migration)
manager = init_user_config()

# Reset zu Defaults
manager = reset_user_config()

# Legacy Config finden
legacy = find_legacy_config()  # Sucht legion.conf

# Legacy migrieren
migrated = migrate_legacy_config(legacy_path)
```

**Legacy Migration**:
- Erkennt alte `legion.conf` (INI-Format)
- Mappt bekannte Settings:
  - `max-fast-processes` → `scanning.max_concurrent`
  - `screenshooter-timeout` → `scanning.timeout`
  - `hydra-path` → `tools.hydra_path`
- Erstellt Backup (`legion.conf.backup`)
- Speichert als neues TOML

**User Config Pfade**:
- **Windows**: `%APPDATA%\legion\legion.toml`
- **Linux**: `~/.config/legion/legion.toml`

---

### 5. Integration Tests (`config_test.py`)
**293 Zeilen, 5 Tests, alle bestanden**

**Test 1: Schema Validation**
- ✅ Default config ist valide
- ✅ Ungültige Werte werden erkannt (timeout < 0)
- ✅ Ungültige Profiles werden erkannt

**Test 2: Config Manager**
- ✅ Config speichern
- ✅ Config laden
- ✅ Update-Methode
- ✅ Persistierung

**Test 3: Template Creation**
- ✅ Template erstellen
- ✅ Template-Inhalt validieren
- ✅ Template als Config laden

**Test 4: Legacy Migration**
- ✅ Legacy INI-Config migrieren
- ✅ Settings korrekt mappen
- ✅ Migrated config validieren

**Test 5: Full Workflow**
- ✅ Default erstellen
- ✅ Modifizieren & speichern
- ✅ Reload & verify
- ✅ Manager-Update
- ✅ Final verification

**Ergebnis**: `5/5 tests passed` ✅

---

## Dateistruktur

```
src/legion/config/
├── __init__.py          (58 Zeilen) - Public API
├── schema.py            (312 Zeilen) - Config Dataclasses
├── manager.py           (235 Zeilen) - TOML Manager
├── defaults.py          (130 Zeilen) - Default Config & Template
├── init.py              (175 Zeilen) - User Config Init & Migration
├── template.toml        (180 Zeilen) - Config Template
└── config_test.py       (293 Zeilen) - Integration Tests
```

**Total**: ~1,383 Zeilen (produktiv + tests)

---

## Verwendung

### Basis-Workflow

```python
from legion.config import init_user_config, get_config

# 1. Init (erste Verwendung)
manager = init_user_config()  # Erstellt ~/.config/legion/legion.toml

# 2. Config laden
config = get_config()

# 3. Werte lesen
print(f"Timeout: {config.scanning.timeout}s")
print(f"Max concurrent: {config.scanning.max_concurrent}")

# 4. Werte ändern
config.scanning.timeout = 600
config.logging.level = "DEBUG"

# 5. Speichern
manager.save()
```

### Update via Manager

```python
from legion.config import get_config_manager

manager = get_config_manager()

# Batch-Update
manager.update(
    scanning__timeout=900,
    logging__level="INFO",
    ui__theme="dark",
    ui__font_size=12
)

manager.save()
```

### Legacy Migration

```python
from legion.config import init_user_config

# Automatische Migration beim ersten Init
manager = init_user_config(migrate_legacy=True)
# Findet legion.conf → Migriert → Erstellt Backup → Speichert als TOML
```

### Config Reset

```python
from legion.config import reset_user_config

# Zurück zu Factory Defaults
manager = reset_user_config()  # Backup + Fresh Config
```

---

## TOML Beispiel

```toml
[scanning]
timeout = 600
max_concurrent = 5
default_profile = "full"
timing_template = 3

[logging]
level = "DEBUG"
file_enabled = true
console_enabled = true
max_file_size_mb = 20

[tools]
auto_discover = true
nmap_path = "/usr/bin/nmap"

[tools.custom_paths]
masscan = "/opt/masscan/bin/masscan"

[ui]
theme = "dark"
font_size = 12
auto_refresh_interval = 10

[database]
type = "sqlite"
auto_backup = true

[project]
name = "pentest_2025"
scan_profile = "aggressive"
```

---

## Integration mit bestehenden Modulen

### Scanner Manager Integration

```python
from legion.config import get_config
from legion.core.scanner import ScanManager

config = get_config()
manager = ScanManager(
    database=db,
    timeout=config.scanning.timeout,
    max_concurrent=config.scanning.max_concurrent
)
```

### Logging Integration

```python
import logging
from legion.config import get_config

config = get_config()
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format=config.logging.format,
    handlers=[
        logging.FileHandler("legion.log") if config.logging.file_enabled else None,
        logging.StreamHandler() if config.logging.console_enabled else None
    ]
)
```

### Tool Discovery Integration

```python
from legion.config import get_config
from legion.tools.discovery import ToolRegistry

config = get_config()
registry = ToolRegistry()

if config.tools.nmap_path:
    registry.register_tool("nmap", config.tools.nmap_path)
elif config.tools.auto_discover:
    registry.discover_tools()
```

---

## Dependencies

Neu hinzugefügt zu `requirements.txt`:

```
tomli>=2.0.0      # TOML parser (Python 3.10 backport)
tomli-w>=1.0.0    # TOML writer
```

Python 3.11+ hat `tomllib` im stdlib → kein `tomli` nötig.

---

## Nächste Schritte (Phase 5+)

### Phase 5: UI Migration (PyQt6)
- Config UI Dialog mit Tabs für jede Sektion
- Live-Update beim Config-Ändern
- Theme-Switcher (light/dark/system)

### Phase 6: Tools Integration
- Tool Registry mit Config-Support
- Custom Tool Paths aus Config
- Tool Discovery Cache

### Phase 7: CLI
- CLI für Config-Management:
  ```bash
  legion config show
  legion config set scanning.timeout 600
  legion config reset
  legion config migrate
  ```

### Phase 8: Advanced Features
- Config Profiles (dev, prod, stealth)
- Hot-Reload Support
- Config Validation CLI
- Config Export/Import

---

## Lessons Learned

### Erfolge ✅
1. **TOML statt JSON**: Besser lesbar, Kommentare möglich
2. **Dataclasses > Dicts**: Type-safe, Validierung, IDE-Support
3. **Legacy Migration**: Smooth Upgrade-Path für alte User
4. **Template**: User-freundlich mit Kommentaren
5. **Comprehensive Tests**: 5/5 Integration Tests

### Herausforderungen 🔧
1. **None-Handling**: TOML kann keine `None` → Filter vor Save
2. **Python 3.10 Support**: `tomllib` erst ab 3.11 → Backport `tomli`
3. **Windows Encoding**: Emoji-Fehler im Terminal → Plain Text in Tests

### Best Practices 📚
1. **Validation**: Immer vor Save validieren
2. **Defaults**: Sensible Defaults für alle Felder
3. **Documentation**: Inline-Kommentare im Template
4. **Testing**: Integration Tests für Full Workflow
5. **Migration**: Backup vor Änderungen

---

## Statistiken

| Metric | Wert |
|--------|------|
| **Zeilen Code (produktiv)** | ~900 |
| **Zeilen Tests** | ~300 |
| **Dateien** | 7 |
| **Funktionen** | 32 |
| **Klassen/Dataclasses** | 8 |
| **Config-Optionen** | 40+ |
| **Tests** | 5 (alle ✅) |
| **Dependencies** | 2 (tomli, tomli-w) |

---

## Fazit

**Phase 4 ist vollständig abgeschlossen!** 🎉

Das Configuration System bietet:
- ✅ Type-safe, validierte Konfiguration
- ✅ User-freundliches TOML-Format
- ✅ Legacy-Migration von alter legion.conf
- ✅ Umfassende Tests (5/5)
- ✅ Ready für Integration in Phase 5+ (UI, Tools, CLI)

**Nächste Phase**: UI Migration (PyQt6) mit Config-Dialog Integration.
