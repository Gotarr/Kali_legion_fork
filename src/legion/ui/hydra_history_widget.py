"""
Hydra History Widget - Shows all completed Hydra attacks.

Displays attack history with:
- Success/failure status
- Target details
- Duration
- Results summary
- Re-run option
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon

logger = logging.getLogger(__name__)


class AttackRecord:
    """Record of a completed attack."""
    
    def __init__(
        self,
        host: str,
        port: int,
        service: str,
        started: datetime,
        duration: float,
        success: bool,
        credentials_found: int = 0,
        attempts: int = 0,
        command: str = "",
        output: str = ""
    ):
        self.host = host
        self.port = port
        self.service = service
        self.started = started
        self.duration = duration
        self.success = success
        self.credentials_found = credentials_found
        self.attempts = attempts
        self.command = command
        self.output = output


class HydraHistoryWidget(QWidget):
    """
    Widget displaying history of all Hydra attacks.
    
    Features:
    - Table showing all attacks (success + failure)
    - Color-coded status (green=success, red=failure)
    - Click to view details
    - Re-run button for failed attacks
    - Clear history button
    """
    
    # Signal emitted when user wants to re-run an attack
    # Args: (host, port, service)
    rerun_requested = pyqtSignal(str, int, str)
    
    def __init__(self, parent=None):
        """Initialize history widget."""
        super().__init__(parent)
        
        # Storage for attack records
        self.attacks: List[AttackRecord] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        header_label = QLabel("📜 Attack History")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.clicked.connect(self.clear_history)
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)
        
        # History table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Status", "Target", "Service", "Started", "Duration", "Results", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)
        
        # Stats footer
        self.stats_label = QLabel("No attacks yet")
        self.stats_label.setStyleSheet("color: gray;")
        layout.addWidget(self.stats_label)
        
        logger.debug("HydraHistoryWidget UI setup complete")
    
    def add_attack(self, attack: AttackRecord) -> None:
        """
        Add an attack to the history.
        
        Args:
            attack: AttackRecord instance
        """
        self.attacks.append(attack)
        
        # Add to table
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Status
        status_text = "✅ Success" if attack.success else "❌ Failed"
        status_item = QTableWidgetItem(status_text)
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if attack.success:
            status_item.setForeground(QColor("#5cb85c"))  # Green
        else:
            status_item.setForeground(QColor("#d9534f"))  # Red
        self.table.setItem(row, 0, status_item)
        
        # Target
        target_item = QTableWidgetItem(f"{attack.host}:{attack.port}")
        target_item.setFlags(target_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, target_item)
        
        # Service
        service_item = QTableWidgetItem(attack.service)
        service_item.setFlags(service_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 2, service_item)
        
        # Started
        started_item = QTableWidgetItem(attack.started.strftime("%Y-%m-%d %H:%M:%S"))
        started_item.setFlags(started_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        started_item.setData(Qt.ItemDataRole.UserRole, attack.started)  # For sorting
        self.table.setItem(row, 3, started_item)
        
        # Duration
        duration_item = QTableWidgetItem(f"{attack.duration:.1f}s")
        duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        duration_item.setData(Qt.ItemDataRole.UserRole, attack.duration)  # For sorting
        self.table.setItem(row, 4, duration_item)
        
        # Results
        if attack.success:
            results_text = f"{attack.credentials_found} cred{'s' if attack.credentials_found != 1 else ''}"
        else:
            results_text = f"{attack.attempts} attempts"
        results_item = QTableWidgetItem(results_text)
        results_item.setFlags(results_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 5, results_item)
        
        # Actions (Re-run button)
        rerun_btn = QPushButton("Re-run")
        rerun_btn.setToolTip("Re-run this attack with same settings")
        rerun_btn.clicked.connect(lambda: self._on_rerun_clicked(attack))
        self.table.setCellWidget(row, 6, rerun_btn)
        
        self._update_stats()
        logger.info(f"Added attack to history: {attack.host}:{attack.port} ({attack.service}) - {'Success' if attack.success else 'Failed'}")
    
    def clear_history(self) -> None:
        """Clear all attack history."""
        self.table.setRowCount(0)
        self.attacks.clear()
        self._update_stats()
        logger.info("Cleared attack history")
    
    def get_attack_at_row(self, row: int) -> Optional[AttackRecord]:
        """Get attack record at specific row."""
        if 0 <= row < len(self.attacks):
            return self.attacks[row]
        return None
    
    def _on_rerun_clicked(self, attack: AttackRecord) -> None:
        """Handle Re-run button click."""
        logger.info(f"Re-running attack: {attack.host}:{attack.port} ({attack.service})")
        self.rerun_requested.emit(attack.host, attack.port, attack.service)
    
    def _update_stats(self) -> None:
        """Update statistics label."""
        total = len(self.attacks)
        if total == 0:
            self.stats_label.setText("No attacks yet")
            return
        
        successful = sum(1 for a in self.attacks if a.success)
        failed = total - successful
        
        self.stats_label.setText(
            f"Total: {total} attacks | "
            f"✅ {successful} successful | "
            f"❌ {failed} failed"
        )
