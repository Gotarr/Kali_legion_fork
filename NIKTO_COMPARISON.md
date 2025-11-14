# Nikto Integration: Legacy vs. New Legion

## Feature-Vergleich

| Feature | Legacy Legion | Neues Legion | Status |
|---------|---------------|--------------|--------|
| **Grundfunktionalität** |
| Nikto Command-Building | ✅ Automatisch via Controller | ✅ NiktoTool API (minimal) | ⚠️ Basis vorhanden |
| Service-Erkennung | ✅ Auto für HTTP/HTTPS | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Port-Selection | ✅ Auto aus Nmap-Scan | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| **Scan Options** |
| Basic Scan | ✅ `-h host -p port` | ✅ NiktoTool.run() | ✅ Gleich |
| SSL/TLS Support | ✅ Auto für HTTPS (`-ssl`) | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Tuning Options | ✅ `-Tuning` Parameter | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Custom User-Agent | ✅ Konfigurierbar | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Timeout | ✅ `-timeout N` | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Follow Redirects | ✅ Option vorhanden | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| **Output Formats** |
| Text Output | ✅ Default | ✅ stdout/stderr | ✅ Gleich |
| CSV Output | ✅ `-Format csv` | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| XML Output | ✅ `-Format xml` | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| HTML Report | ✅ `-Format htm` | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| **UI & UX** |
| Dedizierter Tab | ✅ Tools/Nikto Tab | ❌ Kein UI | ❌ **FEHLT** |
| Live Output Display | ✅ QPlainTextEdit | ❌ Kein UI | ❌ **FEHLT** |
| Progress Indication | ✅ Status Label | ❌ Kein UI | ❌ **FEHLT** |
| Multiple Scans | ✅ Parallel in Tabs | ❌ Kein UI | ❌ **FEHLT** |
| Context Menu | ✅ "Send to Nikto" | ❌ Nicht vorhanden | ❌ **FEHLT** |
| **Results Handling** |
| Parse Results | ✅ Basic Parsing | ⚠️ Nur Lines/Errors | ⚠️ Minimal |
| Vulnerability List | ✅ Strukturiert | ❌ Nicht vorhanden | ❌ **FEHLT** |
| Severity Rating | ✅ Erkennbar | ❌ Nicht vorhanden | ❌ **FEHLT** |
| Export Results | ✅ CSV/XML/HTML | ❌ Nicht vorhanden | ❌ **FEHLT** |
| Database Storage | ✅ Gespeichert | ❌ Nicht vorhanden | ❌ **FEHLT** |
| **Process Management** |
| Kill Process | ✅ PID-Tracking | ⚠️ BaseTool only | ⚠️ Basis vorhanden |
| Process Cancellation | ✅ AsyncIO | ⚠️ BaseTool only | ⚠️ Basis vorhanden |
| **Automated Scans** |
| Scheduler Integration | ✅ legion.conf (`nikto=...`) | ❌ Nicht implementiert | ❌ **FEHLT** |
| Port-basierte Auto-Scans | ✅ 7 Services (http, https, ssl, soap, etc.) | ❌ Nicht implementiert | ❌ **FEHLT** |
| HTTP/HTTPS Auto-Detect | ✅ Auto-Start nach Nmap | ❌ Nicht implementiert | ❌ **FEHLT** |
| Output File Naming | ✅ `nikto_[IP]_[PORT].txt` | ❌ Nicht implementiert | ❌ **FEHLT** |
| `-C all` (All Checks) | ✅ Default in legion.conf | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| **Validation** |
| Port Check | ✅ Nur HTTP Ports | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| SSL Detection | ✅ Auto für 443, 8443 | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| **Configuration** |
| Tool Path | ✅ Settings Dialog | ✅ Registry Auto-Discovery | ✅ Verbessert |
| Default Options | ✅ Config-basiert | ❌ Nicht vorhanden | ❌ **FEHLT** |
| Custom Database | ✅ `-dbcheck` Path | ⚠️ Nicht implementiert | ❌ **FEHLT** |

---

## Zusammenfassung

### ⚠️ **Status: Nur Grundgerüst vorhanden**

Das neue Legion hat aktuell **nur ein minimales NiktoTool-Wrapper**:
- ✅ Tool-Discovery via Registry
- ✅ Async execution
- ✅ Basic stdout/stderr parsing
- ❌ **Keine UI Integration**
- ❌ **Keine automatisierten Scans** (Legacy hatte Scheduler!)
- ❌ **Keine strukturierte Ergebnis-Ausgabe**

**Legacy hatte:**
- ✅ Automatische Nikto-Starts nach Nmap-Scan (legion.conf Scheduler)
- ✅ Trigger für 7 Services: `http`, `https`, `ssl`, `soap`, `http-proxy`, `http-alt`, `https-alt`
- ✅ Command: `nikto -o [OUTPUT].txt -p [PORT] -h [IP] -C all`
- ✅ Prozess-Management im Controller
- ✅ Output-Files automatisch gespeichert

### ❌ **Komplett fehlende Features**

#### **UI Integration**
- Kein Nikto-Tab oder Widget
- Keine "Send to Nikto" Context-Menu Option
- Keine Live-Output-Anzeige
- Keine Results-Darstellung

#### **Scan-Funktionalität**
- Keine Auto-Detection von HTTP/HTTPS Services
- Keine SSL/TLS Support (`-ssl` Flag)
- Keine Tuning-Optionen (`-Tuning 1-9`)
- Keine Output-Format-Auswahl (CSV/XML/HTML)

