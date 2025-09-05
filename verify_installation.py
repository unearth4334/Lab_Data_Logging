#!/usr/bin/env python3
"""
Verify that all required dependencies for Lab Data Logging are correctly installed.
Run this script after installing requirements.txt to ensure everything is working.

Usage: python3 verify_installation.py
"""

def verify_dependencies():
    """Verify that all required dependencies are available and working."""
    print("Lab Data Logging - Dependency Verification")
    print("=" * 45)
    
    all_good = True
    
    # Test colorama
    try:
        import colorama
        colorama.init()
        print(colorama.Fore.GREEN + "✓ colorama" + colorama.Style.RESET_ALL + f" ({colorama.__version__})")
    except ImportError:
        print("✗ colorama - NOT INSTALLED")
        all_good = False
    except Exception as e:
        print(f"✗ colorama - ERROR: {e}")
        all_good = False
    
    # Test pyvisa
    try:
        import pyvisa
        print(f"✓ pyvisa ({pyvisa.__version__})")
        # Note: We don't test ResourceManager creation as it may fail without VISA backend
    except ImportError:
        print("✗ pyvisa - NOT INSTALLED")
        all_good = False
    except Exception as e:
        print(f"✗ pyvisa - ERROR: {e}")
        all_good = False
    
    # Test numpy
    try:
        import numpy
        print(f"✓ numpy ({numpy.__version__})")
    except ImportError:
        print("✗ numpy - NOT INSTALLED")
        all_good = False
    except Exception as e:
        print(f"✗ numpy - ERROR: {e}")
        all_good = False
    
    # Test pyserial
    try:
        import serial
        print(f"✓ pyserial ({serial.__version__})")
    except ImportError:
        print("✗ pyserial - NOT INSTALLED")
        all_good = False
    except Exception as e:
        print(f"✗ pyserial - ERROR: {e}")
        all_good = False
    
    print("=" * 45)
    
    if all_good:
        print("✓ All dependencies are correctly installed!")
        print("You can now use the Lab Data Logging library.")
    else:
        print("✗ Some dependencies are missing or have errors.")
        print("Please run: pip install -r requirements.txt")
        
    return all_good

if __name__ == "__main__":
    import sys
    success = verify_dependencies()
    sys.exit(0 if success else 1)