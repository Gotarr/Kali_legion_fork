"""
Qt Table Models for Legion data.

Provides QAbstractTableModel implementations for:
- Hosts
- Ports/Services
- Scan jobs

These models bridge between legion.core.database and PyQt6 views.
"""

from typing import Optional, Any, List
from datetime import datetime

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt6.QtGui import QColor

from legion.core.database import SimpleDatabase
from legion.core.models import Host, Port


class HostsTableModel(QAbstractTableModel):
    """
    Table model for displaying hosts from SimpleDatabase.
    
    Columns: IP, Hostname, OS, State, Ports, Last Seen
    """
    
    # Column definitions
    COL_IP = 0
    COL_HOSTNAME = 1
    COL_OS = 2
    COL_STATE = 3
    COL_PORTS = 4
    COL_LAST_SEEN = 5
    
    HEADERS = ["IP Address", "Hostname", "Operating System", "State", "Open Ports", "Last Seen"]
    
    def __init__(self, database: SimpleDatabase, parent: Optional[Any] = None):
        """
        Initialize hosts table model.
        
        Args:
            database: SimpleDatabase instance
            parent: Parent QObject
        """
        super().__init__(parent)
        self.database = database
        self._hosts: List[Host] = []
        self.refresh()
    
    def refresh(self) -> None:
        """Reload hosts from database."""
        self.beginResetModel()
        self._hosts = self.database.get_all_hosts()
        self.endResetModel()
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of rows."""
        if parent.isValid():
            return 0
        return len(self._hosts)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of columns."""
        if parent.isValid():
            return 0
        return len(self.HEADERS)
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Get data for index and role.
        
        Args:
            index: Model index
            role: Data role
            
        Returns:
            Data for the given index and role
        """
        if not index.isValid() or not (0 <= index.row() < len(self._hosts)):
            return QVariant()
        
        host = self._hosts[index.row()]
        col = index.column()
        
        # Display role
        if role == Qt.ItemDataRole.DisplayRole:
            if col == self.COL_IP:
                return host.ip
            elif col == self.COL_HOSTNAME:
                return host.hostname or ""
            elif col == self.COL_OS:
                if host.os_name:
                    accuracy = f" ({host.os_accuracy}%)" if host.os_accuracy else ""
                    return f"{host.os_name}{accuracy}"
                return ""
            elif col == self.COL_STATE:
                return host.state or "unknown"
            elif col == self.COL_PORTS:
                # Count open ports for this host
                ports = self.database.get_ports(host.ip)
                open_count = sum(1 for p in ports if p.state == "open")
                return str(open_count)
            elif col == self.COL_LAST_SEEN:
                if host.last_seen:
                    # Format datetime nicely
                    if isinstance(host.last_seen, str):
                        return host.last_seen
                    return host.last_seen.strftime("%Y-%m-%d %H:%M:%S")
                return ""
        
        # Background color role (color-code by state)
        elif role == Qt.ItemDataRole.BackgroundRole:
            if host.state == "up":
                return QColor(200, 255, 200)  # Light green
            elif host.state == "down":
                return QColor(255, 200, 200)  # Light red
        
        # Tooltip role
        elif role == Qt.ItemDataRole.ToolTipRole:
            tooltip = f"IP: {host.ip}\n"
            if host.hostname:
                tooltip += f"Hostname: {host.hostname}\n"
            if host.mac_address:
                tooltip += f"MAC: {host.mac_address}\n"
            if host.vendor:
                tooltip += f"Vendor: {host.vendor}\n"
            if host.os_name:
                tooltip += f"OS: {host.os_name}"
                if host.os_accuracy:
                    tooltip += f" ({host.os_accuracy}%)"
            return tooltip
        
        return QVariant()
    
    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        """
        Get header data.
        
        Args:
            section: Column/row number
            orientation: Horizontal or vertical
            role: Data role
            
        Returns:
            Header data
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self.HEADERS):
                    return self.HEADERS[section]
            else:
                return str(section + 1)
        return QVariant()
    
    def get_host(self, row: int) -> Optional[Host]:
        """
        Get host at given row.
        
        Args:
            row: Row number
            
        Returns:
            Host object or None
        """
        if 0 <= row < len(self._hosts):
            return self._hosts[row]
        return None


