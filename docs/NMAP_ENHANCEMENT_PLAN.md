# Nmap Enhancement Plan (Phase 6)

Status: Sprint 1 ✅ Complete | Sprint 2 Planned (2025-11-12)
Owner: Gotarr

## Ziele
- Funktionsparität und Verbesserungen gegenüber Legacy-Nmap-Integration
- Stabiler Import/Export und reproduzierbare Scans
- Nutzerfreundliche Profile (Easy/Hard), ohne Einschränkung der Flexibilität

## Legacy vs Neu – Gap-Analyse

| Feature | Legacy | Neu (Ist) | Status |
|---|---|---|---|
| Staged Scans (Stage 1–5) | Ja (einstellbar) | Nein | Sprint 2 geplant |
| Host Discovery separat | Optional (Checkbox) | ✅ Discovery-Prepass | ✅ Umgesetzt |
| Hard Mode: FIN/NULL/Xmas etc. | UI + Mapping | ✅ Vollständig gemappt | ✅ Umgesetzt |
| Ping-Typen (ICMP/PS/PT/PP/PM/-Pn) | UI + Mapping | ✅ 7 Typen gemappt | ✅ Umgesetzt |
| Fragmentation (-f) | UI + Mapping | ✅ Flag-Mapping | ✅ Umgesetzt |
| Custom Args | Textfeld | ✅ Whitespace-split append | ✅ Umgesetzt |
| Timing Slider | Konkretisiert Optionen + T-Profile | ✅ T4/T5 RTT/Delay extras | ✅ Umgesetzt |
| Live-Progress (--stats-every) | Teilweise (QProcess) | Nein | Sprint 2 geplant |
| XML Import | Ja | ✅ NmapXMLParser + DB | ✅ Umgesetzt |

## Sprint 1 – Abgeschlossen ✅

### Implementierte Features:
1. **XML Import** (`mainwindow._import_xml()`)
   - Nutzt NmapXMLParser für robustes Parsing
   - Speichert Hosts/Ports über SimpleDatabase
   - UI-Refresh und Erfolgsmeldungen
   - Error-Handling für fehlende/fehlerhafte Dateien

2. **Hard Mode Mapping** (`scanner._build_scan_args()`)
   - Scan-Typen: tcp(-sT), fin(-sF), null(-sN), xmas(-sX), obfuscated(--data-length 5 --randomize-hosts), tcp_ping(-PS), udp_ping(-PU)
   - Ping-Typen: disable(-Pn), default(auto), icmp(-PE), syn(-PS), ack(-PA), timestamp(-PP), netmask(-PM)
   - Fragmentation: -f Flag
   - Custom Args: Whitespace-split und append

3. **Timing Refinement** (`scanner._build_scan_args()`)
   - T4 extras: --max-rtt-timeout 1250ms, --min-rtt-timeout 100ms, --initial-rtt-timeout 500ms, --max-retries 6, --scan-delay 10ms
   - T5 extras: --max-rtt-timeout 300ms, --min-rtt-timeout 50ms, --initial-rtt-timeout 250ms, --max-retries 2, --host-timeout 15m, --script-timeout 10m, --scan-delay 5ms

4. **Discovery Prepass** (`scanner._execute_scan()`)
   - Optional wenn `options['discovery']` gesetzt
   - Führt `nmap -sn target -oX discover.xml` aus
   - Parsed up_hosts aus Discovery-XML
   - Injiziert als `resolved_targets` für Hauptscan

### Test-Ergebnisse:
**14/14 Tests erfolgreich** (100% Pass-Rate)

#### Test-Daten erstellt:
- **3 neue XML-Fixtures**:
  - `multiple-hosts-scan.xml` (3 Hosts, 13 Ports)
  - `discovery-scan.xml` (3 Hosts, 0 Ports, -sn scan)
  - `vuln-scan-with-scripts.xml` (1 Host, 4 Ports, NSE scripts)

- **4 Scan-Logs** (JSONL-Format):
  - Quick Scan (completed, 3 hosts)
  - Discovery Scan (completed, 3 hosts)
  - Vuln Scan (completed, 1 host)
  - Failed Scan (invalid target)

- **3 Scan-Results** (UUID-benannte XML-Kopien in `scan_results/`)

#### Test-Abdeckung:
✅ Parser-Initialisierung  
✅ Gültige XML-Dateien parsen  
✅ Host-Anzahl/-Details korrekt  
✅ Port-Anzahl/-Details korrekt  
✅ Service-Details extrahieren  
✅ Scan-Statistiken  
✅ Fehlerbehandlung (FileNotFound, Malformed XML)  
✅ String-basiertes Parsen  
✅ Multi-Host Scans  
✅ Discovery-only Scans  
✅ NSE Script-Ausgaben  

### Akzeptanzkriterien Sprint 1: ✅ Erfüllt
- ✅ Import von .xml funktioniert und speichert Hosts/Ports
- ✅ Hard Mode Optionen erzeugen nachvollziehbare CLI-Argumente
- ✅ Discovery-Checkbox führt zu vorgeschaltetem `nmap -sn` (Up-Hosts weiterverarbeitet)
- ✅ Alle Parser-Tests bestehen
- ✅ Realistische Test-Daten vorhanden

## Sprint 2 – Geplant

### Prioritäten:
5. **Staged Scan Profile** (mehrere aufeinanderfolgende Läufe je Ziel)
6. **Live-Progress** über `--stats-every` (Streaming/Parsing stdout)
7. **Parser-Erweiterungen** (NSE-Output strukturierter)
8. **AddHostDialog Parsing Test** (Komma/Semikolon/Newline)
9. **Scanner-Event-Logging Test** (JSON-Struktur validieren)

## Erfolgskriterien
- ✅ 80% der Legacy-Nmap-Features abgedeckt (Sprint 1)
- ✅ UI-Operationen (Queue/Cancel/Import) ohne Hänger
- ✅ 100% Test-Pass-Rate für Parser
- 🔄 Dokumentierte Profile und reproduzierbare Ausgaben
- 🔄 Live-Progress für besseres UX

## Technische Notizen

### Dateistruktur:
```
tests/
  ├── test_nmap_parser.py (14 Tests)
  ├── TEST_DATA_README.md (Dokumentation)
  └── parsers/nmap-fixtures/
      ├── valid-nmap-report.xml
      ├── multiple-hosts-scan.xml
      ├── discovery-scan.xml
      ├── vuln-scan-with-scripts.xml
      └── malformed-nmap-report.xml

scan_results/
  ├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.xml
  ├── b2c3d4e5-f6a7-8901-bcde-f12345678901.xml
  └── c3d4e5f6-a7b8-9012-cdef-123456789012.xml

scan_logs/
  ├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.json
  ├── b2c3d4e5-f6a7-8901-bcde-f12345678901.json
  ├── c3d4e5f6-a7b8-9012-cdef-123456789012.json
  └── d4e5f6a7-b8c9-0123-def1-234567890123.json
```

### Code-Änderungen:
- `src/legion/ui/mainwindow.py` (~1306-1360): XML Import
- `src/legion/core/scanner.py` (~242-280, ~308-390): Discovery + Hard Mode
- `tests/test_nmap_parser.py` (172 Lines): Comprehensive tests

### Ausführung:
```powershell
cd tests
py -m pytest test_nmap_parser.py -v
# Ergebnis: 14 passed in 0.06s
```
