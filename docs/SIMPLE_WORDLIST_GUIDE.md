# ⚡ Ultra-Einfache Hydra Wordlist Verwendung

## 🎯 Ein Ordner - Fertig!

**Keine komplizierten Einstellungen mehr!**

```
┌─────────────────────────────────────────┐
│ Wordlists                               │
├─────────────────────────────────────────┤
│ [scripts/wordlists/] [📁 Browse...]    │
└─────────────────────────────────────────┘

Das war's! Nur EIN Feld!
```

---

## 🚀 So funktioniert's

### Schritt 1: Ordner auswählen
```
Hydra Attack Dialog → Browse Directory → scripts/wordlists/
```

### Schritt 2: Start Attack
```
Fertig! Alle Dateien werden automatisch verarbeitet:
- ✅ Single-Format (usernames, passwords)
- ✅ Combo-Format (username:password)
- ✅ Gemischte Formate
- ✅ Alles kombiniert
```

---

## 📂 Was passiert automatisch?

**Ordner enthält**:
```
scripts/wordlists/
├── ssh-user.txt              → Usernames
├── ssh-password.txt          → Passwords
├── test-credentials.txt      → Combo (user:pass)
├── ftp-betterdefault.txt     → Passwords
└── 14 weitere .txt Dateien   → Mixed
```

**Legion macht**:
```
1. Sammelt ALLE .txt Dateien
2. Erkennt automatisch Combo-Format
3. Extrahiert Usernames + Passwords
4. Entfernt Duplikate
5. Merged alles zu 2 Listen:
   → merged_usernames.txt (12,472 Einträge)
   → merged_passwords.txt (12,741 Einträge)
6. Startet Hydra Attack
```

**Du machst**: Ordner auswählen ✓

---

## 💡 Beispiele

### Test mit localhost

```bash
# Terminal 1: Server starten
py test_server.py

# Terminal 2: Legion starten
py legion.py

# In Legion:
1. New Scan → 127.0.0.1:8080
2. Rechtsklick Port 8080 → Brute Force → HTTP
3. Wordlist Directory: scripts/wordlists/
4. Start Attack

✅ Findet: admin:123456!
```

### Eigener Wordlist-Ordner

```
Erstelle: C:/my-wordlists/
├── found-credentials.txt  (combo: admin:pass123)
├── common-users.txt       (admin, root, test)
└── rockyou-top100.txt     (password, 123456, ...)

Legion → Browse → C:/my-wordlists/
→ Alle 3 Dateien kombiniert!
```

---

## 🎨 UI-Unterschied

### ❌ Alt (kompliziert)
```
┌────────────────────────────────────────┐
│ Usernames: [           ] [Browse...]   │
│ Passwords: [           ] [Browse...]   │
└────────────────────────────────────────┘

2 Felder, 2x browsen, verwirrend!
```

### ✅ Neu (einfach)
```
┌────────────────────────────────────────┐
│ Directory: [scripts/wordlists/] [📁]   │
└────────────────────────────────────────┘

1 Feld, 1x browsen, fertig!
```

---

## 📊 Statistiken nach Auswahl

```
Status-Bar zeigt:
📁 wordlists | Files: 18 | Entries: 12,978 (combo format detected)
```

**Bedeutung**:
- `Files: 18` = 18 .txt Dateien gefunden
- `Entries: 12,978` = Unique Credentials (nach Duplikate-Filterung)
- `combo format detected` = Mindestens ein Combo-File dabei

---

## 🔧 Tipps

### Tipp 1: Ordner-Struktur

**Empfohlen**:
```
wordlists/
├── quick/          → Kleine Listen (schnell)
├── thorough/       → Große Listen (langsam)
└── found/          → Gefundene Credentials
```

**Verwendung**:
```
Quick Attack:  wordlists/quick/
Big Attack:    wordlists/thorough/
Reuse Creds:   wordlists/found/
```

### Tipp 2: Combo-Files erstellen

```bash
# Nach erfolgreichem Attack:
# → Auto-Export schreibt found-credentials.txt

# Format:
admin:123456!
root:P@ssword!
test:test123
```

**Wiederverwendung**:
```
Ordner: wordlists/found/
→ Enthält alle gefundenen Credentials
→ Hohe Erfolgsrate bei neuen Targets!
```

### Tipp 3: Default-Ordner

```
Legion nutzt automatisch: scripts/wordlists/
→ Schon vorausgefüllt beim Dialog öffnen
→ Einfach Start Attack klicken!
```

---

## ✅ Vorteile

**Vor der Änderung**:
- ❌ 2 Felder ausfüllen
- ❌ Verwirrung: Was ist Username, was Password?
- ❌ Combo-Files: Beide Felder gleich setzen?
- ❌ Kompliziert!

**Nach der Änderung**:
- ✅ 1 Ordner auswählen
- ✅ Automatische Erkennung
- ✅ Alle Formate unterstützt
- ✅ Ultra-einfach!

---

## 🎓 Für Fortgeschrittene

### Einzelne Datei?

**Funktioniert auch!**
```
Browse → Wähle einzelne .txt Datei
→ Wird behandelt wie 1-Datei-Ordner
→ Kein Problem!
```

### Gemischte Formate?

**Kein Problem!**
```
Ordner enthält:
- users.txt          (single: admin, root)
- passwords.txt      (single: pass123, test)
- found.txt          (combo: admin:secret)

Resultat:
Usernames: admin, root (aus users.txt + found.txt)
Passwords: pass123, test, secret (aus passwords.txt + found.txt)
```

### Performance?

**Sehr schnell!**
```
18 Dateien, 12,000+ Einträge
→ Parse + Merge: <1 Sekunde
→ Attack startet sofort
```

---

**Fazit**: Ein Ordner - und Legion macht den Rest! 🚀
