"""
THC-Hydra brute-force authentication tool integration.

This package provides wrapper and parser for Hydra, supporting 50+ protocols
for password cracking and credential discovery.

Author: Gotham Security
Date: 2025-11-13
"""

from .tool import HydraTool
from .parser import HydraOutputParser, HydraResult, HydraCredential, HydraStatistics

__all__ = [
    "HydraTool",
    "HydraOutputParser",
    "HydraResult",
    "HydraCredential",
    "HydraStatistics",
]

