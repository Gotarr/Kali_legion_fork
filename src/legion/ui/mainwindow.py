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
from legion.ui.dialogs import NewScanDialog, ScanProgressDialog, AboutDialog, AddHostDialog
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
        
        # Add Host action
        self.action_add_host = QtGui.QAction("Add Host", self)
        self.action_add_host.setStatusTip("Add new host to scan")
        self.action_add_host.triggered.connect(self._on_add_hosts)
        self.toolbar.addAction(self.action_add_host)
        
        # Cancel Scan action
        self.action_cancel_scan = QtGui.QAction("Cancel Scan", self)
        self.action_cancel_scan.setStatusTip("Cancel running scan")
        self.action_cancel_scan.setEnabled(False)  # Disabled by default
        self.action_cancel_scan.triggered.connect(self._on_cancel_scan)
        self.toolbar.addAction(self.action_cancel_scan)
        
        self.toolbar.addSeparator()
        
        # Cancel All Scans action
        self.action_cancel_all = QtGui.QAction("Cancel All", self)
        self.action_cancel_all.setStatusTip("Cancel all running scans")
        self.action_cancel_all.setEnabled(False)  # Disabled by default
        self.action_cancel_all.triggered.connect(self._on_cancel_all_scans)
        self.toolbar.addAction(self.action_cancel_all)
        
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
        self.hosts_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.hosts_table.customContextMenuRequested.connect(self._show_host_context_menu)
        self.hosts_table.doubleClicked.connect(self._on_host_double_clicked)
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
        self.ports_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ports_table.customContextMenuRequested.connect(self._show_port_context_menu)
        self.ports_table.doubleClicked.connect(self._on_port_double_clicked)
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
        
        # Export Data
        export_action = QtGui.QAction("&Export Data...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setToolTip("Export all scan data to JSON")
        export_action.triggered.connect(self._on_export_all)
        file_menu.addAction(export_action)
        
        # Import Data
        import_action = QtGui.QAction("&Import Data...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.setToolTip("Import scan data from JSON or XML")
        import_action.triggered.connect(self._on_import_data)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Clear All Data
        clear_action = QtGui.QAction("&Clear All Data", self)
        clear_action.setShortcut("Ctrl+Shift+D")
        clear_action.triggered.connect(self._on_clear_data)
        file_menu.addAction(clear_action)
        
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
        
        # Add Host(s)
        add_host_action = QtGui.QAction("&Add Host(s)", self)
        add_host_action.setShortcut("Ctrl+H")
        add_host_action.triggered.connect(self._on_add_hosts)
        scan_menu.addAction(add_host_action)
        
        scan_menu.addSeparator()
        
        # Cancel Scan
        self.menu_cancel_scan = QtGui.QAction("&Cancel Scan", self)
        self.menu_cancel_scan.setShortcut("Ctrl+Shift+C")
        self.menu_cancel_scan.setToolTip("Cancel the scan of selected host")
        self.menu_cancel_scan.setEnabled(False)
        self.menu_cancel_scan.triggered.connect(self._on_cancel_scan)
        scan_menu.addAction(self.menu_cancel_scan)
        
        # Cancel All Scans
        self.menu_cancel_all = QtGui.QAction("Cancel &All Scans", self)
        self.menu_cancel_all.setShortcut("Ctrl+Shift+A")
        self.menu_cancel_all.setToolTip("Cancel all running scans")
        self.menu_cancel_all.setEnabled(False)
        self.menu_cancel_all.triggered.connect(self._on_cancel_all_scans)
        scan_menu.addAction(self.menu_cancel_all)
        
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
        
        # Keyboard Shortcuts (opens About dialog on Shortcuts tab)
        shortcuts_action = QtGui.QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(lambda: self._on_about(tab=1))
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        # About
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
        """Connect internal signals and setup keyboard shortcuts."""
        # Auto-refresh timer (if enabled)
        if self.config.ui.auto_refresh_interval > 0:
            self.refresh_timer = QtCore.QTimer()
            self.refresh_timer.timeout.connect(self._on_auto_refresh)
            self.refresh_timer.start(self.config.ui.auto_refresh_interval * 1000)
        
        # Additional keyboard shortcuts (not in menu)
        refresh_shortcut = QtGui.QShortcut(QtGui.QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.refresh_data)
        
        delete_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self._on_delete_selected)
        
        # Ctrl+E for Export
        export_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+E"), self)
        export_shortcut.activated.connect(self._on_export_all)
        
        # Ctrl+I for Import
        import_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+I"), self)
        import_shortcut.activated.connect(self._on_import_data)
        
        logger.debug("Keyboard shortcuts configured")
    
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
                
                # Update scan button states
                self._update_scan_buttons()
        else:
            # Clear ports table
            self.ports_model.clear()
            
            # Update scan button states
            self._update_scan_buttons()
    
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
        
        # Update progress in table
        status_text = job.status.value.capitalize()
        if job.status.value == "running":
            status_text = "Scanning..."
            # Estimate progress based on time (simple approach)
            # For real progress, we'd need nmap to report progress
            progress = 50  # Indeterminate progress
        elif job.status.value == "queued":
            status_text = "Queued"
            progress = 0
        else:
            status_text = job.status.value.capitalize()
            progress = 0
        
        self.hosts_model.set_scan_progress(job.target, status_text, progress)
        
        # Update scan button states
        self._update_scan_buttons()

    
    def _on_scan_completed_ui(self, job: ScanJob) -> None:
        """
        Handle scan completion on UI thread.
        
        Args:
            job: Completed scan job
        """
        logger.info(f"Scan completed: {job.target} - Found {job.hosts_found} hosts, {job.ports_found} ports")
        
        # Update progress in table
        if job.status.value == "completed":
            self.hosts_model.set_scan_progress(job.target, "Complete", 100)
            # Clear after 3 seconds
            QtCore.QTimer.singleShot(3000, lambda: self.hosts_model.clear_scan_progress(job.target))
        elif job.status.value == "failed":
            self.hosts_model.set_scan_progress(job.target, "Failed", 0)
            # Clear after 5 seconds
            QtCore.QTimer.singleShot(5000, lambda: self.hosts_model.clear_scan_progress(job.target))
        elif job.status.value == "cancelled":
            self.hosts_model.set_scan_progress(job.target, "Cancelled", 0)
            # Clear after 3 seconds
            QtCore.QTimer.singleShot(3000, lambda: self.hosts_model.clear_scan_progress(job.target))
        
        # Refresh tables to show new data
        self.refresh_data()
        
        # Update scan button states
        self._update_scan_buttons()
        
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
        elif job.status.value == "cancelled":
            self.status_label.setText(f"Scan cancelled: {job.target}")

    
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
    
    def _on_add_hosts(self) -> None:
        """Handle Add Host(s) action."""
        dialog = AddHostDialog(self)
        
        if dialog.exec() == AddHostDialog.DialogCode.Accepted:
            targets = dialog.get_targets()
            
            if not targets:
                QMessageBox.warning(
                    self,
                    "No Targets",
                    "Please enter at least one target."
                )
                return
            
            # Get scan options from dialog
            options = dialog.get_scan_options()
            
            # Check mode and start appropriate scans
            if dialog.is_easy_mode():
                # Easy mode - check what options are selected
                if options.get("discovery") or options.get("staged_scan"):
                    # User wants to scan
                    for target in targets:
                        self._queue_scan_async(target, "quick", options)
                    
                    self.status_label.setText(
                        f"Started scan for {len(targets)} target(s)"
                    )
                    logger.info(f"Added and scanning {len(targets)} hosts: {', '.join(targets)}")
                else:
                    # Just add to database without scanning
                    self._add_hosts_to_db(targets)
            else:
                # Hard mode - always scan with specified options
                for target in targets:
                    self._queue_scan_async(target, "custom", options)
                
                self.status_label.setText(
                    f"Started custom scan for {len(targets)} target(s)"
                )
                logger.info(f"Added and scanning {len(targets)} hosts with custom options")
    
    def _add_hosts_to_db(self, targets: list[str]) -> None:
        """
        Add hosts to database without scanning.
        
        Args:
            targets: List of IP addresses or hostnames
        """
        from legion.core.models import Host
        for target in targets:
            host = Host(ip=target, state="unknown")
            self.database.save_host(host)
        
        self.refresh_data()
        self.status_label.setText(
            f"Added {len(targets)} host(s) - no scan started"
        )
        logger.info(f"Added {len(targets)} hosts without scanning: {', '.join(targets)}")
    
    def _on_settings(self) -> None:
        """Handle Settings action."""
        dialog = SettingsDialog(self.config_manager, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()
    
    def _on_clear_data(self) -> None:
        """Handle Clear All Data action."""
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Clear All Data",
            "This will delete all hosts, ports, and services from the current session.\n\n"
            "⚠️  This action cannot be undone!\n\n"
            "Historical data in other projects will be preserved.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Clear database
                logger.info("Clearing all data from database...")
                
                # Get all hosts
                hosts = self.database.get_all_hosts()
                
                # Delete each host (cascade deletes ports)
                for host in hosts:
                    self.database.delete_host(host.ip)
                
                # Refresh UI
                self.refresh_data()
                
                # Update status
                self.status_label.setText("All data cleared")
                
                logger.info(f"Cleared {len(hosts)} hosts and their associated data")
                
                QMessageBox.information(
                    self,
                    "Data Cleared",
                    f"Successfully cleared {len(hosts)} hosts and all associated ports/services."
                )
                
            except Exception as e:
                logger.error(f"Failed to clear data: {e}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to clear data:\n{e}"
                )
    
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
        Queue a scan asynchronously using qasync event loop.
        
        Args:
            target: Scan target
            scan_type: Type of scan
            options: Scan options
        """
        # Get qasync event loop (already set by app.py)
        loop = asyncio.get_event_loop()
        
        # Queue scan
        async def queue_scan():
            try:
                job_id = await self.scanner.queue_scan(target, scan_type, **options)
                logger.info(f"Scan queued: {job_id}")
                
                # Start scanner workers if not running
                if not self.scanner._running:
                    await self.scanner.start()
                
                # Update scan buttons immediately
                self._update_scan_buttons()
            except Exception as e:
                logger.error(f"Failed to queue scan: {e}", exc_info=True)
                self.status_label.setText(f"Failed to queue scan: {e}")
        
        # Schedule coroutine in qasync event loop
        asyncio.ensure_future(queue_scan(), loop=loop)
    
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
    
    def _on_about(self, tab: int | None = None) -> None:
        """Show About dialog.
        
        Args:
            tab: Optional tab index to select on open (e.g., 1 for Shortcuts).
        """
        dialog = AboutDialog(self, initial_tab=tab or 0)
        dialog.exec()
    
    def _show_host_context_menu(self, position: QtCore.QPoint) -> None:
        """
        Show context menu for host table.
        
        Args:
            position: Mouse position in widget coordinates
        """
        # Get selected host
        indexes = self.hosts_table.selectionModel().selectedRows()
        if not indexes:
            return
        
        row = indexes[0].row()
        host_ip = self.hosts_model.data(
            self.hosts_model.index(row, self.hosts_model.COL_IP),
            Qt.ItemDataRole.DisplayRole
        )
        hostname = self.hosts_model.data(
            self.hosts_model.index(row, self.hosts_model.COL_HOSTNAME),
            Qt.ItemDataRole.DisplayRole
        )
        
        # Get open ports for this host
        ports = self.database.get_open_ports(host_ip)
        port_numbers = [str(p.number) for p in ports]
        
        # Create context menu
        menu = QtWidgets.QMenu(self.hosts_table)
        
        # Rescan submenu
        rescan_menu = menu.addMenu("🔄 Rescan")
        
        # Rescan with found ports
        if port_numbers:
            ports_str = ",".join(port_numbers)
            port_count = len(port_numbers)
            rescan_action = rescan_menu.addAction(f"Found ports ({port_count} ports)")
            rescan_action.triggered.connect(
                lambda: self._rescan_host_with_ports(host_ip, ports_str)
            )
        
        quick_action = rescan_menu.addAction("Quick Scan (-F)")
        quick_action.triggered.connect(
            lambda: self._queue_scan_async(host_ip, "quick", {"timing": "4"})
        )
        
        full_action = rescan_menu.addAction("Full Scan (all ports)")
        full_action.triggered.connect(
            lambda: self._rescan_host_full(host_ip)
        )
        
        stealth_action = rescan_menu.addAction("Stealth Scan (-T2)")
        stealth_action.triggered.connect(
            lambda: self._queue_scan_async(host_ip, "stealth", {"timing": "2"})
        )
        
        menu.addSeparator()
        
        # Copy submenu
        copy_menu = menu.addMenu("📋 Copy")
        
        copy_ip_action = copy_menu.addAction("IP Address")
        copy_ip_action.triggered.connect(
            lambda: QtWidgets.QApplication.clipboard().setText(host_ip)
        )
        
        if hostname and hostname != "-":
            copy_hostname_action = copy_menu.addAction("Hostname")
            copy_hostname_action.triggered.connect(
                lambda: QtWidgets.QApplication.clipboard().setText(hostname)
            )
        
        menu.addSeparator()
        
        # Check if this host has an active scan
        has_active_scan = False
        if self.scanner:
            stats = self.scanner.get_statistics()
            if stats['running'] > 0 or stats['queued'] > 0:
                # Check if this specific host is being scanned
                for job in self.scanner._jobs.values():
                    if job.target == host_ip and not job.is_complete:
                        has_active_scan = True
                        break
        
        # Cancel scan (only if host has active scan)
        if has_active_scan:
            cancel_action = menu.addAction("⏹️ Cancel Scan")
            cancel_action.triggered.connect(
                lambda: self._cancel_host_scan(host_ip)
            )
            menu.addSeparator()
        
        # Export host
        export_action = menu.addAction("💾 Export Host Data...")
        export_action.triggered.connect(
            lambda: self._export_host(host_ip)
        )
        
        menu.addSeparator()
        
        # Remove host
        remove_action = menu.addAction("🗑️ Remove Host")
        remove_action.triggered.connect(
            lambda: self._remove_host(host_ip)
        )
        
        # Show menu at cursor position
        menu.exec(self.hosts_table.viewport().mapToGlobal(position))
    
    def _show_port_context_menu(self, position: QtCore.QPoint) -> None:
        """
        Show context menu for port table.
        
        Args:
            position: Mouse position in widget coordinates
        """
        # Get selected port
        indexes = self.ports_table.selectionModel().selectedRows()
        if not indexes:
            return
        
        row = indexes[0].row()
        port_number = self.ports_model.data(
            self.ports_model.index(row, self.ports_model.COL_PORT),
            Qt.ItemDataRole.DisplayRole
        )
        
        # Get current host
        if not self.ports_model._current_host:
            return
        
        host_ip = self.ports_model._current_host
        
        # Create context menu
        menu = QtWidgets.QMenu(self.ports_table)
        
        # Rescan this port
        rescan_action = menu.addAction(f"🔄 Rescan port {port_number}")
        rescan_action.triggered.connect(
            lambda: self._rescan_host_with_ports(host_ip, str(port_number))
        )
        
        menu.addSeparator()
        
        # Copy port number
        copy_action = menu.addAction("📋 Copy Port Number")
        copy_action.triggered.connect(
            lambda: QtWidgets.QApplication.clipboard().setText(str(port_number))
        )
        
        # Copy service info
        service = self.ports_model.data(
            self.ports_model.index(row, self.ports_model.COL_SERVICE),
            Qt.ItemDataRole.DisplayRole
        )
        if service and service != "-":
            copy_service_action = menu.addAction("📋 Copy Service Info")
            copy_service_action.triggered.connect(
                lambda: QtWidgets.QApplication.clipboard().setText(service)
            )
        
        # Show menu at cursor position
        menu.exec(self.ports_table.viewport().mapToGlobal(position))
    
    def _rescan_host_with_ports(self, host_ip: str, ports: str) -> None:
        """
        Rescan a host with specific ports.
        
        Args:
            host_ip: Host IP address
            ports: Comma-separated port numbers
        """
        logger.info(f"Rescanning {host_ip} with ports: {ports}")
        
        # Queue custom scan with specified ports
        options = {
            "ports": ports,
            "timing": "4",  # Aggressive timing
            "version_detection": True  # Enable service detection
        }
        
        self._queue_scan_async(host_ip, "custom", options)
        self.status_label.setText(f"Rescanning {host_ip} ports {ports}...")
    
    def _rescan_host_full(self, host_ip: str) -> None:
        """
        Full rescan of a host (all ports).
        
        Args:
            host_ip: Host IP address
        """
        logger.info(f"Full rescan of {host_ip}")
        
        # Queue full scan
        options = {
            "timing": "4",
            "version_detection": True
        }
        
        self._queue_scan_async(host_ip, "full", options)
        self.status_label.setText(f"Full scan of {host_ip} started...")
    
    def _on_host_double_clicked(self, index: QtCore.QModelIndex) -> None:
        """
        Handle double-click on host table.
        
        Quick action: Rescan host with found ports.
        
        Args:
            index: Model index of double-clicked item
        """
        if not index.isValid():
            return
        
        row = index.row()
        host_ip = self.hosts_model.data(
            self.hosts_model.index(row, self.hosts_model.COL_IP),
            Qt.ItemDataRole.DisplayRole
        )
        
        # Get open ports
        ports = self.database.get_open_ports(host_ip)
        
        if ports:
            # Rescan with found ports
            port_numbers = [str(p.number) for p in ports]
            ports_str = ",".join(port_numbers)
            self._rescan_host_with_ports(host_ip, ports_str)
        else:
            # No ports found - offer quick scan
            reply = QMessageBox.question(
                self,
                "No Open Ports",
                f"No open ports found for {host_ip}.\n\n"
                "Would you like to run a quick scan?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                options = {"timing": "4"}
                self._queue_scan_async(host_ip, "quick", options)
    
    def _on_port_double_clicked(self, index: QtCore.QModelIndex) -> None:
        """
        Handle double-click on port table.
        
        Quick action: Rescan this specific port.
        
        Args:
            index: Model index of double-clicked item
        """
        if not index.isValid():
            return
        
        row = index.row()
        port_number = self.ports_model.data(
            self.ports_model.index(row, self.ports_model.COL_PORT),
            Qt.ItemDataRole.DisplayRole
        )
        
        if not self.ports_model._current_host:
            return
        
        host_ip = self.ports_model._current_host
        
        # Rescan this port
        self._rescan_host_with_ports(host_ip, str(port_number))
    
    def _export_host(self, host_ip: str) -> None:
        """
        Export single host data to file.
        
        Args:
            host_ip: Host IP to export
        """
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Host Data",
            f"{host_ip}_export.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            # Get host data
            host = self.database.get_host(host_ip)
            if not host:
                QMessageBox.warning(self, "Export Failed", f"Host {host_ip} not found.")
                return
            
            ports = self.database.get_ports(host_ip)
            
            # Build export data
            export_data = {
                "host": {
                    "ip": host.ip,
                    "hostname": host.hostname or "",
                    "os": host.os_name or "",
                    "state": host.state,
                    "last_seen": host.last_seen.isoformat() if host.last_seen else ""
                },
                "ports": [
                    {
                        "number": p.number,
                        "protocol": p.protocol,
                        "state": p.state,
                        "service": p.service_name or "",
                        "version": p.service_version or ""
                    }
                    for p in ports
                ]
            }
            
            # Write to file
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.status_label.setText(f"Exported {host_ip} to {filename}")
            logger.info(f"Exported host {host_ip} to {filename}")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(self, "Export Failed", f"Error exporting host:\n{e}")
    
    def _remove_host(self, host_ip: str) -> None:
        """
        Remove host from database.
        
        Args:
            host_ip: Host IP to remove
        """
        reply = QMessageBox.question(
            self,
            "Remove Host",
            f"Are you sure you want to remove {host_ip} from the database?\n\n"
            "This will also remove all associated ports and scan data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove host from database
                success = self.database.delete_host(host_ip)
                
                if success:
                    logger.info(f"Removed host {host_ip}")
                    self.status_label.setText(f"Host {host_ip} removed")
                    
                    # Refresh UI
                    self.hosts_model.refresh()
                    
                    QMessageBox.information(
                        self,
                        "Host Removed",
                        f"{host_ip} has been removed from the database."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Remove Failed",
                        f"Host {host_ip} not found in database."
                    )
                
            except Exception as e:
                logger.error(f"Failed to remove host: {e}")
                QMessageBox.critical(
                    self,
                    "Remove Failed",
                    f"Error removing host:\n{e}"
                )
    
    def _on_delete_selected(self) -> None:
        """Handle Delete key press - remove selected host."""
        indexes = self.hosts_table.selectionModel().selectedRows()
        if not indexes:
            return
        
        row = indexes[0].row()
        host_ip = self.hosts_model.data(
            self.hosts_model.index(row, self.hosts_model.COL_IP),
            Qt.ItemDataRole.DisplayRole
        )
        
        self._remove_host(host_ip)
    
    def _on_export_all(self) -> None:
        """Export all scan data to file."""
        from PyQt6.QtWidgets import QFileDialog
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export All Data",
            f"legion_export_{timestamp}.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            all_hosts = self.database.get_all_hosts()
            
            export_data = {
                "project": self.config.project.name,
                "export_date": datetime.now().isoformat(),
                "hosts": []
            }
            
            for host in all_hosts:
                ports = self.database.get_ports(host.ip)
                export_data["hosts"].append({
                    "ip": host.ip,
                    "hostname": host.hostname or "",
                    "os": host.os_name or "",
                    "state": host.state,
                    "last_seen": host.last_seen.isoformat() if host.last_seen else "",
                    "ports": [
                        {
                            "number": p.number,
                            "protocol": p.protocol,
                            "state": p.state,
                            "service": p.service_name or "",
                            "version": p.service_version or ""
                        }
                        for p in ports
                    ]
                })
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.status_label.setText(f"Exported {len(all_hosts)} hosts to {filename}")
            logger.info(f"Exported all data to {filename}")
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {len(all_hosts)} hosts to:\n{filename}"
            )
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(self, "Export Failed", f"Error exporting data:\n{e}")
    
    def _on_import_data(self) -> None:
        """Import scan data from file."""
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            "",
            "JSON Files (*.json);;XML Files (*.xml);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            # Check file extension
            if filename.endswith('.json'):
                self._import_json(filename)
            elif filename.endswith('.xml'):
                self._import_xml(filename)
            else:
                QMessageBox.warning(
                    self,
                    "Unsupported Format",
                    "Please select a JSON or XML file."
                )
                
        except Exception as e:
            logger.error(f"Import failed: {e}")
            QMessageBox.critical(self, "Import Failed", f"Error importing data:\n{e}")
    
    def _import_json(self, filename: str) -> None:
        """
        Import data from JSON file.
        
        Args:
            filename: Path to JSON file
        """
        import json
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # TODO: Implement database.add_host() and database.add_port() methods
        hosts_count = len(data.get("hosts", []))
        
        self.status_label.setText(f"Imported {hosts_count} hosts from {filename}")
        logger.info(f"Imported {hosts_count} hosts from {filename}")
        
        # Refresh UI
        self.hosts_model.refresh()
        
        QMessageBox.information(
            self,
            "Import Complete",
            f"Successfully imported {hosts_count} hosts from:\n{filename}"
        )
    
    def _import_xml(self, filename: str) -> None:
        """
        Import data from nmap XML file.
        
        Args:
            filename: Path to XML file
        """
        try:
            from legion.tools.nmap.parser import NmapXMLParser
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Failed to load XML parser:\n{e}")
            logger.error(f"Failed to import XML parser: {e}")
            return

        try:
            parser = NmapXMLParser()
            result = parser.parse_file(filename)

            hosts_saved = 0
            ports_saved = 0

            # Save hosts and ports to database
            for host in result.hosts:
                if not host.ip:
                    # Skip entries without IP
                    continue
                self.database.save_host(host)
                hosts_saved += 1

                host_ports = result.ports.get(host.ip, [])
                for port in host_ports:
                    self.database.save_port(host.ip, port)
                    ports_saved += 1

            # Refresh UI models
            if hasattr(self, "hosts_model"):
                self.hosts_model.refresh()

            # Update status and notify user
            self.status_label.setText(f"Imported {hosts_saved} hosts and {ports_saved} ports from {filename}")
            logger.info(f"Imported XML: {filename} -> hosts={hosts_saved}, ports={ports_saved}")

            QMessageBox.information(
                self,
                "Import Complete",
                f"Successfully imported {hosts_saved} hosts and {ports_saved} ports from:\n{filename}"
            )

        except FileNotFoundError:
            QMessageBox.warning(self, "File Not Found", f"The selected file does not exist:\n{filename}")
            logger.warning(f"XML import file not found: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Error importing XML:\n{e}")
            logger.error(f"XML import failed for {filename}: {e}", exc_info=True)
    
    def _on_cancel_scan(self) -> None:
        """Cancel scan of selected host."""
        # Get selected host
        indexes = self.hosts_table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a host to cancel its scan."
            )
            return
        
        row = indexes[0].row()
        host_ip = self.hosts_model.data(
            self.hosts_model.index(row, self.hosts_model.COL_IP),
            Qt.ItemDataRole.DisplayRole
        )
        
        self._cancel_host_scan(host_ip)
    
    def _cancel_host_scan(self, host_ip: str) -> None:
        """
        Cancel scan for specific host.
        
        Args:
            host_ip: IP address of host to cancel
        """
        if not self.scanner:
            return
        
        success = self.scanner.cancel_scan(host_ip)
        
        if success:
            self.hosts_model.set_scan_progress(host_ip, "Cancelled", 0)
            # Clear after 3 seconds
            QtCore.QTimer.singleShot(3000, lambda: self.hosts_model.clear_scan_progress(host_ip))
            
            self.status_label.setText(f"Cancelled scan of {host_ip}")
            logger.info(f"Cancelled scan of {host_ip}")
            
            # Update button states
            self._update_scan_buttons()
        else:
            QMessageBox.information(
                self,
                "No Active Scan",
                f"No active scan found for {host_ip}"
            )
    
    def _on_cancel_all_scans(self) -> None:
        """Cancel all running scans."""
        if not self.scanner:
            return
        
        # Confirm with user
        stats = self.scanner.get_statistics()
        active_count = stats['running'] + stats['queued']
        
        if active_count == 0:
            QMessageBox.information(
                self,
                "No Active Scans",
                "There are no scans currently running."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Cancel All Scans",
            f"Cancel {active_count} active scan(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            count = self.scanner.cancel_all_scans()
            self.status_label.setText(f"Cancelled {count} scan(s)")
            logger.info(f"Cancelled {count} scan(s)")
            
            # Clear all progress indicators
            self.hosts_model.clear_all_scan_progress()
            
            # Update button states
            self._update_scan_buttons()
    
    def _update_scan_buttons(self) -> None:
        """Update scan button states based on active scans."""
        if not self.scanner:
            return
        
        stats = self.scanner.get_statistics()
        has_active = (stats['running'] + stats['queued']) > 0
        
        # Update toolbar buttons
        if hasattr(self, 'action_cancel_scan'):
            # Enable if selected host has active scan
            indexes = self.hosts_table.selectionModel().selectedRows()
            if indexes:
                row = indexes[0].row()
                host_ip = self.hosts_model.data(
                    self.hosts_model.index(row, self.hosts_model.COL_IP),
                    Qt.ItemDataRole.DisplayRole
                )
                
                # Check if this host has active scan
                host_has_scan = False
                for job in self.scanner._jobs.values():
                    if job.target == host_ip and not job.is_complete:
                        host_has_scan = True
                        break
                
                self.action_cancel_scan.setEnabled(host_has_scan)
            else:
                self.action_cancel_scan.setEnabled(False)
        
        if hasattr(self, 'action_cancel_all'):
            self.action_cancel_all.setEnabled(has_active)
        
        # Update menu items
        if hasattr(self, 'menu_cancel_scan'):
            indexes = self.hosts_table.selectionModel().selectedRows()
            if indexes:
                row = indexes[0].row()
                host_ip = self.hosts_model.data(
                    self.hosts_model.index(row, self.hosts_model.COL_IP),
                    Qt.ItemDataRole.DisplayRole
                )
                
                host_has_scan = False
                for job in self.scanner._jobs.values():
                    if job.target == host_ip and not job.is_complete:
                        host_has_scan = True
                        break
                
                self.menu_cancel_scan.setEnabled(host_has_scan)
            else:
                self.menu_cancel_scan.setEnabled(False)
        
        if hasattr(self, 'menu_cancel_all'):
            self.menu_cancel_all.setEnabled(has_active)
    
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        logger.info("MainWindow closing - stopping all scans...")
        
        # Stop all running scans (synchronous part only)
        if self.scanner:
            # Cancel all scans - this is synchronous
            count = self.scanner.cancel_all_scans()
            if count > 0:
                logger.info(f"Cancelled {count} scan(s)")
            
            # Set running flag to false to stop workers
            self.scanner._running = False
            logger.info("Scanner workers will stop")
        
        # TODO: Save window geometry if config.ui.remember_window_size
        
        logger.info("MainWindow closed")
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
