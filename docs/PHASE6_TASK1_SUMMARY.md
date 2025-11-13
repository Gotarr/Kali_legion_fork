# Phase 6 - Task 1: JSON Import + Legacy Settings

**Status**: ✅ Complete  
**Datum**: 13. November 2025  
**Fortschritt**: 100%

---

## 📋 Übersicht

Dieses Dokument beschreibt die Implementierung von zwei wichtigen Features als Teil der Phase 6 UI-Finalisierung:

1. **JSON Import Funktion**: Vollständige Implementierung des Import-Features mit Unterstützung für Single-Host und Multi-Host Formate
2. **Legacy Settings**: Integration essentieller Einstellungen aus dem Legacy-Legion (Terminal-Auswahl, Screenshot Timeout, Web Services)

---

## 🎯 Ziele

### JSON Import
- Ersetzen des TODO-Stubs in `_import_json()` durch vollständige Implementierung
- Unterstützung für zwei Export-Formate:
  - Single-Host: `{"host": {...}, "ports": [...]}`
  - Multi-Host: `{"hosts": [{...}, {...}]}`
- Integration mit bestehenden Database-Methoden (`save_host()`, `save_port()`)
- Fehlerbehandlung und Benutzer-Feedback

### Legacy Settings
- Analyse der Legacy-Einstellungen (`_old/ui/settingsDialog.py`)
- Identifikation der wichtigsten Features für Basis-Extension
- Integration in das moderne TOML-basierte Config-System
- UI-Implementation mit PyQt6-Widgets

---

## ✅ Implementierte Features

### 1. JSON Import (mainwindow.py)

**Datei**: `src/legion/ui/mainwindow.py` (Zeilen 1268-1336)

**Features**:
- ✅ Format-Erkennung (Single-Host vs Multi-Host)
- ✅ Host-Objekt Erstellung mit allen Feldern:
  - IP-Adresse (erforderlich)
  - Hostname (optional)
  - OS Name (optional)
  - State (optional, Standard: "up")
  - Last Seen (Zeitstempel)
- ✅ Port-Objekt Erstellung mit allen Feldern:
  - Port Number
  - Protocol
  - State
  - Service Name
  - Service Version
- ✅ Database Integration (`save_host()`, `save_port()`)
- ✅ Statistik-Anzeige (X Hosts, Y Ports importiert)
- ✅ Fehlerbehandlung mit Logging
- ✅ Fortsetzung bei Einzelfehlern (robust import)

**Code-Struktur**:
```python
def _import_json(self, filename: str) -> None:
    # 1. JSON laden
    # 2. Format erkennen (hosts array vs single host)
    # 3. Für jeden Host:
    #    a. Host-Objekt erstellen
    #    b. In Database speichern
    #    c. Ports verarbeiten und speichern
    # 4. Statistik anzeigen
    # 5. Fehlerbehandlung
```

**Getestete Formate**:
- ✅ Legion Export Format (Multi-Host mit project metadata)
- ✅ Single-Host Direct Export
- ✅ Fehlerhafte Einträge (Logging, Fortsetzung)

---

### 2. Legacy Settings (settings.py + schema.py)

**Dateien**:
- `src/legion/ui/settings.py` (Extended)
- `src/legion/config/schema.py` (Extended)

#### 2.1 Terminal-Auswahl (General Tab)

**UI Component**: `QComboBox` (lines 139-145)

**Features**:
- ✅ Platform-spezifische Optionen:
  - **Windows**: `cmd`, `powershell`, `wt` (Windows Terminal)
  - **Linux**: `gnome-terminal`, `xterm`, `konsole`, `terminator`
- ✅ Default: `cmd` (Windows) / `gnome-terminal` (Linux)
- ✅ Config Field: `config.ui.default_terminal`

**Code**:
```python
if platform.system() == "Windows":
    terminals = ["cmd", "powershell", "wt"]
else:
    terminals = ["gnome-terminal", "xterm", "konsole", "terminator"]
```

