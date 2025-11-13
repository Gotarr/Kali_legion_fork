# Nmap NSE Scripts Integration

## Überblick

Legion v2.0 integriert Nmap NSE (Nmap Scripting Engine) für erweiterte Vulnerability-Detection und Host-Enumeration. Die Integration nutzt sowohl nmaps built-in Skripte als auch custom Legion-Skripte aus `scripts/nmap/`.

## Verfügbare NSE-Skripte

### Legion Custom Scripts (`scripts/nmap/`)

1. **vulners.nse**
   - **Autor**: gmedian@vulners.com
   - **Funktion**: CVE-Erkennung über vulners.com API
   - **Lizenz**: Same as Nmap
   - **Verwendung**: Erkennt bekannte Schwachstellen basierend auf CPE-Informationen
   - **Größe**: ~221 Zeilen Lua-Code

2. **shodan-api.nse**
   - **Funktion**: Shodan-Integration für zusätzliche Host-Informationen
   - **API-Key**: Erforderlich (über `--script-args` oder Config)
   - **Größe**: ~6.8 KB (neuere Version als nmap built-in)

3. **shodan-hq.nse**
   - **Funktion**: Alternative Shodan-Implementierung
   - **Unterschied**: Möglicherweise für Shodan Enterprise (HQ)

## Installation & Setup

### 1. Nmap Installation Prüfen

```powershell
# Windows
& "C:\Program Files (x86)\Nmap\nmap.exe" --version

# Linux/macOS
nmap --version
```

### 2. Legion NSE-Skripte Verwenden

Legion-Skripte befinden sich in `scripts/nmap/` und werden automatisch erkannt:

```python
from legion.tools.nmap import NmapTool

# Initialize
nmap = NmapTool()

# List available Legion scripts
scripts = await nmap.list_nse_scripts()
print(scripts)  # ['vulners', 'shodan-api', 'shodan-hq']

# Get script paths
legion_path = nmap.get_nse_script_path()  # scripts/nmap/
nmap_path = nmap.get_nmap_script_path()   # C:\Program Files (x86)\Nmap\scripts\
```

## Verwendung

### 1. Vulners CVE-Scan

**Python API:**
```python
from pathlib import Path
from legion.tools.nmap import NmapTool

nmap = NmapTool()

# Basic CVE scan (all vulnerabilities)
result = await nmap.scan_with_vulners("192.168.1.1")

# High-severity only (CVSS >= 7.0)
result = await nmap.scan_with_vulners(
    target="192.168.1.1",
    min_cvss=7.0,
    output_file=Path("scan_results/vulners_scan.xml"),
    timeout=600.0
)

# Parse results
if result.success:
    print(result.stdout)
    # Output enthält CVE-Links und CVSS-Scores
```

**Kommandozeile:**
```bash
# Manuell mit nmap
nmap -sV --script vulners --script-args mincvss=7.0 192.168.1.1

# Mit Legion's Skripten
nmap -sV --script-path ./scripts/nmap --script vulners 192.168.1.1
```

### 2. Shodan-Integration

**Python API:**
```python
from legion.tools.nmap import NmapTool

nmap = NmapTool()

# Shodan scan (requires API key)
result = await nmap.scan_with_shodan(
    target="8.8.8.8",
    api_key="YOUR_SHODAN_API_KEY"
)

if result.success:
    print(result.stdout)
    # Output enthält Shodan-Metadaten
```

**Kommandozeile:**
```bash
nmap -sn --script shodan-api --script-args shodan-api.apikey=YOUR_KEY 8.8.8.8
```

### 3. Custom NSE Scripts

**Python API:**
```python
# Beliebiges NSE-Skript ausführen
result = await nmap.scan(
    target="192.168.1.1",
    args=["-sV"],
    script="http-enum",
    script_args={"displayall": "true"}
)

# Legion's custom scripts verwenden
result = await nmap.scan_with_custom_scripts(
    target="192.168.1.1",
    use_legion_scripts=True  # Aktiviert --script-path
)
```

