"""
Test for Settings Dialog.

Usage:
    py test_settings_dialog.py

Tests:
- Config UI rendering
- Theme switching
- Tool path browsing
- Apply/Save/Reset functionality

Author: Gotham Security
Date: 2025-11-12
"""

import sys
import logging
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from PyQt6.QtWidgets import QApplication

from legion.config.manager import ConfigManager
from legion.ui.settings import SettingsDialog

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run settings dialog test."""
    logger.info("Starting Settings Dialog test")
    
    app = QApplication(sys.argv)
    
    # Initialize config manager
    config_manager = ConfigManager()
    config = config_manager.load()
    
    logger.info(f"Loaded config from: {config_manager.config_path}")
    logger.info(f"Current theme: {config.ui.theme}")
    logger.info(f"Current font size: {config.ui.font_size}")
    
    # Create dialog
    dialog = SettingsDialog(config_manager)
    
    # Connect signals
    def on_settings_changed():
        logger.info("Settings changed!")
        new_config = config_manager.load()
        logger.info(f"New theme: {new_config.ui.theme}")
        logger.info(f"New font size: {new_config.ui.font_size}")
    
    dialog.settings_changed.connect(on_settings_changed)
    
    # Show dialog
    result = dialog.exec()
    
    if result:
        logger.info("Dialog accepted (Save)")
    else:
        logger.info("Dialog rejected (Cancel)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
