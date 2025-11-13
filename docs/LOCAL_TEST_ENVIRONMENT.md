# 🧪 Legion Local Test Environment

Vollständige Testumgebung für realistische Legion-Tests gegen localhost.

## 📋 Übersicht

Dieser Test-Setup erstellt lokale Services auf localhost (127.0.0.1), gegen die Legion sicher getestet werden kann:

- **HTTP Server** (Port 8080) - Immer verfügbar, keine Dependencies
- **FTP Server** (Port 2121) - Optional, benötigt `pyftpdlib`
- **SSH Server** (Port 2222) - Optional, komplex (wird übersprungen)

## 🚀 Quick Start

### 1. Test-Server starten

```bash
# Terminal 1: Test-Services starten
python test_server.py
```

Output:
```
✅ HTTP Server started on port 8080
   URL: http://127.0.0.1:8080
   Endpoints: /, /admin, /test, /api

✅ FTP Server started on port 2121
   Users: admin/admin123, test/test123, ftp/ftp, anonymous

📊 Available Test Services:
  ✅ HTTP (port 8080)
  ✅ FTP (port 2121)

🎯 Test Target: 127.0.0.1 (localhost)

🔑 Test Credentials:
  HTTP:  admin / admin123  (for /admin endpoint)
  FTP:   admin / admin123
  FTP:   test  / test123
  FTP:   ftp   / ftp

⏳ Servers running in background (Ctrl+C to stop)
```

### 2. Test-Plan ausführen

```bash
# Terminal 2: Test-Plan starten
python test_plan_local.py
```

Der Test-Plan führt automatisch aus:
1. **Phase 1**: Nmap Discovery & Port Scan
2. **Phase 2**: Service Detection (-sV)
3. **Phase 3**: Hydra Brute Force Attacks
4. **Phase 4**: Credential Management (Save → DB → Export)

## 📊 Test-Plan Details

### Phase 1: Nmap Discovery
```bash
# Ping Scan
nmap -sn 127.0.0.1

# Port Scan auf Test-Ports
nmap -p 8080,2121,2222 -T4 127.0.0.1
```

### Phase 2: Service Detection
```bash
# Service Version Detection
nmap -p 8080,2121 -sV -T4 127.0.0.1
```

Erwartete Services:
- Port 8080: `http` (SimpleHTTPServer)
- Port 2121: `ftp` (pyftpdlib)

### Phase 3: Hydra Attacks

#### FTP Attack (Port 2121)
```bash
hydra -L scripts/wordlists/ssh-user.txt \
      -P scripts/wordlists/ftp-betterdefaultpasslist.txt \
      -s 2121 -t 4 127.0.0.1 ftp
```

Erwartete Finds:
- `admin:admin123` ✅
- `test:test123` ✅
- `ftp:ftp` ✅

#### HTTP Attack (Port 8080)
```bash
hydra -l admin \
      -P scripts/wordlists/ssh-password.txt \
      -s 8080 -t 4 127.0.0.1 http-get /admin
```

Erwartete Finds:
- `admin:admin123` ✅ (wenn in Wordlist)

### Phase 4: Credential Management

1. **Speichern in DB**:
   ```python
   db = SimpleDatabase("localhost_test")
   db.save_credential(credential)
   ```

2. **Abrufen aus DB**:
   ```python
   creds = db.get_credentials("127.0.0.1")
   ```

3. **Export zu Wordlists**:
   ```python
   export_credentials_to_wordlist(
       creds,
       Path("scripts/wordlists/test_localhost_combo.txt"),
       mode="combo"  # user:pass format
   )
   ```

## 🔑 Test Credentials

### HTTP (Port 8080)
- **Endpoint**: `/admin`
- **User**: `admin`
- **Password**: `admin123`
- **Auth**: Basic Authentication

### FTP (Port 2121)
| Username | Password | Permissions |
|----------|----------|-------------|
| admin | admin123 | Full (elradfmw) |
| test | test123 | Read (elr) |
| ftp | ftp | Read (elr) |
| anonymous | - | Read (elr) |

## 📦 Dependencies

### HTTP Server (Immer verfügbar)
✅ Keine Dependencies - nutzt Python's `http.server`

### FTP Server (Optional)
```bash
pip install pyftpdlib
```

Falls nicht installiert:
```
⚠️  pyftpdlib not installed - FTP server skipped
   Install: pip install pyftpdlib
```

### SSH Server (Übersprungen)
SSH-Server ist zu komplex für schnelles Setup. Alternative:
- Nutze existierenden SSH-Dienst (falls verfügbar)
- Oder überspringe SSH-Tests

## 🧪 Manuelle Tests

