"""
Legion - Cross-Platform Penetration Testing Framework

A semi-automated network penetration testing framework that aids in discovery,
reconnaissance, and exploitation of information systems.

Version: 2.0.0 (Cross-Platform Redesign)
License: GPL-3.0-or-later
"""

__version__ = "2.0.0-alpha1"
__author__ = "GoVanguard, Gotham Security"
__license__ = "GPL-3.0-or-later"

from legion.platform.detector import detect_platform, PlatformInfo

# Expose key components at package level
__all__ = [
    "__version__",
    "detect_platform",
    "PlatformInfo",
]
