"""
UI Dialogs for Legion.

This module provides various dialog windows for user interaction,
including scan configuration, settings, and information displays.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QTextEdit,
    QPushButton, QLabel, QGroupBox, QDialogButtonBox,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QWidget, QRadioButton, QSlider, QSpacerItem, QSizePolicy,
    QPlainTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QT_VERSION_STR
from PyQt6.QtGui import QFont, QIcon, QPixmap
import sys


class NewScanDialog(QDialog):
    """
    Dialog for configuring and starting a new scan.
    
    Allows users to specify:
    - Target (IP, hostname, or CIDR range)
    - Scan type (Quick, Full, Stealth, Custom)
    - Additional options (ports, timing, scripts)
    """
    
    # Signal emitted when user confirms scan
    scan_requested = pyqtSignal(str, str, dict)  # target, scan_type, options
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Scan")
        self.setMinimumWidth(500)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        
        # Target section
        target_group = QGroupBox("Target")
        target_layout = QFormLayout()
        
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g., 192.168.1.1, example.com, 10.0.0.0/24")
        target_layout.addRow("Target:", self.target_input)
        
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # Scan type section
        scan_group = QGroupBox("Scan Type")
        scan_layout = QVBoxLayout()
        
        self.scan_type = QComboBox()
        self.scan_type.addItems([
            "Quick Scan (-T4 -F)",
            "Full Scan (-p-)",
            "Stealth Scan (-sS -T2)",
            "Service Version (-sV)",
            "OS Detection (-O)",
            "Aggressive Scan (-A)",
            "Custom"
        ])
        self.scan_type.currentTextChanged.connect(self._on_scan_type_changed)
        scan_layout.addWidget(self.scan_type)
        
        # Description label
        self.scan_description = QLabel()
        self.scan_description.setWordWrap(True)
        self.scan_description.setStyleSheet("color: gray; font-size: 10pt;")
        scan_layout.addWidget(self.scan_description)
        
        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)
        
        # Options section
        options_group = QGroupBox("Options")
        options_layout = QFormLayout()
        
        # Port range
        self.port_range = QLineEdit()
        self.port_range.setPlaceholderText("e.g., 1-1000, 22,80,443")
        options_layout.addRow("Port Range:", self.port_range)
        
        # Timing template
        self.timing = QComboBox()
        self.timing.addItems(["T0 (Paranoid)", "T1 (Sneaky)", "T2 (Polite)", 
                             "T3 (Normal)", "T4 (Aggressive)", "T5 (Insane)"])
        self.timing.setCurrentText("T4 (Aggressive)")
        options_layout.addRow("Timing:", self.timing)
        
        # Additional options
        self.version_detection = QCheckBox("Service Version Detection (-sV)")
        options_layout.addRow("", self.version_detection)
        
        self.os_detection = QCheckBox("OS Detection (-O)")
        options_layout.addRow("", self.os_detection)
        
        self.script_scan = QCheckBox("Default Scripts (--script=default)")
        options_layout.addRow("", self.script_scan)
        
        # Custom arguments
        self.custom_args = QLineEdit()
        self.custom_args.setPlaceholderText("Additional nmap arguments")
        options_layout.addRow("Custom Args:", self.custom_args)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set initial description
        self._on_scan_type_changed(self.scan_type.currentText())
    
    def _on_scan_type_changed(self, scan_type: str):
        """Update description when scan type changes."""
        descriptions = {
            "Quick Scan (-T4 -F)": "Fast scan of the 100 most common ports",
            "Full Scan (-p-)": "Scan all 65535 ports (slow but thorough)",
            "Stealth Scan (-sS -T2)": "SYN scan with slow timing to avoid detection",
            "Service Version (-sV)": "Detect service versions on open ports",
            "OS Detection (-O)": "Attempt to identify operating system",
            "Aggressive Scan (-A)": "OS detection, version detection, script scanning",
            "Custom": "Configure custom scan options below"
        }
        self.scan_description.setText(descriptions.get(scan_type, ""))
        
        # Enable port range for scans that support it
        # Quick Scan (-F) uses predefined top 100 ports, incompatible with custom ports
        # Full Scan (-p-) scans all ports by default but can be overridden
        # Custom scan allows full configuration
        supports_port_override = ("Custom" in scan_type or 
                                  "Full" in scan_type or 
                                  "Stealth" in scan_type or
                                  "Service" in scan_type or
                                  "OS" in scan_type or
                                  "Aggressive" in scan_type)
        self.port_range.setEnabled(supports_port_override)
    
    def _on_accept(self):
        """Handle OK button click."""
        target = self.target_input.text().strip()
        if not target:
            # Could show error dialog here
            return
        
        # Map UI scan type to internal scan type
        scan_type_map = {
            "Quick Scan (-T4 -F)": "quick",
            "Full Scan (-p-)": "full",
            "Stealth Scan (-sS -T2)": "stealth",
            "Service Version (-sV)": "version",
            "OS Detection (-O)": "os",
            "Aggressive Scan (-A)": "aggressive",
            "Custom": "custom"
        }
        
        scan_type = scan_type_map.get(self.scan_type.currentText(), "quick")
        
        # Build options dict
        options: Dict[str, Any] = {}
        
        if self.port_range.text():
            options["ports"] = self.port_range.text()
        
        # Extract timing number (e.g., "T4 (Aggressive)" -> "4")
        timing_text = self.timing.currentText()
        options["timing"] = timing_text[1]  # Gets the number after 'T'
        
        if self.version_detection.isChecked():
            options["version_detection"] = True
        
        if self.os_detection.isChecked():
            options["os_detection"] = True
        
        if self.script_scan.isChecked():
            options["scripts"] = "default"
        
        if self.custom_args.text():
            options["custom_args"] = self.custom_args.text()
        
        # Emit signal and close
        self.scan_requested.emit(target, scan_type, options)
        self.accept()
    
    @staticmethod
    def get_scan_parameters(parent=None) -> Optional[tuple[str, str, Dict[str, Any]]]:
        """
        Show dialog and return scan parameters if accepted.
        
        Returns:
            Tuple of (target, scan_type, options) or None if cancelled
        """
        dialog = NewScanDialog(parent)
        result_data = None
        
        def capture_data(target: str, scan_type: str, options: Dict[str, Any]):
            nonlocal result_data
            result_data = (target, scan_type, options)
        
        dialog.scan_requested.connect(capture_data)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return result_data
        return None


class ScanProgressDialog(QDialog):
    """
    Dialog showing progress of active scans.
    
    Displays:
    - List of active scans with status
    - Progress bars for each scan
    - Option to cancel scans
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scan Progress")
        self.setMinimumSize(600, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel("Active and queued scans:")
        layout.addWidget(info_label)
        
        # Scans table
        self.scans_table = QTableWidget()
        self.scans_table.setColumnCount(5)
        self.scans_table.setHorizontalHeaderLabels([
            "Target", "Type", "Status", "Progress", "Duration"
        ])
        
        header = self.scans_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.scans_table.setColumnWidth(3, 150)
        self.scans_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        
        layout.addWidget(self.scans_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel Selected")
        self.cancel_button.clicked.connect(self._on_cancel_scan)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def _on_cancel_scan(self):
        """Handle cancel scan button."""
        # TODO: Implement scan cancellation
        pass
    
    def update_scans(self, jobs: list):
        """Update the scans table with current jobs."""
        self.scans_table.setRowCount(len(jobs))
        
        for row, job in enumerate(jobs):
            # Target
            self.scans_table.setItem(row, 0, QTableWidgetItem(job.target))
            
            # Type
            self.scans_table.setItem(row, 1, QTableWidgetItem(job.scan_type))
            
            # Status
            status_item = QTableWidgetItem(job.status.value.upper())
            if job.status.value == "running":
                status_item.setForeground(Qt.GlobalColor.blue)
            elif job.status.value == "completed":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif job.status.value == "failed":
                status_item.setForeground(Qt.GlobalColor.red)
            self.scans_table.setItem(row, 2, status_item)
            
            # Progress
            progress_widget = QProgressBar()
            if job.status.value == "completed":
                progress_widget.setValue(100)
            elif job.status.value == "running":
                progress_widget.setRange(0, 0)  # Indeterminate
            else:
                progress_widget.setValue(0)
            self.scans_table.setCellWidget(row, 3, progress_widget)
            
            # Duration
            duration = job.duration or 0
            duration_text = f"{duration:.1f}s" if duration > 0 else "-"
            self.scans_table.setItem(row, 4, QTableWidgetItem(duration_text))


class AboutDialog(QDialog):
    """About Legion dialog with tabs for different information.

    Parameters:
        initial_tab: Optional index of the tab to select when the dialog opens.
    """
    
    def __init__(self, parent=None, initial_tab: int = 0):
        super().__init__(parent)
        self.setWindowTitle("About Legion")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        # Safely select initial tab if in range
        if 0 <= initial_tab < self.tabs.count():
            self.tabs.setCurrentIndex(initial_tab)
    
    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title section
        title_layout = QVBoxLayout()
        title = QLabel("Legion v2.0")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title_layout.addWidget(title)
        
        subtitle = QLabel("Network Penetration Testing Tool")
        subtitle.setStyleSheet("color: gray;")
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # Tab widget
        tabs = QTabWidget()
        # Store reference for external tab selection
        self.tabs = tabs
        
        # About tab
        about_widget = QWidget()
        about_layout = QVBoxLayout(about_widget)
        
        description = QLabel(
            "<h3>About</h3>"
            "<p>Legion is a cross-platform network penetration testing framework "
            "built with Python and PyQt6.</p>"
            "<p><b>Key Features:</b></p>"
            "<ul>"
            "<li>Network scanning with nmap</li>"
            "<li>Service enumeration and detection</li>"
            "<li>Port history tracking</li>"
            "<li>Automated vulnerability detection</li>"
            "<li>Cross-platform support (Windows & Linux)</li>"
            "<li>Modern Qt-based interface</li>"
            "</ul>"
        )
        description.setWordWrap(True)
        description.setTextFormat(Qt.TextFormat.RichText)
        about_layout.addWidget(description)
        about_layout.addStretch()
        
        tabs.addTab(about_widget, "About")
        
        # Keyboard Shortcuts tab
        shortcuts_widget = QWidget()
        shortcuts_layout = QVBoxLayout(shortcuts_widget)
        
        shortcuts_label = QLabel(
            "<h3>Keyboard Shortcuts</h3>"
            "<table cellpadding='5'>"
            "<tr><td><b>Ctrl+N</b></td><td>New Project</td></tr>"
            "<tr><td><b>Ctrl+O</b></td><td>Open Project</td></tr>"
            "<tr><td><b>Ctrl+Shift+N</b></td><td>New Scan</td></tr>"
            "<tr><td><b>Ctrl+H</b></td><td>Add Host(s)</td></tr>"
            "<tr><td><b>Ctrl+Shift+D</b></td><td>Clear All Data</td></tr>"
            "<tr><td><b>Ctrl+,</b></td><td>Settings</td></tr>"
            "<tr><td><b>Ctrl+Q</b></td><td>Exit</td></tr>"
            "<tr><td><b>F1</b></td><td>Help</td></tr>"
            "</table>"
            "<p style='margin-top: 15px;'><b>Context Menus:</b></p>"
            "<ul>"
            "<li>Right-click on host: Rescan options</li>"
            "<li>Right-click on port: Rescan port</li>"
            "</ul>"
        )
        shortcuts_label.setWordWrap(True)
        shortcuts_label.setTextFormat(Qt.TextFormat.RichText)
        shortcuts_layout.addWidget(shortcuts_label)
        shortcuts_layout.addStretch()
        
        tabs.addTab(shortcuts_widget, "Shortcuts")
        
        # Credits tab
        credits_widget = QWidget()
        credits_layout = QVBoxLayout(credits_widget)
        
        credits_label = QLabel(
            "<h3>Credits</h3>"
            "<p><b>Original Legion:</b><br>"
            "© 2023 Gotham Security<br>"
            "<a href='https://gotham-security.com'>https://gotham-security.com</a></p>"
            "<p><b>Modernized by:</b><br>"
            "Community Contributors</p>"
            "<p><b>Built with:</b></p>"
            "<ul>"
            "<li>Python 3.10+</li>"
            "<li>PyQt6 - GUI Framework</li>"
            "<li>qasync - Async/Await for Qt</li>"
            "<li>nmap - Network Scanner</li>"
            "</ul>"
            "<p><b>License:</b><br>"
            "GNU General Public License v3.0</p>"
        )
        credits_label.setWordWrap(True)
        credits_label.setTextFormat(Qt.TextFormat.RichText)
        credits_label.setOpenExternalLinks(True)
        credits_layout.addWidget(credits_label)
        credits_layout.addStretch()
        
        tabs.addTab(credits_widget, "Credits")
        
        # Version tab
        version_widget = QWidget()
        version_layout = QVBoxLayout(version_widget)
        
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        version_label = QLabel(
            "<h3>Version Information</h3>"
            "<p><b>Legion Version:</b> 2.0.0-alpha5</p>"
            "<p><b>Build:</b> Phase 5 - UI Migration</p>"
            "<p><b>Last Update:</b> 12. November 2025</p>"
            "<br>"
            "<p><b>Using:</b></p>"
            "<ul>"
            f"<li>Python: {python_version}</li>"
            f"<li>Qt Version: {QT_VERSION_STR}</li>"
            "<li>PyQt6</li>"
            "<li>qasync</li>"
            "</ul>"
        )
        version_label.setWordWrap(True)
        version_label.setTextFormat(Qt.TextFormat.RichText)
        version_layout.addWidget(version_label)
        version_layout.addStretch()
        
        tabs.addTab(version_widget, "Version")
        
        # Changelog tab
        changelog_widget = QWidget()
        changelog_layout = QVBoxLayout(changelog_widget)
        
        changelog_text = QPlainTextEdit()
        changelog_text.setReadOnly(True)
        
        # Try to load CHANGELOG.txt from _old directory
        changelog_path = Path(__file__).parent.parent.parent.parent / "_old" / "CHANGELOG.txt"
        if changelog_path.exists():
            try:
                with open(changelog_path, 'r', encoding='utf-8') as f:
                    changelog_text.setPlainText(f.read())
            except Exception as e:
                changelog_text.setPlainText(f"Error loading changelog: {e}")
        else:
            changelog_text.setPlainText(
                "Changelog not available.\n\n"
                "See docs/PHASE*_SUMMARY.md files for detailed change information."
            )
        
        changelog_layout.addWidget(changelog_text)
        tabs.addTab(changelog_widget, "Changelog")
        
        # License tab
        license_widget = QWidget()
        license_layout = QVBoxLayout(license_widget)
        
        license_text = QPlainTextEdit()
        license_text.setReadOnly(True)
        
        # Try to load LICENSE file
        license_path = Path(__file__).parent.parent.parent.parent / "LICENSE"
        if license_path.exists():
            try:
                with open(license_path, 'r', encoding='utf-8') as f:
                    license_text.setPlainText(f.read())
            except Exception as e:
                license_text.setPlainText(f"Error loading license: {e}")
        else:
            license_text.setPlainText(
                "GNU GENERAL PUBLIC LICENSE\n"
                "Version 3, 29 June 2007\n\n"
                "License file not found. Please see:\n"
                "https://www.gnu.org/licenses/gpl-3.0.en.html"
            )
        
        license_layout.addWidget(license_text)
        tabs.addTab(license_widget, "License")
        
        layout.addWidget(tabs)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)


class AddHostDialog(QDialog):
    """
    Dialog for manually adding hosts to scan.
    
    Enhanced version with Easy/Hard mode options:
    - Easy Mode: Quick/Staged scan options with timing control
    - Hard Mode: Detailed nmap options (scan types, ping types, fragmentation)
    - Custom arguments support
    - Validation for input
    
    Migrated from legacy ui/addHostDialog.py with modern improvements.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Host(s) to Scan")
        self.setMinimumWidth(700)
        self.setMinimumHeight(700)
        self.setModal(True)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI with Easy/Hard modes."""
        layout = QVBoxLayout(self)
        
        # Target input section
        target_layout = QHBoxLayout()
        
        target_label = QLabel("IP(s), Range(s), and Host(s)")
        self.target_input = QPlainTextEdit()
        self.target_input.setPlaceholderText(
            "192.168.1.1\n"
            "10.0.0.0/24\n"
            "192.168.1.10-20\n"
            "example.com"
        )
        self.target_input.setMaximumHeight(120)
        
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_input)
        layout.addLayout(target_layout)
        
        # Example label
        example_label = QLabel("Ex: 192.168.1.0/24, 10.10.10.10-20; 1.2.3.4; bing.com (separate with comma, semicolon, or newline)")
        example_label.setFont(QFont("Calibri", 10))
        example_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(example_label)
        
        # Validation label (hidden by default)
        self.validation_label = QLabel("Invalid input. Please try again!")
        self.validation_label.setStyleSheet("QLabel { color: red; }")
        self.validation_label.hide()
        layout.addWidget(self.validation_label)
        
        layout.addSpacing(5)
        
        # Mode selection group
        mode_group = QGroupBox("Mode Selection")
        mode_layout = QHBoxLayout()
        
        self.easy_mode_radio = QRadioButton("Easy")
        self.easy_mode_radio.setToolTip("Easy mode with preset options")
        self.easy_mode_radio.setChecked(True)
        
        self.hard_mode_radio = QRadioButton("Hard")
        self.hard_mode_radio.setToolTip("Hard mode with advanced nmap options")
        
        mode_layout.addWidget(self.easy_mode_radio)
        mode_layout.addWidget(self.hard_mode_radio)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        layout.addSpacing(5)
        
        # Easy mode options
        self.easy_mode_group = QGroupBox("Easy Mode Options")
        easy_layout = QHBoxLayout()
        
        self.discovery_check = QCheckBox("Run nmap host discovery")
        self.discovery_check.setToolTip("Typical host discovery options")
        self.discovery_check.setChecked(True)
        
        self.staged_scan_check = QCheckBox("Run staged nmap scan")
        self.staged_scan_check.setToolTip("Scan ports in stages with typical options")
        self.staged_scan_check.setChecked(True)
        
        easy_layout.addWidget(self.discovery_check)
        easy_layout.addWidget(self.staged_scan_check)
        self.easy_mode_group.setLayout(easy_layout)
        layout.addWidget(self.easy_mode_group)
        
        layout.addSpacing(5)
        
        # Timing and performance options
        timing_group = QGroupBox("Timing and Performance Options")
        timing_vlayout = QVBoxLayout()
        
        # Slider
        self.timing_slider = QSlider(Qt.Orientation.Horizontal)
        self.timing_slider.setRange(0, 5)
        self.timing_slider.setSingleStep(1)
        self.timing_slider.setValue(4)
        self.timing_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        timing_vlayout.addWidget(self.timing_slider)
        
        # Labels
        labels_layout = QHBoxLayout()
        timing_labels = [
            ("Paranoid", "Serialize every scan operation with a 5 minute wait [-T0]"),
            ("Sneaky", "Serialize with a 15 second wait [-T1]"),
            ("Polite", "Serialize with a 0.4 second wait [-T2]"),
            ("Normal", "NMAP defaults including parallelization [-T3]"),
            ("Aggressive", "Fast scan with reduced timeouts [-T4]"),
            ("Insane", "Very fast scan, may sacrifice accuracy [-T5]")
        ]
        
        for text, tooltip in timing_labels:
            label = QLabel(text)
            label.setToolTip(tooltip)
            label.setFont(QFont("Calibri", 8))
            labels_layout.addWidget(label)
        
        timing_vlayout.addLayout(labels_layout)
        timing_group.setLayout(timing_vlayout)
        layout.addWidget(timing_group)
        
        layout.addSpacing(5)
        
        # Hard mode: Port scan options
        self.scan_type_group = QGroupBox("Port Scan Options")
        scan_type_layout = QHBoxLayout()
        
        self.tcp_connect_radio = QRadioButton("TCP")
        self.tcp_connect_radio.setToolTip("TCP connect() scanning [-sT]")
        
        self.obfuscated_radio = QRadioButton("Obfuscated")
        self.obfuscated_radio.setToolTip("Obfuscated scanning for avoiding detection")
        self.obfuscated_radio.setChecked(True)
        
        self.fin_radio = QRadioButton("FIN")
        self.fin_radio.setToolTip("FIN scanning [-sF]")
        
        self.null_radio = QRadioButton("NULL")
        self.null_radio.setToolTip("Null scanning [-sN]")
        
        self.xmas_radio = QRadioButton("Xmas")
        self.xmas_radio.setToolTip("Xmas Tree scanning [-sX]")
        
        self.tcp_ping_radio = QRadioButton("TCP Ping")
        self.tcp_ping_radio.setToolTip("TCP Ping scanning [-sP]")
        
        self.udp_ping_radio = QRadioButton("UDP Ping")
        self.udp_ping_radio.setToolTip("UDP Ping scanning [-sU]")
        
        self.fragmentation_check = QCheckBox("Fragment")
        self.fragmentation_check.setToolTip("Enable packet fragmentation [-f]")
        self.fragmentation_check.setChecked(True)
        
        scan_type_layout.addWidget(self.tcp_connect_radio)
        scan_type_layout.addWidget(self.obfuscated_radio)
        scan_type_layout.addWidget(self.fin_radio)
        scan_type_layout.addWidget(self.null_radio)
        scan_type_layout.addWidget(self.xmas_radio)
        scan_type_layout.addWidget(self.tcp_ping_radio)
        scan_type_layout.addWidget(self.udp_ping_radio)
        scan_type_layout.addWidget(self.fragmentation_check)
        
        self.scan_type_group.setLayout(scan_type_layout)
        self.scan_type_group.setEnabled(False)  # Disabled by default (Easy mode)
        layout.addWidget(self.scan_type_group)
        
        layout.addSpacing(5)
        
        # Hard mode: Host discovery options
        self.ping_type_group = QGroupBox("Host Discovery Options")
        ping_type_layout = QHBoxLayout()
        
        self.ping_disable_radio = QRadioButton("Disable")
        self.ping_disable_radio.setToolTip("Disable Ping entirely [-Pn]")
        self.ping_disable_radio.setChecked(True)
        
        self.ping_default_radio = QRadioButton("Default")
        self.ping_default_radio.setToolTip("ICMP Echo Request and TCP ping [-PB]")
        
        self.ping_icmp_radio = QRadioButton("ICMP")
        self.ping_icmp_radio.setToolTip("Standard ICMP Echo Request [-PE]")
        
        self.ping_syn_radio = QRadioButton("TCP SYN")
        self.ping_syn_radio.setToolTip("TCP Ping with SYN packets [-PS]")
        
        self.ping_ack_radio = QRadioButton("TCP ACK")
        self.ping_ack_radio.setToolTip("TCP Ping with ACK packets [-PT]")
        
        self.ping_timestamp_radio = QRadioButton("Timestamp")
        self.ping_timestamp_radio.setToolTip("ICMP Timestamp Request [-PP]")
        
        self.ping_netmask_radio = QRadioButton("Netmask")
        self.ping_netmask_radio.setToolTip("ICMP Netmask Request [-PM]")
        
        ping_type_layout.addWidget(self.ping_disable_radio)
        ping_type_layout.addWidget(self.ping_default_radio)
        ping_type_layout.addWidget(self.ping_icmp_radio)
        ping_type_layout.addWidget(self.ping_syn_radio)
        ping_type_layout.addWidget(self.ping_ack_radio)
        ping_type_layout.addWidget(self.ping_timestamp_radio)
        ping_type_layout.addWidget(self.ping_netmask_radio)
        
        self.ping_type_group.setLayout(ping_type_layout)
        self.ping_type_group.setEnabled(False)  # Disabled by default (Easy mode)
        layout.addWidget(self.ping_type_group)
        
        layout.addSpacing(5)
        
        # Custom options
        self.custom_group = QGroupBox("Custom Options")
        custom_layout = QHBoxLayout()
        
        custom_label = QLabel("Additional arguments")
        self.custom_args_input = QLineEdit()
        self.custom_args_input.setPlaceholderText("e.g., -sV -O")
        
        custom_layout.addWidget(custom_label)
        custom_layout.addWidget(self.custom_args_input)
        
        self.custom_group.setLayout(custom_layout)
        self.custom_group.setEnabled(False)  # Disabled by default (Easy mode)
        layout.addWidget(self.custom_group)
        
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.submit_button = QPushButton("Submit")
        self.submit_button.setMaximumSize(160, 70)
        self.submit_button.setDefault(True)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMaximumSize(110, 30)
        
        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # Connect signals
        self.easy_mode_radio.toggled.connect(self._on_mode_changed)
        self.hard_mode_radio.toggled.connect(self._on_mode_changed)
        self.submit_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
    
    def _on_mode_changed(self):
        """Handle mode change between Easy and Hard."""
        is_easy = self.easy_mode_radio.isChecked()
        
        # Enable/disable appropriate groups
        self.easy_mode_group.setEnabled(is_easy)
        self.scan_type_group.setEnabled(not is_easy)
        self.ping_type_group.setEnabled(not is_easy)
        self.custom_group.setEnabled(not is_easy)
    
    def validate_input(self) -> bool:
        """
        Validate user input.
        
        Returns:
            True if input is valid, False otherwise
        """
        targets = self.get_targets()
        if not targets:
            self.validation_label.setText("Please enter at least one target!")
            self.validation_label.show()
            return False
        
        self.validation_label.hide()
        return True
    
    def get_targets(self) -> list[str]:
        """
        Get list of targets from input.
        
        Returns:
            List of target strings (cleaned and split)
        """
        text = self.target_input.toPlainText().strip()
        if not text:
            return []
        
        # Split by commas, semicolons or newlines
        targets = []
        # First replace semicolons and commas with newlines for uniform splitting
        text = text.replace(';', '\n').replace(',', '\n')
        
        for line in text.split('\n'):
            line = line.strip()
            if line:
                targets.append(line)
        
        return targets
    
    def is_easy_mode(self) -> bool:
        """Check if Easy mode is selected."""
        return self.easy_mode_radio.isChecked()
    
    def get_scan_options(self) -> dict:
        """
        Get scan options from dialog.
        
        Returns:
            Dictionary with all scan options
        """
        options = {
            "mode": "easy" if self.is_easy_mode() else "hard",
            "timing": str(self.timing_slider.value()),
        }
        
        if self.is_easy_mode():
            # Easy mode options
            options["discovery"] = self.discovery_check.isChecked()
            options["staged_scan"] = self.staged_scan_check.isChecked()
        else:
            # Hard mode options
            options["custom_args"] = self.custom_args_input.text().strip()
            
            # Scan type
            if self.tcp_connect_radio.isChecked():
                options["scan_type"] = "tcp"
            elif self.obfuscated_radio.isChecked():
                options["scan_type"] = "obfuscated"
            elif self.fin_radio.isChecked():
                options["scan_type"] = "fin"
            elif self.null_radio.isChecked():
                options["scan_type"] = "null"
            elif self.xmas_radio.isChecked():
                options["scan_type"] = "xmas"
            elif self.tcp_ping_radio.isChecked():
                options["scan_type"] = "tcp_ping"
            elif self.udp_ping_radio.isChecked():
                options["scan_type"] = "udp_ping"
            
            options["fragmentation"] = self.fragmentation_check.isChecked()
            
            # Ping type
            if self.ping_disable_radio.isChecked():
                options["ping_type"] = "disable"
            elif self.ping_default_radio.isChecked():
                options["ping_type"] = "default"
            elif self.ping_icmp_radio.isChecked():
                options["ping_type"] = "icmp"
            elif self.ping_syn_radio.isChecked():
                options["ping_type"] = "syn"
            elif self.ping_ack_radio.isChecked():
                options["ping_type"] = "ack"
            elif self.ping_timestamp_radio.isChecked():
                options["ping_type"] = "timestamp"
            elif self.ping_netmask_radio.isChecked():
                options["ping_type"] = "netmask"
        
        return options
    
    def accept(self):
        """Override accept to validate input first."""
        if self.validate_input():
            super().accept()


