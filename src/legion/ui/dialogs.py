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
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView
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
        
        # Enable/disable options based on scan type
        is_custom = "Custom" in scan_type
        self.port_range.setEnabled(is_custom or "Full" in scan_type)
    
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
    """About Legion dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Legion")
        self.setFixedSize(400, 300)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Legion v2.0")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Network Penetration Testing Tool")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Description
        description = QLabel(
            "Legion is a cross-platform network penetration testing framework "
            "built with Python and PyQt6.\n\n"
            "Features:\n"
            "• Network scanning with nmap\n"
            "• Service enumeration\n"
            "• Automated vulnerability detection\n"
            "• Cross-platform support (Windows & Linux)"
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        layout.addStretch()
        
        # Copyright
        copyright_label = QLabel("© 2025 Gotham Security")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(copyright_label)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
