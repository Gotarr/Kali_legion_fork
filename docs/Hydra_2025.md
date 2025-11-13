Hydra Status (November 2025)
Ja, Hydra ist noch aktuell:

✅ Letzte Release: v9.6 (September 2024)
✅ Aktiv maintained: 989 Commits, 88 Contributors
✅ GitHub: 11.2k Stars, aktive Community
✅ Lizenz: AGPL-3.0 (ursprünglich von van Hauser/THC)
Unterstützte Protokolle (50+):
SSH, FTP, HTTP(S), SMTP, POP3, IMAP, RDP, SMB, MySQL, PostgreSQL, MongoDB, Redis, Telnet, VNC, und viele mehr

Moderne Alternativen
Für Legion v2.0 sollten wir beide Ansätze kombinieren:

Option 1: Hydra behalten (empfohlen für Legacy-Kompatibilität)
Pro:

Bewährtes Tool, seit 2001 im Einsatz
50+ Protokolle out-of-the-box
In Original-Legion bereits integriert
Cross-platform (Windows/Linux)
Contra:

C-basiert, komplexere Installation auf Windows
Output-Parsing manchmal inkonsistent
Option 2: Moderne Ergänzungen/Alternativen
Crackmapexec → NetExec (Nachfolger, 2024):

Fokus: Windows-Netzwerke (SMB, WinRM, LDAP, MSSQL)
Python-basiert, besseres Output-Format
❌ Aber: Primär Linux, Windows-Support eingeschränkt
Medusa:

Ähnlich wie Hydra, modularer
❌ Weniger aktiv maintained (letzte Release 2015)
Patator (Python):

Flexibler, Python-basiert
Besseres Output-Parsing (XML/JSON)
❌ Weniger Protokolle als Hydra
THC-Hydra + Ncrack (Nmap):

Ncrack: Nmap's Brute-Force-Tool
Fokus: Network authentication
✅ Cross-platform, gute Nmap-Integration