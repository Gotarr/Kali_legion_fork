"""
Legion UI Application Entry Point.

This module provides the main application startup for the new Legion UI.
Integrates qasync for Qt + asyncio compatibility.

Author: Gotham Security
Date: 2025-11-12
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import qasync
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from legion.config.manager import ConfigManager
from legion.platform.paths import get_data_dir
from legion.core.database import SimpleDatabase
from legion.core.scanner import ScanManager
from legion.ui.mainwindow import MainWindow

logger = logging.getLogger(__name__)


class LegionApplication:
    """
    Main Legion application class.
    
    Handles:
    - Config loading
    - Database initialization
    - Scanner setup with qasync
    - UI initialization
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize Legion application.
        
        Args:
            config_path: Optional path to config file
        """
        self.config_path = config_path
        self.config: Optional[ConfigManager] = None
        self.database: Optional[SimpleDatabase] = None
        self.scanner: Optional[ScanManager] = None
        self.app: Optional[QApplication] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.main_window: Optional[MainWindow] = None
    
    def initialize(self) -> None:
        """Initialize all application components."""
        logger.info("Initializing Legion application...")
        
        # 1. Load configuration
        logger.info("Loading configuration...")
        self.config = ConfigManager(self.config_path)
        config = self.config.load()
        
        # 2. Initialize database
        logger.info("Initializing database...")
        db_path = get_data_dir() / "legion.db"
        self.database = SimpleDatabase(db_path)
        
        # 3. Create scanner
        logger.info("Creating scanner...")
        self.scanner = ScanManager(database=self.database)
        
        # 4. Create Qt application
        logger.info("Creating Qt application...")
        self.app = QApplication(sys.argv)
        
        # 5. Setup qasync event loop (CRITICAL for asyncio + Qt!)
        logger.info("Setting up qasync event loop...")
        self.loop = qasync.QEventLoop(self.app)
        asyncio.set_event_loop(self.loop)
        
        # 6. Set application metadata
        self.app.setApplicationName("Legion")
        self.app.setOrganizationName("Gotham Security")
        self.app.setOrganizationDomain("gotham-security.com")
        
        # 7. Set application icon
        icon_path = Path(__file__).parent.parent.parent.parent / "images" / "icons" / "Legion-N_128x128.svg"
        if icon_path.exists():
            self.app.setWindowIcon(QIcon(str(icon_path)))
        
        logger.info("Application components initialized")
    
    async def start_async_components(self) -> None:
        """Start async components (scanner workers)."""
        logger.info("Scanner ready (workers will start on first scan)")
        # Don't start workers yet - they'll start when first scan is queued
        # This prevents the "NoneType has no attribute 'create_future'" errors
        # await self.scanner.start()
        pass
    
    def create_main_window(self) -> None:
        """Create and show main window."""
        logger.info("Creating main window...")
        self.main_window = MainWindow(
            database=self.database,
            scanner=self.scanner,
            config_manager=self.config
        )
        self.main_window.show()
        logger.info("Main window created and shown")
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Exit code
        """
        try:
            # Initialize all components
            self.initialize()
            
            # Start async components
            self.loop.run_until_complete(self.start_async_components())
            
            # Create UI
            self.create_main_window()
            
            # Run event loop
            logger.info("Starting event loop...")
            with self.loop:
                return self.loop.run_forever()
                
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            return 0
        except Exception as e:
            logger.exception(f"Application error: {e}")
            return 1
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up application resources...")
        
        if self.scanner:
            # Stop scanner workers if needed
            pass
        
        if self.database:
            # Close database connections
            pass
        
        logger.info("Cleanup complete")


def main(config_path: Optional[Path] = None) -> int:
    """
    Main entry point for Legion UI.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Exit code
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run application
    app = LegionApplication(config_path)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
