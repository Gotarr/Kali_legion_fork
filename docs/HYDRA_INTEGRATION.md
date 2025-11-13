# Hydra Integration Documentation

## Overview

THC-Hydra is a parallelized network authentication cracker supporting 50+ protocols. Legion v2.0 integrates Hydra for brute-force credential discovery across multiple services.

**Version**: Hydra v9.6 (November 2025)  
**License**: AGPL-3.0  
**Author**: van Hauser/THC & David Maciejak  
**Integration Date**: 2025-11-13  
**Phase**: Phase 6 - Additional Tools

---

## Features

### Supported Protocols (50+)

**Network Services:**
- SSH (v1 & v2)
- FTP, FTPS
- Telnet
- RDP (Remote Desktop)

**Web:**
- HTTP(S) GET/POST
- HTTP(S) Basic/Digest Auth
- HTTP(S) Form-based (POST/GET)
- HTTP Proxy

**Databases:**
- MySQL
- PostgreSQL
- Oracle
- MS-SQL
- MongoDB
- Redis

**Email:**
- SMTP, SMTP Enum
- POP3
- IMAP

**Windows:**
- SMB (Server Message Block)
- RDP (Terminal Services)
- WinRM

**Other:**
- VNC, XMPP, SIP, SNMP, LDAP, Cisco AAA, etc.

### Cross-Platform Support

| Platform | Status | Installation Method |
|----------|--------|---------------------|
| **Windows** | ✅ Supported | Binary download (Cygwin/native) |
| **Linux** | ✅ Native | `apt install hydra` / `yum install hydra` |
| **macOS** | ✅ Supported | `brew install hydra` |

---

## Installation

### Windows

**Option 1: Pre-compiled Binary**
```powershell
# Download from: https://github.com/maaaaz/thc-hydra-windows
# Extract to C:\Tools\Hydra or C:\Program Files\Hydra
```

**Option 2: Cygwin**
```bash
# Install Cygwin, then:
apt-cyg install hydra
```

### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install hydra
```

### Linux (Red Hat/CentOS)

```bash
sudo yum install hydra
# or
sudo dnf install hydra
```

### macOS

```bash
brew install hydra
```

### Verify Installation

```bash
hydra -h
hydra --version
```

---

## Usage

### Python API

#### Basic Attack

```python
from legion.tools.hydra import HydraTool

# Initialize tool
hydra = HydraTool()

# Validate installation
if await hydra.validate():
    # Perform SSH brute-force attack
    result = await hydra.attack(
        target="192.168.1.100",
        service="ssh",
        login_list=["admin", "root", "user"],
        password_list=["password", "123456", "admin"],
        tasks=4  # Parallel threads
    )
    
    # Check results
    if result.parsed_data.success:
        for cred in result.parsed_data.credentials:
            print(f"Found: {cred.login}:{cred.password}")
```

#### Attack with Files

```python
from pathlib import Path

result = await hydra.attack(
    target="ftp.example.com",
    service="ftp",
    login_file=Path("wordlists/users.txt"),
    password_file=Path("wordlists/passwords.txt"),
    tasks=16,
    timeout=300  # 5 minutes
)

# Access parsed data
credentials = result.parsed_data.credentials
stats = result.parsed_data.statistics

print(f"Found {len(credentials)} credentials")
print(f"Duration: {stats.duration_seconds}s")
print(f"Speed: {stats.attempts_per_second:.1f} attempts/s")
```

#### HTTP Form Attack

```python
# HTTP POST form brute-force
result = await hydra.attack(
    target="192.168.1.50",
    service="http-post-form",
    login_list=["admin"],
    password_list=["password123", "admin"],
    additional_args=[
        "/login.php:username=^USER^&password=^PASS^:F=incorrect"
    ]
)
```

#### Combo File (user:pass format)

```python
# Use colon-separated user:pass file
result = await hydra.attack(
    target="192.168.1.1",
    service="ssh",
    combo_file=Path("default_creds.txt"),
    tasks=8
)
```

### Command-Line Examples

```bash
# SSH attack with username and password lists
hydra -L users.txt -P passwords.txt ssh://192.168.1.1

# FTP attack with single user, multiple passwords
hydra -l admin -P passwords.txt ftp://192.168.1.100

# HTTP POST form attack
hydra -L users.txt -P passwords.txt 192.168.1.50 http-post-form "/login:user=^USER^&pass=^PASS^:F=incorrect"

