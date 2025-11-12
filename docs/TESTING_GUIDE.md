# Legion v2.0 - Testing Guide

Anleitung zum Testen aller implementierten Phasen.

---

## 📋 Voraussetzungen

### Python installieren
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
pip install platformdirs PyQt6
```

---

## 🧪 Phase 1 Tests

### Test 1: Platform Detection
```powershell
py src/legion/platform/detector.py
```

### Test 2: Path Management  
```powershell
py src/legion/platform/paths.py
```

### Test 3: Privilege Checking
```powershell
py src/legion/platform/privileges.py
```

### Test 4: Main Entry Point
```powershell
cd src; py -m legion; cd ..
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
```

---

## 🧪 Phase 2 Tests

### Test 5: Tool Discovery
```powershell
py src\legion\tools\discovery.py
```

### Test 6: Tool Registry
```powershell
py src\legion\tools\registry.py
```

### Test 7: Nmap Wrapper (wenn nmap installiert)
```powershell
py src\legion\tools\nmap\wrapper.py
```

---

## 🧪 Phase 3 Tests

### Test 8: Data Models
```powershell
cd src; py -m legion.core.models.host; cd ..
```

### Test 9: Nmap XML Parser
```powershell
cd src; py -m legion.tools.nmap.parser; cd ..
```

### Test 10: Simple Database
```powershell
cd src; py -m legion.core.database; cd ..
```

### Test 11: Scanner Manager (mock mode)
```powershell
cd src; py -m legion.core.scanner; cd ..
```

### Test 12: End-to-End Integration (EMPFOHLEN!)
```powershell
cd src; py -m legion.core.integration_test; cd ..
```

### Erwartete Ausgabe (Phase 3)
```
======================================================================
PHASE 3 - END-TO-END INTEGRATION TEST
======================================================================

Database: integration_test
Location: C:\Users\...\AppData\Local\GothamSecurity\legion\projects\integration_test

----------------------------------------------------------------------
Parsing Sample Nmap XML Files
----------------------------------------------------------------------

Processing: Router (192.168.1.1)
  Found 1 host(s)
  Stored host: 192.168.1.1 with 3 port(s)

Processing: Workstation (192.168.1.10)
  Found 1 host(s)
  Stored host: 192.168.1.10 with 4 port(s)

Total stored: 3 hosts, 7 ports

----------------------------------------------------------------------
Database Contents
----------------------------------------------------------------------

IP Address: 192.168.1.1
Hostname: router.local
State: up
OS: Linux 3.2 - 4.9 (95% accuracy)
MAC: 00:11:22:33:44:55
Vendor: Cisco Systems

Ports: 3
  22/tcp - open - ssh (OpenSSH 8.2p1)
  80/tcp - open - http (Apache httpd 2.4.41)
  443/tcp - open - https (Apache httpd 2.4.41)

----------------------------------------------------------------------
Database Statistics
----------------------------------------------------------------------

Total Hosts: 3
  Up: 2
  Down: 1

Total Ports: 7
  Open: 7

Services detected:
  ssh: 1
  http: 1
  https: 1
  msrpc: 1

======================================================================
✅ Parser: Working
✅ Database: Working
✅ Data Models: Working
✅ Search Functions: Working

Phase 3 Core Logic is COMPLETE!
======================================================================
```

---

## 🧪 Phase 4 Tests

### Config System Tests
```powershell
py src/legion/config/config_test.py
```

### Erwartete Ausgabe
```
Test Results:
✅ Schema Validation (3 sub-tests)
✅ Config Manager (4 sub-tests)
✅ Template Creation (3 sub-tests)
✅ Legacy Migration (verified)
✅ Full Workflow (5 steps)

Results: 5/5 tests passed
```

---

## 🧪 Phase 5 Tests (UI)

Siehe **[tests/ui/README.md](../tests/ui/README.md)** für UI-Test Anleitung.

### Quick-Start
```powershell
# nmap in PATH
$env:Path += ";C:\Program Files (x86)\Nmap"

# Einfacher UI-Test
py tests\ui\simple_ui_test.py

# Mit Sample-Daten
py tests\ui\test_mainwindow.py

# Leere Datenbank (für echte Scans)
py tests\ui\test_empty_scan.py
```

---

**Letztes Update**: 12. November 2025