#### **Results Handling**
- Kein Parser für Nikto-Output
- Keine Vulnerability-Kategorisierung
- Keine Severity-Bewertung
- Kein Export-System

#### **Automation**
- Kein Scheduler für Auto-Scans
- Keine legion.conf Integration
- Keine Port-basierte Trigger

---

## Legacy Implementation (Referenz)

### legion.conf Auto-Scan
```conf
# Legacy Nikto-Config aus legion.conf:
nikto=Run nikto, nikto -o [OUTPUT].txt -p [PORT] -h [IP] -C all, "http,https,ssl,soap,http-proxy,http-alt,https-alt"
```

**Details:**
- **Trigger-Services**: Läuft automatisch für: `http`, `https`, `ssl`, `soap`, `http-proxy`, `http-alt`, `https-alt`
- **Output**: Text-File (`-o [OUTPUT].txt`)
- **Tuning**: `-C all` (alle Checks)
- **Automatisch**: Wird vom Scheduler nach Nmap-Scan gestartet

### Legacy Scheduler Integration
```python
# controller.py - Automatische Nikto-Starts
self.nmapImporter.schedule.connect(self.scheduler)  # run automated attacks

# Beim Nmap-Import wird für jeden HTTP/HTTPS Port automatisch Nikto gestartet
# Basierend auf legion.conf Service-Mapping
```

### Typisches Legacy-Command
```bash
# Automatisch generiert vom Scheduler:
nikto -o /path/to/output/nikto_192.168.1.1_80.txt -p 80 -h 192.168.1.1 -C all
```

---

## Empfohlene Implementierung

### 🎯 **Phase 1: Basic UI Integration**
```python
# 1. NiktoWidget erstellen (ähnlich BruteWidget)
class NiktoWidget(QtWidgets.QWidget):
    - Live Output Console
    - Run/Stop Button
    - Progress Display
    - Results Tree View

# 2. Nikto-Tab hinzufügen
Main Tabs: [Hosts] [Hydra] [Nikto] [Results] [Settings]

# 3. Context Menu
Right-click on HTTP/HTTPS port → "Send to Nikto"
```

### 🎯 **Phase 2: Scan Options**
```python
# NiktoScanDialog
class NiktoScanDialog:
    - Host/Port (pre-filled)
    - SSL Checkbox (auto-detect)
    - Tuning Options (1-9)
    - Output Format (txt/csv/xml/html)
    - Timeout Slider
    - Custom Options TextField
```

### 🎯 **Phase 3: Results Parsing**
```python
# NiktoOutputParser
class NiktoOutputParser:
    def parse_csv(output: str) -> List[NiktoFinding]:
        # Parse CSV format
        # Extract: vulnerability, URL, description, severity
    
    def parse_txt(output: str) -> List[NiktoFinding]:
        # Parse text format
        # Detect OSVDB entries, server info, vulnerabilities
```

### 🎯 **Phase 4: Automation**
```python
# Auto-Scan Integration
def on_nmap_scan_complete(hosts):
    for host in hosts:
        for port in host.ports:
            if port.service in ["http", "https"]:
                # Auto-trigger Nikto
                schedule_nikto_scan(host, port)
```

---

## Nikto-spezifische Features

### Tuning Options (`-Tuning`)
```
1 - Interesting File / Seen in logs
2 - Misconfiguration / Default File
3 - Information Disclosure
4 - Injection (XSS/Script/HTML)
5 - Remote File Retrieval - Inside Web Root
6 - Denial of Service
7 - Remote File Retrieval - Server Wide
8 - Command Execution / Remote Shell
9 - SQL Injection
0 - File Upload
a - Authentication Bypass
b - Software Identification
c - Remote Source Inclusion
x - Reverse Tuning (exclude)
```

### Common Options
```bash
# Basic scan
nikto -h target.com -p 80

# SSL scan
nikto -h target.com -p 443 -ssl

# With tuning (only check for XSS/Injection)
nikto -h target.com -p 80 -Tuning 4

# CSV output
nikto -h target.com -p 80 -Format csv -o results.csv

# Custom user agent
nikto -h target.com -p 80 -useragent "Mozilla/5.0 Custom"

# Timeout
nikto -h target.com -p 80 -timeout 5

# Multiple ports
nikto -h target.com -p 80,443,8080 -ssl
```

---

## Fazit

### ❌ **Aktueller Stand: Nicht produktionsreif**
- Nur minimales Tool-Wrapper vorhanden
- Keine UI-Integration
- Keine automatisierten Scans
- Keine Result-Parsing

### ✅ **Positiv**
- Tool-Discovery funktioniert
- Async execution möglich
- Architektur vorbereitet (BaseTool)

### 🔧 **Empfehlung**
Nikto-Integration komplett **nach dem Hydra-Vorbild** implementieren:

1. **NiktoWidget** mit Live-Output Console
2. **Nikto-Tab** mit Services | Running | History
3. **Context Menu** "Send to Nikto" für HTTP/HTTPS Ports
4. **NiktoOutputParser** für CSV/XML/TXT Parsing
5. **Results-Tab** Integration für Vulnerabilities
6. **Auto-Scan** für neu entdeckte HTTP/HTTPS Services

**Priorität:** Mittel bis Niedrig (Hydra ist wichtiger für Pentesting-Workflow)

**Empfohlene Reihenfolge:**
1. ✅ Hydra komplett fertigstellen (DONE ✅)
2. ⏭️ Nikto UI Integration (Phase 1-2)
3. ⏭️ Nikto Results Parsing (Phase 3)
4. ⏭️ Nikto Automation (Phase 4)
