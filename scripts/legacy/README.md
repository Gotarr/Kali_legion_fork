# Legacy Scripts (Legion v1.x)

⚠️ **WARNUNG**: Diese Scripts sind **nicht kompatibel** mit Legion v2.0!

---

## 📋 Inhalt

### Shell Scripts

#### exec-in-shell
- **Beschreibung**: Interactive shell launcher
- **Plattform**: Linux only
- **Verwendung**: Startet eine interaktive Shell mit eval
- **Status**: Legacy - nicht in v2.0 verwendet

#### fingertool.sh
- **Beschreibung**: Benutzer-Enumeration via finger
- **Autor**: SECFORCE - Antonio Quina
- **Verwendung**: `./fingertool.sh <IP> [<WORDLIST>]`
- **Default Wordlist**: `/usr/share/metasploit-framework/data/wordlists/unix_users.txt`
- **Status**: Legacy - nicht in v2.0 verwendet

#### x11screenshot.sh
- **Beschreibung**: Screenshot über X11
- **Autor**: SECFORCE - Antonio Quina
- **Verwendung**: `./x11screenshot.sh <IP> <DISPLAY> [<OUTFOLDER>]`
- **Dependencies**: xwd, convert (ImageMagick), xdg-open
- **Plattform**: Linux only (X11)
- **Status**: Legacy - nicht in v2.0 verwendet

### Python Scripts (python/)

#### macvendors.py
- **Beschreibung**: MAC-Adresse zu Vendor-Mapping
- **API**: https://api.macvendors.com/
- **Problem**: Verwendet alte `self.dbHost` und `self.session` API
- **Migration**: Benötigt Umschreibung für `SimpleDatabase`

```python
# Alt (v1.x):
self.dbHost.vendor = result
self.session.add(self.dbHost)

# Neu (v2.0):
host = self.db.get_host_by_ip(ip)
host.vendor = result
self.db.save_host(host)
```

#### pyShodan.py
- **Beschreibung**: Shodan API Integration
- **⚠️ SICHERHEITSRISIKO**: Enthält **hardcoded API key**!
- **Problem**: 
  - Hardcoded credential: `apiKey = "SNYEkE0gdwNu9BRURVDjWPXePCquXqht"`
  - Alte DB-API
- **Migration**: 
  1. API Key in Config-System verschieben
  2. `SimpleDatabase` API verwenden

```python
# Richtige Implementierung (v2.0):
from legion.config import ConfigManager

config = ConfigManager.get_instance()
api_key = config.scanning.shodan_api_key  # Aus TOML
```

#### dummy.py
- **Beschreibung**: Test script
- **Funktion**: Gibt "Dummy!" aus und beendet mit Exit Code 1
- **Verwendung**: Test/Placeholder

#### __init__.py
- **Beschreibung**: Python Package Marker
- **Inhalt**: Leer (macht `python/` zum importierbaren Package)

---

## 🔄 Migration zu v2.0

### Schritte zur Portierung

1. **Neue Datei erstellen**: `scripts/custom/script_name.py`

2. **Imports anpassen**:
```python
# Alt
from app.database import Host

# Neu
from legion.core.models import Host
from legion.core.database import SimpleDatabase
from legion.config import ConfigManager
```

3. **Constructor anpassen**:
```python
# Alt
class MyScript():
    def __init__(self):
        self.dbHost = None
        self.session = None
    
    def setDbHost(self, dbHost):
        self.dbHost = dbHost
    
    def setSession(self, session):
        self.session = session

# Neu
class MyScript:
    def __init__(self, database: SimpleDatabase, config: ConfigManager):
        self.db = database
        self.config = config
```

4. **API Calls anpassen**:
```python
# Alt
self.dbHost.latitude = value
self.session.add(self.dbHost)

# Neu
host = self.db.get_host_by_ip(ip)
host.latitude = value
self.db.save_host(host)
```

5. **Credentials aus Config laden**:
```python
# Alt
api_key = "hardcoded_key"

# Neu
api_key = self.config.scanning.api_key
```

---

## 📚 Referenzen

### Neue v2.0 APIs
- **Database**: [src/legion/core/database.py](../../src/legion/core/database.py)
- **Models**: [src/legion/core/models/](../../src/legion/core/models/)
- **Config**: [src/legion/config/](../../src/legion/config/)

### Dokumentation
- **Architecture**: [docs/ARCHITECTURE_DETAILS.md](../../docs/ARCHITECTURE_DETAILS.md)
- **API Examples**: [docs/TESTING_GUIDE.md](../../docs/TESTING_GUIDE.md)

---

## ⚠️ Sicherheitshinweise

1. **API Keys**: Niemals hardcoden! Immer über Config-System
2. **Credentials**: In `legion.toml` oder Umgebungsvariablen
3. **Shell Scripts**: Validierung von Inputs vor `eval`

---

**Archiviert am**: 13. November 2025  
**Grund**: Inkompatibilität mit v2.0 Architecture  
**Alternative**: Neue Scripts in `scripts/custom/` erstellen
