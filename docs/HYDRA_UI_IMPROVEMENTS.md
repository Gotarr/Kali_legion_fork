# 🔑 Hydra UI Verbesserungen

Übersicht der neuesten Verbesserungen an der Hydra-Integration in Legion.

## ✨ Neue Features

### 1. ✅ Erfolgreiche Credentials Markierung

### 1. ✅ Erfolgreiche Credentials Markierung

**Problem**: Alle Credentials sahen gleich aus, keine visuelle Hervorhebung.

**Lösung**: Grünes Häkchen ✓ und fette Schrift für erfolgreiche Credentials.

**Vorher**:
```
┌──────┬──────┬──────────┬──────────┐
│ Host │ Port │ Username │ Password │
├──────┼──────┼──────────┼──────────┤
│ ...  │ ...  │ admin    │ admin123 │
└──────┴──────┴──────────┴──────────┘
```

**Nachher**:
```
┌───┬──────┬──────┬──────────┬──────────┐
│ ✓ │ Host │ Port │ Username │ Password │
├───┼──────┼──────┼──────────┼──────────┤
│ ✓ │ ...  │ ...  │ admin    │ admin123 │  ← Grün + Fett
└───┴──────┴──────┴──────────┴──────────┘
```

**Features**:
- ✅ Grünes Häkchen (✓) in erster Spalte
- ✅ Username & Password in **fetter Courier-Schrift**
- ✅ Bessere Lesbarkeit
- ✅ Schnelle visuelle Identifikation

---

### 2. Automatischer Export zu genutzten Wordlists

**Problem**: Gefundene Credentials mussten manuell exportiert werden.

**Lösung**: Automatischer Export erfolgreicher Credentials **zurück** in die genutzten Wordlists.

**Workflow**:
```
1. Hydra Attack:
   └─ Username-List: scripts/wordlists/ssh-user.txt
   └─ Password-List: scripts/wordlists/ssh-password.txt

2. Credentials gefunden:
   ✓ admin:NewPassword123
   ✓ testuser:SecretPass

3. AUTO-EXPORT:
   ├─ ssh-user.txt     += testuser  (admin existierte schon)
   └─ ssh-password.txt += NewPassword123, SecretPass
```

**Vorteile**:
- ✅ **Kein manueller Export nötig**
- ✅ **Wordlists wachsen automatisch**
- ✅ **Duplikate werden vermieden**
- ✅ **Passwords sofort wiederverwendbar**

**Log-Ausgabe**:
```
INFO: Auto-exported 1 new usernames to ssh-user.txt
INFO: Auto-exported 2 new passwords to ssh-password.txt
INFO: ✅ Auto-export completed: 2 credentials processed
```

---

### 3. Duplikate-Vermeidung

**Problem**: Wordlists enthielten nach mehreren Exports Duplikate.

**Lösung**: Intelligente Duplikate-Erkennung beim Export.

#### 4.1 Auto-Export (immer aktiv)

```python
# Liest existierende Einträge
existing_passwords = {"admin", "password", "123456"}

# Neue Credentials
new_passwords = {"admin", "NewPass", "SecretPass"}

# Filtert Duplikate
to_add = new_passwords - existing_passwords
# Result: {"NewPass", "SecretPass"}  ← Nur neue!
```

#### 4.2 Manueller Export (neue Option)

**Neue Funktion**: `export_credentials_to_wordlist(append=True)`

```python
# Ohne Duplikate-Vermeidung (Standard)
export_credentials_to_wordlist(
    creds,
    Path("wordlist.txt"),
    mode="passwords"
)
# Überschreibt Datei

# Mit Duplikate-Vermeidung (NEU!)
export_credentials_to_wordlist(
    creds,
    Path("wordlist.txt"),
    mode="passwords",
    append=True  # ← Neue Option
)
# Fügt nur neue Einträge hinzu
```

**Algorithmus**:
1. Lese existierende Einträge in Set
2. Sammle neue Einträge in Set
3. Berechne Differenz: `new - existing`
4. Schreibe nur die Differenz (append mode)

**Return-Wert**:
- **Vorher**: Anzahl aller geschriebenen Zeilen
- **Nachher**: Anzahl **NEUER** Zeilen (ohne Duplikate)

