# Tool Analysis - Phase 6 Implementation

**Datum**: 13. November 2025  
**Ziel**: Identifikation sinnvoller Tools für Cross-Platform Legion v2.0 (Windows + Linux)

---

## 🎯 Auswahlkriterien

### Must-Have Kriterien
1. ✅ **Cross-Platform**: Verfügbar auf Windows UND Linux
2. ✅ **Aktiv maintained**: Updates in letzten 12 Monaten
3. ✅ **CLI-basiert**: Einfache programmatische Steuerung
4. ✅ **Parsable Output**: Strukturierte Ausgabe (JSON/XML/Plain)
5. ✅ **Kein GUI erforderlich**: Headless-fähig

### Nice-to-Have
- 📦 Package verfügbar (apt, choco, pip, etc.)
- 📝 Gute Dokumentation
- 🔧 Flexible Konfiguration
- 🚀 Schnelle Ausführung

---

## 📊 Tool-Kategorien

### 1. **Reconnaissance & Scanning** 🔍

#### 1.1 Nmap (✅ Bereits implementiert)
- **Platform**: ✅ Windows, Linux, macOS
- **Status**: ✅ Vollständig integriert (Phase 2-5)
- **Verwendung**: Port-Scanning, Service-Detection, OS-Detection

---

### 2. **Web Application Scanning** 🌐

#### 2.1 Nikto ⭐ HIGH PRIORITY
- **Platform**: ✅ Windows (Perl), Linux (Native)
- **Installation**: 
  - Linux: `apt install nikto` 
  - Windows: Strawberry Perl + Nikto
- **Output**: Plain text, XML, CSV, HTML
- **Verwendung**: Web-Server vulnerability scanning
- **Legacy**: In v1.x verwendet
- **Cross-Platform**: ⚠️ Windows braucht Perl (Strawberry Perl verfügbar)

**Bewertung**: ✅ Implementieren
- Grund: Legacy-Feature, nützlich, Windows-Support via Perl möglich

#### 2.2 WhatWeb ⭐ MEDIUM PRIORITY
- **Platform**: ✅ Windows (Ruby), Linux (Native)
- **Installation**:
  - Linux: `apt install whatweb`
  - Windows: Ruby + gem install
- **Output**: JSON, XML, Plain
- **Verwendung**: Web tech fingerprinting
- **Legacy**: In v1.x verwendet

**Bewertung**: ✅ Implementieren
- Grund: Fingerprinting wichtig, JSON output

#### 2.3 Gobuster ⭐ HIGH PRIORITY
- **Platform**: ✅ Windows, Linux (Go binary)
- **Installation**: 
  - Linux: `apt install gobuster`
  - Windows: Download binary
- **Output**: Plain text (parsable)
- **Verwendung**: Directory/DNS/Vhost bruteforce
- **Legacy**: Nicht in v1.x (aber modern, schnell)

**Bewertung**: ✅ Implementieren
- Grund: Modern, schnell, einfache Binaries, Cross-Platform

#### 2.4 Dirb ⏳ LOW PRIORITY
- **Platform**: ⚠️ Linux-only
- **Installation**: `apt install dirb`
- **Verwendung**: Directory bruteforce

**Bewertung**: ⏸️ Später (nur Linux)
- Grund: Gobuster ist besser + Cross-Platform

---

### 3. **Brute-Force & Credential Testing** 🔐

#### 3.1 Hydra ⭐ HIGH PRIORITY
- **Platform**: ✅ Windows, Linux
- **Installation**:
  - Linux: `apt install hydra`
  - Windows: Download binary oder WSL
- **Output**: Plain text (parsable)
- **Verwendung**: Network service bruteforce (SSH, FTP, HTTP, etc.)
- **Legacy**: Vollständig in v1.x integriert

**Bewertung**: ✅ Implementieren
- Grund: Core-Feature in v1.x, wichtig für Pentesting, Windows-Binary verfügbar

#### 3.2 Medusa ⏳ MEDIUM PRIORITY
- **Platform**: ⚠️ Linux > Windows
- **Installation**: 
  - Linux: `apt install medusa`
  - Windows: Cygwin oder Kompilieren
- **Verwendung**: Alternative zu Hydra

**Bewertung**: ⏸️ Optional (Hydra Priorität)
- Grund: Hydra ist etablierter, besserer Windows-Support

---

### 4. **Exploit & Vulnerability Database** 💣

#### 4.1 Searchsploit ⭐ HIGH PRIORITY
- **Platform**: ✅ Windows, Linux (Python/Bash)
- **Installation**:
  - Linux: `apt install exploitdb`
  - Windows: Git clone + Python