#### 2.2 Screenshot Timeout (Scanning Tab)

**UI Component**: `QSpinBox` (lines 195-199)

**Features**:
- ✅ Wertebereich: 5-300 Sekunden
- ✅ Suffix: " Sekunden"
- ✅ Default: 15 Sekunden
- ✅ Config Field: `config.scanning.screenshot_timeout`

**Verwendung**: Timeout für automatische Screenshot-Erfassung von Web-Services

#### 2.3 Web Services Liste (Scanning Tab)

**UI Component**: `QLineEdit` (lines 201-206)

**Features**:
- ✅ Komma-separierte Liste
- ✅ Placeholder: "http,https,ssl,soap,..."
- ✅ Default: "http,https,ssl,soap"
- ✅ Config Field: `config.scanning.web_services`

**Verwendung**: Definiert welche Services als Web-Services erkannt werden

---

### 3. Config Schema Extensions (schema.py)

#### 3.1 ScanningConfig (lines 12-41)

**Neue Felder**:
```python
@dataclass
class ScanningConfig:
    # ... existing fields ...
    screenshot_timeout: int = 15  # Neu
    web_services: str = "http,https,ssl,soap"  # Neu
```

**Validation**:
```python
def __post_init__(self):
    if self.screenshot_timeout <= 0:
        raise ValueError("screenshot_timeout must be positive")
```

#### 3.2 UIConfig (lines 137-164)

**Neue Felder**:
```python
@dataclass
class UIConfig:
    # ... existing fields ...
    default_terminal: str = "cmd"  # Neu
```

---

### 4. Persistence (settings.py)

**Load Method** (lines 307-329):
```python
def _load_values(self):
    # ... existing loads ...
    
    # Terminal
    terminal = self.config.ui.default_terminal
    index = self.terminal_combo.findText(terminal)
    if index >= 0:
        self.terminal_combo.setCurrentIndex(index)
    
    # Screenshot Timeout
    self.screenshot_timeout_spin.setValue(
        self.config.scanning.screenshot_timeout
    )
    
    # Web Services
    self.web_services_edit.setText(
        self.config.scanning.web_services
    )
```

**Save Method** (lines 348-370):
```python
def _save_values(self):
    # ... existing saves ...
    
    # Terminal
    self.config.ui.default_terminal = self.terminal_combo.currentText()
    
    # Screenshot Timeout
    self.config.scanning.screenshot_timeout = \
        self.screenshot_timeout_spin.value()
    
    # Web Services
    self.config.scanning.web_services = \
        self.web_services_edit.text()
```

---

## 🧪 Testing

### Test-Szenarien

#### JSON Import
1. ✅ **Single-Host Export**: `192.168.3.8_export.json`
   - Host mit IP, Hostname, OS
   - 3 Ports (22/tcp, 80/tcp, 443/tcp)
   - Ergebnis: 1 Host, 3 Ports importiert

2. ✅ **Multi-Host Export**: `legion_export_20251113_080526.json`
   - 2+ Hosts (127.0.0.1, 192.168.3.8)
   - Multiple Ports pro Host
   - Project Metadata
   - Ergebnis: 2+ Hosts, 10+ Ports importiert

3. ✅ **Fehlerhafte Daten**:
   - Fehlende IP-Adressen → Logging, Skip Entry
   - Ungültige Port-Nummern → Logging, Skip Port
   - Malformed JSON → Error Message

#### Settings Dialog
1. ✅ **Terminal-Auswahl**:
   - Windows: cmd, powershell, wt verfügbar
   - Auswahl speichern → Config Update
   - App-Neustart → Wert bleibt erhalten

2. ✅ **Screenshot Timeout**:
   - Wertänderung (5-300s)
   - Speichern → Config Update
   - Persistenz über Neustarts

3. ✅ **Web Services**:
   - Liste editieren: "http,https,ftp,ssh"
   - Speichern → Config Update
   - Persistenz validiert

### User Testing

**Datum**: 13. November 2025

