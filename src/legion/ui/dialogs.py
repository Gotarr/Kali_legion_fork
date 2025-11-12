"""
UI Dialogs for Legion.

This module provides various dialog windows for user interaction,
including scan configuration, settings, and information displays.
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QTextEdit,
    QPushButton, QLabel, QGroupBox, QDialogButtonBox,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


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
        
        layout.addWidget(tabs)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)


class AddHostDialog(QDialog):
    """
    Dialog for manually adding hosts to scan.
    
    Allows users to add:
    - Single IP addresses
    - IP ranges (CIDR notation)
    - Hostnames
    - Multiple targets (one per line)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Host(s)")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Enter one or more targets to add to the scan.\n"
            "Supports: IP addresses, CIDR ranges, hostnames.\n"
            "One target per line."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Examples
        examples = QLabel(
            "Examples:\n"
            "• 192.168.1.1\n"
            "• 192.168.1.0/24\n"
            "• 10.0.0.1-10\n"
            "• example.com"
        )
        examples.setStyleSheet("font-family: monospace; font-size: 9pt; color: #666; margin-bottom: 10px;")
        layout.addWidget(examples)
        
        # Target input
        target_label = QLabel("Targets:")
        target_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(target_label)
        
        self.target_input = QTextEdit()
        self.target_input.setPlaceholderText(
            "192.168.1.1\n"
            "10.0.0.0/24\n"
            "example.com"
        )
        self.target_input.setAcceptRichText(False)
        layout.addWidget(self.target_input)
        
        # Scan options
        options_group = QGroupBox("Scan Options")
        options_layout = QVBoxLayout()
        
        self.quick_scan = QCheckBox("Start quick scan immediately")
        self.quick_scan.setChecked(True)
        self.quick_scan.setToolTip("Start a quick scan (-F) after adding hosts")
        options_layout.addWidget(self.quick_scan)
        
        self.service_detection = QCheckBox("Enable service detection (-sV)")
        self.service_detection.setToolTip("Detect service versions on open ports")
        options_layout.addWidget(self.service_detection)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_targets(self) -> list[str]:
        """
        Get list of targets from input.
        
        Returns:
            List of target strings (one per line, stripped)
        """
        text = self.target_input.toPlainText().strip()
        if not text:
            return []
        
        # Split by lines, strip whitespace, remove empty lines
        targets = [line.strip() for line in text.split('\n')]
        return [t for t in targets if t]
    
    def should_scan(self) -> bool:
        """Check if quick scan should be started."""
        return self.quick_scan.isChecked()
    
    def get_scan_options(self) -> dict:
        """
        Get scan options from dialog.
        
        Returns:
            Dictionary with scan options
        """
        options = {
            "timing": "4",  # Aggressive timing
        }
        
        if self.service_detection.isChecked():
            options["version_detection"] = True
        
        return options

