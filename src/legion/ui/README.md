# Legion New UI (Phase 5)

Modern PyQt6-based user interface for Legion network scanner.

---

## Status: ✅ Production-Ready for Scanning

**Completed**:
- ✅ UI Architecture (MainWindow, Models, Dialogs)
- ✅ Database Integration (Qt Table Models)
- ✅ Scanner Integration (qasync for asyncio+Qt)
- ✅ Production Application (run_legion_ui.py)

**In Progress**:
- 🔄 Config Dialog
- 🔄 Legacy UI Migration
- 🔄 Testing & Polish

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run new UI
py legion.py
```

**Requirements**:
- Python 3.10+
- PyQt6
- qasync (for async scanner integration)
- nmap in PATH

---

## Architecture

```
┌─────────────────────────────────────┐
│     LegionApplication (app.py)      │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────┐  ┌───────────────┐  │
│  │ Config    │  │ Database      │  │
│  │ Manager   │  │ (SQLite)      │  │
│  └───────────┘  └───────────────┘  │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   Scanner (asyncio)         │   │
│  │   + qasync Event Loop       │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   MainWindow (PyQt6)        │   │
│  │   ├── HostsTableModel       │   │
│  │   ├── PortsTableModel       │   │
│  │   └── Dialogs               │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### Key Components

**Application Layer** (`src/legion/ui/app.py`):
- `LegionApplication`: Main application class
- Lifecycle management (init, start, cleanup)
- qasync event loop setup

**UI Layer** (`src/legion/ui/`):
- `MainWindow`: Main window with menu, toolbar, tables
- `HostsTableModel`, `PortsTableModel`: Qt data models
- `NewScanDialog`, `ScanProgressDialog`: Dialogs
- `async_helper.py`: qasync integration utilities

**Data Layer**:
- `SimpleDatabase` (from Phase 3)
- `ScanManager` (from Phase 3)
- `ConfigManager` (from Phase 4)

---

## Critical: qasync Integration

The UI uses **qasync** to integrate asyncio (scanner) with Qt event loop.

### Why qasync?

**Problem**: asyncio and Qt use separate event loops that don't communicate.

**Without qasync**:
```python
app = QApplication(sys.argv)
# asyncio loop never runs → scanner workers never start!
app.exec()
```

**With qasync** ✅:
```python
import qasync
app = QApplication(sys.argv)
loop = qasync.QEventLoop(app)  # Integrated loop!
asyncio.set_event_loop(loop)

await scanner.start()  # Workers run!
with loop:
    loop.run_forever()  # Both Qt and asyncio tasks run
```

**See**: `docs/SCANNER_INTEGRATION_FIX.md` for details.

---

## File Structure

```
src/legion/ui/
├── __init__.py          # Package exports
├── app.py               # Application entry point (174 lines)
├── mainwindow.py        # Main window (541 lines)
├── models.py            # Qt table models (400 lines)
├── dialogs.py           # UI dialogs (380+ lines)
└── async_helper.py      # qasync utilities (119 lines)

run_legion_ui.py         # UI launcher (26 lines)

tests/ui/
├── README.md                   # Testing guide
├── test_mainwindow.py          # UI test with sample data
├── test_empty_scan.py          # Test with real scans
├── test_qasync_fix.py          # qasync proof-of-concept
└── ...                         # Other test scripts

docs/
├── QUICK_START.md              # User guide
├── PHASE5_SUMMARY.md           # Technical progress
└── SCANNER_INTEGRATION_FIX.md  # qasync solution
```

---

## Features

### Scanning
- Multiple scan types (Quick, Full, Stealth, etc.)
- Custom nmap arguments
- Async execution with progress tracking
- Results stored in database

### UI
- Host table with sorting, color-coding
- Port table (master-detail pattern)
- Auto-refresh every 10 seconds
- Status bar with scan progress
- Tooltips with details

### Configuration
- TOML-based config (Phase 4)
- Theme support (light/dark/system)
- Tool path configuration
- Scan defaults

---

## Testing

### Run Tests

```bash
# All UI tests (requires qasync!)
py tests/ui/test_mainwindow.py
py tests/ui/test_empty_scan.py
py tests/ui/test_qasync_fix.py
```

### Test Files

| File | Purpose | qasync |
|------|---------|--------|
| `test_mainwindow.py` | UI with 5 sample hosts | ✅ |
| `test_empty_scan.py` | Real scan with empty DB | ✅ |
| `test_qasync_fix.py` | Proof-of-concept | ✅ |
| `test_scan_dialog.py` | Just the scan dialog | ❌ |

**Note**: Tests using scanner require qasync integration!

---

## Development

### Adding Features

1. **New Dialog**: Add to `dialogs.py`
2. **New Model**: Add to `models.py`
3. **New Menu Item**: Modify `mainwindow.py` → `_create_menu_bar()`
4. **Config Setting**: Update Phase 4 config schema

### Code Style

- **Logging**: Use `logger.info/debug/error` (not print!)
- **Signals**: For thread-safe UI updates
- **Type Hints**: Always use type annotations
- **Docstrings**: Google-style docstrings

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Run with debug prints:
```bash
py legion.py 2>&1 | tee ui_debug.log
```

---

## Known Issues

### Worker Errors

```
Worker error: 'NoneType' object has no attribute 'create_future'
```

**Status**: Non-critical, scanner works fine  
**Cause**: Worker pool initialization timing  
**Fix**: TODO in next iteration

### Auto-Refresh Timing

- Auto-refresh runs every 10 seconds
- Can cause brief UI lag with large datasets
- Solution: Configurable interval, optional disable

---

## Roadmap

### Phase 5 Tasks

- [x] Task 1: UI Architecture Setup
- [x] Task 2: Database Bridge & Models
- [x] Task 3: Scanner Integration
- [x] Task 4: Production Integration
- [ ] Task 5: Config Dialog
- [ ] Task 6: Main Window Migration
- [ ] Task 7: Testing & Polish

### Future Enhancements

- Scan templates
- Export to CSV/JSON
- Network topology graph
- Plugin system
- Custom color schemes
- Keyboard shortcuts

---

## Contributing

1. **Test changes**: Run all tests in `tests/ui/`
2. **Update docs**: Keep README.md and PHASE5_SUMMARY.md current
3. **Use qasync**: Always use qasync for asyncio+Qt
4. **Follow patterns**: Check existing code for patterns

---

## Resources

- **PyQt6 Docs**: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **qasync GitHub**: https://github.com/CabbageDevelopment/qasync
- **Qt Model/View**: https://doc.qt.io/qt-6/model-view-programming.html

---

**Status**: Production-Ready ✅  
**Version**: 0.5.0  
**Last Update**: 12 Nov 2025