- **Output**: Plain text, CSV, JSON
- **Verwendung**: Exploit-DB Suche
- **Legacy**: Erwähnt in v1.x

**Bewertung**: ✅ Implementieren
- Grund: Wichtig für Exploit-Discovery, Cross-Platform möglich

#### 4.2 Metasploit (msfconsole) ⏳ LOW PRIORITY
- **Platform**: ✅ Windows, Linux
- **Installation**: 
  - Linux: `apt install metasploit-framework`
  - Windows: MSF Installer
- **Verwendung**: Exploitation framework

**Bewertung**: ⏸️ Phase 7+ (Komplex)
- Grund: Sehr komplex, eigenes Framework, später

---

### 5. **SSL/TLS & Crypto** 🔒

#### 5.1 SSLyze ⭐ MEDIUM PRIORITY
- **Platform**: ✅ Windows, Linux (Python)
- **Installation**: `pip install sslyze`
- **Output**: JSON, XML
- **Verwendung**: SSL/TLS configuration analysis
- **Legacy**: In v1.x verwendet

**Bewertung**: ✅ Implementieren
- Grund: Python-basiert, JSON output, wichtig für HTTPS

#### 5.2 TestSSL.sh ⏳ MEDIUM PRIORITY
- **Platform**: ⚠️ Linux/WSL, Bash required
- **Installation**: Git clone
- **Verwendung**: SSL/TLS testing

**Bewertung**: ⏸️ Optional (SSLyze bevorzugt)
- Grund: Bash-Script, Windows braucht WSL

---

### 6. **DNS & Network** 🌐

#### 6.1 DNSenum ⏳ LOW PRIORITY
- **Platform**: ⚠️ Linux > Windows
- **Installation**: `apt install dnsenum`
- **Verwendung**: DNS enumeration

**Bewertung**: ⏸️ Später
- Grund: Nmap NSE kann DNS, nicht kritisch

#### 6.2 Fierce ⏳ LOW PRIORITY
- **Platform**: ✅ Windows, Linux (Perl/Python)
- **Installation**: `pip install fierce` (Python version)
- **Verwendung**: DNS reconnaissance

**Bewertung**: ⏸️ Optional
- Grund: Nicht kritisch, Nmap kann DNS

---

### 7. **SMTP & Email** 📧

#### 7.1 smtp-user-enum ⏳ LOW PRIORITY
- **Platform**: ⚠️ Linux (Perl)
- **Installation**: Manual (Perl script)
- **Legacy**: In scripts/ vorhanden

**Bewertung**: ⏸️ Später
- Grund: Sehr spezifisch, selten gebraucht

---

### 8. **SMB & Windows** 🪟

#### 8.1 Enum4linux ⏳ MEDIUM PRIORITY
- **Platform**: ⚠️ Linux-only (Bash)
- **Installation**: `apt install enum4linux`
- **Verwendung**: SMB/Windows enumeration

**Bewertung**: ⏸️ Optional (Linux-only)
- Grund: Windows-target aber Linux-tool

#### 8.2 CrackMapExec (CME) ⭐ MEDIUM PRIORITY
- **Platform**: ✅ Windows, Linux (Python)
- **Installation**: `pip install crackmapexec`
- **Verwendung**: SMB/WinRM/LDAP pentesting
- **Modern**: Sehr aktiv, beliebt

**Bewertung**: ✅ Später (Phase 7)
- Grund: Modern, powerful, aber komplex

---

## 🎯 Empfohlene Implementierungs-Reihenfolge

### Phase 6 - Task 2-7 (Jetzt)

#### Tier 1: HIGH PRIORITY ⭐⭐⭐
1. **Hydra** - Brute-Force (Legacy-Feature, wichtig)
2. **Nikto** - Web scanning (Legacy-Feature)
3. **Gobuster** - Directory bruteforce (Modern, schnell)
4. **Searchsploit** - Exploit-DB (Wichtig für Discovery)

**Begründung**: 
- Alle Cross-Platform
- 3 davon Legacy-Features (User erwartet sie)
- Gobuster ist modern + schnell
- Zusammen decken sie wichtigste Use-Cases ab

#### Tier 2: MEDIUM PRIORITY ⭐⭐
5. **SSLyze** - SSL/TLS testing (Python, einfach)
6. **WhatWeb** - Tech fingerprinting (JSON output)

**Begründung**:
- Python-basiert (einfache Integration)
- Strukturierte Outputs
- Nützlich aber nicht kritisch

### Phase 7 (Später)

#### Tier 3: OPTIONAL / COMPLEX ⭐
- **CrackMapExec** - SMB pentesting (komplex)
- **Medusa** - Brute-Force alternative
- **TestSSL.sh** - SSL alternative
- **Metasploit Integration** - Sehr komplex

