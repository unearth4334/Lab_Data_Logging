#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MSOX4154A Oscilloscope Ethernet Connection Test Script
======================================================

This script tests the MSOX4154A driver's enhanced Ethernet connectivity capabilities,
demonstrating various connection methods and basic instrument operations.

USAGE
-----
The script supports multiple connection modes:

1. **Auto-connect (USB/Ethernet auto-detection)**:
   ```bash
   python test_msox4154a_ethernet.py
   ```
   Automatically searches for MSOX4154A on any available interface (USB or Ethernet)

2. **Connect via IP address**:
   ```bash
   python test_msox4154a_ethernet.py --ip 192.168.1.100
   ```
   Connects to MSOX4154A at the specified IP address via Ethernet/LAN
   (Find IP on device: Utility > I/O > LAN)

3. **Connect via explicit VISA address**:
   ```bash
   # USB connection
   python test_msox4154a_ethernet.py --address "USB0::0x0957::0x17BC::MY59241237::INSTR"
   
   # Ethernet connection
   python test_msox4154a_ethernet.py --address "TCPIP0::192.168.1.100::inst0::INSTR"
   ```
   Connects using a specific VISA resource string

4. **Interactive mode**:
   ```bash
   python test_msox4154a_ethernet.py --interactive
   ```
   Prompts for connection method and parameters

COMMAND LINE OPTIONS
--------------------
  --ip IP_ADDRESS          IP address for ethernet connection (e.g., 192.168.1.100)
  --address VISA_ADDRESS   Full VISA resource string (USB or TCPIP)
  --interactive, -i        Interactive mode - prompts for connection details
  --debug                  Enable debug output (shows VISA resource scanning details)
  --skip-screenshot        Skip the screenshot capture test
  --skip-waveform          Skip the waveform capture test
  --help, -h               Show this help message

EXAMPLES
--------

Example 1: Quick test with auto-detection
```bash
python test_msox4154a_ethernet.py
```

Example 2: Connect to specific IP (as shown on MSOX4154A LAN settings)
```bash
python test_msox4154a_ethernet.py --ip 192.168.1.100
```

Example 3: Use the exact VISA string
```bash
python test_msox4154a_ethernet.py --address "TCPIP0::192.168.1.100::inst0::INSTR"
```

Example 4: Connect via USB with explicit address
```bash
python test_msox4154a_ethernet.py --address "USB0::0x0957::0x17BC::MY59241237::INSTR"
```

Example 5: Interactive mode for manual configuration
```bash
python test_msox4154a_ethernet.py --interactive
```

Example 6: Debug mode to see resource scanning
```bash
python test_msox4154a_ethernet.py --debug
```

NETWORK CONFIGURATION
---------------------
**Finding the MSOX4154A IP Address:**

1. On the MSOX4154A front panel, press **Utility** > **I/O** > **LAN**
2. The LAN configuration screen displays network information:
   ```
   Configuration: DHCP (or Auto IP or Manual)
   IP Address: xxx.xxx.xxx.xxx          <-- Use this IP address
   Subnet Mask: xxx.xxx.xxx.xxx
   Default Gateway: xxx.xxx.xxx.xxx
   ```

3. **Note the IP Address shown** (e.g., 192.168.1.100)
   - Use this with: `python test_msox4154a_ethernet.py --ip 192.168.1.100`
   - Or in code: `KeysightMSOX4154A(ip_address="192.168.1.100")`

**Configuring Network Settings:**

If the MSOX4154A doesn't have an IP address or you need to change it:
1. Press **Utility** > **I/O** > **LAN** > **LAN Config**
2. Select configuration mode:
   - **Auto IP**: Uses link-local address (169.254.x.x)
   - **DHCP**: Automatically obtains IP from network
   - **Manual**: Set static IP address manually
3. If using Manual mode, configure:
   - IP Address
   - Subnet Mask
   - Default Gateway (if needed)
4. Apply settings

**Network Requirements:**
- MSOX4154A must be connected via Ethernet cable
- Computer and MSOX4154A should be on the same network
- Firewall should allow LXI/SCPI communication (typically port 5025)
- For link-local (Auto IP), enable IPv4 Link-Local on your computer

TROUBLESHOOTING
---------------
**Connection Issues:**

1. **Find the actual IP address on the device:**
   - Press Utility > I/O > LAN
   - Look for "IP Address" line (e.g., 192.168.1.100 or 169.254.x.x)

2. **Test network connectivity:**
   ```bash
   ping 192.168.1.100  # Replace with your MSOX4154A IP
   ```

3. **Verify VISA resources are visible:**
   ```bash
   python -c "import pyvisa; rm = pyvisa.ResourceManager(); print(rm.list_resources())"
   ```
   Should show something like: `TCPIP0::192.168.1.100::inst0::INSTR`

