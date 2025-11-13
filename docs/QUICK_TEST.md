# 🎯 Quick Test Guide - Neue Credentials

## Test Credentials

### HTTP (Port 8080)
- **User**: `admin`
- **Password**: `123456!`
- **Endpoint**: `/admin`
- **Base64**: `YWRtaW46MTIzNDU2IQ==`

### SSH (Port 2222)
- **User**: `root`
- **Password**: `P@ssword!`

### FTP (Port 2121)
- **User**: `admin` / Password: `admin123`
- **User**: `test` / Password: `test123`
- **User**: `ftp` / Password: `ftp`

---

## Quick Test

### 1. Start Test Server

```bash
py test_server.py
```

**Erwartung**:
```
✅ HTTP Server started on port 8080
   URL: http://127.0.0.1:8080
   
🔑 Test Credentials:
  HTTP:  admin / 123456!     (for /admin endpoint)
  SSH:   root  / P@ssword!   (port 2222)
  FTP:   admin / admin123
```

### 2. Test HTTP Login

```bash
# Browser
http://127.0.0.1:8080/admin

# Username: admin
# Password: 123456!

# Oder mit curl:
curl -u admin:123456! http://127.0.0.1:8080/admin
```

**Erwartung**: `<h1>Admin Panel - Login Successful!</h1>`

### 3. Test mit Hydra (Legion UI)

**HTTP Attack**:
```
1. Start Legion: py legion.py
2. New Scan: 127.0.0.1, Ports: 8080
3. Nach Scan: Rechtsklick auf Port 8080
4. Brute Force → Hydra - HTTP (http-get)
5. Wordlists:
   - Username: scripts/wordlists/ssh-user.txt
   - Password: scripts/wordlists/ssh-password.txt
   - ODER: scripts/wordlists/test-credentials.txt (combo!)
6. Start Attack
```

**Erwartung**: 
```
✅ Found 1 credential(s)!
   🔓 admin:123456!
```

**SSH Attack** (wenn SSH Server läuft):
```
1-2. Wie oben, Port 2222
3. Brute Force → Hydra - SSH
4. Wordlists:
   - Username: scripts/wordlists/ssh-user.txt
   - Password: scripts/wordlists/ssh-password.txt
5. Start Attack
```

**Erwartung**:
```
✅ Found 1 credential(s)!
   🔓 root:P@ssword!
```

---

## Wordlist Files

### test-credentials.txt (Combo-Format)
```
admin:123456!
root:P@ssword!
```

**Verwendung**: Als Username UND Password Quelle auswählen!

### ssh-password.txt (erweitert)
```
password
p@55w0rd
password123!
P@ssw0rd!
P@ssw0rd
P@ssword!     ← NEU
123456!       ← NEU
```

### ssh-user.txt (unverändert)
```
admin
root
test
user
sysop
```

---

## Verification

### Credentials in Wordlists?

```bash
# Check ssh-password.txt
findstr "P@ssword!" scripts/wordlists/ssh-password.txt
findstr "123456!" scripts/wordlists/ssh-password.txt

# Check test-credentials.txt
type scripts/wordlists/test-credentials.txt
```

**Erwartung**: Beide Passwörter gefunden

### Base64 Encoding korrekt?

```python
import base64

# HTTP Credential
cred = "admin:123456!"
encoded = base64.b64encode(cred.encode()).decode()
print(f"admin:123456! = {encoded}")
# Output: YWRtaW46MTIzNDU2IQ==
```

**Erwartung**: Stimmt mit test_server.py überein

---

## Troubleshooting

### HTTP Login funktioniert nicht

```bash
# Test mit curl (verbose)
curl -v -u admin:123456! http://127.0.0.1:8080/admin

# Prüfe Authorization Header:
# > Authorization: Basic YWRtaW46MTIzNDU2IQ==
```

### Hydra findet keine Credentials

**Check 1**: Sind Credentials in Wordlists?
```bash
findstr "admin" scripts/wordlists/ssh-user.txt
findstr "123456!" scripts/wordlists/ssh-password.txt
```

**Check 2**: Nutze test-credentials.txt (Combo)
```
- Username: scripts/wordlists/test-credentials.txt
- Password: scripts/wordlists/test-credentials.txt
```

**Check 3**: Hydra Command manuell testen
```bash
hydra -l admin -p "123456!" -s 8080 127.0.0.1 http-get /admin
```

---

## Success Indicators

✅ **HTTP Server**:
- Port 8080 läuft
- /admin Endpoint erreichbar
- Basic Auth funktioniert

✅ **Hydra Attack**:
- Findet admin:123456! für HTTP
- Speichert in Database
- Auto-Export zu Wordlists

✅ **Wordlist Processor**:
- test-credentials.txt als Combo erkannt
- Automatisch in User/Pass gesplittet
- Merge funktioniert

---

**Letzte Änderungen**:
- HTTP: `admin:admin123` → `admin:123456!`
- SSH: Neu hinzugefügt `root:P@ssword!`
- Wordlist: ssh-password.txt erweitert
- Wordlist: test-credentials.txt (combo) erstellt