**Kommandozeile:**
```bash
# Einzelnes Skript
nmap -sV --script http-title 192.168.1.1

# Mehrere Skripte
nmap -sV --script "vulners,http-enum" 192.168.1.1

# Script-Argumente
nmap -sV --script vulners --script-args mincvss=5.0 192.168.1.1
```

## Konfiguration

### ScanningConfig Optionen

```python
from legion.config import ScanningConfig

config = ScanningConfig(
    # NSE-Skripte aktivieren/deaktivieren
    enable_nse_scripts=True,
    
    # Custom script path (None = use Legion's scripts/nmap/)
    nse_script_path=None,
    
    # Vulners automatisch bei -sV scans
    enable_vulners=False,
    vulners_min_cvss=0.0,  # 0.0 = alle, 7.0 = high severity
    
    # Shodan API-Key
    shodan_api_key=""  # Niemals hardcoden!
)

# Validate configuration
config.validate()
```

### Environment Variables (Empfohlen)

```bash
# Linux/macOS
export SHODAN_API_KEY="your_key_here"

# Windows PowerShell
$env:SHODAN_API_KEY = "your_key_here"

# Python
import os
api_key = os.environ.get("SHODAN_API_KEY", "")
```

## Script-Details

### Vulners.nse

**Funktionsweise:**
1. Nmap führt Version Detection (`-sV`) durch
2. Extrahiert CPE (Common Platform Enumeration) Strings
3. Sendet CPEs an vulners.com API
4. Empfängt CVE-Liste mit CVSS-Scores
5. Gibt formatierte Ausgabe mit Links aus

**Output-Format:**
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| vulners:
|   cpe:/a:openbsd:openssh:7.2p2:
|       CVE-2016-10009  7.5     https://vulners.com/cve/CVE-2016-10009
|       CVE-2016-10010  7.5     https://vulners.com/cve/CVE-2016-10010
|       CVE-2016-10708  7.5     https://vulners.com/cve/CVE-2016-10708
```

**Vorteile:**
- Keine lokale CVE-Datenbank (250+ GB)
- Aktuelle Daten von vulners.com
- CVSS-Filtering möglich
- Direkte Links zu Exploit-Details

**Limitierungen:**
- Benötigt Internetverbindung
- API rate limits möglich
- Nur für identifizierte Software-Versionen

### Shodan-api.nse

**Funktionsweise:**
1. Nimmt IP-Adresse als Input
2. Fragt Shodan API ab
3. Gibt Metadaten zurück (Ports, Dienste, Geolocation, etc.)

**Output-Format:**
```
Host script results:
| shodan-api:
|   Shodan API response:
|     Open Ports: 22, 80, 443
|     Country: United States
|     City: Mountain View
|     ISP: Google LLC
|     Vulnerabilities:
|_      CVE-2019-12345
```

**Vorteile:**
- Zusätzliche Kontext-Informationen
- Historische Scan-Daten
- Vulnerability-Korrelation

**Limitierungen:**
- API-Key erforderlich (kostenpflichtig)
- Rate limits (je nach Plan)
- Nur für öffentliche IPs

## Best Practices

### 1. API-Keys sicher speichern

```python
# ❌ FALSCH - Niemals hardcoden!
api_key = "SNYEkE0gdwNu9BRURVDjWPXePCquXqht"

# ✅ RICHTIG - Environment Variable
import os
api_key = os.environ.get("SHODAN_API_KEY")
if not api_key:
    raise ValueError("SHODAN_API_KEY not set")

# ✅ RICHTIG - Config-File (mit Permissions 600)
from legion.config import load_config
config = load_config()
api_key = config.scanning.shodan_api_key
```

### 2. CVSS-Filtering

```python
# Nur kritische Schwachstellen (CVSS >= 9.0)
result = await nmap.scan_with_vulners("target", min_cvss=9.0)

# Hohe und kritische (CVSS >= 7.0)
result = await nmap.scan_with_vulners("target", min_cvss=7.0)

