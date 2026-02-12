#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMM6500 Ethernet/USB Connection Test Script
============================================

This script tests the DMM6500 driver's ethernet and USB connectivity capabilities,
demonstrating various connection methods and measurement functions.

USAGE
-----
The script supports multiple connection modes:

1. **Auto-connect (USB/Ethernet auto-detection)**:
   ```bash
   python test_dmm6500_ethernet.py
   ```
   Automatically searches for DMM6500 on any available interface (USB or Ethernet)

2. **Connect via IP address**:
   ```bash
   python test_dmm6500_ethernet.py --ip 169.254.233.96
   ```
   Connects to DMM6500 at the specified IP address via Ethernet/LAN
   (Find IP on device: Menu > System > Communications > LAN)

3. **Connect via explicit VISA address**:
   ```bash
   # USB connection
   python test_dmm6500_ethernet.py --address "USB0::0x05E6::0x6500::04492372::INSTR"
   
   # Ethernet connection (copy from DMM6500 LAN settings screen)
   python test_dmm6500_ethernet.py --address "TCPIP0::169.254.233.96::inst0::INSTR"
   ```
   Connects using a specific VISA resource string

4. **Interactive mode**:
   ```bash
   python test_dmm6500_ethernet.py --interactive
   ```
   Prompts for connection method and parameters

COMMAND LINE OPTIONS
--------------------
  --ip IP_ADDRESS          IP address for ethernet connection (e.g., 192.168.1.100)
  --address VISA_ADDRESS   Full VISA resource string (USB or TCPIP)
  --interactive, -i        Interactive mode - prompts for connection details
  --skip-statistics        Skip statistics measurements (faster testing)
  --skip-digitize         Skip high-speed digitizing tests
  --help, -h              Show this help message

EXAMPLES
--------

Example 1: Quick test with auto-detection
```bash
python test_dmm6500_ethernet.py
```

Example 2: Connect to specific IP (as shown on DMM6500 LAN settings)
```bash
python test_dmm6500_ethernet.py --ip 169.254.233.96
```

Example 3: Use the exact VISA string from DMM6500 display
```bash
python test_dmm6500_ethernet.py --address "TCPIP0::169.254.233.96::inst0::INSTR"
```

Example 4: Connect via USB with explicit address
```bash
python test_dmm6500_ethernet.py --address "USB0::0x05E6::0x6500::04492372::INSTR"
```

Example 5: Interactive mode for manual configuration
```bash
python test_dmm6500_ethernet.py --interactive
```

Example 6: Quick voltage-only test via ethernet
```bash
python test_dmm6500_ethernet.py --ip 169.254.233.96 --skip-statistics --skip-digitize
```

NETWORK CONFIGURATION
---------------------
**Finding the DMM6500 IP Address:**

1. On the DMM6500 front panel, press **MENU**
2. Navigate to: **System > Communications > LAN**
3. The LAN Communications screen displays network information:
   ```
   TCP/IP Mode: Auto (or Manual)
   Gateway: xxx.xxx.xxx.xxx
   IP Address: xxx.xxx.xxx.xxx          <-- Use this IP address
   Subnet: xxx.xxx.xxx.xxx
   MAC Address: xx:xx:xx:xx:xx:xx
   TCPIPn::<IP_ADDRESS>::inst0::INSTR   <-- 'n' is a placeholder - use TCPIP0
   TCPIPn::<IP_ADDRESS>::5025::SOCKET   <-- Socket format
   ```

4. **Note the IP Address shown** (e.g., 169.254.233.96)
   - Use this with: `python test_dmm6500_ethernet.py --ip 169.254.233.96`
   - Or in code: `DMM6500(ip_address="169.254.233.96")`

5. **IMPORTANT: The display shows "TCPIPn" - replace 'n' with '0'**
   - Display shows: `TCPIPn::169.254.233.96::inst0::INSTR`
   - **Actual format**: `TCPIP0::169.254.233.96::inst0::INSTR`
   - Use with: `python test_dmm6500_ethernet.py --address "TCPIP0::169.254.233.96::inst0::INSTR"`

**Configuring Network Settings:**

If the DMM6500 doesn't have an IP address or you need to change it:
1. Press **MENU** > **System > Communications > LAN**
2. Select **TCP/IP Mode**:
   - **Auto (DHCP)**: Automatically obtains IP from network
   - **Manual**: Set static IP address manually
