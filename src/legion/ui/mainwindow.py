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
from datetime import datetime
import logging
import asyncio

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QTableView

from legion.config import get_config, ConfigManager
from legion.core.database import SimpleDatabase
from legion.core.scanner import ScanManager, ScanJob
from legion.core.models import Credential
from legion.ui.models import HostsTableModel, PortsTableModel
from legion.ui.dialogs import NewScanDialog, ScanProgressDialog, AboutDialog, AddHostDialog
from legion.ui.settings import SettingsDialog
from legion.ui.brute_widget import BruteWidget
from legion.ui.hydra_services_widget import HydraServicesWidget
from legion.ui.hydra_history_widget import HydraHistoryWidget, AttackRecord
from legion.ui.results_widget import ResultsWidget, CredentialResult
from legion.tools.hydra import HydraTool
from legion.utils.wordlists import get_service_wordlists, export_credentials_to_wordlist
from legion.utils.wordlist_processor import WordlistProcessor

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
        # Main tab widget (like legacy: Hosts, Hydra, Results, Services, etc.)
        self.main_tabs = QtWidgets.QTabWidget()
        self.main_layout.addWidget(self.main_tabs)
        
        # Tab 1: Hosts view
        self._setup_hosts_tab()
        
        # Tab 2: Hydra tab (renamed from Brute, with 3 sub-tabs)
        self._setup_hydra_tab()
        
        # Tab 3: Results tab (successful credentials)
        self._setup_results_tab()
        
        logger.debug("Main content setup complete")
    
    def _setup_hosts_tab(self) -> None:
        """Setup main Hosts tab with splitter view."""
        hosts_tab = QtWidgets.QWidget()
        hosts_layout = QtWidgets.QVBoxLayout(hosts_tab)
        hosts_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter (horizontal)
        self.main_splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        hosts_layout.addWidget(self.main_splitter)
        
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
        
        # Add Hosts tab to main tabs
        self.main_tabs.addTab(hosts_tab, "Hosts")
        
        logger.debug("Hosts tab setup complete")
    
    def _setup_hydra_tab(self) -> None:
        """Setup Hydra tab with 3 sub-tabs: Services, Running, History."""
        # Create Hydra tab with sub-tabs
        self.hydra_tab_widget = QtWidgets.QTabWidget()
        
        # Sub-tab 1: Services (Nmap import)
        self.hydra_services_widget = HydraServicesWidget()
        self.hydra_services_widget.attack_requested.connect(self._on_services_attack_requested)
        # Connect Import and Refresh buttons
        self.hydra_services_widget.import_btn.clicked.disconnect()  # Disconnect placeholder
        self.hydra_services_widget.import_btn.clicked.connect(self._on_import_from_nmap)
        self.hydra_services_widget.refresh_btn.clicked.disconnect()  # Disconnect placeholder
        self.hydra_services_widget.refresh_btn.clicked.connect(self._on_refresh_hydra_services)
        self.hydra_tab_widget.addTab(self.hydra_services_widget, "Services")
        
        # Sub-tab 2: Running (Active attacks)
        self.hydra_running_widget = QtWidgets.QTabWidget()
        self.hydra_running_widget.setTabsClosable(True)
        self.hydra_running_widget.tabCloseRequested.connect(self._on_running_tab_close_requested)
        
        # Add placeholder
        placeholder = QtWidgets.QLabel(
            "No attacks running.\n\n"
            "Select services from the Services tab or right-click on a port in the Hosts tab."
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: gray; font-size: 14px;")
        self.hydra_running_widget.addTab(placeholder, "Getting Started")
        
        self.hydra_tab_widget.addTab(self.hydra_running_widget, "Running")
        
        # Sub-tab 3: History (Completed attacks)
        self.hydra_history_widget = HydraHistoryWidget()
        self.hydra_history_widget.rerun_requested.connect(self._on_history_rerun_requested)
        self.hydra_tab_widget.addTab(self.hydra_history_widget, "History")
        
        # Add Hydra tab to main tabs
        self.main_tabs.addTab(self.hydra_tab_widget, "Hydra")
        
        logger.debug("Hydra tab setup complete")
    
    def _setup_results_tab(self) -> None:
        """Setup Results tab for successful credentials."""
        self.results_widget = ResultsWidget()
        self.main_tabs.addTab(self.results_widget, "Results")
        
        logger.debug("Results tab setup complete")
    
    def _setup_brute_tab(self) -> None:
        """
        DEPRECATED: Old brute tab setup.
        Kept for backward compatibility, but replaced by _setup_hydra_tab().
        """
        logger.warning("_setup_brute_tab() is deprecated, use _setup_hydra_tab()")
        self._setup_hydra_tab()
    
    def _on_running_tab_close_requested(self, index: int) -> None:
        """
        Handle running attack tab close request.
        
        Args:
            index: Tab index to close
        """
        widget = self.hydra_running_widget.widget(index)
        
        # If it's a BruteWidget and attack is running, confirm
        if isinstance(widget, BruteWidget) and widget.is_running:
            reply = QMessageBox.question(
                self,
                "Stop Attack",
                "Attack is still running. Stop and close tab?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
            
            # Stop the attack first
            self._stop_hydra_attack(widget)
        
        # Remove tab
        self.hydra_running_widget.removeTab(index)
        
        # If no more attack tabs, add placeholder back
        if self.hydra_running_widget.count() == 0:
            placeholder = QtWidgets.QLabel(
                "No attacks running.\n\n"
                "Select services from the Services tab or right-click on a port in the Hosts tab."
            )
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: gray; font-size: 14px;")
            self.hydra_running_widget.addTab(placeholder, "Getting Started")
        
        logger.info(f"Closed running attack tab {index}")
    
    def _on_brute_tab_close_requested(self, index: int) -> None:
        """
        DEPRECATED: Old brute tab close handler.
        Redirects to new running tab handler.
        """
        logger.warning("_on_brute_tab_close_requested() is deprecated, use _on_running_tab_close_requested()")
        self._on_running_tab_close_requested(index)
    
    def _start_hydra_attack(
        self,
        brute_widget: BruteWidget,
        wordlist_path: str,
        tasks: int,
        timeout: int
    ) -> None:
        """
        Start Hydra attack with live output streaming.
        
        Args:
            brute_widget: BruteWidget to update
            wordlist_path: Path to wordlist directory
            tasks: Number of parallel tasks
            timeout: Attack timeout
        """
        async def run_attack_with_streaming():
            try:
                # Get attack options from widget properties
                single_user = brute_widget.property("single_user")
                single_pass = brute_widget.property("single_pass")
                blank_pass = brute_widget.property("blank_pass")
                login_as_pass = brute_widget.property("login_as_pass")
                loop_users = brute_widget.property("loop_users")
                exit_first = brute_widget.property("exit_first")
                verbose = brute_widget.property("verbose")
                custom_args = brute_widget.property("additional_args")
                
                # Import strategy module
                from legion.utils.wordlist_strategy import WordlistStrategy, AttackMode
                import tempfile
                
                # Determine attack mode
                if single_user or single_pass:
                    # Single credential mode
                    brute_widget.append_output("🔑 Single credential mode")
                    if single_user:
                        brute_widget.append_output(f"   Username: {single_user}")
                    if single_pass:
                        brute_widget.append_output(f"   Password: {'*' * len(single_pass)}")
                    
                    username_file = None
                    password_file = None
                    combo_file = None
                    use_single_creds = True
                else:
                    # Wordlist mode
                    use_single_creds = False
                    
                    # Analyze wordlists
                    brute_widget.append_output("🔍 Analyzing wordlists...")
                    analysis = WordlistStrategy.analyze_directory(Path(wordlist_path))
                    
                    brute_widget.append_output(
                        f"📊 Mode: {analysis.mode.value.upper()}\n"
                        f"   Combo files: {len(analysis.combo_files)}\n"
                        f"   Estimated combinations: {analysis.estimated_combinations:,}"
                    )
                    
                    # Prepare files
                    temp_dir = Path(tempfile.gettempdir()) / "legion_wordlists"
                    
                    if analysis.mode == AttackMode.COMBO:
                        combo_file = WordlistStrategy.prepare_combo_file(
                            analysis.combo_files, temp_dir, max_entries=10000
                        )
                        brute_widget.append_output(f"✅ Prepared combo file: {combo_file.name}")
                        username_file = None
                        password_file = None
                    else:
                        merged_user, merged_pass = WordlistStrategy.prepare_separate_files(
                            analysis.username_files,
                            analysis.password_files,
                            temp_dir,
                            max_entries=1000
                        )
                        brute_widget.append_output(
                            f"✅ Prepared wordlists:\n"
                            f"   Users: {merged_user.name}\n"
                            f"   Passwords: {merged_pass.name}"
                        )
                        username_file = str(merged_user)
                        password_file = str(merged_pass)
                        combo_file = None
                
                # Initialize Hydra
                hydra = HydraTool()
                if not await hydra.validate():
                    brute_widget.append_output("❌ ERROR: Hydra not found!")
                    brute_widget.mark_finished(False)
                    return
                
                brute_widget.append_output(f"🔧 Hydra version: {await hydra.get_version()}")
                
                # Build additional args
                additional_args = []
                
                # HTTP services need path
                if brute_widget.service in ['http-get', 'http-post', 'https-get', 'https-post']:
                    additional_args.extend(["-m", "/"])
                
                # Credential helper flags (-e)
                cred_helper_flags = []
                if blank_pass:
                    cred_helper_flags.append("n")  # -e n: try empty password
                if login_as_pass:
                    cred_helper_flags.append("s")  # -e s: try login as password
                
                if cred_helper_flags:
                    additional_args.extend(["-e", "".join(cred_helper_flags)])
                    brute_widget.append_output(f"🔐 Credential helpers: -e {''.join(cred_helper_flags)}")
                
                # Attack modifier flags
                if loop_users:
                    additional_args.append("-u")  # Loop users first
                    brute_widget.append_output("🔄 Loop mode: Users first (-u)")
                if exit_first:
                    additional_args.append("-f")  # Exit on first valid
                    brute_widget.append_output("🎯 Exit on first valid (-f)")
                if verbose:
                    additional_args.append("-V")  # Verbose mode
                    brute_widget.append_output("📢 Verbose mode (-V)")
                
                # Custom arguments
                if custom_args:
                    # Parse custom args into list
                    import shlex
                    additional_args.extend(shlex.split(custom_args))
                    brute_widget.append_output(f"⚙️ Custom args: {custom_args}")
                
                # Start attack
                attack_mode = "Single Credential" if use_single_creds else ("Combo" if combo_file else "Wordlist")
                brute_widget.append_output(
                    f"\n🚀 Starting attack on {brute_widget.service}://"
                    f"{brute_widget.host_ip}:{brute_widget.port}\n"
                    f"   Mode: {attack_mode}\n"
                    f"   Tasks: {tasks}\n"
                    f"   Timeout: {timeout}s\n"
                )
                brute_widget.set_running(True)
                brute_widget.set_stats("Running...")
                
                # Store hydra instance for killing
                brute_widget.setProperty("hydra_tool", hydra)
                
                # Run attack
                import time
                start_time = time.time()
                
                try:
                    if use_single_creds:
                        # Single credential mode
                        result = await hydra.attack(
                            target=brute_widget.host_ip,
                            service=brute_widget.service,
                            login=single_user if single_user else None,
                            password=single_pass if single_pass else None,
                            port=brute_widget.port,
                            tasks=tasks,
                            timeout=float(timeout),
                            additional_args=additional_args if additional_args else None
                        )
                    elif combo_file:
                        # Combo file mode
                        result = await hydra.attack(
                            target=brute_widget.host_ip,
                            service=brute_widget.service,
                            combo_file=Path(combo_file),
                            port=brute_widget.port,
                            tasks=tasks,
                            timeout=float(timeout),
                            additional_args=additional_args if additional_args else None
                        )
                    else:
                        # Wordlist mode
                        result = await hydra.attack(
                            target=brute_widget.host_ip,
                            service=brute_widget.service,
                            login_file=Path(username_file),
                            password_file=Path(password_file),
                            port=brute_widget.port,
                            tasks=tasks,
                            timeout=float(timeout),
                            additional_args=additional_args if additional_args else None
                        )
                except asyncio.CancelledError:
                    brute_widget.append_output("\n⚠️ Attack cancelled by user")
                    brute_widget.mark_finished(False)
                    return
                
                elapsed = time.time() - start_time
                
                # Display output
                brute_widget.append_output("\n" + "="*60)
                brute_widget.append_output("HYDRA OUTPUT:")
                brute_widget.append_output("="*60 + "\n")
                brute_widget.append_output(result.stdout)
                if result.stderr:
                    brute_widget.append_output("\nERRORS:")
                    brute_widget.append_output(result.stderr)
                
                # Parse results
                hydra_result = await hydra.parse_output(result)
                
                # Display results
                brute_widget.append_output("\n" + "="*60)
                brute_widget.append_output(f"✅ Attack completed in {elapsed:.1f}s")
                brute_widget.append_output(f"   Attempts: {hydra_result.statistics.total_attempts}")
                brute_widget.append_output(f"   Credentials found: {len(hydra_result.credentials)}")
                
                if hydra_result.credentials:
                    # Use batch mode for many credentials (more efficient)
                    if len(hydra_result.credentials) > 10:
                        brute_widget.append_output(f"\n🔑 CREDENTIALS FOUND ({len(hydra_result.credentials)} total):")
                        brute_widget.append_output("   (Displaying first 10, see Results tab for all)")
                        
                        # Show only first 10 in output
                        for cred in hydra_result.credentials[:10]:
                            brute_widget.append_output(
                                f"   ✓ {cred.login}:{cred.password} on {cred.service}://{cred.host}:{cred.port}"
                            )
                        
                        # Add all to Results tab in batch (efficient)
                        cred_results = [
                            CredentialResult(
                                host=cred.host,
                                port=cred.port,
                                service=cred.service,
                                username=cred.login,
                                password=cred.password,
                                found_at=datetime.now()
                            )
                            for cred in hydra_result.credentials
                        ]
                        self.results_widget.add_credentials_bulk(cred_results)
                        logger.info(f"Found {len(hydra_result.credentials)} credentials (stored in Results tab)")
                        
                    else:
                        # Few credentials - show all and add individually
                        brute_widget.append_output("\n🔑 CREDENTIALS FOUND:")
                        for cred in hydra_result.credentials:
                            brute_widget.append_output(
                                f"   ✓ {cred.login}:{cred.password} on {cred.service}://{cred.host}:{cred.port}"
                            )
                            
                            # Emit signal
                            brute_widget.credentials_found.emit(cred.login, cred.password)
                            
                            # Add to Results tab (RAM only - no database save)
                            cred_result = CredentialResult(
                                host=cred.host,
                                port=cred.port,
                                service=cred.service,
                                username=cred.login,
                                password=cred.password,
                                found_at=datetime.now()
                            )
                            self.results_widget.add_credential(cred_result)
                            logger.info(f"Found credential: {cred.login}:{cred.password} (stored in Results tab)")
                    
                    # Blink tab
                    tab_index = brute_widget.property("tab_index")
                    if tab_index is not None:
                        self._blink_brute_tab(tab_index)
                
                # Add to History tab
                has_credentials = len(hydra_result.credentials) > 0
                attack_record = AttackRecord(
                    host=brute_widget.host_ip,
                    port=brute_widget.port,
                    service=brute_widget.service,
                    started=datetime.fromtimestamp(start_time),
                    duration=elapsed,
                    success=has_credentials,
                    credentials_found=len(hydra_result.credentials),
                    attempts=hydra_result.statistics.total_attempts,
                    command="",  # Could add full command here
                    output=result.stdout
                )
                self.hydra_history_widget.add_attack(attack_record)
                
                # Blink tab based on success
                tab_index = brute_widget.property("tab_index")
                if tab_index is not None:
                    if has_credentials:
                        # Already blinked green above
                        pass
                    else:
                        # Reset to default color (no credentials = not a failure, just no results)
                        self._reset_tab_color(tab_index)
                
                brute_widget.set_stats(f"Completed - {len(hydra_result.credentials)} credentials found")
                brute_widget.mark_finished(True)
                
            except Exception as e:
                logger.error(f"Hydra attack error: {e}", exc_info=True)
                brute_widget.append_output(f"\n❌ ERROR: {str(e)}")
                brute_widget.mark_finished(False)
                
                # Blink tab red on error
                tab_index = brute_widget.property("tab_index")
                if tab_index is not None:
                    self._blink_brute_tab(tab_index, success=False)
        
        # Run async
        asyncio.create_task(run_attack_with_streaming())
    
    def _stop_hydra_attack(self, brute_widget: BruteWidget) -> None:
        """
        Stop running Hydra attack.
        
        Args:
            brute_widget: BruteWidget to stop
        """
        hydra = brute_widget.property("hydra_tool")
        if hydra and isinstance(hydra, HydraTool):
            if hydra.kill_current_process():
                brute_widget.append_output("\n⚠️ Process killed")
                logger.info("Killed Hydra process")
        
        brute_widget.set_running(False)
        brute_widget.set_stats("Stopped by user")
    
    def _on_credentials_found(self, username: str, password: str) -> None:
        """
        Handle credentials found signal.
        
        Args:
            username: Found username
            password: Found password
        """
        logger.info(f"Credentials found: {username}:{password}")
        self.status_label.setText(f"🔑 Credentials found: {username}:***")
    
    def _blink_brute_tab(self, tab_index: int, success: bool = True) -> None:
        """
        Blink brute tab to indicate attack result.
        
        Args:
            tab_index: Tab index to blink
            success: True for green (credentials found), False for red (failed)
        """
        # Choose color based on success
        color = QtGui.QColor('green') if success else QtGui.QColor('red')
        
        # Change tab text color in Running sub-tab
        self.hydra_running_widget.tabBar().setTabTextColor(tab_index, color)
        
        # Also blink main Hydra tab and Running sub-tab
        hydra_tab_index = self.main_tabs.indexOf(self.hydra_tab_widget)
        self.main_tabs.tabBar().setTabTextColor(hydra_tab_index, color)
        
        running_tab_index = self.hydra_tab_widget.indexOf(self.hydra_running_widget)
        self.hydra_tab_widget.tabBar().setTabTextColor(running_tab_index, color)
        
        # Only blink Results tab on success
        if success:
            results_tab_index = self.main_tabs.indexOf(self.results_widget)
            self.main_tabs.tabBar().setTabTextColor(results_tab_index, color)
        
        status = "credentials found" if success else "attack failed"
        logger.info(f"Blinking tab {tab_index} - {status}")
    
    def _reset_tab_color(self, tab_index: int) -> None:
        """
        Reset tab color to default (no special status).
        
        Args:
            tab_index: Tab index to reset
        """
        # Reset to default color (usually black or system default)
        default_color = self.palette().text().color()
        
        # Reset Running sub-tab
        self.hydra_running_widget.tabBar().setTabTextColor(tab_index, default_color)
        
        logger.info(f"Reset tab {tab_index} color to default")
    
    def _edit_hydra_config(self, brute_widget: 'BruteWidget') -> None:
        """
        Re-open Hydra configuration dialog to edit a finished attack.
        
        Args:
            brute_widget: The BruteWidget to edit
        """
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QHBoxLayout, QCheckBox, QLineEdit, QPushButton, QSpinBox, QFormLayout, QDialogButtonBox, QMessageBox
        
        # Get saved configuration
        host_ip = brute_widget.host_ip
        port = brute_widget.port
        service = brute_widget.service
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Hydra Attack - {service}://{host_ip}:{port}")
        dialog.setMinimumWidth(600)
        
        layout = QVBoxLayout(dialog)
        
        # Target info (read-only)
        info_group = QGroupBox("Target Information")
        info_layout = QVBoxLayout()
        info_label = QtWidgets.QLabel(
            f"<b>Service:</b> {service}<br>"
            f"<b>Host:</b> {host_ip}<br>"
            f"<b>Port:</b> {port}"
        )
        info_layout.addWidget(info_label)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Wordlist directory
        wordlist_group = QGroupBox("Wordlist Directory")
        wordlist_layout = QVBoxLayout()
        
        dir_layout = QHBoxLayout()
        wordlist_edit = QLineEdit()
        wordlist_edit.setPlaceholderText("Path to wordlist directory...")
        wordlist_edit.setText(brute_widget.property("wordlist_path") or "")
        
        wordlist_browse = QPushButton("Browse...")
        wordlist_browse.clicked.connect(
            lambda: self._browse_wordlist_dir(wordlist_edit)
        )
        
        dir_layout.addWidget(wordlist_edit)
        dir_layout.addWidget(wordlist_browse)
        wordlist_layout.addLayout(dir_layout)
        
        wordlist_group.setLayout(wordlist_layout)
        layout.addWidget(wordlist_group)
        
        # Credential Options
        cred_options_group = QGroupBox("Credential Options")
        cred_options_layout = QVBoxLayout()
        
        single_cred_layout = QHBoxLayout()
        
        # Single username
        single_user_check = QCheckBox("Single Username:")
        single_user_edit = QLineEdit()
        single_user_edit.setPlaceholderText("e.g., admin")
        single_user_value = brute_widget.property("single_user") or ""
        if single_user_value:
            single_user_check.setChecked(True)
            single_user_edit.setText(single_user_value)
            single_user_edit.setEnabled(True)
        else:
            single_user_edit.setEnabled(False)
        single_user_check.toggled.connect(single_user_edit.setEnabled)
        
        single_cred_layout.addWidget(single_user_check)
        single_cred_layout.addWidget(single_user_edit)
        
        # Single password
        single_pass_check = QCheckBox("Single Password:")
        single_pass_edit = QLineEdit()
        single_pass_edit.setPlaceholderText("e.g., password123")
        single_pass_value = brute_widget.property("single_pass") or ""
        if single_pass_value:
            single_pass_check.setChecked(True)
            single_pass_edit.setText(single_pass_value)
            single_pass_edit.setEnabled(True)
        else:
            single_pass_edit.setEnabled(False)
        single_pass_check.toggled.connect(single_pass_edit.setEnabled)
        
        single_cred_layout.addWidget(single_pass_check)
        single_cred_layout.addWidget(single_pass_edit)
        
        cred_options_layout.addLayout(single_cred_layout)
        
        # Credential helpers
        helper_layout = QHBoxLayout()
        
        check_blank_pass = QCheckBox("Try blank passwords (-e n)")
        check_blank_pass.setChecked(brute_widget.property("blank_pass") or False)
        helper_layout.addWidget(check_blank_pass)
        
        check_login_as_pass = QCheckBox("Try login as password (-e s)")
        check_login_as_pass.setChecked(brute_widget.property("login_as_pass") or False)
        helper_layout.addWidget(check_login_as_pass)
        
        cred_options_layout.addLayout(helper_layout)
        
        cred_options_group.setLayout(cred_options_layout)
        layout.addWidget(cred_options_group)
        
        # Attack Modifiers
        modifiers_group = QGroupBox("Attack Modifiers")
        modifiers_layout = QHBoxLayout()
        
        check_loop_users = QCheckBox("Loop users first (-u)")
        check_loop_users.setChecked(brute_widget.property("loop_users") or False)
        modifiers_layout.addWidget(check_loop_users)
        
        check_exit_first = QCheckBox("Exit on first valid (-f)")
        check_exit_first.setChecked(brute_widget.property("exit_first") or False)
        modifiers_layout.addWidget(check_exit_first)
        
        check_verbose = QCheckBox("Verbose output (-V)")
        check_verbose.setChecked(brute_widget.property("verbose") or False)
        modifiers_layout.addWidget(check_verbose)
        
        modifiers_group.setLayout(modifiers_layout)
        layout.addWidget(modifiers_group)
        
        # Advanced Options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QVBoxLayout()
        
        additional_label = QtWidgets.QLabel("Additional Hydra arguments:")
        advanced_layout.addWidget(additional_label)
        
        additional_args_edit = QLineEdit()
        additional_args_edit.setPlaceholderText("e.g., -I -w 30")
        additional_args_edit.setText(brute_widget.property("additional_args") or "")
        advanced_layout.addWidget(additional_args_edit)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Performance Options
        options_group = QGroupBox("Performance Options")
        options_layout = QFormLayout()
        
        tasks_spin = QSpinBox()
        tasks_spin.setMinimum(1)
        tasks_spin.setMaximum(64)
        tasks_spin.setValue(brute_widget.property("tasks") or 16)
        options_layout.addRow("Parallel tasks (-t):", tasks_spin)
        
        timeout_spin = QSpinBox()
        timeout_spin.setMinimum(1)
        timeout_spin.setMaximum(600)
        timeout_spin.setValue(brute_widget.property("timeout") or 30)
        options_layout.addRow("Timeout (seconds) (-w):", timeout_spin)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Auto-start option
        autostart_group = QGroupBox("Execution")
        autostart_layout = QVBoxLayout()
        
        autostart_check = QCheckBox("Start attack immediately after updating")
        autostart_check.setChecked(brute_widget.property("auto_start") or True)
        autostart_layout.addWidget(autostart_check)
        
        autostart_group.setLayout(autostart_layout)
        layout.addWidget(autostart_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Update configuration
        wordlist_path = wordlist_edit.text().strip()
        single_user = single_user_edit.text().strip() if single_user_check.isChecked() else ""
        single_pass = single_pass_edit.text().strip() if single_pass_check.isChecked() else ""
        blank_pass = check_blank_pass.isChecked()
        login_as_pass = check_login_as_pass.isChecked()
        loop_users = check_loop_users.isChecked()
        exit_first = check_exit_first.isChecked()
        verbose = check_verbose.isChecked()
        additional_args = additional_args_edit.text().strip()
        tasks_value = tasks_spin.value()
        timeout_value = timeout_spin.value()
        auto_start = autostart_check.isChecked()
        
        # Validation
        if not wordlist_path and not (single_user or single_pass):
            QMessageBox.warning(
                self,
                "Missing Credentials",
                "Please select a wordlist directory OR enter single username/password."
            )
            return
        
        # Update widget properties
        brute_widget.setProperty("single_user", single_user)
        brute_widget.setProperty("single_pass", single_pass)
        brute_widget.setProperty("blank_pass", blank_pass)
        brute_widget.setProperty("login_as_pass", login_as_pass)
        brute_widget.setProperty("loop_users", loop_users)
        brute_widget.setProperty("exit_first", exit_first)
        brute_widget.setProperty("verbose", verbose)
        brute_widget.setProperty("additional_args", additional_args)
        brute_widget.setProperty("auto_start", auto_start)
        brute_widget.setProperty("tasks", tasks_value)
        brute_widget.setProperty("timeout", timeout_value)
        brute_widget.setProperty("wordlist_path", wordlist_path)
        brute_widget.wordlist_path = wordlist_path or "single-creds"
        
        # Reset widget state
        brute_widget.is_finished = False
        brute_widget.output_display.clear()
        brute_widget.set_stats("Ready to re-run with updated configuration")
        brute_widget.run_button.setText("Run")
        brute_widget.run_button.setStyleSheet("")
        brute_widget.stats_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        
        # Reset tab color
        tab_index = brute_widget.property("tab_index")
        if tab_index is not None:
            self._reset_tab_color(tab_index)
        
        self.status_label.setText(f"✏️ Configuration updated for {service}://{host_ip}:{port}")
        logger.info(f"Updated Hydra attack configuration: {service}://{host_ip}:{port}")
        
        # Auto-start if enabled
        if auto_start:
            self.status_label.setText(f"🚀 Re-starting attack: {service}://{host_ip}:{port}...")
            brute_widget.attack_started.emit()
    
    def _on_services_attack_requested(self, services: list) -> None:
        """
        Handle attack request from Services tab.
        
        Args:
            services: List of (host, port, service) tuples
        """
        logger.info(f"Attack requested for {len(services)} services")
        
        for host, port, service in services:
            # Launch attack for each service
            self._launch_hydra_attack_from_nmap(host, port, service)
    
    def _on_history_rerun_requested(self, host: str, port: int, service: str) -> None:
        """
        Handle re-run request from History tab.
        
        Args:
            host: Target host
            port: Target port
            service: Service name
        """
        logger.info(f"Re-running attack: {host}:{port} ({service})")
        self._launch_hydra_attack_from_nmap(host, port, service)
    
    def _on_import_from_nmap(self) -> None:
        """Import all open ports with supported services from current Nmap scan to Hydra Services tab."""
        logger.info("Importing services from Nmap")
        
        # Get all ports from all hosts
        imported_count = 0
        
        for row in range(self.hosts_model.rowCount()):
            host_ip = self.hosts_model.data(
                self.hosts_model.index(row, self.hosts_model.COL_IP),
                Qt.ItemDataRole.DisplayRole
            )
            
            # Get host's ports from database
            ports = self.database.get_ports(host_ip)
            if not ports:
                continue
            
            # Map services - erweiterte Liste
            hydra_services = {
                'ssh': 'ssh',
                'ftp': 'ftp', 
                'ftps': 'ftp',
                'telnet': 'telnet',
                'mysql': 'mysql',
                'postgres': 'postgres',
                'postgresql': 'postgres',
                'mssql': 'mssql',
                'ms-sql': 'mssql',
                'vnc': 'vnc',
                'http': 'http-get',
                'https': 'https-get',
                'http-proxy': 'http-get',
                'http-alt': 'http-get',
                'www': 'http-get',
                'smb': 'smb',
                'microsoft-ds': 'smb',
                'netbios': 'smb',
                'rdp': 'rdp',
                'ms-wbt-server': 'rdp',
                'pop3': 'pop3',
                'pop3s': 'pop3',
                'imap': 'imap',
                'imaps': 'imap',
                'smtp': 'smtp',
                'smtps': 'smtp',
                'ldap': 'ldap',
                'ldaps': 'ldap',
                'oracle': 'oracle-listener',
                'oracle-tns': 'oracle-listener'
            }
            
            for port in ports:
                # Only open ports
                if port.state != "open":
                    continue
                
                # Check if service is supported
                service_lower = port.service_name.lower() if port.service_name else ""
                hydra_service = None
                
                for svc_name, hydra_svc in hydra_services.items():
                    if svc_name in service_lower:
                        hydra_service = hydra_svc
                        break
                
                if hydra_service:
                    self.hydra_services_widget.add_service(
                        host_ip,
                        port.number,
                        hydra_service,
                        port.state
                    )
                    imported_count += 1
        
        logger.info(f"Imported {imported_count} services from Nmap")
        self.status_label.setText(f"📥 Imported {imported_count} services to Hydra tab")
        
        if imported_count == 0:
            QMessageBox.information(
                self,
                "Import from Nmap",
                "No supported services found.\n\n"
                "Run a scan first and make sure hosts have open ports with supported services "
                "(SSH, FTP, HTTP, MySQL, etc.)"
            )
    
    def _on_refresh_hydra_services(self) -> None:
        """Refresh Hydra Services tab by clearing and re-importing from Nmap."""
        logger.info("Refreshing Hydra Services")
        self.hydra_services_widget.clear_services()
        self._on_import_from_nmap()
    
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
        
        # Export credentials (if any)
        host_creds = self.database.get_credentials(host_ip)
        if host_creds:
            export_creds_action = menu.addAction(f"🔑 Export Credentials ({len(host_creds)})...")
            export_creds_action.triggered.connect(
                lambda: self._export_host_credentials(host_ip)
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
        
        # Get port state
        port_state = self.ports_model.data(
            self.ports_model.index(row, self.ports_model.COL_STATE),
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
        
        menu.addSeparator()
        
        # Brute Force submenu
        bruteforce_menu = menu.addMenu("🔑 Brute Force")
        
        # Check if port is open - only offer Hydra for open ports
        if port_state and port_state.lower() != "open":
            port_not_open = bruteforce_menu.addAction(f"Port not open ({port_state})")
            port_not_open.setEnabled(False)
        else:
            # Add Hydra attack for common services
            service_lower = service.lower() if service and service != "-" else ""
            
            # Map service names to Hydra service types
            hydra_services = {
                'ssh': 'ssh',
                'ftp': 'ftp',
                'telnet': 'telnet',
                'mysql': 'mysql',
                'postgres': 'postgres',
                'postgresql': 'postgres',
                'mssql': 'mssql',
                'vnc': 'vnc',
                'http': 'http-get',
                'https': 'https-get',
                'smb': 'smb',
                'rdp': 'rdp'
            }
            
            # Check if service is attackable
            hydra_service = None
            for svc_name, hydra_svc in hydra_services.items():
                if svc_name in service_lower:
                    hydra_service = hydra_svc
                    break
            
            if hydra_service:
                # Option 1: Launch attack immediately
                hydra_action = bruteforce_menu.addAction(f"Launch Hydra - {service}")
                hydra_action.triggered.connect(
                    lambda: self._launch_hydra_attack(host_ip, port_number, hydra_service)
                )
                
                bruteforce_menu.addSeparator()
                
                # Option 2: Send to Hydra Services tab
                send_to_hydra_action = bruteforce_menu.addAction("📤 Send to Hydra Tab")
                send_to_hydra_action.setToolTip("Add this service to Hydra Services tab for later attack")
                send_to_hydra_action.triggered.connect(
                    lambda: self._send_to_hydra_tab(host_ip, port_number, hydra_service, port_state)
                )
            else:
                no_support = bruteforce_menu.addAction("No supported service detected")
                no_support.setEnabled(False)
        
        # Show menu at cursor position
        menu.exec(self.ports_table.viewport().mapToGlobal(position))
    
    def _send_to_hydra_tab(self, host_ip: str, port: int, service: str, state: str) -> None:
        """
        Send a service to Hydra Services tab.
        
        Args:
            host_ip: Target host IP
            port: Port number
            service: Service name
            state: Port state (open, closed, filtered)
        """
        # Add service to Hydra Services widget
        self.hydra_services_widget.add_service(host_ip, port, service, state)
        
        # Switch to Hydra tab -> Services sub-tab
        hydra_tab_index = self.main_tabs.indexOf(self.hydra_tab_widget)
        self.main_tabs.setCurrentIndex(hydra_tab_index)
        
        services_tab_index = self.hydra_tab_widget.indexOf(self.hydra_services_widget)
        self.hydra_tab_widget.setCurrentIndex(services_tab_index)
        
        logger.info(f"Sent to Hydra Services tab: {host_ip}:{port} ({service})")
        self.status_label.setText(f"📤 Added {host_ip}:{port} to Hydra Services tab")
    
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
        from legion.core.models import Host, Port
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        hosts_imported = 0
        ports_imported = 0
        
        # Handle both single host export and full project export
        hosts_data = data.get("hosts", [])
        
        # If no "hosts" key, check if this is a single host export
        if not hosts_data and "host" in data:
            hosts_data = [data["host"]]
            # Merge ports if they're at root level
            if "ports" in data:
                hosts_data[0]["ports"] = data["ports"]
        
        for host_data in hosts_data:
            try:
                # Create Host object
                host = Host(
                    ip=host_data["ip"],
                    hostname=host_data.get("hostname", ""),
                    os_name=host_data.get("os", ""),
                    state=host_data.get("state", "unknown"),
                    last_seen=datetime.fromisoformat(host_data["last_seen"]) if host_data.get("last_seen") else datetime.now()
                )
                
                # Save host to database
                self.database.save_host(host)
                hosts_imported += 1
                
                # Import ports
                for port_data in host_data.get("ports", []):
                    port = Port(
                        number=port_data["number"],
                        protocol=port_data.get("protocol", "tcp"),
                        state=port_data.get("state", "unknown"),
                        service_name=port_data.get("service", ""),
                        service_version=port_data.get("version", ""),
                        last_seen=datetime.now()
                    )
                    
                    self.database.save_port(host.ip, port)
                    ports_imported += 1
                    
            except Exception as e:
                logger.error(f"Failed to import host {host_data.get('ip', 'unknown')}: {e}")
                continue
        
        self.status_label.setText(f"Imported {hosts_imported} hosts, {ports_imported} ports from {filename}")
        logger.info(f"Imported {hosts_imported} hosts, {ports_imported} ports from {filename}")
        
        # Refresh UI
        self.hosts_model.refresh()
        
        QMessageBox.information(
            self,
            "Import Complete",
            f"Successfully imported:\n{hosts_imported} hosts\n{ports_imported} ports\n\nFrom: {filename}"
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
    
    def _launch_hydra_attack(self, host_ip: str, port: int, service: str) -> None:
        """
        Launch Hydra brute force attack against a service.
        
        Creates a new tab in the Brute tab widget with live output.
        
        Args:
            host_ip: Target host IP
            port: Target port number
            service: Service type (ssh, ftp, etc.)
        """
        # Create dialog to configure attack
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Hydra Brute Force - {service}://{host_ip}:{port}")
        dialog.setMinimumWidth(500)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Info label
        info_label = QtWidgets.QLabel(
            f"Configure brute force attack against:\n"
            f"🎯 Target: {host_ip}:{port}\n"
            f"🔧 Service: {service}"
        )
        info_label.setStyleSheet("padding: 10px; background-color: #2b2b2b; color: white; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # Wordlists group
        wordlist_group = QtWidgets.QGroupBox("Wordlists")
        wordlist_layout = QtWidgets.QVBoxLayout()
        
        # Info label
        info_text = QtWidgets.QLabel(
            "📂 Select a directory containing wordlist files.\n"
            "All .txt files will be automatically processed:\n"
            "  • Single format (usernames or passwords)\n"
            "  • Combo format (username:password) - auto-detected\n"
            "  • Mixed formats - all combined"
        )
        info_text.setStyleSheet("color: #888; font-size: 10px; padding: 5px;")
        wordlist_layout.addWidget(info_text)
        
        # Wordlist directory selector
        dir_layout = QtWidgets.QHBoxLayout()
        wordlist_edit = QtWidgets.QLineEdit()
        wordlist_edit.setPlaceholderText("Path to wordlist directory...")
        
        wordlist_browse = QtWidgets.QPushButton("📁 Browse...")
        wordlist_browse.clicked.connect(
            lambda: self._browse_wordlist_directory(wordlist_edit)
        )
        
        dir_layout.addWidget(wordlist_edit)
        dir_layout.addWidget(wordlist_browse)
        wordlist_layout.addLayout(dir_layout)
        
        # Set default
        default_dir = Path("scripts/wordlists")
        if default_dir.exists():
            wordlist_edit.setText(str(default_dir))
        
        wordlist_group.setLayout(wordlist_layout)
        layout.addWidget(wordlist_group)
        
        # Credential Options group (like Legacy)
        cred_options_group = QtWidgets.QGroupBox("Credential Options")
        cred_options_layout = QtWidgets.QVBoxLayout()
        
        # Single credential testing
        single_cred_layout = QtWidgets.QHBoxLayout()
        
        # Single username
        single_user_check = QtWidgets.QCheckBox("Single Username:")
        single_user_edit = QtWidgets.QLineEdit()
        single_user_edit.setPlaceholderText("e.g., admin")
        single_user_edit.setEnabled(False)
        single_user_check.toggled.connect(single_user_edit.setEnabled)
        
        single_cred_layout.addWidget(single_user_check)
        single_cred_layout.addWidget(single_user_edit)
        
        # Single password
        single_pass_check = QtWidgets.QCheckBox("Single Password:")
        single_pass_edit = QtWidgets.QLineEdit()
        single_pass_edit.setPlaceholderText("e.g., password123")
        single_pass_edit.setEnabled(False)
        single_pass_check.toggled.connect(single_pass_edit.setEnabled)
        
        single_cred_layout.addWidget(single_pass_check)
        single_cred_layout.addWidget(single_pass_edit)
        
        cred_options_layout.addLayout(single_cred_layout)
        
        # Credential helpers
        helper_layout = QtWidgets.QHBoxLayout()
        
        check_blank_pass = QtWidgets.QCheckBox("Try blank passwords (-e n)")
        check_blank_pass.setToolTip("Try empty password for each username")
        helper_layout.addWidget(check_blank_pass)
        
        check_login_as_pass = QtWidgets.QCheckBox("Try login as password (-e s)")
        check_login_as_pass.setToolTip("Try username as password (e.g., admin:admin)")
        helper_layout.addWidget(check_login_as_pass)
        
        cred_options_layout.addLayout(helper_layout)
        
        cred_options_group.setLayout(cred_options_layout)
        layout.addWidget(cred_options_group)
        
        # Attack Modifiers group
        modifiers_group = QtWidgets.QGroupBox("Attack Modifiers")
        modifiers_layout = QtWidgets.QHBoxLayout()
        
        check_loop_users = QtWidgets.QCheckBox("Loop users first (-u)")
        check_loop_users.setToolTip("Try all users for one password before next password")
        modifiers_layout.addWidget(check_loop_users)
        
        check_exit_first = QtWidgets.QCheckBox("Exit on first valid (-f)")
        check_exit_first.setToolTip("Stop attack after finding first valid credential")
        modifiers_layout.addWidget(check_exit_first)
        
        check_verbose = QtWidgets.QCheckBox("Verbose output (-V)")
        check_verbose.setToolTip("Show each login attempt")
        modifiers_layout.addWidget(check_verbose)
        
        modifiers_group.setLayout(modifiers_layout)
        layout.addWidget(modifiers_group)
        
        # Advanced Options
        advanced_group = QtWidgets.QGroupBox("Advanced Options")
        advanced_layout = QtWidgets.QVBoxLayout()
        
        additional_label = QtWidgets.QLabel("Additional Hydra arguments:")
        additional_label.setStyleSheet("font-size: 10px; color: #666;")
        advanced_layout.addWidget(additional_label)
        
        additional_args_edit = QtWidgets.QLineEdit()
        additional_args_edit.setPlaceholderText("e.g., -I -w 30 (optional custom flags)")
        additional_args_edit.setToolTip("Custom Hydra command-line arguments")
        advanced_layout.addWidget(additional_args_edit)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Options group (Tasks & Timeout)
        options_group = QtWidgets.QGroupBox("Performance Options")
        options_layout = QtWidgets.QFormLayout()
        
        # Parallel tasks
        tasks_spin = QtWidgets.QSpinBox()
        tasks_spin.setMinimum(1)
        tasks_spin.setMaximum(64)
        tasks_spin.setValue(self.config.tools.hydra_default_tasks)
        options_layout.addRow("Parallel Tasks:", tasks_spin)
        
        # Timeout
        timeout_spin = QtWidgets.QSpinBox()
        timeout_spin.setMinimum(10)
        timeout_spin.setMaximum(3600)
        timeout_spin.setValue(self.config.tools.hydra_default_timeout)
        timeout_spin.setSuffix(" seconds")
        options_layout.addRow("Timeout:", timeout_spin)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Auto-start option
        autostart_group = QtWidgets.QGroupBox("Execution")
        autostart_layout = QtWidgets.QVBoxLayout()
        
        autostart_check = QtWidgets.QCheckBox("Start attack immediately after creating tab")
        autostart_check.setToolTip("If unchecked, you must click 'Run' button manually")
        autostart_check.setChecked(True)  # Default: auto-start
        autostart_layout.addWidget(autostart_check)
        
        autostart_group.setLayout(autostart_layout)
        layout.addWidget(autostart_group)
        
        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        
        # Get values BEFORE dialog is destroyed
        wordlist_path = wordlist_edit.text().strip()
        tasks_value = tasks_spin.value()
        timeout_value = timeout_spin.value()
        
        # Credential options
        single_user = single_user_edit.text().strip() if single_user_check.isChecked() else None
        single_pass = single_pass_edit.text().strip() if single_pass_check.isChecked() else None
        blank_pass = check_blank_pass.isChecked()
        login_as_pass = check_login_as_pass.isChecked()
        
        # Attack modifiers
        loop_users = check_loop_users.isChecked()
        exit_first = check_exit_first.isChecked()
        verbose = check_verbose.isChecked()
        
        # Additional args
        additional_args = additional_args_edit.text().strip()
        
        # Auto-start option
        auto_start = autostart_check.isChecked()
        
        # Validation: Need wordlist OR single credentials
        if not wordlist_path and not (single_user or single_pass):
            QMessageBox.warning(
                self, 
                "Missing Credentials", 
                "Please select a wordlist directory OR enter single username/password."
            )
            return
        
        # Create BruteWidget for this attack
        tab_name = f"{service} ({port}/tcp)"
        brute_widget = BruteWidget(host_ip, port, service, wordlist_path or "single-creds", self)
        
        # Store attack options in widget
        brute_widget.setProperty("single_user", single_user)
        brute_widget.setProperty("single_pass", single_pass)
        brute_widget.setProperty("blank_pass", blank_pass)
        brute_widget.setProperty("login_as_pass", login_as_pass)
        brute_widget.setProperty("loop_users", loop_users)
        brute_widget.setProperty("exit_first", exit_first)
        brute_widget.setProperty("verbose", verbose)
        brute_widget.setProperty("additional_args", additional_args)
        brute_widget.setProperty("auto_start", auto_start)
        brute_widget.setProperty("tasks", tasks_value)
        brute_widget.setProperty("timeout", timeout_value)
        brute_widget.setProperty("wordlist_path", wordlist_path)
        
        # Connect signals with captured values
        brute_widget.attack_started.connect(
            lambda: self._start_hydra_attack(
                brute_widget, wordlist_path, tasks_value, timeout_value
            )
        )
        brute_widget.attack_stopped.connect(
            lambda: self._stop_hydra_attack(brute_widget)
        )
        brute_widget.credentials_found.connect(self._on_credentials_found)
        brute_widget.edit_config.connect(
            lambda: self._edit_hydra_config(brute_widget)
        )
        
        # Remove "Getting Started" placeholder if it exists
        if self.hydra_running_widget.count() == 1:
            first_tab_widget = self.hydra_running_widget.widget(0)
            if isinstance(first_tab_widget, QtWidgets.QLabel):
                self.hydra_running_widget.removeTab(0)
        
        # Add tab to Running sub-tab and switch to it
        tab_index = self.hydra_running_widget.addTab(brute_widget, tab_name)
        self.hydra_running_widget.setCurrentIndex(tab_index)
        
        # Switch to Hydra tab in main tabs, then to Running sub-tab
        hydra_tab_index = self.main_tabs.indexOf(self.hydra_tab_widget)
        self.main_tabs.setCurrentIndex(hydra_tab_index)
        
        running_tab_index = self.hydra_tab_widget.indexOf(self.hydra_running_widget)
        self.hydra_tab_widget.setCurrentIndex(running_tab_index)
        
        # Store widget reference for management
        brute_widget.setProperty("tab_index", tab_index)
        brute_widget.setProperty("host_ip", host_ip)
        
        logger.info(f"Created Hydra attack tab: {tab_name} for {host_ip}:{port}")
        
        # Auto-start if enabled
        if auto_start:
            self.status_label.setText(f"🚀 Starting attack: {tab_name}...")
            brute_widget.attack_started.emit()  # Trigger start immediately
        else:
            self.status_label.setText(f"💡 Hydra attack ready: {tab_name}. Click 'Run' to start.")
    
    def _launch_hydra_attack_from_nmap(self, host_ip: str, port: int, service: str) -> None:
        """
        Launch Hydra attack directly (used from Services tab or "Send to Hydra").
        This bypasses the dialog and uses the same dialog as _launch_hydra_attack.
        
        Args:
            host_ip: Target host IP
            port: Target port number
            service: Service type (ssh, ftp, etc.)
        """
        # Just call the regular launch function which shows the dialog
        self._launch_hydra_attack(host_ip, port, service)
    
    def _browse_wordlist_directory(self, line_edit: QtWidgets.QLineEdit) -> None:
        """
        Browse for wordlist directory (simplified version).
        
        Args:
            line_edit: Line edit to update with selected directory
        """
        # Directory selection dialog
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Wordlist Directory",
            str(Path("scripts/wordlists")),
            QtWidgets.QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            line_edit.setText(directory)
            
            # Show statistics about selected directory
            try:
                from legion.utils.wordlist_processor import WordlistProcessor
                stats = WordlistProcessor.get_wordlist_stats(Path(directory))
                
                info_parts = []
                info_parts.append(f"📁 {Path(directory).name}")
                
                if stats['files'] > 0:
                    info_parts.append(f"Files: {stats['files']}")
                    info_parts.append(f"Entries: {stats['unique_entries']:,}")
                    
                    if stats['is_combo']:
                        info_parts.append("(combo format detected)")
                else:
                    info_parts.append("(no .txt files found)")
                
                self.status_label.setText(" | ".join(info_parts))
                
            except Exception as e:
                logger.warning(f"Could not get wordlist stats: {e}")
    
    def _browse_wordlist(self, line_edit: QtWidgets.QLineEdit, title: str) -> None:
        """
        Browse for wordlist file or directory.
        
        Args:
            line_edit: Line edit to update with selected path
            title: Dialog title
        """
        # Create custom dialog with file AND folder selection
        dialog = QtWidgets.QFileDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.AnyFile)
        dialog.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog, True)
        
        # Enable both file and directory selection
        file_view = dialog.findChild(QtWidgets.QListView, "listView")
        if file_view:
            file_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        
        tree_view = dialog.findChild(QtWidgets.QTreeView)
        if tree_view:
            tree_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        
        # Add "Select Folder" button
        dialog.setOption(QtWidgets.QFileDialog.Option.ShowDirsOnly, False)
        dialog.setNameFilter("Wordlists (*.txt);;All Files (*.*)")
        
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected = dialog.selectedFiles()
            if selected:
                path = selected[0]
                line_edit.setText(path)
                
                # Show info about selected path
                from legion.utils.wordlist_processor import WordlistProcessor
                stats = WordlistProcessor.get_wordlist_stats(Path(path))
                
                info_text = f"Selected: {Path(path).name}\n"
                if stats['files'] > 1:
                    info_text += f"Files: {stats['files']}\n"
                info_text += f"Entries: {stats['unique_entries']}"
                if stats['is_combo']:
                    info_text += " (combo format detected)"
                
                self.status_label.setText(info_text)
    
    def _run_hydra_attack_async(
        self,
        host_ip: str,
        port: int,
        service: str,
        username_file: Optional[str],
        password_file: Optional[str],
        tasks: int,
        timeout: int,
        original_wordlist_path: Optional[str] = None,
        combo_file: Optional[str] = None
    ) -> None:
        """
        Run Hydra attack asynchronously.
        
        Args:
            host_ip: Target host
            port: Target port
            service: Service type
            username_file: Path to (merged) username wordlist (None if combo mode)
            password_file: Path to (merged) password wordlist (None if combo mode)
            tasks: Number of parallel tasks
            timeout: Attack timeout in seconds
            original_wordlist_path: Original directory path (for auto-export)
            combo_file: Path to combo file (user:pass format) - if provided, uses -C mode
        """
        async def run_attack():
            # Initialize Hydra tool first (needed for process killing)
            hydra = HydraTool()
            
            if not await hydra.validate():
                QMessageBox.critical(
                    self,
                    "Hydra Not Found",
                    "Hydra is not installed or not found in PATH.\n"
                    "Please install Hydra and configure the path in Settings."
                )
                return
            
            # Create and show progress dialog
            progress_dialog = QtWidgets.QProgressDialog(
                f"Running Hydra attack on {service}://{host_ip}:{port}...",
                "Cancel",
                0,
                0,  # Indeterminate progress (no max value)
                self
            )
            progress_dialog.setWindowTitle("Hydra Attack in Progress")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setMinimumDuration(0)  # Show immediately
            progress_dialog.setAutoClose(False)
            progress_dialog.setAutoReset(False)
            
            # Track if user cancelled
            cancelled = False
            
            def on_cancel():
                nonlocal cancelled
                cancelled = True
                progress_dialog.setLabelText("⚠️ Cancelling attack...")
                # Actually kill the Hydra process
                if hydra.kill_current_process():
                    logger.info("Killed running Hydra process")
            
            progress_dialog.canceled.connect(on_cancel)
            progress_dialog.show()
            QtWidgets.QApplication.processEvents()
            
            # Use QTimer for progress updates (avoids asyncio task conflicts)
            import time
            start_time = time.time()
            
            def update_progress_timer():
                """Update progress dialog text (called by QTimer)."""
                if not cancelled and progress_dialog.isVisible():
                    elapsed = int(time.time() - start_time)
                    progress_dialog.setLabelText(
                        f"Running Hydra attack on {service}://{host_ip}:{port}...\n"
                        f"⏱️ Elapsed time: {elapsed}s\n"
                        f"🔍 Testing credentials..."
                    )
            
            # Create timer for progress updates
            progress_timer = QtCore.QTimer()
            progress_timer.timeout.connect(update_progress_timer)
            progress_timer.start(500)  # Update every 500ms
            
            try:
                # Update status
                if combo_file:
                    self.status_label.setText(
                        f"🔑 Hydra attacking {service}://{host_ip}:{port} (COMBO mode)..."
                    )
                else:
                    self.status_label.setText(
                        f"🔑 Hydra attacking {service}://{host_ip}:{port} (SEPARATE mode)..."
                    )
                
                # Run attack (combo mode or separate mode)
                # For HTTP services, pass path as module option (-m)
                additional_args = []
                if service in ['http-get', 'http-post', 'https-get', 'https-post']:
                    # Use -m option for HTTP path
                    additional_args = ["-m", "/"]
                
                # Wrap attack in try/except to catch cancellation
                try:
                    if combo_file:
                        # Combo mode: -C file
                        result = await hydra.attack(
                            target=host_ip,
                            service=service,
                            combo_file=Path(combo_file),
                            port=port,
                            tasks=tasks,
                            timeout=float(timeout),
                            additional_args=additional_args if additional_args else None
                        )
                    else:
                        # Separate mode: -L users -P passwords
                        result = await hydra.attack(
                            target=host_ip,
                            service=service,
                            login_file=Path(username_file),
                            password_file=Path(password_file),
                            port=port,
                            tasks=tasks,
                            timeout=float(timeout),
                            additional_args=additional_args if additional_args else None
                        )
                except asyncio.CancelledError:
                    # Attack was cancelled
                    progress_timer.stop()
                    progress_dialog.close()
                    self.status_label.setText("⚠️ Hydra attack cancelled by user")
                    QMessageBox.information(
                        self,
                        "Attack Cancelled",
                        "Hydra attack was cancelled by user."
                    )
                    return
                
                # Stop progress timer and close dialog
                progress_timer.stop()
                progress_dialog.close()
                
                # Check if user cancelled (backup check)
                if cancelled:
                    self.status_label.setText("⚠️ Hydra attack cancelled by user")
                    return
                
                # Parse results
                hydra_result = await hydra.parse_output(result)
                
                # Auto-export successful credentials to used wordlists
                if hydra_result.credentials:
                    await self._auto_export_to_wordlists(
                        hydra_result.credentials,
                        username_file,
                        password_file,
                        combo_file
                    )
                
                # Show results dialog
                self._show_hydra_results(
                    host_ip,
                    port,
                    service,
                    hydra_result,
                    result.success
                )
                
                # Credentials are already in Results tab (added during streaming)
                # No database save to prevent blocking/corruption
                
                self.status_label.setText("✅ Hydra attack completed")
                
            except Exception as e:
                # Stop timer and close progress dialog on error
                if 'progress_timer' in locals():
                    progress_timer.stop()
                if 'progress_dialog' in locals():
                    progress_dialog.close()
                
                logger.error(f"Hydra attack failed: {e}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Attack Failed",
                    f"Hydra attack failed:\n{str(e)}"
                )
                self.status_label.setText("❌ Hydra attack failed")
        
        # Run in event loop
        asyncio.create_task(run_attack())
    
    def _show_hydra_results(
        self,
        host_ip: str,
        port: int,
        service: str,
        hydra_result,
        success: bool
    ) -> None:
        """
        Show Hydra attack results in dialog.
        
        Args:
            host_ip: Target host
            port: Target port
            service: Service type
            hydra_result: HydraResult object
            success: Whether attack completed successfully
        """
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Hydra Results - {service}://{host_ip}:{port}")
        dialog.setMinimumSize(600, 400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Status label
        if hydra_result.credentials:
            status_text = f"✅ Found {len(hydra_result.credentials)} credential(s)!"
            status_color = "#00ff00"
        elif success:
            status_text = "⚠️ Attack completed, but no credentials found"
            status_color = "#ffaa00"
        else:
            status_text = "❌ Attack failed or was stopped"
            status_color = "#ff0000"
        
        status_label = QtWidgets.QLabel(status_text)
        status_label.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {status_color}; "
            f"padding: 10px; background-color: #2b2b2b; border-radius: 5px;"
        )
        layout.addWidget(status_label)
        
        # Credentials table
        if hydra_result.credentials:
            cred_group = QtWidgets.QGroupBox("Found Credentials")
            cred_layout = QtWidgets.QVBoxLayout()
            
            table = QtWidgets.QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["✓", "Host", "Port", "Username", "Password"])
            table.setRowCount(len(hydra_result.credentials))
            
            for i, cred in enumerate(hydra_result.credentials):
                # Status icon (all found credentials are successful)
                status_item = QtWidgets.QTableWidgetItem("✓")
                status_item.setForeground(QtGui.QColor("#00ff00"))  # Green
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, 0, status_item)
                
                table.setItem(i, 1, QtWidgets.QTableWidgetItem(cred.host))
                table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(cred.port)))
                
                # Username (bold)
                user_item = QtWidgets.QTableWidgetItem(cred.login)
                user_item.setFont(QtGui.QFont("Courier", weight=QtGui.QFont.Weight.Bold))
                table.setItem(i, 3, user_item)
                
                # Password (bold)
                pass_item = QtWidgets.QTableWidgetItem(cred.password)
                pass_item.setFont(QtGui.QFont("Courier", weight=QtGui.QFont.Weight.Bold))
                table.setItem(i, 4, pass_item)
            
            table.resizeColumnsToContents()
            cred_layout.addWidget(table)
            cred_group.setLayout(cred_layout)
            layout.addWidget(cred_group)
        
        # Statistics
        if hydra_result.statistics:
            stats = hydra_result.statistics
            stats_group = QtWidgets.QGroupBox("Attack Statistics")
            stats_layout = QtWidgets.QFormLayout()
            
            stats_layout.addRow("Total Attempts:", QtWidgets.QLabel(str(stats.total_attempts)))
            stats_layout.addRow("Successful:", QtWidgets.QLabel(str(stats.successful_attempts)))
            
            if stats.total_attempts > 0:
                success_rate = (stats.successful_attempts / stats.total_attempts) * 100
                stats_layout.addRow("Success Rate:", QtWidgets.QLabel(f"{success_rate:.2f}%"))
            
            stats_group.setLayout(stats_layout)
            layout.addWidget(stats_group)
        
        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        # Export credentials button (only if credentials found)
        if hydra_result.credentials:
            export_btn = QtWidgets.QPushButton("💾 Export to Wordlist...")
            export_btn.clicked.connect(
                lambda: self._export_hydra_credentials(hydra_result.credentials, dialog)
            )
            button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _export_hydra_credentials(self, credentials, parent_dialog) -> None:
        """
        Export Hydra credentials to wordlist file.
        
        Args:
            credentials: List of HydraCredential objects
            parent_dialog: Parent dialog (to close after export)
        """
        # Ask user for export format
        format_dialog = QtWidgets.QDialog(parent_dialog)
        format_dialog.setWindowTitle("Export Credentials")
        format_dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(format_dialog)
        
        layout.addWidget(QtWidgets.QLabel("Select export format:"))
        
        # Format options
        format_combo = QtWidgets.QComboBox()
        format_combo.addItems([
            "Passwords only",
            "Usernames only",
            "Username:Password (combo)",
        ])
        layout.addWidget(format_combo)
        
        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(format_dialog.accept)
        button_box.rejected.connect(format_dialog.reject)
        layout.addWidget(button_box)
        
        if format_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        
        # Map format to mode
        format_modes = {
            0: "passwords",
            1: "usernames",
            2: "combo"
        }
        mode = format_modes[format_combo.currentIndex()]
        
        # Ask for output file
        from legion.utils.wordlists import get_wordlists_dir
        
        default_dir = get_wordlists_dir()
        default_name = f"hydra_export_{mode}.txt"
        
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent_dialog,
            "Export Credentials",
            str(default_dir / default_name),
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        # Convert HydraCredentials to Credential objects for export
        from legion.core.models import Credential
        creds_to_export = []
        
        for hcred in credentials:
            creds_to_export.append(
                Credential(
                    host=hcred.host,
                    port=hcred.port,
                    service=hcred.service,
                    username=hcred.login,
                    password=hcred.password,
                    source="hydra"
                )
            )
        
        # Export
        try:
            count = export_credentials_to_wordlist(
                creds_to_export,
                Path(file_path),
                mode=mode
            )
            
            QMessageBox.information(
                parent_dialog,
                "Export Successful",
                f"Exported {count} entries to:\n{file_path}"
            )
            
            logger.info(f"Exported {count} credentials to {file_path}")
            
        except Exception as e:
            QMessageBox.critical(
                parent_dialog,
                "Export Failed",
                f"Failed to export credentials:\n{str(e)}"
            )
            logger.error(f"Credential export failed: {e}", exc_info=True)
    
    async def _auto_export_to_wordlists(
        self,
        credentials,
        username_file: Optional[str],
        password_file: Optional[str],
        combo_file: Optional[str] = None
    ) -> None:
        """
        Automatically export successful credentials back to used wordlists.
        Avoids duplicates by checking existing entries.
        
        Args:
            credentials: List of HydraCredential objects
            username_file: Original username wordlist path (None if combo mode)
            password_file: Original password wordlist path (None if combo mode)
            combo_file: Original combo wordlist path (for combo mode)
        """
        try:
            from legion.core.models import Credential
            
            # Convert to Credential objects
            creds_to_export = []
            for hcred in credentials:
                creds_to_export.append(
                    Credential(
                        host=hcred.host,
                        port=hcred.port,
                        service=hcred.service,
                        username=hcred.login,
                        password=hcred.password,
                        source="hydra",
                        verified=True
                    )
                )
            
            # If combo mode, export to combo file
            if combo_file and Path(combo_file).exists():
                combo_path = Path(combo_file)
                existing_combos = set()
                
                # Read existing entries
                try:
                    with open(combo_path, 'r', encoding='utf-8') as f:
                        existing_combos = {line.strip() for line in f if line.strip() and ':' in line}
                except Exception as e:
                    logger.warning(f"Could not read existing combos: {e}")
                
                # Add new unique combos
                new_combos = {
                    f"{cred.username}:{cred.password}"
                    for cred in creds_to_export
                    if cred.username and cred.password
                }
                combos_to_add = new_combos - existing_combos
                
                if combos_to_add:
                    with open(combo_path, 'a', encoding='utf-8') as f:
                        for combo in sorted(combos_to_add):
                            f.write(f"{combo}\n")
                    
                    logger.info(
                        f"Auto-exported {len(combos_to_add)} new combos to {combo_path.name}"
                    )
                
                return  # Done with combo mode
            
            # Separate mode: Auto-export usernames to username wordlist (avoid duplicates)
            if username_file and Path(username_file).exists():
                username_path = Path(username_file)
                existing_users = set()
                
                # Read existing entries
                try:
                    with open(username_path, 'r', encoding='utf-8') as f:
                        existing_users = {line.strip() for line in f if line.strip()}
                except Exception as e:
                    logger.warning(f"Could not read existing usernames: {e}")
                
                # Add new unique usernames
                new_users = {cred.username for cred in creds_to_export if cred.username}
                users_to_add = new_users - existing_users
                
                if users_to_add:
                    with open(username_path, 'a', encoding='utf-8') as f:
                        for user in sorted(users_to_add):
                            f.write(f"{user}\n")
                    
                    logger.info(
                        f"Auto-exported {len(users_to_add)} new usernames to {username_path.name}"
                    )
            
            # Auto-export passwords to password wordlist (avoid duplicates)
            if password_file and Path(password_file).exists():
                password_path = Path(password_file)
                existing_passwords = set()
                
                # Read existing entries
                try:
                    with open(password_path, 'r', encoding='utf-8') as f:
                        existing_passwords = {line.strip() for line in f if line.strip()}
                except Exception as e:
                    logger.warning(f"Could not read existing passwords: {e}")
                
                # Add new unique passwords
                new_passwords = {cred.password for cred in creds_to_export if cred.password}
                passwords_to_add = new_passwords - existing_passwords
                
                if passwords_to_add:
                    with open(password_path, 'a', encoding='utf-8') as f:
                        for pwd in sorted(passwords_to_add):
                            f.write(f"{pwd}\n")
                    
                    logger.info(
                        f"Auto-exported {len(passwords_to_add)} new passwords to {password_path.name}"
                    )
            
            logger.info(
                f"✅ Auto-export completed: {len(creds_to_export)} credentials processed"
            )
            
        except Exception as e:
            logger.warning(f"Auto-export to wordlists failed: {e}", exc_info=True)
    
    def _export_host_credentials(self, host_ip: str) -> None:
        """
        Export all credentials for a specific host.
        
        Args:
            host_ip: Host IP address
        """
        credentials = self.database.get_credentials(host_ip)
        
        if not credentials:
            QMessageBox.information(
                self,
                "No Credentials",
                f"No credentials found for {host_ip}"
            )
            return
        
        # Ask user for export format
        format_dialog = QtWidgets.QDialog(self)
        format_dialog.setWindowTitle(f"Export Credentials - {host_ip}")
        format_dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(format_dialog)
        
        layout.addWidget(QtWidgets.QLabel(
            f"Found {len(credentials)} credential(s) for {host_ip}\n"
            f"Select export format:"
        ))
        
        # Format options
        format_combo = QtWidgets.QComboBox()
        format_combo.addItems([
            "Passwords only",
            "Usernames only",
            "Username:Password (combo)",
        ])
        layout.addWidget(format_combo)
        
        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(format_dialog.accept)
        button_box.rejected.connect(format_dialog.reject)
        layout.addWidget(button_box)
        
        if format_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        
        # Map format to mode
        format_modes = {
            0: "passwords",
            1: "usernames",
            2: "combo"
        }
        mode = format_modes[format_combo.currentIndex()]
        
        # Ask for output file
        from legion.utils.wordlists import get_wordlists_dir
        
        default_dir = get_wordlists_dir()
        default_name = f"{host_ip}_{mode}.txt"
        
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Credentials",
            str(default_dir / default_name),
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        # Export
        try:
            count = export_credentials_to_wordlist(
                credentials,
                Path(file_path),
                mode=mode
            )
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {count} entries to:\n{file_path}"
            )
            
            logger.info(f"Exported {count} credentials from {host_ip} to {file_path}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export credentials:\n{str(e)}"
            )
            logger.error(f"Credential export failed: {e}", exc_info=True)


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
