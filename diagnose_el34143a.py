#!/usr/bin/env python
"""
Diagnostic script for Keysight EL34143A DC Electronic Load connectivity.

This script helps troubleshoot connection issues by:
- Checking VISA installation
- Listing all available VISA resources
- Testing connection to specific IP addresses
- Probing common addresses for EL34143A
"""

import sys
import socket
from colorama import init as colorama_init, Fore, Style

try:
    import pyvisa
    PYVISA_AVAILABLE = True
except ImportError:
    PYVISA_AVAILABLE = False

colorama_init()


def print_header(title):
    """Print a formatted section header."""
    print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{title:^60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")


def check_pyvisa():
    """Check if PyVISA is installed and working."""
    print_header("CHECKING PYVISA INSTALLATION")
    
    if not PYVISA_AVAILABLE:
        print(f"{Fore.RED}✗ PyVISA is NOT installed{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}To install PyVISA:{Style.RESET_ALL}")
        print(f"  pip install pyvisa")
        return False
    
    print(f"{Fore.GREEN}✓ PyVISA is installed{Style.RESET_ALL}")
    print(f"  Version: {pyvisa.__version__}")
    
    # Check for VISA backend
    try:
        rm = pyvisa.ResourceManager()
        backend = rm.visalib
        print(f"{Fore.GREEN}✓ VISA backend found{Style.RESET_ALL}")
        print(f"  Backend: {backend}")
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ Could not initialize VISA backend{Style.RESET_ALL}")
        print(f"  Error: {e}")
        print(f"\n{Fore.YELLOW}Install VISA libraries:{Style.RESET_ALL}")
        print(f"  - Keysight IO Libraries Suite: https://www.keysight.com/find/iosuite")
        print(f"  - NI-VISA: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html")
        return False


def list_visa_resources():
    """List all available VISA resources."""
    print_header("AVAILABLE VISA RESOURCES")
    
    if not PYVISA_AVAILABLE:
        print(f"{Fore.RED}PyVISA not available{Style.RESET_ALL}")
        return []
    
    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        
        if not resources:
            print(f"{Fore.YELLOW}No VISA resources found{Style.RESET_ALL}")
            return []
        
        print(f"Found {len(resources)} VISA resource(s):\n")
        
        for i, resource in enumerate(resources, 1):
            print(f"{Fore.CYAN}{i}. {resource}{Style.RESET_ALL}")
            
            # Try to open and identify
            try:
                inst = rm.open_resource(resource)
                inst.timeout = 2000
                idn = inst.query("*IDN?").strip()
                print(f"   {Fore.GREEN}IDN: {idn}{Style.RESET_ALL}")
                inst.close()
            except Exception as e:
                print(f"   {Fore.YELLOW}Could not query: {e}{Style.RESET_ALL}")
        
        return resources
    except Exception as e:
        print(f"{Fore.RED}Error listing resources: {e}{Style.RESET_ALL}")
        return []


def test_ping(ip_address):
    """Test if an IP address responds to ping."""
    print(f"Testing ping to {ip_address}...", end=" ")
    
    # Use platform-specific ping command
    import platform
    import subprocess
    
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-w', '1000', ip_address]
    
    try:
        result = subprocess.run(command, capture_output=True, timeout=2)
        if result.returncode == 0:
            print(f"{Fore.GREEN}✓ Reachable{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}✗ No response{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.YELLOW}? Could not ping: {e}{Style.RESET_ALL}")
        return False


def test_tcp_connection(ip_address, port=5025):
    """Test if TCP connection can be established (SCPI port)."""
    print(f"Testing TCP connection to {ip_address}:{port}...", end=" ")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    
    try:
        result = sock.connect_ex((ip_address, port))
        sock.close()
        
        if result == 0:
            print(f"{Fore.GREEN}✓ Port {port} is open{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}✗ Port {port} is closed{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.YELLOW}? Could not connect: {e}{Style.RESET_ALL}")
        return False


def test_visa_connection(ip_address):
    """Test VISA connection to specific IP address."""
    print_header(f"TESTING VISA CONNECTION TO {ip_address}")
    
    if not PYVISA_AVAILABLE:
        print(f"{Fore.RED}PyVISA not available{Style.RESET_ALL}")
        return
    
    # Test network connectivity first
    test_ping(ip_address)
    test_tcp_connection(ip_address)
    
    rm = pyvisa.ResourceManager()
    
    # Try different VISA address formats
    addresses = [
        f"TCPIP0::{ip_address}::inst0::INSTR",
        f"TCPIP0::{ip_address}::hislip0::INSTR",
        f"TCPIP0::{ip_address}::5025::SOCKET",
    ]
    
    print(f"\nTrying VISA addresses:\n")
    
    for address in addresses:
        print(f"{Fore.CYAN}{address}{Style.RESET_ALL}")
        
        try:
            inst = rm.open_resource(address)
            inst.timeout = 3000
            
            # Try to query IDN
            try:
                idn = inst.query("*IDN?").strip()
                print(f"  {Fore.GREEN}✓ Connected!{Style.RESET_ALL}")
                print(f"  {Fore.GREEN}IDN: {idn}{Style.RESET_ALL}")
                
                # Check if it's an EL34143A
                if "EL34143A" in idn.upper():
                    print(f"  {Fore.GREEN}✓ This is an EL34143A!{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.YELLOW}! Not an EL34143A{Style.RESET_ALL}")
                
                inst.close()
                return True
            except Exception as e:
                print(f"  {Fore.RED}✗ Could not query IDN: {e}{Style.RESET_ALL}")
                inst.close()
        except Exception as e:
            print(f"  {Fore.RED}✗ Could not open: {e}{Style.RESET_ALL}")
    
    return False


def main():
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"  EL34143A CONNECTION DIAGNOSTICS")
    print(f"{'=' * 60}{Style.RESET_ALL}\n")
    
    # Check PyVISA
    if not check_pyvisa():
        print(f"\n{Fore.RED}Cannot proceed without working PyVISA installation{Style.RESET_ALL}")
        sys.exit(1)
    
    # List all resources
    resources = list_visa_resources()
    
    # Check if user provided IP address
    if len(sys.argv) > 1:
        ip_address = sys.argv[1]
        test_visa_connection(ip_address)
    else:
        print(f"\n{Fore.YELLOW}To test a specific IP address:{Style.RESET_ALL}")
        print(f"  python diagnose_el34143a.py <ip_address>")
        print(f"\n{Fore.YELLOW}Example:{Style.RESET_ALL}")
        print(f"  python diagnose_el34143a.py 192.168.10.66")
    
    # Summary
    print_header("SUMMARY")
    
    if resources:
        print(f"{Fore.GREEN}✓ VISA is working and can see resources{Style.RESET_ALL}")
        
        # Check if any are EL34143A
        el34143a_found = any("EL34143A" in str(r).upper() for r in resources)
        if el34143a_found:
            print(f"{Fore.GREEN}✓ EL34143A detected in resource list{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}! No EL34143A found in automatic scan{Style.RESET_ALL}")
            print(f"  Try specifying IP address manually")
    else:
        print(f"{Fore.YELLOW}! No VISA resources detected{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Possible issues:{Style.RESET_ALL}")
        print(f"  - Instrument is not powered on")
        print(f"  - Network cable is not connected")
        print(f"  - Instrument is on different network/subnet")
        print(f"  - VISA drivers need to be reinstalled")
        print(f"  - Firewall blocking communication")


if __name__ == "__main__":
    main()