3. If using Manual mode, configure:
   - IP Address
   - Subnet Mask
   - Gateway (if needed)
4. Press **ENTER** to save settings
5. The device may need to restart for changes to take effect

**Network Requirements:**
- DMM6500 must be connected via Ethernet cable
- Computer and DMM6500 should be on the same network
- Firewall should allow VISA/LXI communication (port 5025)
- For link-local addresses (169.254.x.x), ensure computer is on same subnet

**Configuring Your Computer for Link-Local Connection (169.254.x.x):**

When connecting DMM6500 directly to your laptop (no router/DHCP), configure manually:

- **Windows**:
  1. Control Panel > Network and Sharing Center > Change adapter settings
  2. Right-click Ethernet adapter > Properties > Internet Protocol Version 4 (TCP/IPv4)
  3. Select "Use the following IP address":
     - IP address: 169.254.233.1 (must be different from DMM, same 169.254.x.x range)
     - Subnet mask: 255.255.0.0 (same as DMM)
     - Gateway: (leave blank)
  4. Click OK, disable Wi-Fi to avoid routing conflicts

- **Linux**:
  ```bash
  sudo ip addr add 169.254.233.1/16 dev eth0  # Replace eth0 with your interface
  sudo ip link set eth0 up
  ```

- **macOS**:
  1. System Preferences > Network > Ethernet
  2. Configure IPv4: Manually
  3. IP Address: 169.254.233.1
  4. Subnet Mask: 255.255.0.0
  5. Apply settings, disable Wi-Fi

After configuring, test with: `ping 169.254.233.96`

TROUBLESHOOTING
---------------
**Common Mistakes:**

⚠️ **IMPORTANT: The DMM6500 display shows "TCPIPn" where 'n' is a PLACEHOLDER**
   - The display shows: `TCPIPn::169.254.233.96::inst0::INSTR`
   - **Correct format**: `TCPIP0::169.254.233.96::inst0::INSTR` (use '0' not 'n')
   - Wrong: `TCPINn::169.254.233.96::inst0::INSTR` (typo - TCPIN instead of TCPIP)
   - Wrong: `TCPIP::169.254.233.96::inst0::INSTR` (missing '0')

**Connection Issues:**

1. **Find the actual IP address on the device:**
   - Press MENU > System > Communications > LAN
   - Look for "IP Address" line (e.g., 169.254.233.96)
   - The display shows `TCPIPn::...` - replace 'n' with '0'

2. **For link-local addresses (169.254.x.x) - Direct laptop connection:**
   - Configure your laptop's Ethernet adapter for the same subnet:
     - Windows: Network Settings > Change Adapter Options > Ethernet Properties > IPv4
       - Set IP: 169.254.233.1 (different from DMM)
       - Set Subnet: 255.255.0.0
     - Linux: `sudo ip addr add 169.254.233.1/16 dev eth0`
     - Mac: System Preferences > Network > Ethernet > Configure IPv4: Manually
       - IP: 169.254.233.1, Subnet: 255.255.0.0
   - **Important**: Disable Wi-Fi to avoid routing conflicts

3. **Test network connectivity:**
   ```bash
   ping 169.254.233.96  # Should reply if network is configured correctly
   ```

4. **Verify VISA resources are visible:**
   ```bash
   python -c "import pyvisa; rm = pyvisa.ResourceManager(); print(rm.list_resources())"
   ```
   Should show something like: `TCPIP0::169.254.233.96::inst0::INSTR`
   
   If no TCPIP resources appear:
   - Check NI-VISA is installed (required for ethernet/LAN)
   - Verify network adapter configuration (step 2)
   - Try restarting the VISA service or rebooting

5. **Use the correct VISA string format:**
   - **Correct**: `python test_dmm6500_ethernet.py --address "TCPIP0::169.254.233.96::inst0::INSTR"`
   - Or simply: `python test_dmm6500_ethernet.py --ip 169.254.233.96`

6. **Check physical connection:**
   - Verify Ethernet cable is properly connected
   - Check link lights on both laptop and DMM6500 ports
   - Try a different Ethernet cable if available

For USB connections:
1. Ensure USB cable is connected
2. Check that VISA drivers are installed (NI-VISA or similar)
3. List available resources: `python -c "import pyvisa; print(pyvisa.ResourceManager().list_resources())"`