# RDP attack with custom port
hydra -L users.txt -P passwords.txt rdp://192.168.1.1:3389

# MySQL attack with verbose output
hydra -l root -P passwords.txt -vV mysql://192.168.1.1

# Use combo file (user:pass per line)
hydra -C combo.txt ssh://192.168.1.1
```

---

## Output Format

### Successful Attack

```
Hydra v9.6 (c) 2023 by van Hauser/THC
Hydra (https://github.com/vanhauser-thc/thc-hydra) starting at 2025-11-13 10:30:00
[DATA] max 16 tasks per 1 server, overall 16 tasks, 100 login tries (l:10/p:10)
[DATA] attacking ssh://192.168.1.1:22/
[22][ssh] host: 192.168.1.1   login: admin   password: admin123
[22][ssh] host: 192.168.1.1   login: root   password: toor
1 of 1 target successfully completed, 2 valid passwords found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2025-11-13 10:30:15
```

### Parsed Result

```python
result.parsed_data = HydraResult(
    credentials=[
        HydraCredential(
            host="192.168.1.1",
            port=22,
            service="ssh",
            login="admin",
            password="admin123"
        ),
        HydraCredential(
            host="192.168.1.1",
            port=22,
            service="ssh",
            login="root",
            password="toor"
        )
    ],
    statistics=HydraStatistics(
        total_attempts=100,
        successful_attempts=2,
        duration_seconds=15.0,
        attempts_per_second=6.67,
        tasks=16
    ),
    target="192.168.1.1",
    service="ssh"
)
```

---

## Architecture

### Components

```
src/legion/tools/hydra/
├── __init__.py          # Package exports
├── tool.py              # HydraTool wrapper
└── parser.py            # Output parser
```

### Class Hierarchy

```
BaseTool (tools/base.py)
    └── HydraTool (tools/hydra/tool.py)
            ├── attack() - Execute brute-force
            ├── parse_output() - Parse results
            └── validate() - Check installation

HydraOutputParser (tools/hydra/parser.py)
    └── parse() - Parse stdout/stderr
            ├── _parse_credential()
            ├── _parse_statistics()
            ├── _parse_error()
            └── _parse_warning()
```

### Data Models

```python
@dataclass
class HydraCredential:
    host: str
    port: int
    service: str
    login: str
    password: str

@dataclass
class HydraStatistics:
    total_attempts: int
    successful_attempts: int
    duration_seconds: float
    attempts_per_second: float
    tasks: int

@dataclass
class HydraResult:
    credentials: List[HydraCredential]
    statistics: HydraStatistics
    target: str
    service: str
    errors: List[str]
    warnings: List[str]
```

---

## Configuration

### Registry Integration

Hydra is auto-discovered via `ToolRegistry`:

```python
from legion.tools.registry import get_registry

registry = get_registry()

# Auto-discover Hydra
hydra_path = registry.get_tool("hydra")

# Set custom path
registry.set_tool_path("hydra", Path("C:/Tools/Hydra/hydra.exe"))

# Add custom search directory
registry.add_custom_path("hydra", Path("C:/CustomTools"))
```

### Discovery Locations

**Windows:**
- `C:\Program Files\Hydra`
- `C:\Program Files (x86)\Hydra`
- `C:\Program Files\THC-Hydra`
- `C:\Tools\Hydra`
- `%USERPROFILE%\Tools`
- System PATH

**Linux:**
- `/usr/bin/hydra`
- `/usr/local/bin/hydra`
- `/snap/bin/hydra`
- `~/.local/bin/hydra`

**macOS:**
- `/usr/local/bin/hydra` (Homebrew Intel)
- `/opt/homebrew/bin/hydra` (Homebrew Apple Silicon)
- `/opt/local/bin/hydra` (MacPorts)

---

## Performance Tuning

### Parallel Tasks

```python
# Low impact (4 threads)
result = await hydra.attack(..., tasks=4)

# Medium impact (16 threads) - Recommended
result = await hydra.attack(..., tasks=16)

# High impact (64 threads) - May trigger IDS/IPS
result = await hydra.attack(..., tasks=64)
```

### Timeouts

```python
# Short timeout (60 seconds)
result = await hydra.attack(..., timeout=60)

# Medium timeout (5 minutes)
result = await hydra.attack(..., timeout=300)

# Long timeout (30 minutes)
result = await hydra.attack(..., timeout=1800)
```

### Additional Flags

```python
# Verbose output
result = await hydra.attack(..., additional_args=["-vV"])

# Stop after first success
result = await hydra.attack(..., additional_args=["-f"])

# Restore session
result = await hydra.attack(..., additional_args=["-R"])

# Use SSL
result = await hydra.attack(..., additional_args=["-S"])
```

---

## Security Considerations

### Legal Usage

⚠️ **WARNING**: Hydra is a penetration testing tool.

**Legal use cases:**
- Authorized penetration testing
- Security audits with written permission
- Testing your own systems
- Educational purposes in controlled environments

**Illegal use cases:**
- Unauthorized access attempts
- Attacking systems without permission
- Military/secret service usage (per author's request)

### Detection Avoidance

```python
# Slower, stealthier attack
result = await hydra.attack(
    target="...",
    service="ssh",
    login_list=[...],
    password_list=[...],
    tasks=1,  # Single thread
    additional_args=[
        "-w", "5",  # 5 second wait between attempts
        "-t", "1"   # 1 task only
    ]
)
```

### Rate Limiting

Most services implement rate limiting:
- SSH: Often 3-5 attempts before delay
- RDP: Lockout after failed attempts
- Web: Varies by application

Adjust `tasks` and add delays accordingly.

---

## Testing

### Run Tests

```bash
# Unit tests (parser)
pytest tests/test_hydra_parser.py -v

# Integration tests (requires Hydra installed)
pytest tests/test_hydra_tool.py -v

# All Hydra tests
pytest tests/test_hydra*.py -v

# Skip integration tests
pytest tests/test_hydra*.py -v -m "not integration"
```

### Test Coverage

```bash
pytest tests/test_hydra*.py --cov=src/legion/tools/hydra --cov-report=html
```

---

## Troubleshooting

### Common Issues

**1. Hydra not found**

```python
# Check registry
from legion.tools.registry import get_registry
registry = get_registry()
hydra_path = registry.get_tool("hydra")
print(f"Hydra path: {hydra_path}")

# Set manually
registry.set_tool_path("hydra", Path("C:/Tools/Hydra/hydra.exe"))
```

**2. Connection timeout**

```python
# Increase timeout
result = await hydra.attack(..., timeout=600)  # 10 minutes
```

**3. No credentials found**

- Verify target is reachable
- Check service is running on target port
- Ensure wordlists are correct
- Try verbose mode: `additional_args=["-vV"]`

**4. Windows: "Cannot find hydra.exe"**

- Add Hydra directory to PATH
- Use full path in registry
- Check binary is actually `hydra.exe` not `hydra`

---

## Performance Benchmarks

### Attack Speed (estimates)

| Service | Tasks | Speed (attempts/sec) | Notes |
|---------|-------|---------------------|-------|
| SSH | 4 | 1-2 | Connection overhead |
| FTP | 16 | 10-15 | Fast protocol |
| HTTP | 16 | 5-10 | Depends on server |
| RDP | 4 | 0.5-1 | Slow handshake |
| MySQL | 16 | 15-20 | Fast after connect |

**Factors affecting speed:**
- Network latency
- Service rate limiting
- Target server performance
- Number of parallel tasks
- Protocol complexity

---

## Integration with Legion

### Scanner Integration

```python
from legion.core.scanner import ScanManager

scanner = ScanManager(database=db)

# Add Hydra to scan pipeline
# (Future implementation in Phase 7)
```

### UI Integration

```python
# Settings Dialog integration
# (Future implementation in Phase 7)
```

---

## References

- **Official Repository**: https://github.com/vanhauser-thc/thc-hydra
- **Documentation**: https://github.com/vanhauser-thc/thc-hydra/blob/master/README
- **Windows Build**: https://github.com/maaaaz/thc-hydra-windows
- **Kali Tools**: https://www.kali.org/tools/hydra/

---

## Changelog

### 2025-11-13 - Initial Integration
- ✅ HydraTool wrapper class
- ✅ HydraOutputParser with regex parsing
- ✅ Tool registry integration
- ✅ Cross-platform support (Windows/Linux/macOS)
- ✅ Unit tests (parser)
- ✅ Integration tests (tool wrapper)
- ✅ Documentation

### Future Enhancements
- [ ] GUI integration (Phase 7)
- [ ] Credential storage in database
- [ ] Attack templates for common services
- [ ] Progress callbacks during attack
- [ ] Auto-resume on failure

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-13  
**Author**: Gotham Security