---

## 🎯 Verwendung

### Credentials Markierung

Automatisch! Alle gefundenen Credentials haben:
- ✓ Grünes Häkchen
- **Fette Schrift** für Username & Password
- Courier-Font für bessere Lesbarkeit

### Auto-Export

**Vollautomatisch nach jedem erfolgreichen Attack!**

```python
# Nach Hydra-Attack:
if hydra_result.credentials:
    # Auto-Export zu genutzten Wordlists
    await self._auto_export_to_wordlists(
        hydra_result.credentials,
        username_file,  # Original-Datei
        password_file   # Original-Datei
    )
```

**Keine Aktion nötig** - läuft automatisch im Hintergrund.

### Duplikate vermeiden

#### Auto-Export (automatisch)

```python
# In _auto_export_to_wordlists():
# 1. Lese existierende Einträge
existing_users = {line.strip() for line in file}

# 2. Neue Einträge sammeln
new_users = {cred.username for cred in creds}

# 3. Nur neue hinzufügen
users_to_add = new_users - existing_users
```

#### Manueller Export

```python
from legion.utils.wordlists import export_credentials_to_wordlist

# Standard: Überschreiben (alte Methode)
count = export_credentials_to_wordlist(
    credentials,
    Path("found_passwords.txt"),
    mode="passwords"
)

# NEU: Anhängen ohne Duplikate
count = export_credentials_to_wordlist(
    credentials,
    Path("found_passwords.txt"),
    mode="passwords",
    append=True  # ← Duplikate werden vermieden!
)

print(f"{count} neue Einträge hinzugefügt")
```

---

## 🧪 Testing

### Test 1: Credentials Markierung

```bash
# Nach Test 1:
# Prüfe Results-Dialog:
```

**Erwartung**:
- ✅ Grüne Häkchen in erster Spalte
- ✅ Username & Password in fetter Schrift
- ✅ Gute Lesbarkeit

### Test 2: Auto-Export

```bash
# 1. Vorher: Zähle Zeilen in ssh-password.txt
wc -l scripts/wordlists/ssh-password.txt
# z.B. 100 Zeilen

# 2. Führe Hydra-Attack aus (findet z.B. 3 Credentials)

# 3. Nachher: Zähle Zeilen erneut
wc -l scripts/wordlists/ssh-password.txt
# z.B. 102 Zeilen (2 neue Passwords)

# 4. Prüfe Log:
# "Auto-exported 2 new passwords to ssh-password.txt"
```

### Test 3: Duplikate-Vermeidung

```bash
# 1. Führe Attack 2x aus (gleiche Wordlists)

# 2. Nach 1. Attack: +2 neue Passwords
# 3. Nach 2. Attack: +0 neue Passwords (Duplikate gefiltert!)

# 4. Prüfe Log:
# "Auto-exported 0 new passwords to ssh-password.txt"
```

---

## 📊 Statistiken

### Auto-Export Beispiel

```
🔑 Hydra Attack abgeschlossen
═══════════════════════════════════════════

✅ Credentials gefunden: 5
   - admin:NewPass123
   - root:SecretPassword
   - testuser:Password1
   - john:JohnPass
   - alice:AlicePass

📤 Auto-Export:
   ├─ Usernames: 3 neue → ssh-user.txt
   │  (admin & root existierten schon)
   │
   └─ Passwords: 5 neue → ssh-password.txt
      (alle waren neu)

💾 Database: 5 credentials gespeichert
```

### Duplikate-Vermeidung Beispiel

**Erste Attack**:
```
Found: admin:pass123, root:secret
Auto-export: 2 usernames, 2 passwords
```

**Zweite Attack** (gleiche Credentials):
```
Found: admin:pass123, root:secret
Auto-export: 0 usernames, 0 passwords  ← Duplikate gefiltert!
```

**Dritte Attack** (teilweise neu):
```
Found: admin:pass123, john:newpass
Auto-export: 1 username (john), 1 password (newpass)
           ← admin:pass123 wurde übersprungen
```

---

## 🎓 Best Practices

### 1. Wordlist-Strategie

