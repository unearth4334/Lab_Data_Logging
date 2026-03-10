"""CSV to BIN.GZ Converter - Desktop Application Package

Electron-based desktop application for converting CSV files to binary .bin.gz format
with JSON metadata support.
"""

__version__ = "1.0.0"
__author__ = "Lab Automation Team"
__license__ = "Apache License 2.0"

from .launcher import launch_app
from .nodejs_manager import get_node, NODE_VERSION, CACHE_DIR

__all__ = ["launch_app", "get_node", "NODE_VERSION", "CACHE_DIR", "__version__"]
