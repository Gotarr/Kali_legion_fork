# Legion Scripts

Scripts und Tools für erweiterte Funktionalität in Legion v2.0.

---

## 📂 Struktur

### nmap/
Nmap NSE (Nmap Scripting Engine) Scripts für erweiterte Scans:

- **vulners.nse** - Vulnerability Database Integration (Vulners.com)
- **shodan-api.nse** - Shodan API Integration
- **shodan-hq.nse** - Shodan HQ Integration

**Verwendung**: Diese Scripts werden automatisch von Nmap geladen, wenn sie im richtigen Verzeichnis liegen.

```bash
# Beispiel: Vulners Scan
nmap --script vulners -sV <target>

# Beispiel: Shodan API
nmap --script shodan-api --script-args shodan-api.apikey=<key> <target>
```

### legacy/
Archivierte Scripts aus Legion v1.x - **nicht kompatibel mit v2.0**.

Siehe **[legacy/README.md](legacy/README.md)** für Details.

---

## 🔧 Verwendung in Legion v2.0

### Nmap Scripts
Legion v2.0 kann diese NSE Scripts automatisch nutzen:

1. **Automatisch**: Wenn Nmap die Scripts findet
2. **Manuell**: Über Custom Scan-Profile in Settings

**Konfiguration**:
```toml
# legion.toml
[scanning]
nmap_script_path = "scripts/nmap"
```

### Eigene Scripts hinzufügen

Für neue v2.0-kompatible Scripts:

1. Erstelle `scripts/custom/` Verzeichnis
2. Implementiere mit neuem `SimpleDatabase` API
3. Dokumentiere in diesem README

**Beispiel-Struktur**:
```python
# scripts/custom/my_script.py
from legion.core.database import SimpleDatabase

class MyScript:
    def __init__(self, database: SimpleDatabase):
        self.db = database
    
    def run(self, host_ip: str):
        # Implementierung
        pass
```

---

## ⚠️ Wichtige Hinweise

### Legacy Scripts (scripts/legacy/)
- ❌ **Nicht kompatibel** mit v2.0 `SimpleDatabase`
- ❌ Verwenden altes SQLAlchemy API
- ❌ Hardcoded credentials (Sicherheitsrisiko!)
- ✅ Nur für Referenz archiviert

### Migration
Wenn du Legacy-Scripts portieren möchtest:

1. Ersetze `self.session` mit `SimpleDatabase` calls
2. Ersetze `self.dbHost` mit `Host` model
3. Entferne hardcoded API keys
4. Nutze Config-System für Credentials

Siehe **[docs/ARCHITECTURE_DETAILS.md](../docs/ARCHITECTURE_DETAILS.md)** für neue API.

---

## 📚 Weitere Ressourcen

- **Nmap NSE Scripts**: https://nmap.org/nsedoc/
- **Vulners API**: https://vulners.com/api
- **Shodan API**: https://developer.shodan.io/

---

**Version**: 2.0.0-alpha6  
**Letzte Aktualisierung**: 13. November 2025
