# Legacy Code Archive

**Date Archived**: 12. November 2025  
**Reason**: Phase 5 Migration - New Architecture Complete  

---

## What's Here

This folder contains the **original Legion codebase** before the v2.0 rewrite.

**DO NOT USE THESE FILES** - They are kept for reference only.

---

## Archived Components

### Legacy Application Code
- `app/` - Original application logic (before `src/legion/`)
- `ui/` - Legacy PyQt6 UI (before `src/legion/ui/`)
- `controller/` - Legacy controller pattern
- `db/` - Legacy database code (before `src/legion/core/database.py`)
- `parsers/` - Legacy nmap parsers (before `src/legion/parsers/`)
- `plugins/` - Legacy plugin system
- `utilities/` + `utilities.py` - Legacy utilities

### Legacy Scripts
- `buildHugeNmapTest.py` - Old test data generator
- `primeExploitDb.py` - ExploitDB setup script
- `startLegion.sh` - Old Unix launcher (replaced by `legion.py`)
- `precommit.sh` - Old pre-commit hook

### Legacy Configs
- `legion.conf` - Old config format (replaced by TOML)
- `nmap.xsl` - Old nmap stylesheet
- `pyproject.toml` - Old Python project config

### Build/Deploy (Old)
- `debian/` - Debian packaging (outdated)
- `docker/` - Old Docker setup (needs update)
- `deps/` - Old dependency installation scripts
- `.travis.yml` - Travis CI config (deprecated)
- `.codeclimate.yml` - CodeClimate config
- `.flake8` - Old linter config
- `.justcloned` - Marker file
- `.github/` - Old GitHub workflows

### Old Documentation
- `ARCHITECTURE.md` - Old architecture docs
- `DESIGN_PRINCIPLES.md` - Legacy design philosophy
- `MIGRATION_PLAN.md` - Phase 1-2 migration plan
- `PHASE1_REVIEW.md` - Phase 1 review
- `PHASE2_SUMMARY.md` - Phase 2 summary
- `QUICKSTART.md` - Old quickstart (see `docs/QUICK_START.md`)
- `SETUP_GUIDE.md` - Old setup guide
- `TEST_RESULTS.md` - Old test results
- `STATUS.md.old` - Previous status file
- `CHANGELOG.txt` - Old changelog
- `CONTRIBUTING.md` - Old contribution guidelines

### Temporary Data
- `backup/` - Old backups
- `log/` - Old log files
- `scan_results/` - Old scan results

---

## New Architecture (Active)

**Current codebase** (use these instead):

```
legion/
├── legion.py                    # Main launcher (40 lines)
├── src/legion/                  # New architecture
│   ├── platform/                # Cross-platform support
│   ├── tools/                   # Tool discovery
│   ├── config/                  # TOML config system
│   ├── core/                    # Database, Scanner
│   ├── parsers/                 # Modern parsers
│   └── ui/                      # PyQt6 UI
│       ├── app.py               # Application class
│       ├── mainwindow.py        # Main window
│       ├── models.py            # Qt models
│       ├── dialogs.py           # Dialogs
│       └── settings.py          # Settings dialog
├── tests/                       # Test suite
├── docs/                        # Documentation
├── scripts/nmap/                # NSE scripts
├── wordlists/                   # Password lists
└── images/                      # Icons/logos
```

---

## Migration Summary

### What Changed

| Old | New | Status |
|-----|-----|--------|
| `app/` | `src/legion/` | ✅ Replaced |
| `ui/` | `src/legion/ui/` | ✅ Replaced |
| `db/` | `src/legion/core/database.py` | ✅ Replaced |
| `controller/` | `src/legion/ui/mainwindow.py` | ✅ Replaced |
| `parsers/` | `src/legion/parsers/` | ✅ Replaced |
| `legion.conf` | `legion.toml` (TOML) | ✅ Replaced |
| `startLegion.sh` | `legion.py` | ✅ Replaced |

### Key Improvements

1. **Cross-Platform**: Windows/Linux/macOS support
2. **Modern Config**: TOML instead of custom format
3. **Type Safety**: Full type hints throughout
4. **Async Scanner**: Proper asyncio + Qt (qasync)
5. **Modular**: Clean separation of concerns
6. **Tested**: Comprehensive test suite
7. **Documented**: Full documentation in `docs/`

---

## Why Archive Instead of Delete?

1. **Reference**: Useful to understand old behavior
2. **Migration Aid**: Some features may need porting later
3. **Documentation**: Old code documents original intentions
4. **Recovery**: Can extract specific logic if needed

---

## Can I Delete This?

**Short answer**: Not yet.

**Long answer**: 
- Phase 5 is 75% complete (6/8 tasks)
- Tasks 7-8 may need reference to old code
- After Phase 5 complete → safe to delete
- Recommend keeping until Phase 6 (Plugin System)

---

## Restoration (If Needed)

To restore old code (NOT recommended):

```powershell
# Move everything back
Move-Item _old\* . -Force

# Run old Legion
python legion.py  # (old version had 173 lines)
```

**WARNING**: Old code is not maintained and may not work!

---

## Questions?

See current documentation:
- **Quick Start**: `docs/QUICK_START.md`
- **Phase 5 Progress**: `docs/PHASE5_SUMMARY.md`
- **Architecture**: `docs/` folder
- **Status**: `STATUS.md`

---

**Archive maintained by**: Gotham Security  
**Last updated**: 12. November 2025
