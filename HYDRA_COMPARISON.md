# Hydra Integration: Legacy vs. New Legion

## Feature-Vergleich

| Feature | Legacy Legion | Neues Legion | Status |
|---------|---------------|--------------|--------|
| **Grundfunktionalität** |
| Hydra Command-Building | ✅ Manuell via Dialog | ✅ Automatisch via Tool API | ✅ Verbessert |
| Service-Erkennung | ✅ Manuell im Dialog | ✅ Automatisch aus Nmap | ✅ Verbessert |
| Port-Selection | ✅ Textfeld-Eingabe | ✅ Rechtsklick auf Port | ✅ Verbessert |
| **Wordlist-Handling** |
| User/Pass Listen | ✅ Separate Dateien | ✅ Separate Dateien | ✅ Gleich |
| Combo-Listen (user:pass) | ❌ Nicht unterstützt | ✅ Volle Unterstützung (-C) | ✅ **NEU** |
| Smart Wordlist Strategy | ❌ Keine Analyse | ✅ Auto-Erkennung & Merge | ✅ **NEU** |
| Wordlist Analysis Dialog | ❌ Nein | ✅ Zeigt Mode & Stats | ✅ **NEU** |
| Duplicate Removal | ❌ Nein | ✅ Auto-Deduplizierung | ✅ **NEU** |
| **Credential Options** |
| Single Username | ✅ `-l user` | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Single Password | ✅ `-p pass` | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Username File | ✅ `-L file` | ✅ `-L file` | ✅ Gleich |
| Password File | ✅ `-P file` | ✅ `-P file` | ✅ Gleich |
| Blank Password Check | ✅ `-e n` | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Login as Password | ✅ `-e s` | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Both (-e ns) | ✅ Checkbox-Kombi | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| **Attack Options** |
| Parallel Tasks | ✅ `-t N` (Dropdown) | ✅ `-t N` (SpinBox) | ✅ Gleich |
| Loop Users | ✅ `-u` (Checkbox) | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Exit on First Valid | ✅ `-f` (Checkbox) | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Verbose Mode | ✅ `-V` (Checkbox) | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Timeout | ✅ Konfigurierbar | ✅ SpinBox (30s default) | ✅ Gleich |
| Additional Options | ✅ Freitext-Feld | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| **Service-Spezifisch** |
| HTTP Form Fields | ✅ Warnlabel für Forms | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Service-spezifische Optionen | ✅ "More Options" Feld | ⚠️ Nur HTTP path (-m /) | ⚠️ Teilweise |
| No-Username Services | ✅ Config-basiert | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| No-Password Services | ✅ Config-basiert | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| **UI & UX** |
| Dedizierter Brute-Tab | ✅ Eigener Tab-Bereich | ❌ Nur Main Window | ⚠️ Unterschied |
| Live Output Display | ✅ QPlainTextEdit | ❌ Nur Progress Dialog | ⚠️ **FEHLT** |
| Tab Blinking bei Fund | ✅ Roter Tab bei Erfolg | ❌ Nicht implementiert | ❌ **FEHLT** |
| Kill/Cancel Button | ✅ Button wechselt | ✅ Cancel im Dialog | ✅ Gleich |
| Progress Indication | ⚠️ Nur "Running" | ✅ Timer + Elapsed Time | ✅ Verbessert |
| **Results Handling** |
| Output File | ✅ Hydra `-o` Flag | ✅ HydraTool managed | ✅ Gleich |
| Parse Results | ✅ Regex-basiert | ✅ HydraOutputParser | ✅ Verbessert |
| Save to Wordlist | ✅ Auto-Export | ✅ Auto-Export | ✅ Gleich |
| Database Storage | ✅ Found Users/Passwords | ✅ Credentials DB | ✅ Gleich |
| Results Dialog | ⚠️ Einfache Anzeige | ✅ Detaillierte Stats | ✅ Verbessert |
| **Process Management** |
| Kill Process | ✅ PID-Tracking | ✅ Process Reference | ✅ Gleich |
| Process Cancellation | ✅ AsyncIO | ✅ AsyncIO + taskkill | ✅ Verbessert |
| Prevent Duplicate Runs | ✅ Tab-Name Check | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| **Automated Attacks** |
| Scheduler Integration | ✅ legion.conf Regeln | ❌ Nicht implementiert | ❌ **FEHLT** |
| Port-basierte Auto-Attacks | ✅ Config-gesteuert | ❌ Nicht implementiert | ❌ **FEHLT** |
| **Validation** |
| IP/Port Validation | ✅ validateNmapInput() | ⚠️ Keine explizite | ⚠️ Teilweise |
| Host in Scope Check | ✅ Dialog bei Out-of-Scope | ⚠️ Nicht implementiert | ❌ **FEHLT** |
| Port State Check | ❌ Nicht geprüft | ✅ Nur für "open" Ports | ✅ **NEU** |
| **Configuration** |
| Service Mappings | ✅ Hardcoded in Dialog | ✅ Hardcoded in Context Menu | ✅ Gleich |
| Default Wordlists | ✅ Config-Pfade | ✅ Config-Pfade | ✅ Gleich |
| Tool Path | ✅ Settings Dialog | ✅ Registry Auto-Discovery | ✅ Verbessert |

---

