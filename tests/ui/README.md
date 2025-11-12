# UI Tests

UI-Tests für Legion Phase 5 (UI Migration).

---

## ⚠️ Wichtig: qasync erforderlich!

**Scanner-Integration benötigt qasync** für Qt + asyncio:
```powershell
pip install qasync
```

Ohne qasync: UI lädt, aber Scans triggern keine UI-Updates!

---

## 🚀 Haupt-Programm

```powershell
# Windows
$env:Path += ";C:\Program Files (x86)\Nmap"
py legion.py

# Settings-Dialog: File → Settings (Ctrl+,)
```

```bash
# Linux
python3 legion.py
```

**Neue Features:**
- ✅ Settings-Dialog mit 4 Tabs (General, Scanning, Tools, Advanced)
- ✅ TOML-Config Editor
- ✅ Theme-Switcher (light/dark/system)
- ✅ Tool-Path-Konfiguration

---

## 📋 Test-Dateien

### Aktive Tests (6 total)

| Datei | Zweck | qasync |
|-------|-------|--------|
| `test_mainwindow.py` | UI mit 5 Sample-Hosts | ✅ |
| `test_empty_scan.py` | Leere DB für echte Scans | ✅ |
| `test_settings_dialog.py` | Settings-Dialog | ❌ |
| `test_qasync_fix.py` | qasync Proof-of-Concept | ✅ |
| `test_scan_dialog.py` | Nur Scan-Dialog | ❌ |
| `test_nmap_scan.py` | Scanner ohne UI | ❌ |

### Gelöscht (Cleanup 12. Nov)

- ~~simple_ui_test.py~~ → `test_mainwindow.py`
- ~~start_ui.py~~ → `legion.py`
- ~~test_debug_scan.py~~ → Nicht mehr nötig
- ~~test_fresh_ui.py~~ → `test_empty_scan.py`
- ~~test_pipeline.py~~ → Veraltet
- ~~test_scan_debug.py~~ → Veraltet
- ~~test_eventfilter.py~~ → Legacy UI

---

## 🧪 Testing

### Test 1: UI mit Sample-Daten

```powershell
py tests\ui\test_mainwindow.py
```

- 5 Dummy-Hosts (192.168.1.x)
- Scan → New Scan funktioniert
- UI-Refresh bei Scan-Completion

### Test 2: Echte Scans

```powershell
py tests\ui\test_empty_scan.py
```

- Leere Tabelle beim Start
- Target: `127.0.0.1`
- Host erscheint nach Scan ✅

### Test 3: qasync Validation

```powershell
py tests\ui\test_qasync_fix.py
```

- Zeigt Callback-Kette in Console
- Validiert Scanner-Workers

---

## 📚 Dokumentation

- `docs/PHASE5_SUMMARY.md` - Progress
- `docs/SCANNER_INTEGRATION_FIX.md` - qasync
- `docs/QUICK_START.md` - User Guide

**Update**: 12. Nov 2025