---

## 📋 Implementierungs-Matrix

| Tool | Platform | Output | Legacy | Priority | Phase |
|------|----------|--------|--------|----------|-------|
| **Nmap** | ✅ Win/Lin | XML | ✅ | ✅✅✅ | Done |
| **Hydra** | ✅ Win/Lin | Plain | ✅ | ✅✅✅ | 6 |
| **Nikto** | ⚠️ Win(Perl)/Lin | XML | ✅ | ✅✅✅ | 6 |
| **Gobuster** | ✅ Win/Lin | Plain | ❌ | ✅✅✅ | 6 |
| **Searchsploit** | ✅ Win/Lin | JSON | ✅ | ✅✅✅ | 6 |
| **SSLyze** | ✅ Win/Lin | JSON | ✅ | ✅✅ | 6 |
| **WhatWeb** | ⚠️ Win(Ruby)/Lin | JSON | ✅ | ✅✅ | 6 |
| **CrackMapExec** | ✅ Win/Lin | - | ❌ | ✅ | 7 |
| **Dirb** | ❌ Lin | Plain | ✅ | ⏸️ | - |
| **Enum4linux** | ❌ Lin | Plain | ✅ | ⏸️ | - |
| **Metasploit** | ✅ Win/Lin | - | ✅ | ⏸️ | 8 |

**Legende**:
- ✅ Voll unterstützt
- ⚠️ Eingeschränkt (z.B. braucht Perl/Ruby)
- ❌ Nicht unterstützt
- ⏸️ Zurückgestellt

---

## 💡 Technische Überlegungen

### Windows-Spezifische Herausforderungen

1. **Perl/Ruby Dependencies** (Nikto, WhatWeb):
   - Lösung: Strawberry Perl, Ruby Installer
   - Alternative: WSL-Unterstützung prüfen
   - Check: Installation-Detection

2. **Binary Verfügbarkeit**:
   - Hydra: Windows-Binary verfügbar (THC-Hydra)
   - Gobuster: Go-Binary (einfach)
   - Searchsploit: Python-Script (portable)

3. **Path-Handling**:
   - Windows: `C:\Program Files\...`
   - Linux: `/usr/bin/...`
   - Lösung: Platform-agnostisches Discovery (Phase 2)

### Output-Parsing

| Tool | Format | Parser-Komplexität |
|------|--------|-------------------|
| Hydra | Plain text | Medium (Regex) |
| Nikto | XML/JSON | Low (XML Parser) |
| Gobuster | Plain text | Low (Line-by-line) |
| Searchsploit | JSON | Low (JSON Parser) |
| SSLyze | JSON | Low (JSON Parser) |
| WhatWeb | JSON | Low (JSON Parser) |

---

## 🚀 Nächste Schritte

### Phase 6 - Task 2: Wrapper-Gerüst

**Empfohlene Reihenfolge**:

1. **Hydra** (Wichtigste Legacy-Feature)
   - Brute-Force ist Core-Funktionalität
   - Benutzer erwarten es

2. **Gobuster** (Einfachste Implementierung)
   - Binary, einfacher Output
   - Schnell testbar

3. **Searchsploit** (Python-basiert)
   - Python-Script, einfach
   - JSON output

4. **Nikto** (XML-Parsing)
   - Komplexer (Perl), aber wichtig
   - XML-Parser bereits vorhanden (Nmap)

5. **SSLyze** (Python)
   - Python-Package
   - JSON output

6. **WhatWeb** (Optional)
   - Ruby-Dependency
   - Wenn Zeit

---

## 📝 Entscheidungs-Zusammenfassung

**Für Phase 6 implementieren (4-6 Tools)**:
1. ✅ Hydra (HIGH)
2. ✅ Gobuster (HIGH)
3. ✅ Searchsploit (HIGH)
4. ✅ Nikto (HIGH)
5. ✅ SSLyze (MEDIUM)
6. ⏳ WhatWeb (MEDIUM - optional)

**Zurückstellen**:
- ⏸️ Linux-only Tools (Dirb, Enum4linux)
- ⏸️ Komplexe Frameworks (Metasploit, CME)
- ⏸️ Duplikate (Medusa, TestSSL.sh)

**Begründung**:
- Fokus auf Cross-Platform
- Legacy-Features abdecken (User-Erwartung)
- Moderne Tools ergänzen (Gobuster)
- Machbare Komplexität
- Strukturierte Outputs bevorzugen

---

**Maintainer**: Gotarr  
**Status**: Proposal for Phase 6 Implementation  
**Datum**: 13. November 2025