### Test 1: HTTP Server
```bash
# Browser öffnen
http://127.0.0.1:8080

# Admin-Seite (benötigt Auth)
http://127.0.0.1:8080/admin
# Username: admin
# Password: admin123
```

### Test 2: FTP Server
```bash
# FTP Client
ftp 127.0.0.1 2121

# Login testen
Name: admin
Password: admin123
```

### Test 3: Nmap Manual
```bash
# Quick Scan
nmap -p 8080,2121 127.0.0.1

# Service Detection
nmap -p 8080,2121 -sV 127.0.0.1

# Aggressive Scan
nmap -p 8080,2121 -A -T4 127.0.0.1
```

### Test 4: Hydra Manual
```bash
# FTP Brute Force
hydra -L scripts/wordlists/ssh-user.txt \
      -P scripts/wordlists/ftp-betterdefaultpasslist.txt \
      -s 2121 127.0.0.1 ftp

# HTTP Basic Auth
hydra -l admin \
      -P scripts/wordlists/ssh-password.txt \
      -s 8080 127.0.0.1 http-get /admin
```

## 📂 Generierte Dateien

Nach Test-Durchlauf:

```
data/projects/localhost_test/
├── credentials.json        # Gespeicherte Credentials
├── hosts.json             # Host-Informationen
└── ports.json             # Port-Informationen

scripts/wordlists/
├── test_localhost_passwords.txt   # Exportierte Passwörter
└── test_localhost_combo.txt       # Exportierte user:pass
```

## 🎯 Erwartete Ergebnisse

### Erfolgreicher Durchlauf:

```
📊 TEST SUMMARY
════════════════════════════════════════════════════════════════

🎯 Target: 127.0.0.1
📅 Date: 2025-11-13 12:00:00

📡 Services Detected: 2
   Port 8080: http (open)
   Port 2121: ftp (open)

🔑 Credentials Found: 3
   ftp:2121 - admin:admin123
   ftp:2121 - test:test123
   ftp:2121 - ftp:ftp

💾 Database Stats:
   Total credentials: 3
   Database location: data/projects/localhost_test

════════════════════════════════════════════════════════════════
✅ TEST PLAN SUCCESSFUL - Credentials Found!
════════════════════════════════════════════════════════════════
```

## 🚨 Troubleshooting

### HTTP Server startet nicht (Port belegt)
```python
# In test_server.py, ändere Port:
port = 8081  # statt 8080
```

### FTP Server nicht verfügbar
```bash
# Installation
pip install pyftpdlib

# Test
python -c "import pyftpdlib; print('OK')"
```

### Nmap findet keine Ports
```bash
# Windows Firewall prüfen
# Port 8080 und 2121 freigeben

# Oder direkt testen
curl http://127.0.0.1:8080
```

### Hydra schlägt fehl
```bash
# Hydra Installation prüfen
hydra -h

# Version
hydra -V  # oder: hydra -h (Windows)
```

## 📖 Weiterführende Tests

### UI-Test mit Legion
1. Test-Server laufen lassen: `python test_server.py`
2. Legion starten: `python legion.py`
3. New Scan → Target: `127.0.0.1`
4. Ports: `8080,2121`
5. Nach Scan: Rechtsklick auf FTP-Port → "🔑 Brute Force"
6. Credentials gefunden → In DB gespeichert
7. Host-Kontextmenü → "🔑 Export Credentials"

### Stress-Test
```python
# In test_plan_local.py
# Erhöhe Tasks:
tasks=16  # statt 4

# Erhöhe Timeout:
timeout=60.0  # statt 30.0
```

## ✅ Checkliste

Vor dem Test:
- [ ] `test_server.py` läuft
- [ ] HTTP-Server erreichbar (Browser: http://127.0.0.1:8080)
- [ ] FTP-Server erreichbar (optional, mit `pyftpdlib`)
- [ ] Nmap installiert und im PATH
- [ ] Hydra installiert und im PATH

Nach dem Test:
- [ ] Credentials in `data/projects/localhost_test/credentials.json`
- [ ] Wordlists in `scripts/wordlists/test_localhost_*.txt`
- [ ] Keine Fehler im Test-Output
- [ ] Test-Server stoppen (Ctrl+C)

## 🎓 Lernziele

Dieser Test demonstriert:
1. ✅ **Nmap Integration** - Discovery, Port Scan, Service Detection
2. ✅ **Hydra Integration** - Brute Force mit Wordlists
3. ✅ **Wordlist Management** - Auto-Select, Export, Import
4. ✅ **Database** - Credential Storage & Retrieval
5. ✅ **Full Workflow** - Scan → Attack → Store → Export

---

**⏱️ Geschätzte Dauer**: 2-3 Minuten pro Durchlauf

**🎯 Success Rate**: ~90% (abhängig von Wordlists)
