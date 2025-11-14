"""
Brute Force attack widget with live output display.

Similar to legacy Legion's BruteWidget, this provides:
- Live command output streaming
- Run/Stop button toggle
- Attack statistics
- Results highlighting
"""

from pathlib import Path
from typing import Optional
import logging

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt, pyqtSignal

logger = logging.getLogger(__name__)


class BruteWidget(QtWidgets.QWidget):
    """
    Widget for displaying a single Hydra brute force attack.
    
    Features:
    - Live output display (like legacy)
    - Run/Stop button
    - Attack parameters display
    - Credential highlighting
    
    Signals:
        attack_started: Emitted when attack starts
        attack_stopped: Emitted when attack is stopped/cancelled
        attack_finished: Emitted when attack completes
        credentials_found: Emitted when credentials are discovered (username, password)
        edit_config: Emitted when user wants to edit attack configuration
    """
    
    attack_started = pyqtSignal()
    attack_stopped = pyqtSignal()
    attack_finished = pyqtSignal()
    credentials_found = pyqtSignal(str, str)  # username, password
    edit_config = pyqtSignal()  # Request config edit
    
    def __init__(
        self,
        host_ip: str,
        port: int,
        service: str,
        wordlist_path: str,
        parent: Optional[QtWidgets.QWidget] = None
    ):
        """
        Initialize brute widget.
        
        Args:
            host_ip: Target IP address
            port: Target port
            service: Service type (ssh, ftp, http-get, etc.)
            wordlist_path: Path to wordlist directory/file
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.host_ip = host_ip
        self.port = port
        self.service = service
        self.wordlist_path = wordlist_path
        self.is_running = False
        self.is_finished = False
        self.process_id = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup widget UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Top panel: Attack info and controls
        top_panel = QtWidgets.QWidget()
        top_layout = QtWidgets.QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Attack info
        info_label = QtWidgets.QLabel(
            f"<b>Target:</b> {self.service}://{self.host_ip}:{self.port} | "
            f"<b>Wordlist:</b> {Path(self.wordlist_path).name}"
        )
        top_layout.addWidget(info_label)
        
        top_layout.addStretch()
        
        # Run/Stop button
        self.run_button = QtWidgets.QPushButton("Run")
        self.run_button.setMinimumWidth(80)
        self.run_button.clicked.connect(self._on_run_stop_clicked)
        top_layout.addWidget(self.run_button)
        
        layout.addWidget(top_panel)
        
        # Output display (like legacy: QPlainTextEdit)
        self.output_display = QtWidgets.QPlainTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Apply dark background for output (like legacy)
        self.output_display.setStyleSheet(
            "QPlainTextEdit {"
            "  background-color: #1e1e1e;"
            "  color: #d4d4d4;"
            "  font-family: 'Consolas', 'Courier New', monospace;"
            "  font-size: 10pt;"
            "}"
        )
        
        layout.addWidget(self.output_display)
        
        # Bottom panel: Statistics
        self.stats_label = QtWidgets.QLabel("Status: Ready")
        self.stats_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.stats_label)
    
    def _on_run_stop_clicked(self) -> None:
        """Handle Run/Stop button click."""
        if self.is_running:
            # Stop attack
            self.attack_stopped.emit()
        elif self.is_finished:
            # Edit finished attack configuration
            self.edit_config.emit()
        else:
            # Start attack
            self.attack_started.emit()
    
    def set_running(self, running: bool) -> None:
        """
        Set running state and update UI.
        
        Args:
            running: True if attack is running
        """
        self.is_running = running
        
        if running:
            self.run_button.setText("Stop")
            self.run_button.setStyleSheet("background-color: #d9534f; color: white;")
            self.stats_label.setText("Status: Running...")
        else:
            self.run_button.setText("Run")
            self.run_button.setStyleSheet("")
            if "Stopped" not in self.stats_label.text():
                self.stats_label.setText("Status: Ready")
    
    def append_output(self, text: str) -> None:
        """
        Append text to output display (thread-safe).
        
        Args:
            text: Text to append
        """
        cursor = self.output_display.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        
        # Highlight credentials in green
        if "login:" in text.lower() or "password:" in text.lower():
            # Found credentials - use green color
            cursor.insertHtml(
                f'<span style="color: #4ec9b0; font-weight: bold;">{text}</span><br>'
            )
        elif "ERROR" in text or "error" in text:
            # Error - use red color
            cursor.insertHtml(
                f'<span style="color: #f48771;">{text}</span><br>'
            )
        else:
            # Normal output
            cursor.insertText(text + "\n")
        
        # Auto-scroll to bottom
        scrollbar = self.output_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def set_stats(self, stats: str) -> None:
        """
        Update statistics label.
        
        Args:
            stats: Statistics text
        """
        self.stats_label.setText(f"Status: {stats}")
    
    def mark_finished(self, success: bool = True) -> None:
        """
        Mark attack as finished.
        
        Args:
            success: Whether attack completed successfully
        """
        self.set_running(False)
        self.is_finished = True
        
        # Change button to Edit mode
        self.run_button.setText("Edit")
        self.run_button.setStyleSheet("background-color: #5bc0de; color: white;")  # Blue
        
        if success:
            self.stats_label.setText("Status: ✅ Completed")
            self.stats_label.setStyleSheet(
                "padding: 5px; background-color: #d4edda; color: #155724;"
            )
        else:
            self.stats_label.setText("Status: ❌ Stopped")
            self.stats_label.setStyleSheet(
                "padding: 5px; background-color: #f8d7da; color: #721c24;"
            )
        
        self.attack_finished.emit()
    
    def get_output_text(self) -> str:
        """
        Get all output text.
        
        Returns:
            Complete output as plain text
        """
        return self.output_display.toPlainText()
