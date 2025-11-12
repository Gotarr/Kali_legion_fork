"""
Main window for Legion application.

Modernized version of legacy UI with:
- Integration with new backend (SimpleDatabase, ScanManager)
- Config system integration
- Theme support
- Model-View-Controller architecture
"""

from pathlib import Path
from typing import Optional, Callable
import logging
import asyncio

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QTableView

from legion.config import get_config, ConfigManager
from legion.core.database import SimpleDatabase
from legion.core.scanner import ScanManager, ScanJob
from legion.ui.models import HostsTableModel, PortsTableModel
from legion.ui.dialogs import NewScanDialog, ScanProgressDialog, AboutDialog
from legion.ui.settings import SettingsDialog

logger = logging.getLogger(__name__)


class ScanSignals(QObject):
    """Qt signals for scanner callbacks (thread-safe UI updates)."""
    progress = pyqtSignal(object)  # ScanJob
    completed = pyqtSignal(object)  # ScanJob


class MainWindow(QMainWindow):
    """
    Legion main application window.
    
    This is the modernized version of the legacy UI, integrated with:
    - Phase 1: Platform detection
    - Phase 2: Tool discovery
    - Phase 3: Core logic (Database, Scanner)
    - Phase 4: Configuration system
    """
    
    def __init__(
        self,
        database: Optional[SimpleDatabase] = None,
        scanner: Optional[ScanManager] = None,
        config_manager: Optional[ConfigManager] = None,
        parent: Optional[QtWidgets.QWidget] = None
    ):
        """
        Initialize main window.
        
        Args:
            database: Database instance (creates default if None)
            scanner: Scanner manager (creates default if None)
            config_manager: Config manager (uses global if None)
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Core components
        self.config = get_config()
        self.config_manager = config_manager
        self.database = database or SimpleDatabase(project_name=self.config.project.name)
        self.scanner = scanner or ScanManager(
            database=self.database,
            max_concurrent_scans=self.config.scanning.max_concurrent
        )
        
        # UI state
        self._theme = self.config.ui.theme
        
        # Table models
        self.hosts_model = HostsTableModel(self.database)
        self.ports_model = PortsTableModel(self.database)
        
        # Scanner signals for thread-safe UI updates
        self.scan_signals = ScanSignals()
        self.scan_signals.progress.connect(self._on_scan_progress_ui)
        self.scan_signals.completed.connect(self._on_scan_completed_ui)
        
        # Register scanner callbacks (these run on scanner thread)
        self.scanner.add_progress_callback(self._on_scan_progress_callback)
        self.scanner.add_completion_callback(self._on_scan_completed_callback)
        
        # Setup UI
        self._setup_ui()
        self._apply_config()
        self._connect_signals()
        
        logger.info("MainWindow initialized")
    
    def _setup_ui(self) -> None:
        """Setup main UI components."""
        # Window properties
        self.setWindowTitle("Legion - Network Penetration Testing Tool")
        self.setMinimumSize(1024, 768)
        
        # Apply window settings from config
        if self.config.ui.remember_window_size:
            # TODO: Load saved window geometry
            pass
        
        # Central widget with main layout
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Setup components
        self._setup_toolbar()
        self._setup_main_content()
        self._setup_statusbar()
        self._setup_menubar()
        
        logger.debug("UI components setup complete")
    
    def _setup_toolbar(self) -> None:
        """Setup main toolbar."""
        if not self.config.ui.show_toolbar:
            return
        
        self.toolbar = self.addToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setMovable(False)
        
        # TODO: Add toolbar actions (Phase 5.2)
        # - New scan
        # - Stop scan
        # - Settings
        # - Help
        
        logger.debug("Toolbar setup complete")
    
    def _setup_main_content(self) -> None:
        """Setup main content area."""
        # Main splitter (horizontal)
        self.main_splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Left panel: Hosts view
        self.left_panel = QtWidgets.QWidget()
        self.left_layout = QtWidgets.QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(5, 5, 5, 5)
        self.main_splitter.addWidget(self.left_panel)
        
        # Hosts table
        hosts_label = QtWidgets.QLabel("Hosts")
        hosts_label.setStyleSheet("font-weight: bold;")
        self.left_layout.addWidget(hosts_label)
        
        self.hosts_table = QTableView()
        self.hosts_table.setModel(self.hosts_model)
        self.hosts_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.hosts_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.hosts_table.setAlternatingRowColors(True)
        self.hosts_table.setSortingEnabled(True)
        self.hosts_table.horizontalHeader().setStretchLastSection(True)
        self.hosts_table.selectionModel().selectionChanged.connect(self._on_host_selected)
        self.left_layout.addWidget(self.hosts_table)
        
        # Right panel: Services/Ports view
        self.right_panel = QtWidgets.QWidget()
        self.right_layout = QtWidgets.QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(5, 5, 5, 5)
        self.main_splitter.addWidget(self.right_panel)
        
        # Ports/Services table
        ports_label = QtWidgets.QLabel("Ports / Services")
        ports_label.setStyleSheet("font-weight: bold;")
        self.right_layout.addWidget(ports_label)
        
        self.ports_table = QTableView()
        self.ports_table.setModel(self.ports_model)
        self.ports_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.ports_table.setAlternatingRowColors(True)
        self.ports_table.setSortingEnabled(True)
        self.ports_table.horizontalHeader().setStretchLastSection(True)
        self.right_layout.addWidget(self.ports_table)
        
        # Set splitter sizes (60/40 split)
        self.main_splitter.setSizes([600, 400])
        
        logger.debug("Main content setup complete")
    
    def _setup_statusbar(self) -> None:
        """Setup status bar."""
        if not self.config.ui.show_statusbar:
            return
        
        self.status = self.statusBar()
        
        # Left: Status message
        self.status_label = QtWidgets.QLabel("Ready")
        self.status.addWidget(self.status_label)
        
        # Right: Project info
        self.project_label = QtWidgets.QLabel(f"Project: {self.config.project.name}")
        self.status.addPermanentWidget(self.project_label)
        
        logger.debug("Statusbar setup complete")
    
    def _setup_menubar(self) -> None:
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New Project
        new_action = QtGui.QAction("&New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_action)
        
        # Open Project
        open_action = QtGui.QAction("&Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Settings
        settings_action = QtGui.QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._on_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QtGui.QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Scan menu
        scan_menu = menubar.addMenu("&Scan")
        
        # New Scan
        scan_action = QtGui.QAction("&New Scan", self)
        scan_action.setShortcut("Ctrl+Shift+N")
        scan_action.triggered.connect(self._on_new_scan)
        scan_menu.addAction(scan_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Theme submenu
        theme_menu = view_menu.addMenu("&Theme")
        
        theme_group = QtGui.QActionGroup(self)
        for theme_name in ["light", "dark", "system"]:
            theme_action = QtGui.QAction(theme_name.capitalize(), self)
            theme_action.setCheckable(True)
            theme_action.setChecked(self.config.ui.theme == theme_name)
            theme_action.triggered.connect(lambda checked, t=theme_name: self._on_theme_change(t))
            theme_group.addAction(theme_action)
            theme_menu.addAction(theme_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QtGui.QAction("&About Legion", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
        logger.debug("Menubar setup complete")
    
    def _apply_config(self) -> None:
        """Apply configuration to UI."""
        # Font size
        font = self.font()
        font.setPointSize(self.config.ui.font_size)
        self.setFont(font)
        
        # Theme
        self._apply_theme(self.config.ui.theme)
        
        # Window state
        if self.config.ui.remember_window_size:
            self.setWindowState(Qt.WindowState.WindowMaximized)
        
        logger.debug(f"Config applied: theme={self.config.ui.theme}, font={self.config.ui.font_size}pt")
    
    def _apply_theme(self, theme: str) -> None:
        """
        Apply theme to application.
        
        Args:
            theme: "light", "dark", or "system"
        """
        # TODO: Implement theme switching (Phase 5.4)
        # For now, just store preference
        self._theme = theme
        logger.info(f"Theme set to: {theme}")
    
    def _connect_signals(self) -> None:
        """Connect internal signals."""
        # Auto-refresh timer (if enabled)
        if self.config.ui.auto_refresh_interval > 0:
            self.refresh_timer = QtCore.QTimer()
            self.refresh_timer.timeout.connect(self._on_auto_refresh)
            self.refresh_timer.start(self.config.ui.auto_refresh_interval * 1000)
    
    # ========================================
    # Event Handlers
    # ========================================
    
    def _on_host_selected(self) -> None:
        """Handle host selection change."""
        indexes = self.hosts_table.selectionModel().selectedRows()
        if indexes:
            row = indexes[0].row()
            host = self.hosts_model.get_host(row)
            if host:
                # Update ports table for selected host
                self.ports_model.set_host(host.ip)
                self.ports_table.resizeColumnsToContents()
                logger.debug(f"Selected host: {host.ip}")
        else:
            # Clear ports table
            self.ports_model.clear()
    
    def _on_auto_refresh(self) -> None:
        """Handle auto-refresh timer."""
        self.refresh_data()
    
    def refresh_data(self) -> None:
        """Refresh all data from database."""
        logger.debug("Refreshing data...")
        
        # Remember current selection
        current_host_ip = None
        indexes = self.hosts_table.selectionModel().selectedRows()
        if indexes:
            host = self.hosts_model.get_host(indexes[0].row())
            if host:
                current_host_ip = host.ip
        
        # Refresh models
        self.hosts_model.refresh()
        
        # Restore selection if possible
        if current_host_ip:
            for row in range(self.hosts_model.rowCount()):
                host = self.hosts_model.get_host(row)
                if host and host.ip == current_host_ip:
                    self.hosts_table.selectRow(row)
                    break
        
        # Resize columns
        self.hosts_table.resizeColumnsToContents()
        self.status_label.setText(f"Refreshed - {self.hosts_model.rowCount()} hosts")
    
    # ========================================
    # Scanner Callbacks (called from scanner thread)
    # ========================================
    
    def _on_scan_progress_callback(self, job: ScanJob) -> None:
        """
        Scanner callback - emits signal for UI thread.
        
        Args:
            job: Scan job with updated status
        """
        # Emit signal to update UI on main thread
        self.scan_signals.progress.emit(job)
    
    def _on_scan_completed_callback(self, job: ScanJob) -> None:
        """
        Scanner callback - emits signal for UI thread.
        
        Args:
            job: Completed scan job
        """
        logger.debug(f"Scan completed: {job.target} - {job.hosts_found} hosts, {job.ports_found} ports")
        # Emit signal to update UI on main thread
        self.scan_signals.completed.emit(job)
    
    # ========================================
    # Scanner UI Updates (called on Qt main thread)
    # ========================================
    
    def _on_scan_progress_ui(self, job: ScanJob) -> None:
        """
        Handle scan progress updates on UI thread.
        
        Args:
            job: Scan job with updated status
        """
        logger.debug(f"Scan progress: {job.target} - {job.status.value}")
        self.status_label.setText(f"Scanning {job.target}... ({job.status.value})")
    
    def _on_scan_completed_ui(self, job: ScanJob) -> None:
        """
        Handle scan completion on UI thread.
        
        Args:
            job: Completed scan job
        """
        logger.info(f"Scan completed: {job.target} - Found {job.hosts_found} hosts, {job.ports_found} ports")
        
        # Refresh tables to show new data
        self.refresh_data()
        
        # Update status
        if job.status.value == "completed":
            self.status_label.setText(
                f"Scan complete: {job.target} - {job.hosts_found} hosts, {job.ports_found} ports"
            )
        elif job.status.value == "failed":
            self.status_label.setText(f"Scan failed: {job.target} - {job.error}")
            QMessageBox.warning(
                self,
                "Scan Failed",
                f"Scan of {job.target} failed:\n{job.error}"
            )
    
    # ========================================
    # Menu Actions
    # ========================================
    
    def _on_new_project(self) -> None:
        """Handle New Project action."""
        # TODO: Implement project creation dialog (Phase 5.2)
        QMessageBox.information(self, "New Project", "New Project dialog (TODO)")
    
    def _on_open_project(self) -> None:
        """Handle Open Project action."""
        # TODO: Implement project open dialog (Phase 5.2)
        QMessageBox.information(self, "Open Project", "Open Project dialog (TODO)")
    
    def _on_settings(self) -> None:
        """Handle Settings action."""
        dialog = SettingsDialog(self.config_manager, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()
    
    def _on_new_scan(self) -> None:
        """Handle New Scan action."""
        # Show New Scan dialog
        result = NewScanDialog.get_scan_parameters(self)
        
        if result:
            target, scan_type, options = result
            logger.info(f"Starting scan: {target} ({scan_type})")
            
            # Queue the scan (async)
            self._queue_scan_async(target, scan_type, options)
            
            # Update status
            self.status_label.setText(f"Queuing scan: {target}...")
    
    def _queue_scan_async(self, target: str, scan_type: str, options: dict) -> None:
        """
        Queue a scan asynchronously.
        
        Args:
            target: Scan target
            scan_type: Type of scan
            options: Scan options
        """
        # Create new event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Queue scan
        async def queue_scan():
            job_id = await self.scanner.queue_scan(target, scan_type, **options)
            logger.info(f"Scan queued: {job_id}")
            
            # Start scanner workers if not running
            if not self.scanner._running:
                await self.scanner.start()
        
        # Run in event loop
        loop.create_task(queue_scan())
    
    def _on_theme_change(self, theme: str) -> None:
        """
        Handle theme change.
        
        Args:
            theme: New theme name
        """
        self._apply_theme(theme)
        
        # Save to config
        if self.config_manager:
            self.config_manager.update(ui__theme=theme)
            self.config_manager.save()
            logger.info(f"Theme changed to: {theme}")
    
    def _on_settings_changed(self) -> None:
        """Handle settings changed from settings dialog."""
        # Reload config
        self.config = self.config_manager.load()
        
        # Apply theme if changed
        self._apply_theme(self.config.ui.theme)
        
        # Update UI elements
        if hasattr(self, 'toolbar'):
            self.toolbar.setVisible(self.config.ui.show_toolbar)
        if hasattr(self, 'statusbar'):
            self.statusbar.setVisible(self.config.ui.show_statusbar)
        
        logger.info("Settings reloaded and applied")
    
    def _on_about(self) -> None:
        """Show About dialog."""
        dialog = AboutDialog(self)
        dialog.exec()
    
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        # TODO: Save window geometry if config.ui.remember_window_size
        # TODO: Stop all running scans
        # TODO: Cleanup resources
        
        logger.info("MainWindow closing")
        event.accept()


# Demo/Test
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create application
    app = QtWidgets.QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Run
    sys.exit(app.exec())
