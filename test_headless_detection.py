#!/usr/bin/env python3
"""
Test script for headless environment detection in stanfordps310_gui_desktop.py
Validates that the application properly detects and handles headless environments.
"""

import sys
import os
import unittest
from unittest.mock import patch

# Import the function we want to test
from stanfordps310_gui_desktop import is_headless_environment


class TestHeadlessDetection(unittest.TestCase):
    """Test cases for headless environment detection."""
    
    def test_headless_when_display_empty_string(self):
        """Test detection when DISPLAY is empty string (Linux/macOS)."""
        with patch.dict(os.environ, {'DISPLAY': ''}, clear=False):
            with patch('sys.platform', 'linux'):
                self.assertTrue(is_headless_environment())
    
    def test_headless_when_display_whitespace(self):
        """Test detection when DISPLAY is only whitespace (Linux/macOS)."""
        with patch.dict(os.environ, {'DISPLAY': '  '}, clear=False):
            with patch('sys.platform', 'linux'):
                self.assertTrue(is_headless_environment())
    
    def test_headless_when_display_unset(self):
        """Test detection when DISPLAY is not set at all (Linux/macOS)."""
        # Remove DISPLAY from environment
        env = {k: v for k, v in os.environ.items() if k != 'DISPLAY'}
        with patch.dict(os.environ, env, clear=True):
            with patch('sys.platform', 'linux'):
                self.assertTrue(is_headless_environment())
    
    def test_not_headless_when_display_set(self):
        """Test detection when DISPLAY is set (Linux/macOS)."""
        with patch.dict(os.environ, {'DISPLAY': ':0'}, clear=False):
            with patch('sys.platform', 'linux'):
                self.assertFalse(is_headless_environment())
    
    def test_explicit_headless_flag(self):
        """Test explicit HEADLESS environment variable."""
        with patch.dict(os.environ, {'HEADLESS': 'true', 'DISPLAY': ':0'}, clear=False):
            with patch('sys.platform', 'linux'):
                self.assertTrue(is_headless_environment())
    
    def test_pywebview_gui_override(self):
        """Test PYWEBVIEW_GUI override flag."""
        with patch.dict(os.environ, {'PYWEBVIEW_GUI': '1', 'DISPLAY': ''}, clear=False):
            with patch('sys.platform', 'linux'):
                self.assertFalse(is_headless_environment())
    
    def test_windows_not_headless_by_default(self):
        """Test that Windows is not considered headless by default."""
        # Clear DISPLAY and HEADLESS from environment
        env = {k: v for k, v in os.environ.items() if k not in ['DISPLAY', 'HEADLESS']}
        with patch.dict(os.environ, env, clear=True):
            with patch('sys.platform', 'win32'):
                self.assertFalse(is_headless_environment())
    
    def test_macos_headless_when_no_display(self):
        """Test macOS detection when DISPLAY is not set."""
        with patch.dict(os.environ, {'DISPLAY': ''}, clear=False):
            with patch('sys.platform', 'darwin'):
                self.assertTrue(is_headless_environment())


def test_main_function_headless_exit():
    """Integration test: Verify main() exits early in headless environment."""
    from stanfordps310_gui_desktop import main
    
    # Clear DISPLAY to simulate headless
    env = os.environ.copy()
    env.pop('DISPLAY', None)
    env.pop('PYWEBVIEW_GUI', None)
    
    with patch.dict(os.environ, env, clear=True):
        with patch('sys.platform', 'linux'):
            result = main()
            # Should return 1 (error) when headless
            assert result == 1, f"Expected return code 1, got {result}"
    
    print("✓ Main function exits properly in headless environment")


if __name__ == '__main__':
    print("=" * 70)
    print("Testing Headless Environment Detection")
    print("=" * 70)
    print()
    
    # Run unit tests
    print("Running unit tests...")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHeadlessDetection)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        print("\n❌ Unit tests failed")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("Running integration test...")
    print("=" * 70)
    print()
    
    try:
        test_main_function_headless_exit()
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)
    print()
