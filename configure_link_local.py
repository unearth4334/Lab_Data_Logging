#!/usr/bin/env python
"""
Link-Local Network Configuration Helper

This script helps configure Windows network adapters for link-local (169.254.x.x)
communication with instruments like the Keysight EL34143A.

The "PING: transmit failed. General failure" error means your network adapter
needs a link-local IP address to communicate with devices at 169.254.x.x addresses.
"""

import subprocess
import sys
import re
from colorama import init as colorama_init, Fore, Style

colorama_init()


def print_header(title):
    """Print a formatted section header."""
    print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{title:^70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")


def run_command(cmd):
    """Run a command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error running command: {e}"


def check_link_local_config():
    """Check if any network adapter has a link-local IP."""
    print_header("CHECKING NETWORK CONFIGURATION")
    
    output = run_command("ipconfig")
    
    # Look for 169.254.x.x addresses
    link_local_pattern = r'169\.254\.\d+\.\d+'
    matches = re.findall(link_local_pattern, output)
    
    if matches:
        print(f"{Fore.GREEN}✓ Found link-local IP address(es):{Style.RESET_ALL}")
        for ip in matches:
            print(f"  {Fore.GREEN}{ip}{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.RED}✗ No link-local IP address found{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Your network adapter needs a 169.254.x.x IP to communicate")
        print(f"with link-local devices.{Style.RESET_ALL}")
        return False


def list_ethernet_adapters():
    """List available Ethernet adapters."""
    print_header("AVAILABLE NETWORK ADAPTERS")
    
    output = run_command("netsh interface ipv4 show interfaces")
    print(output)
    
    # Parse adapter names
    adapters = []
    for line in output.split('\n'):
        if 'connected' in line.lower() or 'ethernet' in line.lower():
            # Extract adapter info
            parts = line.split()
            if len(parts) >= 4:
                # Try to find the adapter name (usually the last column)
                adapter_name = ' '.join(parts[3:])
                if adapter_name and adapter_name not in ['Loopback', 'Pseudo-Interface']:
                    adapters.append(adapter_name)
    
    return adapters


def show_manual_configuration_steps():
    """Show manual configuration steps."""
    print_header("MANUAL CONFIGURATION STEPS")
    
    print(f"{Fore.YELLOW}To manually configure link-local networking:{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}Step 1: Open Network Settings{Style.RESET_ALL}")
    print(f"  • Press {Fore.WHITE}Win + R{Style.RESET_ALL}, type {Fore.WHITE}ncpa.cpl{Style.RESET_ALL}, press Enter")
    print(f"  • Or: Control Panel → Network and Sharing Center → Change adapter settings\n")
    
    print(f"{Fore.CYAN}Step 2: Select Your Ethernet Adapter{Style.RESET_ALL}")
    print(f"  • Right-click on the Ethernet adapter connected to the EL34143A")
    print(f"  • Select {Fore.WHITE}Properties{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}Step 3: Configure IPv4{Style.RESET_ALL}")
    print(f"  • Double-click {Fore.WHITE}Internet Protocol Version 4 (TCP/IPv4){Style.RESET_ALL}")
    print(f"  • Select {Fore.WHITE}Use the following IP address{Style.RESET_ALL}")
    print(f"  • Enter these values:")
    print(f"    {Fore.GREEN}IP address:{Style.RESET_ALL}     169.254.19.100")
    print(f"    {Fore.GREEN}Subnet mask:{Style.RESET_ALL}   255.255.0.0")
    print(f"    {Fore.GREEN}Default gateway:{Style.RESET_ALL} (leave blank)")
    print(f"  • Click {Fore.WHITE}OK{Style.RESET_ALL} on all windows\n")
    
    print(f"{Fore.CYAN}Step 4: Verify Configuration{Style.RESET_ALL}")
    print(f"  • Open PowerShell or CMD")
    print(f"  • Run: {Fore.WHITE}ping 169.254.19.101{Style.RESET_ALL}")
    print(f"  • You should see replies instead of 'General failure'\n")
    
    print(f"{Fore.YELLOW}Note: Choose an IP like 169.254.19.100 (anything except .101)")
    print(f"to avoid conflicts with the instrument.{Style.RESET_ALL}")


def show_automated_configuration():
    """Show automated configuration using netsh."""
    print_header("AUTOMATED CONFIGURATION (ADVANCED)")
    
    print(f"{Fore.YELLOW}You can configure link-local networking using netsh commands:{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}To add a link-local IP to an adapter:{Style.RESET_ALL}")
    print(f'{Fore.WHITE}netsh interface ipv4 set address name="Ethernet" static 169.254.19.100 255.255.0.0{Style.RESET_ALL}\n')
    
    print(f"{Fore.CYAN}To add as a secondary IP (keeps your existing IP):{Style.RESET_ALL}")
    print(f'{Fore.WHITE}netsh interface ipv4 add address name="Ethernet" 169.254.19.100 255.255.0.0{Style.RESET_ALL}\n')
    
    print(f"{Fore.CYAN}To remove the link-local IP later:{Style.RESET_ALL}")
    print(f'{Fore.WHITE}netsh interface ipv4 delete address name="Ethernet" 169.254.19.100{Style.RESET_ALL}\n')
    
    print(f"{Fore.RED}⚠ WARNING:{Style.RESET_ALL}")
    print(f"  • Replace {Fore.WHITE}\"Ethernet\"{Style.RESET_ALL} with your actual adapter name")
    print(f"  • Using 'set' will replace your existing IP")
    print(f"  • Using 'add' will keep your existing IP and add a secondary one")
    print(f"  • Requires Administrator privileges (Run PowerShell as Administrator)")
    print(f"  • May temporarily disconnect your network")


def generate_batch_file(adapter_name="Ethernet"):
    """Generate a batch file for configuration."""
    print_header("GENERATE CONFIGURATION SCRIPT")
    
    batch_content = f"""@echo off
REM Link-Local Configuration Script for EL34143A
REM This script adds a link-local IP address to your network adapter
REM Run as Administrator

echo Configuring link-local networking for EL34143A...
echo.

REM Add link-local IP as secondary address (keeps existing IP)
netsh interface ipv4 add address name="{adapter_name}" 169.254.19.100 255.255.0.0

echo.
echo Configuration complete!
echo Testing connection...
ping 169.254.19.101 -n 2

echo.
echo To remove this configuration later, run:
echo netsh interface ipv4 delete address name="{adapter_name}" 169.254.19.100
echo.
pause
"""
    
    filename = "configure_el34143a_network.bat"
    
    try:
        with open(filename, 'w') as f:
            f.write(batch_content)
        
        print(f"{Fore.GREEN}✓ Created {filename}{Style.RESET_ALL}\n")
        print(f"{Fore.YELLOW}To use this script:{Style.RESET_ALL}")
        print(f"  1. Right-click on {Fore.WHITE}{filename}{Style.RESET_ALL}")
        print(f"  2. Select {Fore.WHITE}Run as Administrator{Style.RESET_ALL}")
        print(f"  3. Follow the prompts\n")
        
        print(f"{Fore.YELLOW}Note: Update the adapter name in the script if needed.{Style.RESET_ALL}")
        print(f"Your adapters are listed above in the 'Available Network Adapters' section.")
        
        return True
    except Exception as e:
        print(f"{Fore.RED}Failed to create batch file: {e}{Style.RESET_ALL}")
        return False


def show_recommendations():
    """Show recommendations for different scenarios."""
    print_header("RECOMMENDATIONS")
    
    print(f"{Fore.CYAN}Scenario 1: Direct Connection (Recommended for Lab Use){Style.RESET_ALL}")
    print(f"  • Connect PC directly to EL34143A with Ethernet cable")
    print(f"  • Configure PC with static link-local IP: 169.254.19.100")
    print(f"  • This is the simplest and most reliable setup\n")
    
    print(f"{Fore.CYAN}Scenario 2: Shared Network Connection{Style.RESET_ALL}")
    print(f"  • PC and EL34143A connected to same network switch")
    print(f"  • Configure EL34143A with proper static IP (e.g., 192.168.1.100)")
    print(f"  • Configure PC network adapter to same subnet")
    print(f"  • Better for labs with multiple instruments\n")
    
    print(f"{Fore.CYAN}Scenario 3: Secondary IP (Keep Internet Access){Style.RESET_ALL}")
    print(f"  • Use 'netsh add address' to add 169.254.19.100 as secondary IP")
    print(f"  • Keeps your existing IP and internet connection")
    print(f"  • Allows instrument connection without losing network access\n")
    
    print(f"{Fore.YELLOW}For production use, consider configuring the EL34143A with a proper")
    print(f"static IP in your network subnet instead of using link-local addressing.{Style.RESET_ALL}")


def main():
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"  LINK-LOCAL NETWORK CONFIGURATION HELPER")
    print(f"  For Keysight EL34143A at 169.254.19.101")
    print(f"{'=' * 70}{Style.RESET_ALL}\n")
    
    # Check current configuration
    has_link_local = check_link_local_config()
    
    if has_link_local:
        print(f"\n{Fore.GREEN}Your network is already configured for link-local communication!{Style.RESET_ALL}")
        print(f"\nTry connecting again:")
        print(f"  {Fore.WHITE}python test_el34143a_ethernet.py --ip 169.254.19.101 --measure{Style.RESET_ALL}")
        return
    
    # List adapters
    adapters = list_ethernet_adapters()
    
    # Show configuration options
    show_manual_configuration_steps()
    show_automated_configuration()
    
    # Generate batch file
    if adapters:
        print(f"\n{Fore.YELLOW}Would you like to generate a configuration script?{Style.RESET_ALL}")
        print(f"This will create a .bat file you can run as Administrator.\n")
        
        response = input(f"Generate script? (y/n): ").strip().lower()
        if response == 'y':
            # Use first Ethernet adapter found, or let user specify
            if len(adapters) > 1:
                print(f"\n{Fore.YELLOW}Multiple adapters found. Please specify the adapter name.{Style.RESET_ALL}")
                adapter_name = input(f"Adapter name (or press Enter for 'Ethernet'): ").strip()
                if not adapter_name:
                    adapter_name = "Ethernet"
            else:
                adapter_name = adapters[0] if adapters else "Ethernet"
            
            generate_batch_file(adapter_name)
    
    # Show recommendations
    show_recommendations()
    
    print(f"\n{Fore.CYAN}After configuration, test with:{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}ping 169.254.19.101{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}python test_el34143a_ethernet.py --ip 169.254.19.101 --measure{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
