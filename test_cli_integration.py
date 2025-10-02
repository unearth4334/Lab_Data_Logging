#!/usr/bin/env python3
"""
Integration Tests for Lab Data Logging CLI API

This script tests the CLI functionality without requiring actual hardware.
"""

import subprocess
import sys
import os
import tempfile
from pathlib import Path

def run_cli_command(cmd):
    """Run a CLI command and return result."""
    full_cmd = [".venv/Scripts/python.exe", "lab_cli.py"] + cmd
    print(f"Running: {' '.join(full_cmd)}")
    
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        return result
    except Exception as e:
        print(f"Error running command: {e}")
        return None

def test_help_commands():
    """Test help commands."""
    print("Testing help commands...")
    
    # Test main help
    result = run_cli_command(["--help"])
    if result and result.returncode == 0:
        print("OK: Main help command works")
    else:
        print("FAIL: Main help command failed")
        return False
    
    # Test subcommand help
    for cmd in ["run-test", "list-results", "generate-report", "validate-config"]:
        result = run_cli_command([cmd, "--help"])
        if result and result.returncode == 0:
            print(f"OK: {cmd} help works")
        else:
            print(f"FAIL: {cmd} help failed")
            return False
    
    return True

def test_validate_config():
    """Test configuration validation."""
    print("\nTesting configuration validation...")
    
    # Test valid configuration
    result = run_cli_command(["validate-config", "example_config.yml"])
    if result and result.returncode == 0:
        print("OK: Valid configuration validation works")
    else:
        print("FAIL: Valid configuration validation failed")
        if result:
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
        return False
    
    # Test invalid configuration file
    result = run_cli_command(["validate-config", "nonexistent_config.yml"])
    if result and result.returncode != 0:
        print("OK: Invalid configuration properly detected")
    else:
        print("FAIL: Invalid configuration not properly detected")
        return False
    
    return True

def test_list_results():
    """Test listing results."""
    print("\nTesting list results...")
    
    result = run_cli_command(["list-results"])
    if result and result.returncode == 0:
        print("OK: List results works")
        if "Found" in result.stdout:
            print("OK: Results found and displayed")
        else:
            print("OK: No results found (expected)")
    else:
        print("FAIL: List results failed")
        if result:
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
        return False
    
    return True

def test_config_file_operations():
    """Test configuration file operations."""
    print("\nTesting configuration file operations...")
    
    # Create a temporary config file
    temp_config = {
        "visa_address": "TEST::ADDRESS",
        "destination": "./test_output",
        "board_number": "TEST",
        "label": "ConfigTest",
        "channels": {
            "CH1": True,
            "CH2": False,
            "CH3": False,
            "CH4": False,
            "M1": False
        },
        "capture_types": {
            "measurements": True,
            "waveforms": False,
            "screenshot": False,
            "config": False,
            "html_report": False
        },
        "auto_timestamp": True,
        "timestamp_format": "YYYYMMDD_HHMMSS"
    }
    
    # Write temp config
    import yaml
    temp_file = "temp_test_config.yml"
    try:
        with open(temp_file, 'w') as f:
            yaml.dump(temp_config, f)
        
        # Validate the temp config
        result = run_cli_command(["validate-config", temp_file])
        if result and result.returncode == 0:
            print("OK: Temporary configuration validation works")
        else:
            print("FAIL: Temporary configuration validation failed")
            return False
            
    except Exception as e:
        print(f"✗ Error creating temporary configuration: {e}")
        return False
    finally:
        # Clean up
        if Path(temp_file).exists():
            Path(temp_file).unlink()
    
    return True

def test_command_line_overrides():
    """Test command line parameter parsing."""
    print("\nTesting command line parameter parsing...")
    
    # This tests the argument parsing without actually running a test
    # We'll use a dry-run approach by checking if the help systems work
    
    # Test run-test with various parameters (help only)
    result = run_cli_command(["run-test", "--help"])
    if result and result.returncode == 0 and "--channels" in result.stdout:
        print("OK: Command line parameter parsing structure is correct")
    else:
        print("FAIL: Command line parameter parsing structure failed")
        return False
    
    return True

def main():
    """Run all integration tests."""
    print("Lab Data Logging CLI API - Integration Tests")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("lab_cli.py").exists():
        print("Error: lab_cli.py not found. Please run from the correct directory.")
        return 1
    
    # Check if virtual environment exists
    if not Path(".venv/Scripts/python.exe").exists():
        print("Error: Virtual environment not found. Please ensure .venv is set up.")
        return 1
    
    tests = [
        test_help_commands,
        test_validate_config,
        test_list_results,
        test_config_file_operations,
        test_command_line_overrides
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print(f"\n" + "=" * 50)
    print(f"Integration Test Results:")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\nSUCCESS: All integration tests passed!")
        print("The CLI API is working correctly.")
        return 0
    else:
        print(f"\nERROR: {failed} test(s) failed.")
        print("Please check the CLI implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())