**Lass die Wordlists wachsen**:
1. Starte mit kleinen Listen (100-500 Einträge)
2. Jeder erfolgreiche Attack fügt neue Credentials hinzu
3. Nach mehreren Scans: Wordlist enthält **validierte** Credentials
4. Diese sind **deutlich effektiver** als generische Listen

**Beispiel-Entwicklung**:
```
Tag 1: ssh-password.txt → 100 Einträge (Standard)
Tag 2: ssh-password.txt → 105 Einträge (+5 gefundene)
Tag 7: ssh-password.txt → 150 Einträge (+50 gefundene)
Tag 30: ssh-password.txt → 300 Einträge (+200 gefundene)
                           ↑ Hochgradig effektive Liste!
```

### 2. Duplikate-Management

**Auto-Export**: 
- ✅ Immer aktiv
- ✅ Keine Konfiguration nötig
- ✅ Duplikate automatisch gefiltert

**Manueller Export**:
- ✅ Nutze `append=True` für kumulative Listen
- ✅ Nutze `append=False` (Standard) für neue Dateien

### 3. Credential-Wiederverwendung

**Password-Spray-Attack**:
```python
# 1. Sammle Credentials aus mehreren Targets
credentials = []
for host in ["192.168.1.10", "192.168.1.20"]:
    creds = db.get_credentials(host)
    credentials.extend(creds)

# 2. Exportiere zu gemeinsamer Wordlist
export_credentials_to_wordlist(
    credentials,
    Path("scripts/wordlists/found_passwords.txt"),
    mode="passwords",
    append=True  # Kumulative Liste!
)

# 3. Nutze für nächste Attacks
# → Deutlich höhere Erfolgsrate!
```

---

## 🔧 Technische Details

### Auto-Export Implementierung

```python
async def _auto_export_to_wordlists(
    self,
    credentials,
    username_file: str,
    password_file: str
) -> None:
    """
    Auto-Export mit Duplikate-Vermeidung.
    """
    # 1. Lese existierende Usernames
    existing_users = set()
    with open(username_file, 'r') as f:
        existing_users = {line.strip() for line in f}
    
    # 2. Sammle neue Usernames
    new_users = {cred.username for cred in credentials}
    
    # 3. Filtere Duplikate
    to_add = new_users - existing_users
    
    # 4. Append zu Datei
    if to_add:
        with open(username_file, 'a') as f:
            for user in sorted(to_add):
                f.write(f"{user}\n")
    
    # Gleicher Prozess für Passwords...
```

### Export mit Append-Mode

```python
def export_credentials_to_wordlist(
    credentials: List,
    output_file: Path,
    mode: str = "passwords",
    append: bool = False  # ← Neue Option
) -> int:
    """Returns: Anzahl NEUER Einträge (ohne Duplikate)"""
    
    # Sammle neue Einträge
    lines = {cred.password for cred in credentials}
    
    # Lese existierende Einträge (bei append=True)
    existing = set()
    if append and output_file.exists():
        with open(output_file, 'r') as f:
            existing = {line.strip() for line in f}
    
    # Filtere Duplikate
    to_write = lines - existing
    
    # Schreibe
    mode = 'a' if append else 'w'
    with open(output_file, mode) as f:
        for line in sorted(to_write):
            f.write(f"{line}\n")
    
    return len(to_write)  # Nur neue!
```

---

## ✅ Checkliste

Nach Implementation:
- [x] Grüne Häkchen für erfolgreiche Credentials
- [x] Fette Schrift für Username & Password
- [x] Auto-Export zu genutzten Wordlists
- [x] Duplikate-Vermeidung im Auto-Export
- [x] `append=True` Parameter für manuellen Export
- [x] Return-Wert: Anzahl NEUER Einträge
- [x] Set-basierte Duplikate-Filterung
- [x] Logging für Auto-Export Aktionen

**Hinweis**: Target Path wurde **absichtlich nicht implementiert**, da Angreifer den korrekten Auth-Pfad typischerweise nicht kennen. Hydra nutzt stattdessen den Service-Standard (z.B. `/` für HTTP Basic Auth).

---

**Datum**: 13. November 2025  
**Version**: Legion Hydra Integration v2.0  
**Status**: ✅ Produktionsreif
