"""
Hydra Services Widget - Displays Nmap scan results for Hydra attacks.

Shows all discovered services from Nmap scans in a table with:
- Checkboxes for multi-select
- Import from Nmap button
- Attack Selected button
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QCheckBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)


class HydraServicesWidget(QWidget):
    """
    Widget displaying available services from Nmap scans for Hydra attacks.
    
    Features:
    - Table with Host, Port, Service, State columns
    - Checkboxes for selection
    - Import from Nmap button
    - Attack Selected button
    - Auto-updates when new scans complete
    """
    
    # Signal emitted when user wants to attack selected services
    # Args: List of (host, port, service) tuples
    attack_requested = pyqtSignal(list)
    
    def __init__(self, parent=None):
        """Initialize services widget."""
        super().__init__(parent)
        
        # Storage for services: {(host, port, service): state}
        self.services: Dict[Tuple[str, int, str], str] = {}
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with buttons
        header_layout = QHBoxLayout()
        
        header_label = QLabel("📊 Available Services (from Nmap)")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Buttons
        self.import_btn = QPushButton("Import from Nmap")
        self.import_btn.setToolTip("Import selected services from Hosts tab")
        self.import_btn.clicked.connect(self._on_import_clicked)
        header_layout.addWidget(self.import_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setToolTip("Refresh service list")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(self.refresh_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear all services")
        self.clear_btn.clicked.connect(self.clear_services)
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)
        
        # Services table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["☑", "Host", "Port", "Service", "State"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)
        
        # Footer with attack button
        footer_layout = QHBoxLayout()
        
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.stateChanged.connect(self._on_select_all_changed)
        footer_layout.addWidget(self.select_all_cb)
        
        self.count_label = QLabel("0 services")
        footer_layout.addWidget(self.count_label)
        
        footer_layout.addStretch()
        
        self.attack_btn = QPushButton("Attack Selected")
        self.attack_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.attack_btn.setEnabled(False)
        self.attack_btn.clicked.connect(self._on_attack_clicked)
        footer_layout.addWidget(self.attack_btn)
        
        layout.addLayout(footer_layout)
        
        logger.debug("HydraServicesWidget UI setup complete")
    
    def add_service(self, host: str, port: int, service: str, state: str = "open") -> None:
        """
        Add a service to the table.
        
        Args:
            host: Host IP/hostname
            port: Port number
            service: Service name
            state: Port state (open, closed, filtered)
        """
        # Only add open ports
        if state != "open":
            logger.debug(f"Skipping non-open port {host}:{port} ({state})")
            return
        
        # Check if already exists
        key = (host, port, service)
        if key in self.services:
            logger.debug(f"Service {host}:{port} ({service}) already in list")
            return
        
        # Add to storage
        self.services[key] = state
        
        # Add to table
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Checkbox
        checkbox = QCheckBox()
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, 0, checkbox_widget)
        checkbox.stateChanged.connect(self._on_checkbox_changed)
        
        # Host
        host_item = QTableWidgetItem(host)
        host_item.setFlags(host_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, host_item)
        
        # Port
        port_item = QTableWidgetItem(str(port))
        port_item.setFlags(port_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        port_item.setData(Qt.ItemDataRole.UserRole, port)  # Store as int for sorting
        self.table.setItem(row, 2, port_item)
        
        # Service
        service_item = QTableWidgetItem(service)
        service_item.setFlags(service_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 3, service_item)
        
        # State
        state_item = QTableWidgetItem(state)
        state_item.setFlags(state_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if state == "open":
            state_item.setForeground(QColor("#5cb85c"))  # Green
        elif state == "closed":
            state_item.setForeground(QColor("#d9534f"))  # Red
        else:
            state_item.setForeground(QColor("#f0ad4e"))  # Orange
        self.table.setItem(row, 4, state_item)
        
        self._update_count()
        logger.info(f"Added service: {host}:{port} ({service})")
    
    def add_services_bulk(self, services: List[Tuple[str, int, str, str]]) -> None:
        """
        Add multiple services at once.
        
        Args:
            services: List of (host, port, service, state) tuples
        """
        for host, port, service, state in services:
            self.add_service(host, port, service, state)
    
    def get_selected_services(self) -> List[Tuple[str, int, str]]:
        """
        Get list of selected services.
        
        Returns:
            List of (host, port, service) tuples
        """
        selected = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    host = self.table.item(row, 1).text()
                    port = self.table.item(row, 2).data(Qt.ItemDataRole.UserRole)
                    service = self.table.item(row, 3).text()
                    selected.append((host, port, service))
        
        return selected
    
    def clear_services(self) -> None:
        """Clear all services from the table."""
        self.table.setRowCount(0)
        self.services.clear()
        self._update_count()
        logger.info("Cleared all services")
    
    def _on_import_clicked(self) -> None:
        """Handle Import from Nmap button click."""
        # This will be connected to MainWindow method
        logger.debug("Import from Nmap clicked (to be implemented in MainWindow)")
    
    def _on_refresh_clicked(self) -> None:
        """Handle Refresh button click."""
        # This will be connected to MainWindow method
        logger.debug("Refresh clicked (to be implemented in MainWindow)")
    
    def _on_attack_clicked(self) -> None:
        """Handle Attack Selected button click."""
        selected = self.get_selected_services()
        if selected:
            logger.info(f"Attacking {len(selected)} services")
            self.attack_requested.emit(selected)
        else:
            logger.warning("No services selected for attack")
    
    def _on_checkbox_changed(self, state) -> None:
        """Handle checkbox state change."""
        selected_count = len(self.get_selected_services())
        self.attack_btn.setEnabled(selected_count > 0)
        
        # Update Select All checkbox
        if selected_count == 0:
            self.select_all_cb.setCheckState(Qt.CheckState.Unchecked)
        elif selected_count == self.table.rowCount():
            self.select_all_cb.setCheckState(Qt.CheckState.Checked)
        else:
            self.select_all_cb.setCheckState(Qt.CheckState.PartiallyChecked)
    
    def _on_select_all_changed(self, state) -> None:
        """Handle Select All checkbox change."""
        checked = state == Qt.CheckState.Checked.value
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(checked)
    
    def _update_count(self) -> None:
        """Update service count label."""
        count = self.table.rowCount()
        self.count_label.setText(f"{count} service{'s' if count != 1 else ''}")
