#!/usr/bin/env python3
"""
LEGION v2.0 (https://gotham-security.com)
Copyright (c) 2023 Gotham Security

Cross-platform network penetration testing framework.
This is the main entry point for the new modular architecture.

Usage:
    python legion.py

For the legacy UI, see: legacy/legion_old.py

This program is free software: you can redistribute it and/or modify it under 
the terms of the GNU General Public License as published by the Free Software 
Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY 
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A 
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with 
this program. If not, see <http://www.gnu.org/licenses/>.

Author: Gotham Security
Date: 2025-11-12
Version: 2.0.0-alpha5
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run new UI
from legion.ui.app import main

if __name__ == "__main__":
    sys.exit(main())
