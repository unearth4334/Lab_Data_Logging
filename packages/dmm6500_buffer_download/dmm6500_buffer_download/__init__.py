"""
DMM6500 Buffer Download Tool
============================

Command-line tool and Python API for downloading buffer data from
Keithley DMM6500 digital multimeters.
"""

__version__ = "1.0.0"

from .download import download_buffer, calculate_statistics

__all__ = ["download_buffer", "calculate_statistics"]
