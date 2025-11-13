# Legion Scripts Directory

This directory contains external scripts, tools, wordlists, and resources that Legion uses for automated scanning and exploitation tasks.

## 📂 Structure

```
scripts/
├── nmap/              ✅ Nmap NSE (Nmap Scripting Engine) scripts
│   ├── vulners.nse         # CVE detection via vulners.com
│   ├── shodan-api.nse      # Shodan integration
│   └── shodan-hq.nse       # Shodan HQ variant
│
├── wordlists/         ✅ Password and dictionary lists
│   ├── ftp-betterdefaultpasslist.txt
│   ├── ssh-betterdefaultpasslist.txt
│   ├── mysql-betterdefaultpasslist.txt
│   ├── mssql-betterdefaultpasslist.txt
│   ├── oracle-betterdefaultpasslist.txt
│   ├── postgres-betterdefaultpasslist.txt
│   ├── telnet-betterdefaultpasslist.txt
│   ├── vnc-betterdefaultpasslist.txt
│   ├── windows-betterdefaultpasslist.txt
│   ├── db2-betterdefaultpasslist.txt
│   ├── tomcat-betterdefaultpasslist.txt
│   ├── routers-userpass.txt
│   ├── root-userpass.txt
│   ├── snmp-default.txt
│   ├── ssh-password.txt
│   ├── ssh-user.txt
│   └── gvit_subdomain_wordlist.txt
│
├── nikto/             📋 TODO: Nikto plugins and databases
│   └── (to be added in Phase 6, Task 3)
│
├── hydra/             📋 TODO: Hydra custom modules (optional)
│   └── (custom protocol modules)
│
├── metasploit/        📋 TODO: Custom Metasploit modules
│   ├── exploits/
│   ├── payloads/
│   └── auxiliary/
│
├── exploits/          📋 TODO: Custom exploit scripts
│   └── (Python/Bash exploit scripts)
│
├── exec-in-shell      ⚠️  Legacy script (review needed)
└── README.md          # This file
```

## 🔄 Integration Status

| Directory      | Status | Phase | Description |
|----------------|--------|-------|-------------|
| `nmap/`        | ✅ Done | 6.2 | NSE scripts integrated into NmapTool |
| `wordlists/`   | ✅ Done | 6.2 | Ready for Hydra/Gobuster/custom tools |
| `nikto/`       | 📋 TODO | 6.3 | Nikto plugins and vulnerability databases |
| `hydra/`       | 📋 TODO | 6.3+ | Custom Hydra protocol modules (optional) |
| `metasploit/`  | 📋 TODO | 7+ | Custom MSF modules for Legion |
| `exploits/`    | 📋 TODO | 7+ | Custom exploit scripts (Python/Bash) |

## 🛠️ Usage in Legion v2.0

### Nmap NSE Scripts ✅

**Python API:**
```python
from legion.tools.nmap import NmapTool

nmap = NmapTool()

# Vulners CVE scan (CVSS >= 7.0)
result = await nmap.scan_with_vulners("192.168.1.1", min_cvss=7.0)

# Shodan scan
result = await nmap.scan_with_shodan("8.8.8.8", api_key="YOUR_KEY")
```

**CLI:**
```bash
nmap -sV --script vulners --script-args mincvss=7.0 192.168.1.1
```

### Wordlists ✅

**Python API:**
```python
from pathlib import Path
from legion.tools.hydra import HydraTool

wordlist_dir = Path("scripts/wordlists")
ssh_passwords = wordlist_dir / "ssh-betterdefaultpasslist.txt"

hydra = HydraTool()
result = await hydra.attack(
    target="192.168.1.1",
    service="ssh",
    login_list=["root", "admin"],
    password_file=ssh_passwords
)
```

### Nikto 📋 TODO
**Planned for Phase 6, Task 3**

### Hydra Modules 📋 TODO
**Optional custom protocol modules**

### Metasploit 📋 TODO
**Planned for Phase 7+**

### Exploits 📋 TODO
**Planned for Phase 7+**

## 📚 References

- [Nmap NSE](https://nmap.org/book/nse.html)
- [Vulners](https://github.com/vulnersCom/nmap-vulners)
- [Shodan API](https://developer.shodan.io/)
- [Nikto](https://github.com/sullo/nikto)
- [Hydra](https://github.com/vanhauser-thc/thc-hydra)
- [Metasploit](https://docs.metasploit.com/)

---

**Version**: 2.0.0-alpha6  
**Last Updated**: 13. November 2025  
**Phase**: 6 (Tool Integration - 30%)
