#!/usr/bin/env python
"""
Test script for Keysight EL34143A DC Electronic Load with Ethernet connectivity.

This script demonstrates the EL34143A driver functionality including:
- Auto-detection and connection via Ethernet
- Current setting in constant current mode
- Voltage, current, and power measurement
- Output enable/disable control

Usage:
    python test_el34143a_ethernet.py                           # Auto-connect
    python test_el34143a_ethernet.py --ip 169.254.153.48      # Connect via IP
    python test_el34143a_ethernet.py --address "TCPIP::..."   # Explicit VISA address
    python test_el34143a_ethernet.py --debug                   # Enable debug output
    python test_el34143a_ethernet.py --set-current 0.5         # Set load current to 0.5A
    python test_el34143a_ethernet.py --enable                  # Enable output
    python test_el34143a_ethernet.py --disable                 # Disable output
    python test_el34143a_ethernet.py --measure                 # Measure voltage, current, power

Examples:
    # Quick test with auto-detection
    python test_el34143a_ethernet.py --measure
    
    # Set current to 100mA and enable output
    python test_el34143a_ethernet.py --set-current 0.1 --enable --measure
    
    # Disable output and disconnect
    python test_el34143a_ethernet.py --disable
    
    # Connect to specific IP and run measurements
    python test_el34143a_ethernet.py --ip 169.254.153.48 --set-current 0.2 --enable --measure
"""

import sys
import argparse
import time
from colorama import init as colorama_init, Fore, Style

# Add libs directory to path
sys.path.insert(0, 'libs')

from KeysightEL34143A import KeysightEL34143A

# Initialize colorama for Windows color support
colorama_init()


def format_value(value, unit, precision=4):
    """Format a measurement value with appropriate units."""
    if value is None:
        return "N/A"
    return f"{value:.{precision}f} {unit}"


