# Hydra Integration - Wordlist Features

## 📋 Zusammenfassung

Hydra ist vollständig in Legion integriert mit intelligenter Wordlist-Verwaltung aus `scripts/wordlists/`.

## 🎯 Features

### 1. **Automatische Wordlist-Auswahl**

Beim Starten eines Hydra-Angriffs wählt Legion automatisch die passenden Wordlists:

```python
# Für SSH-Angriff:
Usernames: scripts/wordlists/ssh-user.txt
Passwords: scripts/wordlists/ssh-betterdefaultpasslist.txt

# Für FTP-Angriff:
Usernames: scripts/wordlists/ssh-user.txt
Passwords: scripts/wordlists/ftp-betterdefaultpasslist.txt
```

**Service-Mapping:**
- SSH → `ssh-betterdefaultpasslist.txt`
- FTP → `ftp-betterdefaultpasslist.txt`
- MySQL → `mysql-betterdefaultpasslist.txt`
- MSSQL → `mssql-betterdefaultpasslist.txt`
- PostgreSQL → `postgres-betterdefaultpasslist.txt`
- VNC → `vnc-betterdefaultpasslist.txt`
- Telnet → `telnet-betterdefaultpasslist.txt`
- Tomcat → `tomcat-betterdefaultpasslist.txt`
- Windows/SMB/RDP → `windows-betterdefaultpasslist.txt`
- DB2 → `db2-betterdefaultpasslist.txt`
- Oracle → `oracle-betterdefaultpasslist.txt`

### 2. **Credential Export**

Gefundene Credentials können direkt als Wordlists exportiert werden:

#### Nach Hydra-Angriff:
1. Hydra-Ergebnisse-Dialog zeigt gefundene Credentials
2. **"💾 Export to Wordlist..."** Button
3. Wähle Format:
   - **Passwords only** → Nur Passwörter (für Passwort-Reuse)
   - **Usernames only** → Nur Benutzernamen
   - **Username:Password (combo)** → user:pass Format (für Hydra -C)
4. Speichern in `scripts/wordlists/`

#### Aus Datenbank (Host-Kontextmenü):
1. Rechtsklick auf Host → **"🔑 Export Credentials (X)..."**
2. Wähle Format
3. Exportiere alle Credentials für diesen Host

### 3. **Wordlist-Utilities API**

```python
from legion.utils.wordlists import (
    get_service_wordlists,
    list_all_wordlists,
    export_credentials_to_wordlist,
    import_wordlist
)

# Auto-detect wordlists für Service
user_wl, pass_wl = get_service_wordlists("ssh")

# Alle verfügbaren Wordlists
wordlists = list_all_wordlists()  # List[Path]

# Credentials exportieren
from legion.core.models import Credential

creds = [
    Credential(host="192.168.1.1", port=22, service="ssh", 
               username="admin", password="pass123")
]

# Export als combo-file (user:pass)
count = export_credentials_to_wordlist(
    credentials=creds,
    output_file=Path("scripts/wordlists/found_creds.txt"),
    mode="combo"  # "passwords", "usernames", "combo"
)

# Import wordlist
entries = import_wordlist(
    Path("scripts/wordlists/ssh-betterdefaultpasslist.txt"),
    format="auto"  # auto-detect user:pass vs plain passwords
)
# Returns: [(username, password), ...] or [(None, password), ...]
```

## 📂 Wordlist-Verzeichnis-Struktur

```
scripts/wordlists/
├── ssh-betterdefaultpasslist.txt    # SSH Passwörter (8 entries)
├── ftp-betterdefaultpasslist.txt    # FTP Passwörter
├── mysql-betterdefaultpasslist.txt  # MySQL Passwörter
├── mssql-betterdefaultpasslist.txt  # MSSQL Passwörter
├── postgres-betterdefaultpasslist.txt
├── oracle-betterdefaultpasslist.txt
├── vnc-betterdefaultpasslist.txt
├── telnet-betterdefaultpasslist.txt
├── tomcat-betterdefaultpasslist.txt
├── windows-betterdefaultpasslist.txt
├── db2-betterdefaultpasslist.txt
├── ssh-user.txt                     # SSH Benutzernamen
├── ssh-password.txt                 # Generische Passwörter
├── root-userpass.txt                # Root user:pass combos
├── routers-userpass.txt             # Router defaults
├── snmp-default.txt                 # SNMP community strings
└── gvit_subdomain_wordlist.txt      # Subdomain enumeration
```

## 🔄 Workflow-Beispiel

### Szenario: SSH Brute Force Attack

1. **Scan durchführen:**
   - Nmap findet 192.168.1.100:22 (SSH)

