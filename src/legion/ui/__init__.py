"""
Modern UI components for Legion.

This package provides PyQt6-based UI with clean architecture:
- Model-View-Controller pattern
- Integration with new backend (Phase 1-4)
- Theme support (light/dark/system)
- Config-driven UI settings
"""

from legion.ui.mainwindow import MainWindow
from legion.ui.models import HostsTableModel, PortsTableModel
from legion.ui.dialogs import NewScanDialog, ScanProgressDialog, AboutDialog

__all__ = [
    "MainWindow", 
    "HostsTableModel", 
    "PortsTableModel",
    "NewScanDialog",
    "ScanProgressDialog",
    "AboutDialog"
]