4. **Check network settings:**
   - For corporate networks, use DHCP mode or consult IT for static IP configuration
   - Verify Ethernet cable is properly connected (check link lights)
   - For Auto IP (169.254.x.x), ensure computer can reach link-local addresses

For USB connections:
1. Ensure USB cable is connected
2. Check that VISA drivers are installed (Keysight IO Libraries or NI-VISA)
3. List available resources: `python -c "import pyvisa; print(pyvisa.ResourceManager().list_resources())"`

REQUIREMENTS
------------
- Python 3.7+
- pyvisa >= 1.11.0
- colorama >= 0.4.6
- Keysight IO Libraries or NI-VISA

Install dependencies:
```bash
pip install pyvisa colorama
```

ABOUT
-----
Author: Lab Data Logging Project
Date: February 2026
License: Apache 2.0
"""

import argparse
import sys
import time
import os
import tempfile
from typing import Optional

try:
    from libs.KeysightMSOX4154A import KeysightMSOX4154A
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError as e:
    print(f"Error: Missing required module: {e}")
    print("Please install dependencies: pip install pyvisa colorama")
    sys.exit(1)


# --- Console formatting ---
_SUCCESS = Fore.GREEN + Style.BRIGHT
_ERROR = Fore.RED + Style.BRIGHT
_WARNING = Fore.YELLOW + Style.BRIGHT
_INFO = Fore.CYAN
_RESET = Style.RESET_ALL


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"{_INFO}{title}{_RESET}")
    print("=" * 70)


def print_test(description: str):
    """Print a test description."""
    print(f"\n{_INFO}>>> {description}...{_RESET}")


def print_success(message: str):
    """Print a success message."""
    print(f"{_SUCCESS}✓ {message}{_RESET}")


def print_error(message: str):
    """Print an error message."""
    print(f"{_ERROR}✗ {message}{_RESET}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{_WARNING}⚠ {message}{_RESET}")


def test_identity_query(scope: KeysightMSOX4154A) -> bool:
    """Test instrument identification query."""
    print_header("Identity Query Test")
    
    try:
        print_test("Querying instrument identification")
        identity = scope.get_idn()
        print_success(f"Instrument Identity: {identity}")
        
        # Verify it's the correct model
        if "MSOX4154A" in identity or "MSO-X 4154A" in identity:
            print_success("Confirmed MSOX4154A model")
        else:
            print_warning(f"Unexpected model in identity string")
        
        return True
        
    except Exception as e:
        print_error(f"Identity query failed: {e}")
        return False


def test_screenshot(scope: KeysightMSOX4154A) -> bool:
    """Test screenshot capture functionality."""
    print_header("Screenshot Capture Test")
    
    try:
        # Create temporary file for screenshot
        temp_fd, temp_path = tempfile.mkstemp(suffix='.png', prefix='msox4154a_screenshot_')
        os.close(temp_fd)
        
        print_test("Capturing oscilloscope screenshot")
        success = scope.save_screenshot(temp_path)
        
        if success and os.path.exists(temp_path):
            file_size = os.path.getsize(temp_path)
            print_success(f"Screenshot captured successfully ({file_size} bytes)")
            print(f"  File saved: {temp_path}")
            
            # Optionally delete the temp file
            try:
                os.remove(temp_path)
                print("  (Temporary file cleaned up)")
            except:
                pass
        else:
            print_error("Screenshot capture failed")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Screenshot test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_waveform_capture(scope: KeysightMSOX4154A) -> bool:
    """Test waveform capture functionality."""
    print_header("Waveform Capture Test")
    
    try:
        # Test capturing from channel 1
        print_test("Capturing waveform from Channel 1")
        time_data, voltage_data, metadata = scope.get_waveform(source="CHAN1")
        
        print_success(f"Captured {len(time_data)} data points")
        print(f"  Time range: {time_data[0]:.9f} to {time_data[-1]:.9f} seconds")
        print(f"  Voltage range: {min(voltage_data):.6f} to {max(voltage_data):.6f} V")
        
        # Display metadata
        if 'x_increment' in metadata:
            sample_rate = 1.0 / metadata['x_increment']
            print(f"  Sample rate: {sample_rate/1e6:.3f} MS/s")
        
        if 'vpp' in metadata:
            print(f"  Peak-to-peak: {metadata['vpp']:.6f} V")
        
        if 'mean' in metadata:
            print(f"  Mean voltage: {metadata['mean']:.6f} V")
        
        return True
        
    except Exception as e:
        print_error(f"Waveform capture failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_connection_methods(args) -> bool:
    """Test various connection methods based on command line arguments."""
    print_header("MSOX4154A Connection Test")
    
    scope = None
    
    try:
        # Test the specified connection method
        if args.ip:
            print_test(f"Connecting via IP address: {args.ip}")
            scope = KeysightMSOX4154A(ip_address=args.ip, debug=args.debug)
        elif args.address:
            print_test(f"Connecting via explicit address: {args.address}")
            scope = KeysightMSOX4154A(address=args.address, debug=args.debug)
        else:
            print_test("Searching for MSOX4154A (auto-connect)")
            scope = KeysightMSOX4154A(debug=args.debug)
        
        print_success(f"Successfully connected to MSOX4154A")
        print(f"  Address: {scope.address}")
        print(f"  Status: {scope.status}")
        
        # Run identity query test
        if not test_identity_query(scope):
            return False
        
        # Run screenshot test (unless skipped)
        if not args.skip_screenshot:
            if not test_screenshot(scope):
                print_warning("Screenshot test failed (this is optional)")
        else:
            print_warning("Skipping screenshot test (--skip-screenshot)")
        
        # Run waveform capture test (unless skipped)
        if not args.skip_waveform:
            if not test_waveform_capture(scope):
                print_warning("Waveform capture test failed (this is optional)")
        else:
            print_warning("Skipping waveform capture test (--skip-waveform)")
        
        return True
        
    except ConnectionError as e:
        print_error(f"Connection failed: {e}")
        print_warning("Troubleshooting tips:")
        print("  1. Check that MSOX4154A is powered on")
        print("  2. Verify USB cable connection (if using USB)")
        print("  3. Check network connectivity: ping [IP_ADDRESS]")
        print("  4. Verify VISA drivers are installed (Keysight IO Libraries)")
        print("  5. List resources: python -c \"import pyvisa; print(pyvisa.ResourceManager().list_resources())\"")
        print("  6. Check IP address: Utility > I/O > LAN on the MSOX4154A")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if scope:
            print_test("Disconnecting from MSOX4154A")
            scope.disconnect()
            print_success("Disconnected successfully")


def interactive_mode() -> argparse.Namespace:
    """Interactive mode - prompt user for connection details."""
    print_header("MSOX4154A Interactive Connection Mode")
    
    print("\nSelect connection method:")
    print("  1. Auto-connect (search USB and Ethernet)")
    print("  2. Connect via IP address")
    print("  3. Connect via explicit VISA address")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    args = argparse.Namespace()
    args.debug = False
    args.ip = None
    args.address = None
    args.skip_screenshot = False
    args.skip_waveform = False
    
    if choice == "1":
        print("\nUsing auto-connect mode...")
        enable_debug = input("Enable debug output? (y/n): ").strip().lower()
        args.debug = (enable_debug == 'y')
    elif choice == "2":
        ip = input("\nEnter IP address (e.g., 192.168.1.100): ").strip()
        args.ip = ip
        enable_debug = input("Enable debug output? (y/n): ").strip().lower()
        args.debug = (enable_debug == 'y')
    elif choice == "3":
        address = input("\nEnter VISA address (e.g., USB0::0x0957::...::INSTR): ").strip()
        args.address = address
        enable_debug = input("Enable debug output? (y/n): ").strip().lower()
        args.debug = (enable_debug == 'y')
    else:
        print_error("Invalid choice. Using auto-connect mode.")
    
    return args


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test Keysight MSOX4154A Oscilloscope Ethernet connectivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_msox4154a_ethernet.py                              # Auto-connect
  python test_msox4154a_ethernet.py --ip 192.168.1.100          # Connect via IP
  python test_msox4154a_ethernet.py --address "TCPIP0::192.168.1.100::inst0::INSTR"  # Explicit address
  python test_msox4154a_ethernet.py --interactive                # Interactive mode
  python test_msox4154a_ethernet.py --debug                      # Debug mode
        """
    )
    
    parser.add_argument('--ip', type=str, help='IP address for Ethernet connection')
    parser.add_argument('--address', type=str, help='Explicit VISA resource address')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug output (shows resource scanning)')
    parser.add_argument('--skip-screenshot', action='store_true',
                       help='Skip screenshot capture test')
    parser.add_argument('--skip-waveform', action='store_true',
                       help='Skip waveform capture test')
    
    args = parser.parse_args()
    
    # Handle interactive mode
    if args.interactive:
        args = interactive_mode()
    
    # Run connection tests
    print_header("Keysight MSOX4154A Oscilloscope Ethernet Test Suite")
    print(f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    success = test_connection_methods(args)
    
    # Print summary
    print_header("Test Summary")
    if success:
        print_success("All tests passed successfully!")
        print("\nNext steps:")
        print("  - Use the KeysightMSOX4154A class with ip_address parameter in your scripts")
        print("  - Integrate with data_logger for automated data collection")
        print("  - Refer to libs/KeysightMSOX4154A.py docstring for usage examples")
        return 0
    else:
        print_error("Some tests failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
