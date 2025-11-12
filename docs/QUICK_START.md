# Legion New UI - Quick Start Guide

**Version**: Phase 5 (New UI)  
**Status**: ✅ Scanner Integration Complete  
**Date**: 12. November 2025

---

## 🚀 Schnellstart

### 1. Starten

```powershell
# Windows (mit nmap im PATH)
$env:Path += ";C:\Program Files (x86)\Nmap"
py legion.py
```

```bash
# Linux
python3 legion.py
```

### 2. Ersten Scan starten

1. **Scan → New Scan** (oder `Ctrl+N`)
2. **Target eingeben**: z.B. `127.0.0.1` oder `192.168.1.0/24`
3. **Scan Type wählen**: Quick Scan (empfohlen für Start)
4. **OK klicken**

### 3. Ergebnisse sehen

- **Hosts-Tabelle**: Zeigt alle gefundenen Hosts
  - 🟢 Grün = Online
  - 🔴 Rot = Offline
  
- **Ports-Tabelle**: Zeigt Ports des ausgewählten Hosts
  - Klick auf Host → Ports werden angezeigt
  
- **Auto-Refresh**: Alle 10 Sekunden automatisch

---

## 📋 Features

### Aktuell verfügbar ✅

- **Scanning**:
  - Quick Scan (Top 100 Ports)
  - Full Scan (Alle Ports)
  - Stealth Scan (SYN Scan)
  - Custom Scans mit eigenen Args
  
- **UI**:
  - Host-Tabelle mit Sortierung
  - Port-Details pro Host
  - Color-Coding (State-based)
  - Tooltips mit Zusatzinfos
  - Status-Bar mit Scan-Progress
  
- **Database**:
  - Persistente Speicherung
  - Auto-Refresh
  - Selection-Preservation

### In Arbeit 🔄

- Config Dialog
- Theme-Switcher (Light/Dark)
- Progress Dialog während Scan
- Scan-Cancellation

---

## ⚙️ Konfiguration

### Config-Datei

**Windows**: `%LOCALAPPDATA%\GothamSecurity\legion\legion.toml`  
**Linux**: `~/.config/legion/legion.toml`

### Wichtige Settings

```toml
[scanning]
max_concurrent = 3  # Max. parallele Scans

[ui]
theme = "system"    # light, dark, system
auto_refresh = 10   # Sekunden

[tools]
nmap_path = "nmap"  # Pfad zu nmap
```

---

## 🔧 Scan-Typen

| Type | Ports | Speed | Stealth | Use Case |
|------|-------|-------|---------|----------|
| **Quick** | Top 100 | ⚡⚡⚡ | 🟡 Medium | Schneller Überblick |
| **Full** | 1-65535 | 🐌 Slow | 🟡 Medium | Vollständiger Scan |
| **Stealth** | Top 1000 | ⚡⚡ Fast | 🟢 High | Unauffälliger Scan |
| **Version** | Top 1000 | ⚡ Medium | 🔴 Low | Service-Erkennung |
| **OS Detection** | Top 1000 | ⚡ Medium | 🔴 Low | Betriebssystem |
| **Aggressive** | Top 1000 | ⚡ Medium | 🔴 Low | Alle Features |

---

## 🎨 UI-Elemente

### Menu Bar

- **File**: New Project, Open, Save, Exit
- **Scan**: New Scan, Stop Scan, Cancel All
- **View**: Refresh, Show Toolbar, Show Statusbar
- **Tools**: Settings (coming soon)
- **Help**: Documentation, About

### Toolbar

- 🔍 **New Scan**: Scan-Dialog öffnen
- 🔄 **Refresh**: Daten neu laden
- ⏹️ **Stop**: Aktiven Scan stoppen

### Status Bar

- **Links**: Aktueller Status (Ready, Scanning, etc.)
- **Rechts**: Projekt-Name

---

## 🐛 Troubleshooting

### UI startet nicht

```powershell
# Prüfen: Python-Version
py --version  # Sollte 3.10+

# Prüfen: Dependencies
pip install -r requirements.txt

# Prüfen: nmap
nmap --version  # Sollte 7.80+
```

### Scans laufen nicht

1. **nmap im PATH?**
   ```powershell
   # Windows
   $env:Path += ";C:\Program Files (x86)\Nmap"
   
   # Oder permanent in System-Umgebungsvariablen
   ```

2. **Firewall/Antivirus?**
   - nmap.exe erlauben
   - Python erlauben
   - Raw Socket Access (Admin-Rechte)

### UI aktualisiert sich nicht

- **F5 drücken**: Manueller Refresh
- **View → Refresh**: Menu-Item
- Auto-Refresh läuft alle 10 Sek

### Keine Hosts erscheinen

1. **Scan erfolgreich?** → Status-Bar prüfen
2. **Target erreichbar?** → Ping testen
3. **Firewall?** → Outbound-Rules prüfen

---

## 📝 Keyboard Shortcuts

| Shortcut | Aktion |
|----------|--------|
| `Ctrl+N` | New Scan |
| `F5` | Refresh |
| `Ctrl+Q` | Exit |
| `Ctrl+W` | Close Window |

*(Mehr Shortcuts in Zukunft)*

---

## 🔗 Weitere Dokumentation

- **PHASE5_SUMMARY.md**: Technische Details & Fortschritt
- **SCANNER_INTEGRATION_FIX.md**: qasync Problem & Lösung
- **tests/ui/README.md**: Test-Scripts & Debugging

---

## ✨ Was macht diese UI besonders?

### Modern Architecture

- **Qt6**: Neueste UI-Framework-Version
- **MVC Pattern**: Saubere Trennung
- **Async**: Scanner läuft parallel (qasync!)
- **Config**: TOML-basierte Konfiguration

### User Experience

- **Color-Coding**: Visuelles State-Feedback
- **Tooltips**: Zusatzinfos on-hover
- **Auto-Refresh**: Keine manuellen Clicks
- **Responsive**: UI bleibt flüssig während Scans

### Developer Experience

- **Dependency Injection**: Einfaches Testing
- **Qt Models**: Daten-UI getrennt
- **Signals/Slots**: Thread-safe Updates
- **Logging**: Statt print-Statements

---

## 🎯 Roadmap

### ✅ Completed (Phase 5)

- Task 1: UI Architecture
- Task 2: Database Bridge
- Task 3: Scanner Integration
- Task 4: Production Integration

### 📋 Coming Soon

- Task 5: Config Dialog
- Task 6: Main Window Migration
- Task 7: Testing & Polish

### 🔮 Future

- Plugin-System
- Custom Scripts
- Export/Import
- Advanced Filtering
- Network Graphs

---

**Fragen? Bugs?** → GitHub Issues  
**Beitragen?** → CONTRIBUTING.md

**Status**: Production-Ready für Scanning ✅  
**Version**: 0.5.0 (Phase 5)
