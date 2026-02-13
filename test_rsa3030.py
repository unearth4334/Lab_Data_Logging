#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSA3030 Spectrum Analyzer Connection Test Script
================================================

This script tests the RSA3030 driver's Ethernet and USB connectivity capabilities,
demonstrating various connection methods and basic instrument queries.

USAGE
-----
The script supports multiple connection modes:

1. **Auto-connect (USB/Ethernet auto-detection)**:
   ```bash
   python test_rsa3030.py
   ```
   Automatically searches for RSA3030 on any available interface (USB or Ethernet)

2. **Connect via IP address**:
   ```bash
   python test_rsa3030.py --ip 192.168.1.100
   ```
   Connects to RSA3030 at the specified IP address via Ethernet/LAN
   (Find IP on device: System > Interface > LAN)

3. **Connect via explicit VISA address**:
   ```bash
   # USB connection
   python test_rsa3030.py --address "USB0::0x1AB1::0x0960::RSA3XXXXXXXX::INSTR"
   
   # Ethernet connection
   python test_rsa3030.py --address "TCPIP0::192.168.1.100::INSTR"
   ```
   Connects using a specific VISA resource string

4. **Interactive mode**:
   ```bash
   python test_rsa3030.py --interactive
   ```
   Prompts for connection method and parameters

5. **TCPIP Auto-connect test**:
   ```bash
   python test_rsa3030.py --tcpip-autoconnect
   ```
   Tests the TCPIP auto-connect feature (scans all TCPIP and USB resources)

COMMAND LINE OPTIONS
--------------------
  --ip IP_ADDRESS          IP address for ethernet connection (e.g., 192.168.1.100)
  --address VISA_ADDRESS   Full VISA resource string (USB or TCPIP)
  --interactive, -i        Interactive mode - prompts for connection details
  --tcpip-autoconnect      Test TCPIP auto-connect (scans all TCPIP resources)
  --debug                  Enable debug output (shows VISA resource scanning details)
  --skip-spectrogram       Skip the spectrogram capture test
  --center-freq FREQUENCY  Center frequency for spectrum capture (e.g., 10E6 or 1E9) [default: 1E9]
  --span SPAN              Frequency span for spectrum capture (e.g., 10E6 or 100E6) [default: 100E6]
  --help, -h               Show this help message

EXAMPLES
--------

Example 1: Quick test with auto-detection
```bash
python test_rsa3030.py
```

Example 2: Connect to specific IP (as shown on RSA3030 LAN settings)
```bash
python test_rsa3030.py --ip 192.168.1.100
```

Example 3: Use the exact VISA string from RSA3030 display
```bash
python test_rsa3030.py --address "TCPIP0::192.168.1.100::INSTR"
```

Example 4: Connect via USB with explicit address
```bash
python test_rsa3030.py --address "USB0::0x1AB1::0x0960::RSA3XXXXXXXX::INSTR"
```

Example 5: Interactive mode for manual configuration
```bash
python test_rsa3030.py --interactive
```

Example 6: Test TCPIP auto-connect feature
```bash
python test_rsa3030.py --tcpip-autoconnect
```

Example 7: Debug TCPIP auto-connect (see what resources are being scanned)
```bash
python test_rsa3030.py --tcpip-autoconnect --debug
```

NETWORK CONFIGURATION
---------------------
**Finding the RSA3030 IP Address:**

1. On the RSA3030 front panel, press **System** or **Menu**
2. Navigate to: **Interface > LAN**
3. The LAN settings screen displays network information:
   ```
   Config: DHCP (or Static)
   IP Address: xxx.xxx.xxx.xxx          <-- Use this IP address
   Subnet Mask: xxx.xxx.xxx.xxx
   Gateway: xxx.xxx.xxx.xxx
   ```

4. **Note the IP Address shown** (e.g., 192.168.1.100)
   - Use this with: `python test_rsa3030.py --ip 192.168.1.100`
   - Or in code: `RSA3030(ip_address="192.168.1.100")`

**Configuring Network Settings:**

If the RSA3030 doesn't have an IP address or you need to change it:
1. Press **System** > **Interface > LAN**
2. Select **Config Mode**:
   - **DHCP**: Automatically obtains IP from network
   - **Static**: Set static IP address manually
3. If using Static mode, configure:
   - IP Address
   - Subnet Mask
   - Gateway (if needed)
4. Apply settings and restart if necessary

**Network Requirements:**
- RSA3030 must be connected via Ethernet cable
- Computer and RSA3030 should be on the same network
- Firewall should allow VISA/LXI communication (typically port 5025)

TROUBLESHOOTING
---------------
**Connection Issues:**

1. **Find the actual IP address on the device:**
   - Press System > Interface > LAN
   - Look for "IP Address" line (e.g., 192.168.1.100)

2. **Test network connectivity:**
   ```bash
   ping 192.168.1.100  # Replace with your RSA3030 IP
   ```

