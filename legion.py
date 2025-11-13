#!/usr/bin/env python3
"""
LEGION v2.0 - Cross-Platform Network Penetration Testing Framework
Copyright (c) 2023 Gotham Security
Copyright (c) 2025 GoVanguard (https://github.com/GoVanguard/legion)

This is a fork with cross-platform migration and modernization efforts.

Usage:
    python legion.py

For the legacy UI, see: _old/

This program is free software: you can redistribute it and/or modify it under 
the terms of the GNU General Public License as published by the Free Software 
Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY 
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A 
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with 
this program. If not, see <http://www.gnu.org/licenses/>.

ORIGINAL AUTHORS:
- GoVanguard (https://govanguard.com) - Legion v1.x development
- SECFORCE - Original Sparta codebase

CONTRIBUTORS:
- Gotarr (https://github.com/Gotarr) - v2.0 Cross-Platform Migration
  (Phase 1-6: Platform abstraction, Tool discovery, Core logic, Configuration,
   UI Migration, Additional tools integration)

DISCLAIMER:
Contributors to this fork provide modifications "AS IS" without warranty of any kind.
All contributors disclaim any liability for damages resulting from the use of this software.
See LICENSE file for full terms.

Version: 2.0.0-alpha6
Date: 2025-11-13
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
