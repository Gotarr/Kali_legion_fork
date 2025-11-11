# Legion v2.0 - Cross-Platform Migration

This directory contains the new cross-platform implementation of Legion.

## 🚀 Quick Test

To test the new platform-independent foundation:

```bash
# From the repository root (Windows)
py -m src.legion

# Linux/macOS
python3 -m src.legion

# Or after installing in development mode:
pip install -e .
py -m legion
```

## 📁 Structure

```
src/legion/
├── __init__.py           # Package initialization
├── __main__.py           # Entry point (python -m legion)
│
├── platform/             # OS abstraction layer
│   ├── detector.py       # Platform detection
│   ├── paths.py          # Cross-platform paths
│   └── privileges.py     # Admin/root handling
│
├── core/                 # Business logic (OS-independent)
│   └── (coming soon)
│
├── tools/                # Tool wrappers
│   └── (coming soon)
│
├── config/               # Configuration management
│   └── (coming soon)
│
└── utils/                # Utilities
    └── (coming soon)
```

## ✅ What's Working

### Platform Layer
- ✅ OS detection (Windows, Linux, macOS)
- ✅ WSL detection
- ✅ Admin/root privilege checking
- ✅ Cross-platform directory paths
- ✅ Safe path operations

### Tested Platforms
- ✅ Windows 10/11
- ✅ Linux (Ubuntu, Kali)
- ✅ WSL (Windows Subsystem for Linux)
- ⏳ macOS (architecture ready, needs testing)

## 🔨 Testing Individual Modules

### Platform Detection
```bash
# Windows
py src/legion/platform/detector.py

# Linux/macOS
python3 src/legion/platform/detector.py
```

### Path Management
```bash
py src/legion/platform/paths.py
```

### Privilege Checking
```bash
py src/legion/platform/privileges.py
```

## 📝 Next Steps

See [MIGRATION_PLAN.md](../MIGRATION_PLAN.md) for the complete migration roadmap.

**Current Phase**: Phase 1 - Foundation ✅ (Complete)  
**Next Phase**: Phase 2 - Tool Discovery & Wrapper

## 🧪 Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src/legion tests/
```

## 📚 Documentation

- [Migration Plan](../MIGRATION_PLAN.md) - Complete migration strategy
- [Architecture](../ARCHITECTURE.md) - Technical architecture details
- [Legacy Code](../legacy/) - Original implementation (for reference)