# Alle (default)
result = await nmap.scan_with_vulners("target")
```

### 3. Timeout-Management

```python
# NSE-Skripte können langsam sein
result = await nmap.scan(
    target="192.168.1.0/24",
    script="vulners",
    timeout=1800.0  # 30 Minuten für /24 Netz
)
```

### 4. Error Handling

```python
try:
    result = await nmap.scan_with_vulners("target", min_cvss=7.0)
    if not result.success:
        print(f"Scan failed: {result.stderr}")
except Exception as e:
    print(f"Error: {e}")
```

## Performance

### Vulners.nse

- **Geschwindigkeit**: ~1-2 Sekunden pro Host (bei -sV)
- **Bottleneck**: Netzwerk-Latenz zu vulners.com
- **Optimierung**: 
  - Parallele Scans mit `-T4` oder `-T5`
  - `--min-hostgroup` für Batch-Queries

### Shodan-api.nse

- **Geschwindigkeit**: ~0.5-1 Sekunde pro Host
- **Bottleneck**: Shodan API rate limits
- **Optimierung**:
  - Premium API-Plan (höhere Limits)
  - Batch-Requests (wenn unterstützt)

## Troubleshooting

### 1. "nmap not found"

**Problem**: nmap nicht im PATH

**Lösung (Windows)**:
```powershell
# Temporär
$env:PATH += ";C:\Program Files (x86)\Nmap"