def print_header(title):
    """Print a formatted section header."""
    print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{title:^60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")


def print_status(label, value, color=Fore.GREEN):
    """Print a formatted status line."""
    print(f"{color}{label:.<30} {value}{Style.RESET_ALL}")


def main():
    parser = argparse.ArgumentParser(
        description="Test script for Keysight EL34143A DC Electronic Load",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Connection arguments
    connection_group = parser.add_mutually_exclusive_group()
    connection_group.add_argument(
        '--ip',
        type=str,
        help='IP address of the EL34143A (e.g., 169.254.153.48)'
    )
    connection_group.add_argument(
        '--address',
        type=str,
        help='Full VISA address (e.g., "TCPIP::169.254.153.48::inst0::INSTR")'
    )
    
    # Control arguments
    parser.add_argument(
        '--set-current',
        type=float,
        metavar='AMPS',
        help='Set constant current load value in amperes (e.g., 0.5 for 500mA)'
    )
    
    parser.add_argument(
        '--enable',
        action='store_true',
        help='Enable the electronic load output'
    )
    
    parser.add_argument(
        '--disable',
        action='store_true',
        help='Disable the electronic load output'
    )
    
    parser.add_argument(
        '--measure',
        action='store_true',
        help='Measure voltage, current, and power'
    )
    
    parser.add_argument(
        '--monitor',
        type=int,
        metavar='SECONDS',
        help='Continuously monitor measurements for specified duration'
    )
    
    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        metavar='SECONDS',
        help='Measurement interval for monitor mode (default: 1.0s)'
    )
    
    # Debug argument
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    
    args = parser.parse_args()
    
    # If no action specified, default to measure
    if not any([args.set_current, args.enable, args.disable, args.measure, args.monitor]):
        args.measure = True
    
    try:
        # Connect to EL34143A
        print_header("KEYSIGHT EL34143A DC ELECTRONIC LOAD")
        
        print(f"{Fore.YELLOW}Connecting to EL34143A...{Style.RESET_ALL}")
        
        if args.address:
            load = KeysightEL34143A(address=args.address, debug=args.debug)
            print_status("Connection method", "Explicit VISA address")
        elif args.ip:
            load = KeysightEL34143A(ip_address=args.ip, debug=args.debug)
            print_status("Connection method", "IP address")
        else:
            load = KeysightEL34143A(debug=args.debug)
            print_status("Connection method", "Auto-detection")
        
        # Get instrument information
        idn = load.get_idn()
        if idn:
            print_status("Instrument ID", idn.replace(',', ' - '))
        print_status("VISA Address", load.address)
        
        # Set current if requested
        if args.set_current is not None:
            print_header("SETTING CURRENT")
            print(f"{Fore.YELLOW}Setting current to {args.set_current} A...{Style.RESET_ALL}")
            load.set_current(args.set_current)
            time.sleep(0.1)  # Wait for setting to take effect
            
            # Verify setpoint
            setpoint = load.get_current_setpoint()
            if setpoint is not None:
                print_status("Current setpoint", format_value(setpoint, "A"))
                if abs(setpoint - args.set_current) > 0.001:
                    print(f"{Fore.RED}Warning: Setpoint mismatch!{Style.RESET_ALL}")
        
        # Enable output if requested
        if args.enable:
            print_header("ENABLING OUTPUT")
            print(f"{Fore.YELLOW}Enabling electronic load output...{Style.RESET_ALL}")
            load.enable_output()
            time.sleep(0.1)
            
            if load.is_output_enabled():
                print_status("Output status", "ENABLED", Fore.GREEN)
            else:
                print_status("Output status", "FAILED TO ENABLE", Fore.RED)
        
        # Disable output if requested
        if args.disable:
            print_header("DISABLING OUTPUT")
            print(f"{Fore.YELLOW}Disabling electronic load output...{Style.RESET_ALL}")
            load.disable_output()
            time.sleep(0.1)
            
            if not load.is_output_enabled():
                print_status("Output status", "DISABLED", Fore.YELLOW)
            else:
                print_status("Output status", "FAILED TO DISABLE", Fore.RED)
        
        # Single measurement
        if args.measure:
            print_header("MEASUREMENTS")
            
            # Check output status
            output_enabled = load.is_output_enabled()
            print_status("Output status", "ENABLED" if output_enabled else "DISABLED",
                        Fore.GREEN if output_enabled else Fore.YELLOW)
            
            # Get setpoint
            setpoint = load.get_current_setpoint()
            if setpoint is not None:
                print_status("Current setpoint", format_value(setpoint, "A"))
            
            # Measure actual values
            voltage = load.measure_voltage()
            current = load.measure_current()
            power = load.measure_power()
            
            print()
            print_status("Voltage", format_value(voltage, "V"))
            print_status("Current", format_value(current, "A"))
            print_status("Power", format_value(power, "W"))
            
            if voltage is not None and current is not None and power is not None:
                # Calculate expected power and compare
                expected_power = voltage * current
                power_error = abs(power - expected_power) / expected_power * 100 if expected_power > 0 else 0
                print_status("Calculated power", format_value(expected_power, "W"))
                print_status("Power error", f"{power_error:.2f}%")
        
        # Continuous monitoring
        if args.monitor:
            print_header(f"CONTINUOUS MONITORING ({args.monitor}s)")
            print(f"{Fore.YELLOW}Press Ctrl+C to stop early{Style.RESET_ALL}\n")
            
            # Check output status
            if not load.is_output_enabled():
                print(f"{Fore.YELLOW}Warning: Output is disabled. Enable output to see active measurements.{Style.RESET_ALL}\n")
            
            print(f"{'Time':>8}  {'Voltage':>12}  {'Current':>12}  {'Power':>12}")
            print(f"{'(s)':>8}  {'(V)':>12}  {'(A)':>12}  {'(W)':>12}")
            print("-" * 50)
            
            start_time = time.time()
            try:
                while time.time() - start_time < args.monitor:
                    elapsed = time.time() - start_time
                    voltage = load.measure_voltage()
                    current = load.measure_current()
                    power = load.measure_power()
                    
                    print(f"{elapsed:8.1f}  {voltage:12.4f}  {current:12.4f}  {power:12.4f}")
                    
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Monitoring stopped by user{Style.RESET_ALL}")
        
        # Disconnect
        print(f"\n{Fore.YELLOW}Disconnecting...{Style.RESET_ALL}")
        load.disconnect()
        print_status("Status", "Disconnected successfully", Fore.GREEN)
        
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        import traceback
        if args.debug:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
