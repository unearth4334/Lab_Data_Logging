"""
UV/OV Lockout Hysteresis Test Package
======================================

Automated test for measuring under-voltage and over-voltage lockout hysteresis.
"""

__version__ = "1.0.0"

from .test import run_lockout_test

__all__ = ["run_lockout_test"]