2. **Hydra-Angriff starten:**
   - Rechtsklick auf Port 22 → "🔑 Brute Force" → "Hydra - SSH"
   - Dialog öffnet sich mit:
     ```
     Usernames: scripts/wordlists/ssh-user.txt          ← automatisch gewählt
     Passwords: scripts/wordlists/ssh-betterdefaultpasslist.txt
     Tasks: 16 threads
     Timeout: 300 seconds
     ```

3. **Angriff läuft:**
   - Status: "🔑 Hydra attacking ssh://192.168.1.100:22..."
   - Async-Ausführung (UI nicht blockiert)

4. **Ergebnisse:**
   - Dialog zeigt:
     ```
     ✅ Found 2 credential(s)!
     
     Host          Port  Username  Password
     192.168.1.100  22   admin     admin123
     192.168.1.100  22   root      toor
     ```
   - Credentials automatisch in DB gespeichert

5. **Export für Reuse:**
   - Click "💾 Export to Wordlist..."
   - Wähle "Passwords only"
   - Speichern als `scripts/wordlists/192.168.1.100_passwords.txt`
   - Nutze für weitere Systeme im Netzwerk!

## ⚙️ Konfiguration

### Settings → Tools Tab → Hydra:

```toml
[tools]
hydra_path = "C:\\Program Files\\Hydra\\hydra.exe"
hydra_default_tasks = 16
hydra_default_timeout = 300
hydra_wordlist_path = ""  # Leer = scripts/wordlists/
```

### Custom Wordlist-Verzeichnis:

```python
# In Settings-Dialog
Tools → Hydra Brute Force → Wordlist Directory → Browse...
# Wähle eigenes Verzeichnis (z.B. C:\wordlists\)
```

## 🎓 Best Practices

### 1. **Wordlist-Qualität**
- Kleine, fokussierte Listen für schnelle Tests (default)
- Große Listen (rockyou.txt) für intensive Angriffe
- Service-spezifische Listen für höhere Erfolgsrate

### 2. **Export-Strategie**
```
Gefundene Credentials exportieren → Für ähnliche Systeme wiederverwenden
Beispiel: Admin-Pass von Server1 oft gleich auf Server2-5
```

### 3. **Combo-Files verwenden**
```python
# Hydra unterstützt user:pass combo files mit -C flag
# Exportiere als "combo" und nutze für schnellere Angriffe
hydra -C scripts/wordlists/found_creds.txt ssh://192.168.1.0/24
```

### 4. **Wordlist-Pflege**
```bash
# Regelmäßig erfolgreiche Credentials exportieren
# In scripts/wordlists/custom/ organisieren
# Versionskontrolle für Team-Sharing
```

## 🔐 Sicherheit

**⚠️ Wichtig:**
- Credentials werden **unverschlüsselt** in DB gespeichert
- `credentials.json` ist sensibel → `.gitignore` prüfen
- Exportierte Wordlists enthalten **Klartext-Passwörter**
- Nur für legale Penetrationstests verwenden!

## 📊 Statistiken

```python
# Credential-Statistiken aus DB
db = SimpleDatabase()

total = db.get_credential_count()
host_creds = db.get_credentials("192.168.1.100")

print(f"Total: {total} credentials")
print(f"For host: {len(host_creds)} credentials")
```

## 🚀 Erweiterte Nutzung

### Bulk-Export aller Credentials:

```python
from legion.core.database import SimpleDatabase
from legion.utils.wordlists import export_credentials_to_wordlist
from pathlib import Path

db = SimpleDatabase()
all_creds = db.get_credentials()  # Alle Credentials

# Export als mega combo-file
export_credentials_to_wordlist(
    all_creds,
    Path("scripts/wordlists/all_found_creds.txt"),
    mode="combo"
)
```

### Wordlist-Merger:

```python
from legion.utils.wordlists import import_wordlist

# Merge mehrere Wordlists
wl1 = import_wordlist(Path("scripts/wordlists/ssh-password.txt"))
wl2 = import_wordlist(Path("scripts/wordlists/exported_passwords.txt"))

# Deduplizieren
all_passwords = set()
for _, password in wl1 + wl2:
    if password:
        all_passwords.add(password)

# Speichern
with open("scripts/wordlists/merged_passwords.txt", 'w') as f:
    for pwd in sorted(all_passwords):
        f.write(f"{pwd}\n")
```

## ✅ Tests

```bash
# Test wordlist utilities
python test_wordlist_utils.py

# Test Hydra UI integration
python test_hydra_ui_integration.py
```

Beide sollten `✅ ALL TESTS PASSED` zeigen.