## Zusammenfassung

### ✅ **Verbesserungen im neuen Legion**
1. **Combo-Mode Support**: Native `-C` Unterstützung für user:pass Dateien
2. **Smart Wordlist Strategy**: Automatische Analyse und Optimierung
3. **Port-State Check**: Hydra nur für offene Ports
4. **Besseres Progress Feedback**: Timer mit Elapsed Time
5. **Tool Discovery**: Auto-Registry statt manueller Config
6. **Moderne Code-Architektur**: Async/await, Tool-API, Parser-Module
7. **Cancel verbessert**: taskkill für Windows

### ❌ **Fehlende Features vs. Legacy**
1. **Single User/Pass**: Keine `-l`/`-p` Optionen
2. **Credential Options**: Keine `-e n/s` Flags (blank/login-as-pass)
3. **Attack Modifiers**: Keine `-u`/`-f`/`-V` Flags
4. **Additional Options**: Kein Freitext-Feld für Custom Args
5. **HTTP Form Support**: Keine Warnung/Hilfe für Forms
6. **Live Output**: Kein Live-Stream während Attack
7. **Tab Blinking**: Keine visuelle Benachrichtigung bei Fund
8. **Scheduler**: Keine Auto-Attacks aus legion.conf
9. **Duplicate Prevention**: Keine Tab-Name Checks

### 🔧 **Empfohlene Next Steps**

#### **Priorität 1 - Essential Missing**
- [ ] Single User/Pass Support (`-l`, `-p`)
- [ ] Exit on First Valid Flag (`-f`)
- [ ] Additional Options Freitext-Feld
- [ ] Live Output während Attack (wie Legacy)

#### **Priorität 2 - UX Improvements**
- [ ] Verbose Mode (`-V`) Toggle
- [ ] Loop Users (`-u`) Toggle
- [ ] Blank Password (`-e n`) Check
- [ ] Login as Password (`-e s`) Check
- [ ] Visual Feedback bei Success (Tab Blinking)

#### **Priorität 3 - Advanced**
- [ ] HTTP Form Field Support & Warnings
- [ ] Service-spezifische No-User/Pass Handling
- [ ] Scheduler für Auto-Attacks
- [ ] Duplicate Run Prevention

---

## Legacy Config Beispiele

### legion.conf Automated Attacks
```conf
ssh-default=Check for default ssh credentials, hydra -s [PORT] -C ./wordlists/ssh-betterdefaultpasslist.txt -u -t 4 -o "[OUTPUT].txt" -f [IP] ssh, ssh
ftp-default=Check for default ftp credentials, hydra -s [PORT] -C ./wordlists/ftp-betterdefaultpasslist.txt -u -o "[OUTPUT].txt" -f [IP] ftp, ftp
mysql-default=Check for default mysql credentials, hydra -s [PORT] -C ./wordlists/mysql-betterdefaultpasslist.txt -u -o "[OUTPUT].txt" -f [IP] mysql, mysql
```

### Legacy Dialog Command-Building
```python
# Beispiel-Command aus Legacy:
hydra 192.168.1.1 -s 22 -o "output.txt" -L users.txt -P passwords.txt -e ns -u -f -V -t 4 ssh
```

**Flags die fehlen:**
- `-e ns`: Try blank passwords AND login as password
- `-u`: Loop users (try all users for one pass before next pass)
- `-f`: Exit on first valid credential found
- `-V`: Verbose output showing each attempt

---

## Code-Beispiele Legacy

### buildHydraCommand() - Alle Optionen
```python
# Single user
if self.singleUserRadio.isChecked():
    self.command += " -l " + self.usersTextinput.text()

# Single password mit Escaping
if self.singlePassRadio.isChecked():
    escaped_password = self.passwordsTextinput.text().replace('"', '\"\"\"')
    self.command += " -p \"" + escaped_password + "\""

# Blank password
if self.checkBlankPass.isChecked():
    self.command += " -e n"
    
# Login as password
if self.checkLoginAsPass.isChecked():
    self.command += " -e s"  # oder "ns" wenn beide

# Loop users first
if self.checkLoopUsers.isChecked():
    self.command += " -u"

# Exit on first valid
if self.checkExitOnValid.isChecked():
    self.command += " -f"

# Verbose
if self.checkVerbose.isChecked():
    self.command += " -V"

# Additional options (Freitext!)
if self.checkAddMoreOptions.isChecked():
    self.command += " " + str(self.labelPath.text())
```

---

## Fazit

Das neue Legion hat eine **deutlich bessere Architektur** und einige **moderne Verbesserungen** (Combo-Mode, Smart Strategy, Port-Check), aber es fehlen wichtige **Hydra-Features** die Power-User brauchen:

- **Single credential testing** (schnelle Tests)
- **Attack modifiers** (-u, -f, -V für Kontrolle)
- **Credential helpers** (-e ns für blank/login-as-pass)
- **Live output** (wichtig für lange Attacks)
- **Additional options** (für Edge-Cases & Custom Services)

**Recommendation**: Die fehlenden Flags sollten nachgerüstet werden, besonders `-l/-p`, `-f`, `-V` und das Additional Options Feld. Die Smart Wordlist Strategy ist ein Alleinstellungsmerkmal und sollte beibehalten werden!