3. **Verify VISA resources are visible:**
   ```bash
   python -c "import pyvisa; rm = pyvisa.ResourceManager(); print(rm.list_resources())"
   ```
   Should show something like: `TCPIP0::192.168.1.100::INSTR`

4. **Check network settings:**
   - For corporate networks, use DHCP mode or consult IT for static IP configuration
   - Verify Ethernet cable is properly connected (check link lights)

For USB connections:
1. Ensure USB cable is connected
2. Check that VISA drivers are installed (NI-VISA or similar)
3. List available resources: `python -c "import pyvisa; print(pyvisa.ResourceManager().list_resources())"`

REQUIREMENTS
------------
- Python 3.7+
- pyvisa >= 1.11.0
- colorama >= 0.4.6
- NI-VISA or compatible VISA backend

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
from typing import Optional

try:
    from libs.RSA3030 import RSA3030
    from libs.loading import loading
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


def test_identity_query(rsa: RSA3030) -> bool:
    """Test instrument identification query."""
    print_header("Identity Query Test")
    
    try:
        # Test direct identity query
        print_test("Querying instrument identification")
        identity = rsa.get_identity()
        print_success(f"Instrument Identity: {identity}")
        
        # Test generic get() method
        print_test("Testing generic get('identity') method")
        identity2 = rsa.get("identity")
        print_success(f"Identity (via get): {identity2}")
        
        # Verify both methods return the same result
        if identity == identity2:
            print_success("Both methods returned consistent results")
        else:
            print_warning("Methods returned different results (unexpected)")
        
        return True
        
    except Exception as e:
        print_error(f"Identity query failed: {e}")
        return False