class PortsTableModel(QAbstractTableModel):
    """
    Table model for displaying ports/services.
    
    Columns: Port, Protocol, State, Service, Version
    """
    
    # Column definitions
    COL_PORT = 0
    COL_PROTOCOL = 1
    COL_STATE = 2
    COL_SERVICE = 3
    COL_VERSION = 4
    COL_STATUS = 5
    
    HEADERS = ["Port", "Protocol", "State", "Service", "Version", "Status"]
    
    def __init__(self, database: SimpleDatabase, parent: Optional[Any] = None):
        """
        Initialize ports table model.
        
        Args:
            database: SimpleDatabase instance
            parent: Parent QObject
        """
        super().__init__(parent)
        self.database = database
        self._ports: List[Port] = []
        self._current_host: Optional[str] = None
    
    def set_host(self, host_ip: str) -> None:
        """
        Set current host to display ports for.
        
        Args:
            host_ip: IP address of host
        """
        self.beginResetModel()
        self._current_host = host_ip
        self._ports = self.database.get_ports(host_ip)
        self.endResetModel()
    
    def clear(self) -> None:
        """Clear the model."""
        self.beginResetModel()
        self._current_host = None
        self._ports = []
        self.endResetModel()
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of rows."""
        if parent.isValid():
            return 0
        return len(self._ports)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of columns."""
        if parent.isValid():
            return 0
        return len(self.HEADERS)
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Get data for index and role.
        
        Args:
            index: Model index
            role: Data role
            
        Returns:
            Data for the given index and role
        """
        if not index.isValid() or not (0 <= index.row() < len(self._ports)):
            return QVariant()
        
        port = self._ports[index.row()]
        col = index.column()
        
        # Display role
        if role == Qt.ItemDataRole.DisplayRole:
            if col == self.COL_PORT:
                return str(port.number)
            elif col == self.COL_PROTOCOL:
                return port.protocol or ""
            elif col == self.COL_STATE:
                return port.state or ""
            elif col == self.COL_SERVICE:
                return port.service_name or ""
            elif col == self.COL_VERSION:
                # Combine product and version
                parts = []
                if port.service_product:
                    parts.append(port.service_product)
                if port.service_version:
                    parts.append(port.service_version)
                return " ".join(parts)
            elif col == self.COL_STATUS:
                # Show status change with icon and text
                change = port.status_change
                labels = {
                    "new_open": f"{port.status_icon} Newly Opened",
                    "new_closed": f"{port.status_icon} Newly Closed",
                    "still_open": f"{port.status_icon} Still Open",
                    "still_closed": f"{port.status_icon} Still Closed",
                    "none": f"{port.status_icon} First Seen"
                }
                return labels.get(change, "")
        
        # Background color role (color-code by status change)
        elif role == Qt.ItemDataRole.BackgroundRole:
            change = port.status_change
            
            # Priority: Status change colors override state colors
            if change == "new_open":
                return QColor(144, 238, 144)  # Light green - newly opened!
            elif change == "new_closed":
                return QColor(255, 160, 160)  # Light red - newly closed!
            elif change == "still_open":
                return QColor(230, 255, 230)  # Very light green - stable open
            elif port.state == "open":
                return QColor(200, 255, 200)  # Light green - open (no history)
            elif port.state == "closed":
                return QColor(255, 200, 200)  # Light red
            elif port.state == "filtered":
                return QColor(255, 255, 200)  # Light yellow
        
        # Tooltip role
        elif role == Qt.ItemDataRole.ToolTipRole:
            tooltip = f"Port: {port.number}/{port.protocol}\n"
            tooltip += f"State: {port.state}\n"
            
            # Status change info
            if port.previous_state:
                tooltip += f"Previous State: {port.previous_state}\n"
                tooltip += f"Status: {port.status_change.replace('_', ' ').title()}\n"
            
            # Timestamps
            if port.discovered_at:
                tooltip += f"First Seen: {port.discovered_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            if port.last_seen:
                tooltip += f"Last Seen: {port.last_seen.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Service info
            if port.service_name:
                tooltip += f"Service: {port.service_name}\n"
            if port.service_product:
                tooltip += f"Product: {port.service_product}"
                if port.service_version:
                    tooltip += f" {port.service_version}"
            return tooltip
        
        return QVariant()
    
    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        """
        Get header data.
        
        Args:
            section: Column/row number
            orientation: Horizontal or vertical
            role: Data role
            
        Returns:
            Header data
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self.HEADERS):
                    return self.HEADERS[section]
            else:
                return str(section + 1)
        return QVariant()
    
    def get_port(self, row: int) -> Optional[Port]:
        """
        Get port at given row.
        
        Args:
            row: Row number
            
        Returns:
            Port object or None
        """
        if 0 <= row < len(self._ports):
            return self._ports[row]
        return None


# Demo/Test
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QTableView, QVBoxLayout, QWidget
    from legion.core.database import SimpleDatabase
    from legion.core.models import Host, Port
    
    print("Legion Table Models Test")
    print("=" * 60)
    
    # Create test database
    db = SimpleDatabase(project_name="test_models")
    
    # Add test data
    host1 = Host(ip="192.168.1.1", hostname="router.local", state="up", os_name="Linux 3.x")
    host2 = Host(ip="192.168.1.100", hostname="workstation", state="up", os_name="Windows 10")
    
    db.save_host(host1)
    db.save_host(host2)
    
    port1 = Port(number=22, protocol="tcp", state="open", service_name="ssh", service_product="OpenSSH")
    port2 = Port(number=80, protocol="tcp", state="open", service_name="http", service_product="Apache")
    
    db.save_port("192.168.1.1", port1)
    db.save_port("192.168.1.1", port2)
    
    print(f"Created test database with {len(db.get_all_hosts())} hosts")
    
    # Create Qt app
    app = QApplication(sys.argv)
    
    # Create window with table views
    window = QWidget()
    layout = QVBoxLayout(window)
    
    # Hosts table
    hosts_view = QTableView()
    hosts_model = HostsTableModel(db)
    hosts_view.setModel(hosts_model)
    hosts_view.resizeColumnsToContents()
    layout.addWidget(hosts_view)
    
    # Ports table
    ports_view = QTableView()
    ports_model = PortsTableModel(db)
    ports_model.set_host("192.168.1.1")
    ports_view.setModel(ports_model)
    ports_view.resizeColumnsToContents()
    layout.addWidget(ports_view)
    
    window.setWindowTitle("Legion Table Models Test")
    window.resize(800, 600)
    window.show()
    
    print("\n[OK] Models created and displayed")
    print(f"Hosts model: {hosts_model.rowCount()} rows, {hosts_model.columnCount()} columns")
    print(f"Ports model: {ports_model.rowCount()} rows, {ports_model.columnCount()} columns")
    
    sys.exit(app.exec())
