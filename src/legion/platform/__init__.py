"""Platform abstraction layer for Legion."""

from legion.platform.detector import (
    PlatformInfo,
    detect_platform,
    get_platform_info,
    get_platform_name,
)

__all__ = [
    "PlatformInfo",
    "detect_platform",
    "get_platform_info",
    "get_platform_name",
]
