"""A2A Registry - Protocol buffer definitions and Python client for A2A message registry."""

__version__ = "0.1.2"
__author__ = "Allen Day"
__email__ = "allenday@users.github.com"

# A2A Protocol version this registry supports
A2A_PROTOCOL_VERSION = "0.3.0"

# Version info for programmatic access
VERSION = __version__
VERSION_INFO = tuple(int(x) for x in __version__.split("."))

# Package metadata
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "A2A_PROTOCOL_VERSION",
    "VERSION",
    "VERSION_INFO",
]
