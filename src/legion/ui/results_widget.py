"""
Results Widget - Shows successful credentials from all attacks.

Displays credentials with:
- Expandable rows (click to expand/collapse)
- Grouped by host:port
- Export functionality
- Copy to clipboard
- Only successful results (no failures)
"""

from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
import logging
import json
import csv

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QLabel, QMenu, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QClipboard, QGuiApplication

logger = logging.getLogger(__name__)


class CredentialResult:
    """A single credential result."""
    
    def __init__(
        self,
        host: str,
        port: int,
        service: str,
        username: str,
        password: str,
        found_at: datetime
    ):
        self.host = host
        self.port = port
        self.service = service
        self.username = username
        self.password = password
        self.found_at = found_at


class ResultsWidget(QWidget):
    """
    Widget displaying successful credentials from all attacks.
    
    Features:
    - Tree view grouped by host:port
    - Expandable rows to show credentials
    - Export to CSV, JSON, TXT
    - Copy to clipboard
    - Only shows successful results
    """
    
    def __init__(self, parent=None):
        """Initialize results widget."""
        super().__init__(parent)
        
        # Storage for credentials: {(host, port, service): [CredentialResult]}
        self.credentials: Dict[tuple, List[CredentialResult]] = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        header_label = QLabel("🎯 Successful Credentials")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Export buttons
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(lambda: self._export("csv"))
        header_layout.addWidget(self.export_csv_btn)
        
        self.export_json_btn = QPushButton("Export JSON")
        self.export_json_btn.clicked.connect(lambda: self._export("json"))
        header_layout.addWidget(self.export_json_btn)
        
        self.export_txt_btn = QPushButton("Export TXT")
        self.export_txt_btn.clicked.connect(lambda: self._export("txt"))
        header_layout.addWidget(self.export_txt_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_all)
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)
        
        # Tree widget (expandable rows)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Target", "Service", "Credentials", "Found At"])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree)
        
        # Stats footer
        self.stats_label = QLabel("No credentials found yet")
        self.stats_label.setStyleSheet("color: gray;")
        layout.addWidget(self.stats_label)
        
        logger.debug("ResultsWidget UI setup complete")
    
    def add_credential(self, cred: CredentialResult) -> None:
        """
        Add a credential to the results.
        
        Args:
            cred: CredentialResult instance
        """
        key = (cred.host, cred.port, cred.service)
        
        # Add to storage
        if key not in self.credentials:
            self.credentials[key] = []
        self.credentials[key].append(cred)
        
        # Update tree incrementally (more efficient than full rebuild)
        self._add_credential_to_tree(cred, key)
        
        logger.info(f"Added credential: {cred.username}@{cred.host}:{cred.port}")
    
    def _add_credential_to_tree(self, cred: CredentialResult, key: tuple) -> None:
        """
        Add a single credential to the tree incrementally.
        
        Args:
            cred: Credential to add
            key: (host, port, service) tuple
        """
        host, port, service = key
        
        # Find or create parent item
        parent = None
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if (item.text(0) == f"{host}:{port}" and 
                item.text(1) == service):
                parent = item
                break
        
        # Create parent if not found
        if not parent:
            parent = QTreeWidgetItem(self.tree)
            parent.setText(0, f"{host}:{port}")
            parent.setText(1, service)
            parent.setText(3, "")
            
            # Style parent (bold, green)
            for col in range(4):
                parent.setForeground(col, QColor("#5cb85c"))
                font = parent.font(col)
                font.setBold(True)
                parent.setFont(col, font)
        
        # Update parent count
        cred_count = len(self.credentials[key])
        parent.setText(2, f"{cred_count} credential{'s' if cred_count != 1 else ''}")
        
        # Add child credential
        child = QTreeWidgetItem(parent)
        child.setText(0, "")
        child.setText(1, "")
        child.setText(2, f"{cred.username}:{cred.password}")
        child.setText(3, cred.found_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Store credential data
        child.setData(0, Qt.ItemDataRole.UserRole, cred)
        
        # Update stats
        self._update_stats()
    
    def add_credentials_bulk(self, credentials: List[CredentialResult]) -> None:
        """
        Add multiple credentials at once.
        
        Args:
            credentials: List of CredentialResult instances
        """
        for cred in credentials:
            key = (cred.host, cred.port, cred.service)
            if key not in self.credentials:
                self.credentials[key] = []
            self.credentials[key].append(cred)
        
        self._rebuild_tree()
        logger.info(f"Added {len(credentials)} credentials in bulk")
    
    def clear_all(self) -> None:
        """Clear all credentials."""
        reply = QMessageBox.question(
            self,
            "Clear All",
            "Are you sure you want to clear all credential results?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.credentials.clear()
            self.tree.clear()
            self._update_stats()
            logger.info("Cleared all credentials")
    
    def get_all_credentials(self) -> List[CredentialResult]:
        """Get all credentials as a flat list."""
        all_creds = []
        for creds in self.credentials.values():
            all_creds.extend(creds)
        return all_creds
    
    def _rebuild_tree(self) -> None:
        """Rebuild the entire tree from scratch."""
        self.tree.clear()
        
        # Group by host:port:service
        for (host, port, service), creds in sorted(self.credentials.items()):
            # Create parent item (collapsed by default)
            parent = QTreeWidgetItem(self.tree)
            parent.setText(0, f"{host}:{port}")
            parent.setText(1, service)
            parent.setText(2, f"{len(creds)} credential{'s' if len(creds) != 1 else ''}")
            parent.setText(3, "")
            
            # Style parent (bold, green)
            for col in range(4):
                parent.setForeground(col, QColor("#5cb85c"))
                font = parent.font(col)
                font.setBold(True)
                parent.setFont(col, font)
            
            # Add children (credentials)
            for cred in creds:
                child = QTreeWidgetItem(parent)
                child.setText(0, "")
                child.setText(1, "")
                child.setText(2, f"{cred.username}:{cred.password}")
                child.setText(3, cred.found_at.strftime("%Y-%m-%d %H:%M:%S"))
                
                # Store credential data
                child.setData(0, Qt.ItemDataRole.UserRole, cred)
        
        self._update_stats()
    
    def _show_context_menu(self, position) -> None:
        """Show context menu for credential items."""
        item = self.tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # Get credential data
        cred = item.data(0, Qt.ItemDataRole.UserRole)
        
        if cred:  # Child item (actual credential)
            copy_user_action = menu.addAction("Copy Username")
            copy_pass_action = menu.addAction("Copy Password")
            copy_both_action = menu.addAction("Copy Username:Password")
            
            action = menu.exec(self.tree.viewport().mapToGlobal(position))
            
            if action == copy_user_action:
                self._copy_to_clipboard(cred.username)
            elif action == copy_pass_action:
                self._copy_to_clipboard(cred.password)
            elif action == copy_both_action:
                self._copy_to_clipboard(f"{cred.username}:{cred.password}")
        
        else:  # Parent item (target)
            expand_action = menu.addAction("Expand All")
            collapse_action = menu.addAction("Collapse All")
            menu.addSeparator()
            copy_all_action = menu.addAction("Copy All Credentials")
            
            action = menu.exec(self.tree.viewport().mapToGlobal(position))
            
            if action == expand_action:
                item.setExpanded(True)
                for i in range(item.childCount()):
                    item.child(i).setExpanded(True)
            elif action == collapse_action:
                item.setExpanded(False)
            elif action == copy_all_action:
                # Copy all credentials under this target
                creds_text = []
                for i in range(item.childCount()):
                    child = item.child(i)
                    cred_data = child.data(0, Qt.ItemDataRole.UserRole)
                    if cred_data:
                        creds_text.append(f"{cred_data.username}:{cred_data.password}")
                self._copy_to_clipboard("\n".join(creds_text))
    
    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        logger.info(f"Copied to clipboard: {text}")
    
    def _export(self, format: str) -> None:
        """
        Export credentials to file.
        
        Args:
            format: Export format (csv, json, txt)
        """
        if not self.credentials:
            QMessageBox.information(self, "Export", "No credentials to export")
            return
        
        # Get all credentials
        all_creds = self.get_all_credentials()
        
        # File dialog
        if format == "csv":
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export CSV", "", "CSV Files (*.csv)"
            )
            if filename:
                self._export_csv(filename, all_creds)
        
        elif format == "json":
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export JSON", "", "JSON Files (*.json)"
            )
            if filename:
                self._export_json(filename, all_creds)
        
        elif format == "txt":
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export TXT", "", "Text Files (*.txt)"
            )
            if filename:
                self._export_txt(filename, all_creds)
    
    def _export_csv(self, filename: str, credentials: List[CredentialResult]) -> None:
        """Export to CSV format."""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Host", "Port", "Service", "Username", "Password", "Found At"])
                for cred in credentials:
                    writer.writerow([
                        cred.host,
                        cred.port,
                        cred.service,
                        cred.username,
                        cred.password,
                        cred.found_at.strftime("%Y-%m-%d %H:%M:%S")
                    ])
            logger.info(f"Exported {len(credentials)} credentials to CSV: {filename}")
            QMessageBox.information(self, "Export", f"Exported {len(credentials)} credentials to {filename}")
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV:\n{e}")
    
    def _export_json(self, filename: str, credentials: List[CredentialResult]) -> None:
        """Export to JSON format."""
        try:
            data = []
            for cred in credentials:
                data.append({
                    "host": cred.host,
                    "port": cred.port,
                    "service": cred.service,
                    "username": cred.username,
                    "password": cred.password,
                    "found_at": cred.found_at.isoformat()
                })
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported {len(credentials)} credentials to JSON: {filename}")
            QMessageBox.information(self, "Export", f"Exported {len(credentials)} credentials to {filename}")
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export JSON:\n{e}")
    
    def _export_txt(self, filename: str, credentials: List[CredentialResult]) -> None:
        """Export to TXT format with full scan information."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Header
                f.write("="*70 + "\n")
                f.write("LEGION HYDRA SCAN RESULTS\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Credentials Found: {len(credentials)}\n")
                f.write("="*70 + "\n\n")
                
                # Group by target
                targets = {}
                for cred in credentials:
                    key = (cred.host, cred.port, cred.service)
                    if key not in targets:
                        targets[key] = []
                    targets[key].append(cred)
                
                # Write each target
                for (host, port, service), creds in sorted(targets.items()):
                    f.write("-"*70 + "\n")
                    f.write(f"Target: {host}:{port}\n")
                    f.write(f"Service: {service}\n")
                    f.write(f"Credentials Found: {len(creds)}\n")
                    f.write("-"*70 + "\n")
                    
                    for cred in creds:
                        f.write(f"  Username: {cred.username}\n")
                        f.write(f"  Password: {cred.password}\n")
                        f.write(f"  Found At: {cred.found_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"  Format: {cred.username}:{cred.password}\n")
                        f.write("\n")
                    
                    f.write("\n")
                
                # Footer with combo format
                f.write("="*70 + "\n")
                f.write("QUICK COPY FORMAT (username:password)\n")
                f.write("="*70 + "\n")
                for cred in credentials:
                    f.write(f"{cred.username}:{cred.password}\n")
            
            logger.info(f"Exported {len(credentials)} credentials to TXT: {filename}")
            QMessageBox.information(self, "Export", f"Exported {len(credentials)} credentials with full details to {filename}")
        except Exception as e:
            logger.error(f"Failed to export TXT: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export TXT:\n{e}")
    
    def _update_stats(self) -> None:
        """Update statistics label."""
        total_targets = len(self.credentials)
        total_creds = sum(len(creds) for creds in self.credentials.values())
        
        if total_creds == 0:
            self.stats_label.setText("No credentials found yet")
        else:
            self.stats_label.setText(
                f"Total: {total_creds} credential{'s' if total_creds != 1 else ''} "
                f"across {total_targets} target{'s' if total_targets != 1 else ''}"
            )