def test_spectrogram_capture(rsa: RSA3030, center_freq: float = 1e9, span: float = 100e6) -> bool:
    """Test spectrogram capture functionality.
    
    Args:
        rsa: RSA3030 instance
        center_freq: Center frequency in Hz (default: 1 GHz)
        span: Frequency span in Hz (default: 100 MHz)
    """
    print_header("Spectrogram Capture Test")
    
    try:
        # Test configuration
        print_test("Configuring spectrum analyzer")
        rsa.configure_spectrum(
            center_freq=center_freq,
            span=span,
            rbw=10e3,           # 10 kHz
            vbw=10e3            # 10 kHz
        )
        print_success("Spectrum analyzer configured")
        
        # Test trace capture
        print_test("Capturing trace data")
        freqs, amps = rsa.capture_trace(trace_number=1)
        print_success(f"Captured {len(freqs)} data points")
        
        # Display some statistics
        if amps:
            max_amp = max(amps)
            min_amp = min(amps)
            avg_amp = sum(amps) / len(amps)
            max_freq = freqs[amps.index(max_amp)] if freqs else 0
            
            print(f"  Frequency range: {freqs[0]/1e9:.3f} - {freqs[-1]/1e9:.3f} GHz")
            print(f"  Peak amplitude: {max_amp:.2f} dBm at {max_freq/1e9:.3f} GHz")
            print(f"  Min amplitude: {min_amp:.2f} dBm")
            print(f"  Avg amplitude: {avg_amp:.2f} dBm")
        
        # Test spectrogram capture with file save
        print_test("Capturing spectrogram and saving to file")
        import tempfile
        import os
        
        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.csv', prefix='rsa3030_spectrum_')
        os.close(temp_fd)
        
        data = rsa.capture_spectrogram(filename=temp_path)
        print_success(f"Spectrogram captured and saved")
        print(f"  Center frequency: {data['center_freq']/1e9:.3f} GHz")
        print(f"  Span: {data['span']/1e6:.1f} MHz")
        print(f"  Resolution BW: {data['rbw']/1e3:.1f} kHz")
        print(f"  Video BW: {data['vbw']/1e3:.1f} kHz")
        print(f"  Data points: {data['points']}")
        print(f"  File saved: {temp_path}")
        
        # Verify file exists and has content
        if os.path.exists(temp_path):
            file_size = os.path.getsize(temp_path)
            print_success(f"File verified ({file_size} bytes)")
            # Clean up temp file
            os.remove(temp_path)
        else:
            print_warning("File was not created")
        
        return True
        
    except Exception as e:
        print_error(f"Spectrogram capture failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_connection_methods(args) -> bool:
    """Test various connection methods based on command line arguments."""
    print_header("RSA3030 Connection Test")
    
    rsa = None
    loader = loading()
    
    try:
        # Test the specified connection method
        if args.ip:
            print_test(f"Connecting via IP address: {args.ip}")
            rsa = RSA3030(ip_address=args.ip, debug=args.debug)
        elif args.address:
            print_test(f"Connecting via explicit address: {args.address}")
            rsa = RSA3030(address=args.address, debug=args.debug)
        elif args.tcpip_autoconnect:
            print_test("Searching for RSA3030 (TCPIP auto-discovery)")
            if not args.debug:
                loader.start_spinner("Searching for connection")
            try:
                rsa = RSA3030(debug=args.debug)
            finally:
                if not args.debug:
                    loader.stop_spinner()
        else:
            print_test("Searching for RSA3030 (auto-connect)")
            if not args.debug:
                loader.start_spinner("Searching for connection")
            try:
                rsa = RSA3030(debug=args.debug)
            finally:
                if not args.debug:
                    loader.stop_spinner()
        
        print_success(f"Successfully connected to RSA3030")
        print(f"  Address: {rsa.address}")
        print(f"  Status: {rsa.status}")
        
        # Run identity query test
        if not test_identity_query(rsa):
            return False
        
        # Test direct SCPI query
        print_test("Testing direct SCPI query")
        idn_direct = rsa.instrument.query("*IDN?").strip()
        print_success(f"Direct *IDN? query: {idn_direct}")
        
        # Run spectrogram capture test (unless skipped)
        if not args.skip_spectrogram:
            if not test_spectrogram_capture(rsa, args.center_freq, args.span):
                print_warning("Spectrogram capture test failed (this is optional)")
        else:
            print_warning("Skipping spectrogram capture test (--skip-spectrogram)")
        
        return True
        
    except ConnectionError as e:
        print_error(f"Connection failed: {e}")
        print_warning("Troubleshooting tips:")
        print("  1. Check that RSA3030 is powered on")
        print("  2. Verify USB cable connection (if using USB)")
        print("  3. Check network connectivity: ping [IP_ADDRESS]")
        print("  4. Verify VISA drivers are installed")
        print("  5. List resources: python -c \"import pyvisa; print(pyvisa.ResourceManager().list_resources())\"")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if rsa:
            print_test("Disconnecting from RSA3030")
            rsa.disconnect()
            print_success("Disconnected successfully")


def interactive_mode() -> argparse.Namespace:
    """Interactive mode - prompt user for connection details."""
    print_header("RSA3030 Interactive Connection Mode")
    
    print("\nSelect connection method:")
    print("  1. Auto-connect (search USB and Ethernet)")
    print("  2. Connect via IP address")
    print("  3. Connect via explicit VISA address")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    args = argparse.Namespace()
    args.debug = False
    args.ip = None
    args.address = None
    args.tcpip_autoconnect = False
    args.skip_spectrogram = False
    args.center_freq = 1e9  # Default 1 GHz
    args.span = 100e6       # Default 100 MHz
    
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
        address = input("\nEnter VISA address (e.g., USB0::0x1AB1::0x0960::...::INSTR): ").strip()
        args.address = address
        enable_debug = input("Enable debug output? (y/n): ").strip().lower()
        args.debug = (enable_debug == 'y')
    else:
        print_error("Invalid choice. Using auto-connect mode.")
    
    return args


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test Rigol RSA3030-TG Spectrum Analyzer connectivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_rsa3030.py                              # Auto-connect
  python test_rsa3030.py --ip 192.168.1.100          # Connect via IP
  python test_rsa3030.py --address "TCPIP0::192.168.1.100::INSTR"  # Explicit address
  python test_rsa3030.py --interactive                # Interactive mode
  python test_rsa3030.py --tcpip-autoconnect --debug  # Debug auto-connect
  python test_rsa3030.py --center-freq 10E6 --span 10E6  # Custom frequency settings
  python test_rsa3030.py --ip 192.168.1.100 --center-freq 2.4E9 --span 50E6  # 2.4 GHz with 50 MHz span
        """
    )
    
    parser.add_argument('--ip', type=str, help='IP address for Ethernet connection')
    parser.add_argument('--address', type=str, help='Explicit VISA resource address')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--tcpip-autoconnect', action='store_true', 
                       help='Test TCPIP auto-connect feature')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug output (shows resource scanning)')
    parser.add_argument('--skip-spectrogram', action='store_true',
                       help='Skip spectrogram capture test')
    parser.add_argument('--center-freq', type=float, default=1e9,
                       help='Center frequency for spectrum capture in Hz (e.g., 10E6 or 1E9) [default: 1E9]')
    parser.add_argument('--span', type=float, default=100e6,
                       help='Frequency span for spectrum capture in Hz (e.g., 10E6 or 100E6) [default: 100E6]')
    
    args = parser.parse_args()
    
    # Handle interactive mode
    if args.interactive:
        args = interactive_mode()
    
    # Run connection tests
    print_header("Rigol RSA3030-TG Spectrum Analyzer Test Suite")
    print(f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    success = test_connection_methods(args)
    
    # Print summary
    print_header("Test Summary")
    if success:
        print_success("All tests passed successfully!")
        print("\nNext steps:")
        print("  - Use the RSA3030 class in your measurement scripts")
        print("  - Integrate with data_logger for automated data collection")
        print("  - Refer to libs/RSA3030.py docstring for usage examples")
        return 0
    else:
        print_error("Some tests failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