**Feedback**: 
> "sieht gut aus. Export und Import funktioniert auch das ändern in den optionen sieht gut aus."

**Validierte Features**:
- ✅ JSON Export funktioniert
- ✅ JSON Import funktioniert
- ✅ Settings-Änderungen werden gespeichert
- ✅ Settings-Änderungen persistieren
- ✅ Keine Fehler in der UI

---

## 📊 Statistiken

### Code Changes

| Datei | Zeilen Vorher | Zeilen Nachher | Diff |
|-------|---------------|----------------|------|
| `mainwindow.py` | 1268 (TODO stub) | 1336 | +68 |
| `settings.py` | 459 | 503 | +44 |
| `schema.py` | 318 | 342 | +24 |
| **Total** | - | - | **+136** |

### Features Added

| Feature | LOC | Complexity |
|---------|-----|------------|
| JSON Import | 68 | Medium |
| Terminal Selection | 15 | Low |
| Screenshot Timeout | 8 | Low |
| Web Services | 8 | Low |
| Config Schema | 24 | Low |
| Persistence Logic | 13 | Low |
| **Total** | **136** | - |

---

## 🔍 Legacy Analysis

### Verglichene Dateien
- `_old/ui/settingsDialog.py` (1629 Zeilen)
- `src/legion/ui/settings.py` (459 → 503 Zeilen)

### Identifizierte Legacy Features

#### ✅ Implementiert (Basis-Extensions)
1. **Terminal Selection** - General Tab
2. **Screenshot Timeout** - Scanning Tab
3. **Web Services List** - Scanning Tab

#### 📋 Noch Verfügbar (Optional)
4. **Brute-Force Tab**:
   - Username/Password Wordlists
   - Credential Management
   - Hydra Integration

5. **Wordlists Tab**:
   - Default Wordlist Paths
   - Custom Wordlist Management

6. **Automated Attacks Tab**:
   - Auto-Attack Settings
   - Service-specific Attack Configs

7. **Custom Commands**:
   - Host Commands
   - Port Commands
   - Terminal Commands

8. **Staged Nmap**:
   - Multi-Stage Scan Configuration
   - Port Discovery → Service Detection → Version Scan

### Design-Entscheidung

**Gewählt**: Option A (Basis-Extensions)

**Begründung**:
- Minimaler Scope für MVP
- Essenzielle Features ohne Komplexität
- Einfache UI-Integration
- Schnelle Implementierung (< 2h)
- Validierung durch User Testing

**Zukünftige Erweiterungen**:
- Optional: Brute-Force Tab (wenn Hydra-Wrapper implementiert)
- Optional: Wordlists Tab (wenn Wordlist-Management benötigt)
- Optional: Automated Attacks (Phase 6)

---

## 🚀 Nächste Schritte

### Abgeschlossen
- ✅ JSON Import Implementation
- ✅ Legacy Settings (Terminal, Screenshot, Web Services)
- ✅ Config Schema Extensions
- ✅ User Testing & Validation
- ✅ Dokumentation

### Optional (Phase 6)
- 📋 Tool Discovery für Hydra, Nikto, Searchsploit
- 📋 Brute-Force Tab (wenn Hydra verfügbar)
- 📋 Wordlists Tab (wenn benötigt)
- 📋 Automated Attacks Configuration

---

## 📚 Referenzen

### Dokumentation
- [PHASE5_SUMMARY.md](PHASE5_SUMMARY.md) - UI Migration Overview
- [ARCHITECTURE_DETAILS.md](ARCHITECTURE_DETAILS.md) - Config System
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing Guidelines

### Source Files
- `src/legion/ui/mainwindow.py` - JSON Import
- `src/legion/ui/settings.py` - Settings Dialog
- `src/legion/config/schema.py` - Config Schema
- `src/legion/core/database.py` - Database Methods

### Legacy Reference
- `_old/ui/settingsDialog.py` - Original Settings (1629 lines)

---

**Maintainer**: Gotarr  
**Completion Date**: 13. November 2025  
**Status**: ✅ Production Ready
