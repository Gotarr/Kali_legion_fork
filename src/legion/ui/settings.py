"""
Settings dialog for Legion configuration.

Provides UI for editing TOML-based configuration with live preview.

Author: Gotham Security
Date: 2025-11-12
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QSpinBox, QCheckBox,
    QComboBox, QPushButton, QFileDialog, QGroupBox,
    QFormLayout, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from legion.config.manager import ConfigManager
from legion.config.schema import LegionConfig

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """
    Settings dialog with tabbed interface.
    
    Tabs:
    - General: UI theme, auto-refresh, logging
    - Scanning: Scan defaults, timing, concurrency
    - Tools: Tool paths (nmap, hydra, etc.)
    - Advanced: TOML editor for manual editing
    
    Signals:
        settings_changed: Emitted when settings are applied
    """
    
    settings_changed = pyqtSignal()
    
    def __init__(
        self,
        config_manager: ConfigManager,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize settings dialog.
        
        Args:
            config_manager: Configuration manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.config = config_manager.load()
        self._original_config = self.config  # For reset
        
        self.setWindowTitle("Legion Settings")
        self.setMinimumSize(600, 500)
        
        self._init_ui()
        self._load_values()
    
    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self._create_general_tab()
        self._create_scanning_tab()
        self._create_tools_tab()
        self._create_advanced_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._on_reset)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._on_apply)
        button_layout.addWidget(self.apply_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._on_save)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def _create_general_tab(self) -> None:
        """Create General settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # UI Settings
        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["system", "light", "dark"])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        ui_layout.addRow("Theme:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 24)
        self.font_size_spin.setSuffix(" pt")
        ui_layout.addRow("Font Size:", self.font_size_spin)
        
        self.show_toolbar_check = QCheckBox("Show Toolbar")
        ui_layout.addRow("", self.show_toolbar_check)
        
        self.show_statusbar_check = QCheckBox("Show Status Bar")
        ui_layout.addRow("", self.show_statusbar_check)
        
        self.auto_refresh_spin = QSpinBox()
        self.auto_refresh_spin.setRange(0, 60)
        self.auto_refresh_spin.setSuffix(" seconds")
        self.auto_refresh_spin.setSpecialValueText("Disabled")
        ui_layout.addRow("Auto-Refresh:", self.auto_refresh_spin)
        
        # Terminal Selection (Legacy feature)
        self.terminal_combo = QComboBox()
        import platform
        if platform.system() == "Windows":
            self.terminal_combo.addItems(["cmd", "powershell", "wt"])
        else:
            self.terminal_combo.addItems(["gnome-terminal", "xterm", "konsole", "terminator"])
        ui_layout.addRow("Default Terminal:", self.terminal_combo)
        
        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)
        
        # Logging Settings
        log_group = QGroupBox("Logging")
        log_layout = QFormLayout()
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("Log Level:", self.log_level_combo)
        
        self.log_file_check = QCheckBox("Enable File Logging")
        log_layout.addRow("", self.log_file_check)
        
        self.log_console_check = QCheckBox("Enable Console Logging")
        log_layout.addRow("", self.log_console_check)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "General")
    
    def _create_scanning_tab(self) -> None:
        """Create Scanning settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scan Defaults
        scan_group = QGroupBox("Scan Defaults")
        scan_layout = QFormLayout()
        
        self.scan_profile_combo = QComboBox()
        self.scan_profile_combo.addItems(["quick", "full", "stealth", "version", "os", "aggressive"])
        scan_layout.addRow("Default Profile:", self.scan_profile_combo)
        
        self.scan_timeout_spin = QSpinBox()
        self.scan_timeout_spin.setRange(10, 3600)
        self.scan_timeout_spin.setSuffix(" seconds")
        scan_layout.addRow("Timeout:", self.scan_timeout_spin)
        
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        scan_layout.addRow("Max Concurrent Scans:", self.max_concurrent_spin)
        
        self.timing_combo = QComboBox()
        self.timing_combo.addItems([
            "0 - Paranoid (slowest)",
            "1 - Sneaky",
            "2 - Polite",
            "3 - Normal",
            "4 - Aggressive (default)",
            "5 - Insane (fastest)"
        ])
        scan_layout.addRow("Timing Template:", self.timing_combo)
        
        # Screenshot Timeout (Legacy feature)
        self.screenshot_timeout_spin = QSpinBox()
        self.screenshot_timeout_spin.setRange(5, 300)
        self.screenshot_timeout_spin.setSuffix(" seconds")
        self.screenshot_timeout_spin.setValue(15)
        scan_layout.addRow("Screenshot Timeout:", self.screenshot_timeout_spin)
        
        # Web Services (Legacy feature)
        self.web_services_edit = QLineEdit()
        self.web_services_edit.setPlaceholderText("http,https,ssl,soap,...")
        self.web_services_edit.setToolTip("Comma-separated list of services to treat as web services")
        scan_layout.addRow("Web Services:", self.web_services_edit)
        
        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)
        
        # Scan Options
        options_group = QGroupBox("Scan Options")
        options_layout = QVBoxLayout()
        
        self.auto_parse_check = QCheckBox("Automatically parse scan results")
        options_layout.addWidget(self.auto_parse_check)
        
        self.auto_save_check = QCheckBox("Automatically save results to database")
        options_layout.addWidget(self.auto_save_check)
        
        self.verbose_check = QCheckBox("Enable verbose output")
        options_layout.addWidget(self.verbose_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Scanning")
    
    def _create_tools_tab(self) -> None:
        """Create Tools settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        tools_group = QGroupBox("Tool Paths")
        tools_layout = QFormLayout()
        
        # Helper to create path input with browse button
        def create_path_input(label: str, is_directory: bool = False) -> tuple[QLineEdit, QPushButton]:
            h_layout = QHBoxLayout()
            line_edit = QLineEdit()
            browse_btn = QPushButton("Browse...")
            browse_btn.clicked.connect(
                lambda: self._browse_for_tool(line_edit, is_directory)
            )
            h_layout.addWidget(line_edit)
            h_layout.addWidget(browse_btn)
            tools_layout.addRow(label, h_layout)
            return line_edit, browse_btn
        
        self.nmap_path_edit, _ = create_path_input("nmap:")
        self.hydra_path_edit, _ = create_path_input("hydra:")
        self.nikto_path_edit, _ = create_path_input("nikto:")
        self.searchsploit_path_edit, _ = create_path_input("searchsploit:")
        
        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)
        
        # NSE Scripts Settings
        nse_group = QGroupBox("Nmap NSE Scripts")
        nse_layout = QFormLayout()
        
        # NSE script path
        nse_path_layout = QHBoxLayout()
        self.nse_script_path_edit = QLineEdit()
        self.nse_script_path_edit.setPlaceholderText("Leave empty to use Legion's scripts/nmap/")
        nse_browse_btn = QPushButton("Browse...")
        nse_browse_btn.clicked.connect(
            lambda: self._browse_for_tool(self.nse_script_path_edit, is_directory=True)
        )
        nse_path_layout.addWidget(self.nse_script_path_edit)
        nse_path_layout.addWidget(nse_browse_btn)
        nse_layout.addRow("NSE Scripts Path:", nse_path_layout)
        
        # Enable NSE
        self.enable_nse_check = QCheckBox("Enable Nmap NSE Scripts")
        nse_layout.addRow("", self.enable_nse_check)
        
        # Vulners settings
        self.enable_vulners_check = QCheckBox("Auto-run Vulners CVE scan")
        nse_layout.addRow("", self.enable_vulners_check)
        
        self.vulners_min_cvss_spin = QSpinBox()
        self.vulners_min_cvss_spin.setRange(0, 10)
        self.vulners_min_cvss_spin.setSingleStep(1)
        self.vulners_min_cvss_spin.setSuffix(" (0 = all)")
        nse_layout.addRow("Min CVSS Score:", self.vulners_min_cvss_spin)
        
        # Shodan API key
        self.shodan_api_key_edit = QLineEdit()
        self.shodan_api_key_edit.setPlaceholderText("Enter Shodan API key (optional)")
        self.shodan_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        nse_layout.addRow("Shodan API Key:", self.shodan_api_key_edit)
        
        nse_group.setLayout(nse_layout)
        layout.addWidget(nse_group)
        
        # Hydra Settings
        hydra_group = QGroupBox("Hydra Brute Force")
        hydra_layout = QFormLayout()
        
        # Default tasks
        self.hydra_tasks_spin = QSpinBox()
        self.hydra_tasks_spin.setRange(1, 64)
        self.hydra_tasks_spin.setValue(16)
        self.hydra_tasks_spin.setSuffix(" threads")
        hydra_layout.addRow("Default Tasks:", self.hydra_tasks_spin)
        
        # Default timeout
        self.hydra_timeout_spin = QSpinBox()
        self.hydra_timeout_spin.setRange(10, 3600)
        self.hydra_timeout_spin.setValue(300)
        self.hydra_timeout_spin.setSuffix(" seconds")
        hydra_layout.addRow("Default Timeout:", self.hydra_timeout_spin)
        
        # Wordlist path
        hydra_wordlist_layout = QHBoxLayout()
        self.hydra_wordlist_edit = QLineEdit()
        self.hydra_wordlist_edit.setPlaceholderText("Leave empty to use scripts/wordlists/")
        hydra_wordlist_browse = QPushButton("Browse...")
        hydra_wordlist_browse.clicked.connect(
            lambda: self._browse_for_tool(self.hydra_wordlist_edit, is_directory=True)
        )
        hydra_wordlist_layout.addWidget(self.hydra_wordlist_edit)
        hydra_wordlist_layout.addWidget(hydra_wordlist_browse)
        hydra_layout.addRow("Wordlist Directory:", hydra_wordlist_layout)
        
        hydra_group.setLayout(hydra_layout)
        layout.addWidget(hydra_group)
        
        # Tool Cache Settings
        cache_group = QGroupBox("Tool Discovery")
        cache_layout = QFormLayout()
        
        self.cache_enabled_check = QCheckBox("Enable tool cache")
        cache_layout.addRow("", self.cache_enabled_check)
        
        self.cache_ttl_spin = QSpinBox()
        self.cache_ttl_spin.setRange(0, 86400)
        self.cache_ttl_spin.setSuffix(" seconds")
        cache_layout.addRow("Cache TTL:", self.cache_ttl_spin)
        
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Tools")
    
    def _create_advanced_tab(self) -> None:
        """Create Advanced settings tab (TOML editor)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info_label = QLabel(
            "⚠️ <b>Advanced Users Only</b><br>"
            "Direct TOML editing. Invalid syntax may break configuration!"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self.toml_editor = QTextEdit()
        self.toml_editor.setFont(QFont("Courier", 9))
        layout.addWidget(self.toml_editor)
        
        reload_btn = QPushButton("Reload from File")
        reload_btn.clicked.connect(self._reload_toml)
        layout.addWidget(reload_btn)
        
        self.tabs.addTab(tab, "Advanced")
    
    def _load_values(self) -> None:
        """Load current config values into UI."""
        # General
        self.theme_combo.setCurrentText(self.config.ui.theme)
        self.font_size_spin.setValue(self.config.ui.font_size)
        self.show_toolbar_check.setChecked(self.config.ui.show_toolbar)
        self.show_statusbar_check.setChecked(self.config.ui.show_statusbar)
        self.auto_refresh_spin.setValue(self.config.ui.auto_refresh_interval)
        self.terminal_combo.setCurrentText(self.config.ui.default_terminal)
        
        self.log_level_combo.setCurrentText(self.config.logging.level)
        self.log_file_check.setChecked(self.config.logging.file_enabled)
        self.log_console_check.setChecked(self.config.logging.console_enabled)
        
        # Scanning
        self.scan_profile_combo.setCurrentText(self.config.scanning.default_profile)
        self.scan_timeout_spin.setValue(self.config.scanning.timeout)
        self.max_concurrent_spin.setValue(self.config.scanning.max_concurrent)
        self.timing_combo.setCurrentIndex(self.config.scanning.timing_template)
        self.screenshot_timeout_spin.setValue(self.config.scanning.screenshot_timeout)
        self.web_services_edit.setText(self.config.scanning.web_services)
        
        self.auto_parse_check.setChecked(self.config.scanning.auto_parse)
        self.auto_save_check.setChecked(self.config.scanning.auto_save)
        self.verbose_check.setChecked(self.config.scanning.verbose_output)
        
        # Tools
        self.nmap_path_edit.setText(self.config.tools.nmap_path or "")
        self.hydra_path_edit.setText(self.config.tools.hydra_path or "")
        self.nikto_path_edit.setText(self.config.tools.nikto_path or "")
        self.searchsploit_path_edit.setText(self.config.tools.searchsploit_path or "")
        
        self.cache_enabled_check.setChecked(self.config.tools.cache_enabled)
        self.cache_ttl_spin.setValue(self.config.tools.cache_ttl)
        
        # NSE Scripts
        self.nse_script_path_edit.setText(self.config.scanning.nse_script_path or "")
        self.enable_nse_check.setChecked(self.config.scanning.enable_nse_scripts)
        self.enable_vulners_check.setChecked(self.config.scanning.enable_vulners)
        self.vulners_min_cvss_spin.setValue(int(self.config.scanning.vulners_min_cvss))
        self.shodan_api_key_edit.setText(self.config.scanning.shodan_api_key or "")
        
        # Hydra
        self.hydra_tasks_spin.setValue(self.config.tools.hydra_default_tasks)
        self.hydra_timeout_spin.setValue(self.config.tools.hydra_default_timeout)
        self.hydra_wordlist_edit.setText(self.config.tools.hydra_wordlist_path or "")
        
        # Advanced (TOML)
        self._reload_toml()
    
    def _save_values(self) -> None:
        """Save UI values to config object."""
        # General
        self.config.ui.theme = self.theme_combo.currentText()
        self.config.ui.font_size = self.font_size_spin.value()
        self.config.ui.show_toolbar = self.show_toolbar_check.isChecked()
        self.config.ui.show_statusbar = self.show_statusbar_check.isChecked()
        self.config.ui.auto_refresh_interval = self.auto_refresh_spin.value()
        self.config.ui.default_terminal = self.terminal_combo.currentText()
        
        self.config.logging.level = self.log_level_combo.currentText()
        self.config.logging.file_enabled = self.log_file_check.isChecked()
        self.config.logging.console_enabled = self.log_console_check.isChecked()
        
        # Scanning
        self.config.scanning.default_profile = self.scan_profile_combo.currentText()
        self.config.scanning.timeout = self.scan_timeout_spin.value()
        self.config.scanning.max_concurrent = self.max_concurrent_spin.value()
        self.config.scanning.timing_template = self.timing_combo.currentIndex()
        self.config.scanning.screenshot_timeout = self.screenshot_timeout_spin.value()
        self.config.scanning.web_services = self.web_services_edit.text()
        
        self.config.scanning.auto_parse = self.auto_parse_check.isChecked()
        self.config.scanning.auto_save = self.auto_save_check.isChecked()
        self.config.scanning.verbose_output = self.verbose_check.isChecked()
        
        # Tools
        self.config.tools.nmap_path = self.nmap_path_edit.text() or None
        self.config.tools.hydra_path = self.hydra_path_edit.text() or None
        self.config.tools.nikto_path = self.nikto_path_edit.text() or None
        self.config.tools.searchsploit_path = self.searchsploit_path_edit.text() or None
        
        self.config.tools.cache_enabled = self.cache_enabled_check.isChecked()
        self.config.tools.cache_ttl = self.cache_ttl_spin.value()
        
        # NSE Scripts
        self.config.scanning.nse_script_path = self.nse_script_path_edit.text() or None
        self.config.scanning.enable_nse_scripts = self.enable_nse_check.isChecked()
        self.config.scanning.enable_vulners = self.enable_vulners_check.isChecked()
        self.config.scanning.vulners_min_cvss = float(self.vulners_min_cvss_spin.value())
        self.config.scanning.shodan_api_key = self.shodan_api_key_edit.text() or ""
        
        # Hydra
        self.config.tools.hydra_default_tasks = self.hydra_tasks_spin.value()
        self.config.tools.hydra_default_timeout = self.hydra_timeout_spin.value()
        self.config.tools.hydra_wordlist_path = self.hydra_wordlist_edit.text() or None
    
    def _browse_for_tool(self, line_edit: QLineEdit, is_directory: bool = False) -> None:
        """
        Open file browser to select tool executable or directory.
        
        Args:
            line_edit: Line edit to update with selected path
            is_directory: If True, select directory instead of file
        """
        if is_directory:
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "Select Directory",
                ""
            )
            if dir_path:
                line_edit.setText(dir_path)
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Tool Executable",
                "",
                "Executables (*.exe);;All Files (*.*)"
            )
            
            if file_path:
                line_edit.setText(file_path)
    
    def _reload_toml(self) -> None:
        """Reload TOML content from file."""
        try:
            with open(self.config_manager.config_path, 'r') as f:
                toml_content = f.read()
            self.toml_editor.setPlainText(toml_content)
        except Exception as e:
            logger.error(f"Failed to load TOML: {e}")
            self.toml_editor.setPlainText(f"# Error loading TOML: {e}")
    
    def _on_theme_changed(self, theme: str) -> None:
        """
        Handle theme change (live preview).
        
        Args:
            theme: Selected theme
        """
        # TODO: Apply theme preview
        logger.info(f"Theme changed to: {theme}")
    
    def _on_apply(self) -> None:
        """Apply settings without closing dialog."""
        self._save_values()
        
        try:
            # Validate
            self.config.validate()
            
            # Save to file
            self.config_manager.save(self.config)
            
            # Emit signal
            self.settings_changed.emit()
            
            logger.info("Settings applied successfully")
            
            QMessageBox.information(
                self,
                "Settings Applied",
                "Settings have been applied successfully."
            )
            
        except Exception as e:
            logger.error(f"Failed to apply settings: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to apply settings:\n{e}"
            )
    
    def _on_save(self) -> None:
        """Save settings and close dialog."""
        self._save_values()
        
        try:
            # Validate
            self.config.validate()
            
            # Save to file
            self.config_manager.save(self.config)
            
            # Emit signal
            self.settings_changed.emit()
            
            logger.info("Settings saved successfully")
            
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings:\n{e}"
            )
    
    def _on_reset(self) -> None:
        """Reset to default configuration."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset all settings to defaults?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config = LegionConfig()  # New default config
            self._load_values()
            logger.info("Settings reset to defaults")
