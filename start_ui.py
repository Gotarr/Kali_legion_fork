"""
Quick start script to launch Legion UI.

This demonstrates the new MainWindow with Phase 1-4 integration.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
from legion.ui import MainWindow
from legion.config import init_user_config

def main():
    """Launch Legion UI."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Legion...")
    
    # Initialize config (creates default if not exists)
    config_manager = init_user_config()
    logger.info(f"Config loaded: {config_manager.config_path}")
    
    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Legion")
    app.setOrganizationName("GothamSecurity")
    
    # Create and show main window
    window = MainWindow(config_manager=config_manager)
    window.show()
    
    logger.info("Legion UI started successfully")
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
