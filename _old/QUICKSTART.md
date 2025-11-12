# Legion v2.0 - Quick Start Guide

## ✅ Alle Tests erfolgreich auf Windows 10!

### System-Info
- **OS**: Windows 10.0.19045
- **Python**: 3.10.5
- **Architecture**: AMD64

---

## 🚀 Schnelltest

```powershell
# Im Repository-Root ausführen:

# 1. Platform Detection
py src/legion/platform/detector.py

# 2. Path Management
py src/legion/platform/paths.py

# 3. Privilege Check
py src/legion/platform/privileges.py

# 4. Main Application
cd src
py -m legion
cd ..
```

---

## ✅ Getestete Funktionen

### ✅ Platform Detection
```
Platform: Windows 10.0.19045 on AMD64 - Python 3.10.5
System: Windows
is_windows: True
is_admin: False
```

### ✅ Path Management
Automatisch erstellte Verzeichnisse:
```
C:\Users\Kit_User_ML.MLML-U8FNBREUV2\AppData\Local\GothamSecurity\legion\
├── Cache\
│   └── tmp\
├── Logs\
├── projects\
├── wordlists\
└── tools\
```

### ✅ Privilege Management
```
is_admin: False
can_raw_socket: False
elevation_possible: True
```

---

## 📋 Nächste Schritte

### Phase 2: Tool Discovery (bereit zu starten)

Implementiere automatisches Finden von Tools:

```python
# src/legion/tools/discovery.py

class ToolDiscovery:
    def find_nmap(self) -> Optional[Path]:
        """
        Sucht nmap in:
        1. PATH
        2. C:\Program Files\Nmap\
        3. C:\Program Files (x86)\Nmap\
        4. User Config
        """
```

### Wichtig: Namenskonflikt vermeiden

**Problem**: Das alte `legion.py` im Root-Verzeichnis kollidiert mit dem neuen `src/legion/` Package.

**Lösung 1** (temporär - funktioniert):
```powershell
cd src
py -m legion
```

**Lösung 2** (später):
- Legacy Code nach `legacy/` verschieben
- Oder: Development-Installation mit `pip install -e .`

---

## 🎯 Was als nächstes?

1. **Tool Discovery implementieren** (Phase 2 starten)
2. **Nmap Wrapper** erstellen
3. **Erste Unit Tests** schreiben

**Bereit für Phase 2?** 🚀

---

**Datum**: 2025-11-11  
**Status**: Phase 1 ✅ Complete & Tested on Windows 10