# Permanent (Systemvariable)
[System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files (x86)\Nmap", [System.EnvironmentVariableTarget]::Machine)
```

**Lösung (Linux)**:
```bash
# Ubuntu/Debian
sudo apt install nmap

# CentOS/RHEL
sudo yum install nmap

# Verify
which nmap
```

### 2. "Script not found: vulners"

**Problem**: Legion-Skript nicht in nmap's search path

**Lösung**:
```python
# Use scan_with_custom_scripts() instead of scan_with_vulners()
result = await nmap.scan(
    target="192.168.1.1",
    args=["-sV", "--script-path", "./scripts/nmap", "--script", "vulners"]
)
```

### 3. "API key invalid" (Shodan)

**Problem**: Ungültiger oder fehlender API-Key

**Lösung**:
```python
# Test API key first
import requests
r = requests.get(f"https://api.shodan.io/api-info?key={api_key}")
if r.status_code != 200:
    print("Invalid API key")
```

### 4. "No vulnerabilities found"

**Mögliche Ursachen**:
1. Software-Version nicht erkannt (`-sV` nicht verwendet)
2. Keine bekannten CVEs für diese Version
3. `mincvss` zu hoch gesetzt
4. Vulners.com API nicht erreichbar

**Diagnose**:
```bash
# Verify version detection
nmap -sV 192.168.1.1

# Test vulners manually
nmap -sV --script vulners -d 192.168.1.1  # Debug mode
```

## Vergleich: Built-in vs Legion Scripts

| Skript | Nmap Built-in | Legion Custom | Unterschied |
|--------|---------------|---------------|-------------|
| vulners.nse | ❌ Nein | ✅ Ja | Legion-exklusiv |
| shodan-api.nse | ✅ Ja (6.5 KB) | ✅ Ja (6.8 KB) | Legion hat neuere Version |
| shodan-hq.nse | ❌ Nein | ✅ Ja | Legion-exklusiv |

**Empfehlung**: Verwende `--script-path` um Legion-Skripte zu priorisieren:

```bash
nmap --script-path ./scripts/nmap --script shodan-api 8.8.8.8
```

## Integration mit Legion UI

### Zukünftige Features (Phase 7+)

- [ ] UI-Button "Scan with Vulners" in Host-Details
- [ ] Automatische CVE-Anzeige neben Service-Versionen
- [ ] Shodan-Integration im Host-Profil
- [ ] NSE-Skript-Auswahl im Scan-Dialog
- [ ] API-Key-Management in Settings
- [ ] Vulnerability-Dashboard mit CVSS-Scores

## Sicherheit

### Do's

✅ **API-Keys in Environment Variables**
```bash
export SHODAN_API_KEY="your_key"
```

✅ **Config-Files mit restriktiven Permissions**
```bash
chmod 600 ~/.legion/config.yaml
```

✅ **Validate API responses**
```python
if "error" in response:
    raise ValueError(f"API error: {response['error']}")
```

### Don'ts

❌ **Niemals API-Keys in Code hardcoden**
```python
# FALSCH!
api_key = "SNYEkE0gdwNu9BRURVDjWPXePCquXqht"
```

❌ **Niemals Keys in Git committen**
```bash
# Add to .gitignore
*.key
secrets.yaml
.env
```

❌ **Niemals Keys in Logs ausgeben**
```python
# FALSCH!
print(f"Using API key: {api_key}")

# RICHTIG!
print(f"Using API key: {api_key[:4]}...{api_key[-4:]}")
```

## Testing

### Unit Tests

```python
import pytest
from legion.tools.nmap import NmapTool

@pytest.mark.asyncio
async def test_vulners_scan():
    nmap = NmapTool()
    result = await nmap.scan_with_vulners(
        "scanme.nmap.org",
        min_cvss=7.0,
        timeout=300.0
    )
    assert result.success
    assert "vulners" in result.stdout.lower()

@pytest.mark.asyncio
async def test_list_nse_scripts():
    nmap = NmapTool()
    scripts = await nmap.list_nse_scripts()
    assert "vulners" in scripts
    assert "shodan-api" in scripts
```

### Integration Tests

```bash
# Test with safe target (scanme.nmap.org)
nmap -sV --script vulners scanme.nmap.org

# Test with local test server
python scripts/test_servers.py &
nmap -sV --script vulners localhost -p 8080
```

## Referenzen

### Offizielle Dokumentation

- [Nmap Scripting Engine (NSE)](https://nmap.org/book/nse.html)
- [Vulners.com API](https://vulners.com/api/v3/)
- [Shodan API Documentation](https://developer.shodan.io/)
- [Nmap NSE Library](https://nmap.org/nsedoc/)

### Tools

- [Vulners NSE Script](https://github.com/vulnersCom/nmap-vulners)
- [Shodan CLI](https://cli.shodan.io/)
- [Nmap Official Site](https://nmap.org/)

### CVE Datenbanken

- [Vulners Database](https://vulners.com/)
- [NVD (National Vulnerability Database)](https://nvd.nist.gov/)
- [CVE.org](https://cve.org/)
- [Exploit-DB](https://www.exploit-db.com/)

## Changelog

### Version 2.0.0 (13. November 2025)

- ✅ Initial NSE integration
- ✅ Added vulners.nse support
- ✅ Added shodan-api.nse support
- ✅ Created NmapTool.scan_with_vulners()
- ✅ Created NmapTool.scan_with_shodan()
- ✅ Added ScanningConfig NSE options
- ✅ Documentation created

## FAQ

**Q: Warum 250+ GB CVE-Datenbank nicht lokal?**
A: Vulners.nse nutzt bewusst eine Remote-API, da die vollständige CVE-Datenbank zu groß ist und ständig aktualisiert wird.

**Q: Benötige ich Shodan API-Key?**
A: Ja, für shodan-api.nse. Free Plan: 100 Queries/Monat, Premium: unbegrenzt.

**Q: Funktionieren NSE-Skripte auf Windows?**
A: Ja, Nmap for Windows enthält Lua-Runtime. Alle NSE-Skripte sind cross-platform.

**Q: Kann ich eigene NSE-Skripte schreiben?**
A: Ja! Lua-Kenntnisse erforderlich. Siehe [NSE Development](https://nmap.org/book/nse-tutorial.html).

**Q: Wie update ich NSE-Skripte?**
A: 
```bash
# Update nmap (enthält neue Skripte)
sudo apt update && sudo apt upgrade nmap

# Oder manuell herunterladen
wget https://svn.nmap.org/nmap/scripts/vulners.nse -O scripts/nmap/vulners.nse
```

**Q: Sind die Skripte sicher?**
A: Legion's NSE-Skripte stammen von vertrauenswürdigen Quellen (Nmap project, vulners.com). Immer Source-Code reviewen vor Ausführung!