REQUIREMENTS
------------
- Python 3.7+
- pyvisa >= 1.11.0
- colorama >= 0.4.6
- numpy >= 1.21.0
- NI-VISA or compatible VISA backend

Install dependencies:
```bash
pip install pyvisa colorama numpy
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
    from libs.DMM6500 import DMM6500
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError as e:
    print(f"Error: Missing required module: {e}")
    print("Please install dependencies: pip install pyvisa colorama numpy")
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


def test_basic_measurements(dmm: DMM6500) -> bool:
    """Test basic DC measurement functions."""
    print_header("Basic Measurements Test")
    
    try:
        # Test DC voltage measurement
        print_test("Measuring DC voltage")
        voltage = dmm.measure_voltage()
        print_success(f"DC Voltage: {voltage:.6f} V")
        
        # Test DC current measurement
        print_test("Measuring DC current")
        try:
            current = dmm.measure_current()
            print_success(f"DC Current: {current:.9f} A")
        except Exception as e:
            print_warning(f"Current measurement skipped (may require specific setup): {e}")
        
        # Test resistance measurement
        print_test("Measuring 2-wire resistance")
        try:
            resistance = dmm.measure_resistance(four_wire=False)
            print_success(f"Resistance (2W): {resistance:.3f} Ω")
        except Exception as e:
            print_warning(f"Resistance measurement skipped (may require specific setup): {e}")
        
        return True
        
    except Exception as e:
        print_error(f"Basic measurements failed: {e}")
        return False


def test_statistics(dmm: DMM6500, num_samples: int = 10) -> bool:
    """Test statistics calculation."""
    print_header("Statistics Test")
    
    try:
        print_test(f"Collecting {num_samples} voltage samples for statistics")
        mean, stdev, vmin, vmax = dmm.calculate_statistics(
            n=num_samples,
            measurement_type="VOLTAGE:DC",
            delay_s=0.05
        )
        
        print_success(f"Statistics Results ({num_samples} samples):")
        print(f"  Mean:   {mean:.6f} V")
        print(f"  StdDev: {stdev:.6f} V")
        print(f"  Min:    {vmin:.6f} V")
        print(f"  Max:    {vmax:.6f} V")
        print(f"  Range:  {vmax - vmin:.6f} V")
        
        return True
        
    except Exception as e:
        print_error(f"Statistics test failed: {e}")
        return False


def test_configuration(dmm: DMM6500) -> bool:
    """Test configuration commands."""
    print_header("Configuration Test")
    
    try:
        # Test voltage configuration
        print_test("Configuring voltage measurement (10V range, 1µV resolution)")
        dmm.configure("VOLTAGE:DC", max_value=10.0, resolution=1e-6)
        print_success("Configuration successful")
        
        # Test NPLC setting
        print_test("Setting integration time to 1 NPLC")
        dmm.set_nplc(1.0)
        print_success("NPLC set to 1")
        
        # Take a measurement with new settings
        print_test("Taking measurement with configured settings")
        voltage = dmm.measure_voltage()
        print_success(f"Configured measurement: {voltage:.6f} V")
        
        return True
        
    except Exception as e:
        print_error(f"Configuration test failed: {e}")
        return False


def test_digitize(dmm: DMM6500) -> bool:
    """Test high-speed digitizing mode."""
    print_header("Digitizing Mode Test")
    
    try:
        print_test("Capturing high-speed voltage data (0.5 seconds)")
        print_warning("This may take a moment...")
        
        data = dmm.digitize_voltage(
            duration_s=0.5,
            fixed_range=10.0,
            nplc=0.01
        )
        
        if data and len(data) > 0:
            print_success(f"Captured {len(data)} samples")
            print(f"  Sample mean: {sum(data)/len(data):.6f} V")
            print(f"  Sample min:  {min(data):.6f} V")
            print(f"  Sample max:  {max(data):.6f} V")
            print(f"  Approx rate: {len(data)/0.5:.1f} samples/sec")
            return True
        else:
            print_warning("No data captured")
            return False
            
    except Exception as e:
        print_error(f"Digitize test failed: {e}")
        print_warning("Digitizing may require specific firmware or settings")
        return False


def test_get_interface(dmm: DMM6500) -> bool:
    """Test the generic get() interface used by data_logger."""
    print_header("Generic get() Interface Test")
    
    try:
        print_test("Testing get('voltage')")
        voltage = dmm.get("voltage")
        print_success(f"Voltage via get(): {voltage:.6f} V")
        
        print_test("Testing get('statistics')")
        stats = dmm.get("statistics")
        print_success(f"Statistics via get(): mean={stats[0]:.6f}, std={stats[1]:.6f}, min={stats[2]:.6f}, max={stats[3]:.6f}")
        
        return True
        
    except Exception as e:
        print_error(f"get() interface test failed: {e}")
        return False


def interactive_connect() -> tuple[Optional[str], Optional[str]]:
    """Interactive mode for connection setup."""
    print_header("Interactive Connection Setup")
    
    print("\nConnection Methods:")
    print("  1. Auto-detect (USB/Ethernet)")
    print("  2. Ethernet via IP address")
    print("  3. Explicit VISA address (USB or TCPIP)")
    
    choice = input("\nSelect connection method (1-3): ").strip()
    
    if choice == "1":
        return None, None
    elif choice == "2":
        ip = input("Enter IP address (e.g., 192.168.1.100): ").strip()
        return None, ip if ip else None
    elif choice == "3":
        addr = input("Enter VISA address: ").strip()
        return addr if addr else None, None
    else:
        print_error("Invalid choice, using auto-detect")
        return None, None


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test DMM6500 ethernet and USB connectivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Auto-detect connection
  %(prog)s --ip 192.168.1.100                 # Connect via ethernet
  %(prog)s --address "USB0::0x05E6::..."      # Connect via USB
  %(prog)s --interactive                      # Interactive mode
        """
    )
    
    parser.add_argument("--ip", type=str, help="IP address for ethernet connection")
    parser.add_argument("--address", type=str, help="Explicit VISA resource address")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--skip-statistics", action="store_true", help="Skip statistics test")
    parser.add_argument("--skip-digitize", action="store_true", help="Skip digitize test")
    
    args = parser.parse_args()
    
    # Print welcome message
    print_header("DMM6500 Ethernet/USB Connection Test")
    print(f"{_INFO}This script tests ethernet and USB connectivity for the Keithley DMM6500{_RESET}")
    
    # Determine connection parameters
    address = None
    ip_address = None
    
    if args.interactive:
        address, ip_address = interactive_connect()
    else:
        address = args.address
        ip_address = args.ip
    
    # Show connection mode
    if ip_address:
        print(f"\n{_INFO}Connection Mode: Ethernet (IP: {ip_address}){_RESET}")
    elif address:
        print(f"\n{_INFO}Connection Mode: Explicit VISA address{_RESET}")
    else:
        print(f"\n{_INFO}Connection Mode: Auto-detect{_RESET}")
    
    # Connect to DMM6500
    print_test("Connecting to DMM6500")
    try:
        dmm = DMM6500(auto_connect=False)
        dmm.connect(address=address, ip_address=ip_address)
    except Exception as e:
        print_error(f"Failed to connect: {e}")
        print("\nTroubleshooting tips:")
        print("  1. Check device is powered on")
        print("  2. Verify network/USB connection")
        print("  3. For ethernet, check IP address on device")
        print("  4. Try explicit VISA address format")
        print(f"\n  Run: {sys.argv[0]} --help for more information")
        return 1
    
    # Run test suite
    results = []
    
    # Basic measurements
    results.append(("Basic Measurements", test_basic_measurements(dmm)))
    
    # Configuration
    results.append(("Configuration", test_configuration(dmm)))
    
    # Statistics (optional)
    if not args.skip_statistics:
        results.append(("Statistics", test_statistics(dmm, num_samples=20)))
    
    # get() interface
    results.append(("get() Interface", test_get_interface(dmm)))
    
    # Digitizing (optional)
    if not args.skip_digitize:
        results.append(("Digitizing", test_digitize(dmm)))
    
    # Disconnect
    print_test("Disconnecting")
    dmm.disconnect()
    print_success("Disconnected successfully")
    
    # Print summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{_SUCCESS}PASS" if result else f"{_ERROR}FAIL"
        print(f"  {test_name:<25} {status}{_RESET}")
    
    print(f"\n{_INFO}Results: {passed}/{total} tests passed{_RESET}")
    
    if passed == total:
        print(f"\n{_SUCCESS}✓ All tests completed successfully!{_RESET}")
        return 0
    else:
        print(f"\n{_WARNING}⚠ Some tests failed or were skipped{_RESET}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{_WARNING}Test interrupted by user{_RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{_ERROR}Unexpected error: {e}{_RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
