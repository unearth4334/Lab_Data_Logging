#!/usr/bin/env python
"""
Test script to compare EL34143A load measurements with AVDD1_0 current from FastAPI.

This script:
1. Sets a current on the EL34143A electronic load
2. Measures voltage, current, and power from the load
3. Queries AVDD1_0 current from the FastAPI endpoint
4. Compares the measurements

Usage:
    python test_el34143a_compare_avdd.py --ip 169.254.117.30 --set-current 0.1
    python test_el34143a_compare_avdd.py --ip 169.254.117.30 --set-current 0.05 --base-url http://127.0.0.1:7860
    python test_el34143a_compare_avdd.py --ip 169.254.117.30 --set-current 0.1 --enable
"""

import sys
import argparse
import time
from colorama import init as colorama_init, Fore, Style
from typing import Dict, Any, Optional

# Add libs directory to path
sys.path.insert(0, 'libs')

from KeysightEL34143A import KeysightEL34143A

# Check for requests library
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Initialize colorama for Windows color support
colorama_init()


def print_header(title):
    """Print a formatted section header."""
    print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{title:^70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")


def print_measurement(label, value, unit="", color=Fore.GREEN):
    """Print a formatted measurement line."""
    if value is None:
        value_str = "N/A"
    elif isinstance(value, (int, float)):
        value_str = f"{value:.4f} {unit}".strip()
    else:
        value_str = str(value)
    print(f"{color}{label:.<40} {value_str}{Style.RESET_ALL}")


def get_fastapi_avdd_current(base_url: str) -> Optional[float]:
    """Query AVDD1_0 current from FastAPI endpoint."""
    if not REQUESTS_AVAILABLE:
        print(f"{Fore.YELLOW}Warning: 'requests' module not installed. Cannot query FastAPI.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Install with: pip install requests{Style.RESET_ALL}")
        return None
    
    try:
        url = f"{base_url.rstrip('/')}/state"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        
        state = resp.json()
        monitor = state.get("monitor_data", {})
        value = monitor.get("avdd1_0_current")
        
        return value
    except requests.exceptions.RequestException as e:
        print(f"{Fore.YELLOW}Warning: Could not connect to FastAPI at {base_url}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Error: {e}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Error parsing FastAPI response: {e}{Style.RESET_ALL}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Compare EL34143A measurements with FastAPI AVDD1_0 current",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Connection arguments
    parser.add_argument(
        '--ip',
        type=str,
        default='169.254.117.30',
        help='IP address of the EL34143A (default: 169.254.117.30)'
    )
    
    parser.add_argument(
        '--address',
        type=str,
        help='Full VISA address (overrides --ip)'
    )
    
    # Load control arguments
    parser.add_argument(
        '--set-current',
        type=float,
        required=True,
        metavar='AMPS',
        help='Set constant current load value in amperes (e.g., 0.1 for 100mA)'
    )
    
    parser.add_argument(
        '--enable',
        action='store_true',
        help='Enable the electronic load output before measuring'
    )
    
    parser.add_argument(
        '--disable-after',
        action='store_true',
        help='Disable the electronic load output after measurements'
    )
    
    # FastAPI arguments
    parser.add_argument(
        '--base-url',
        default='http://127.0.0.1:7860',
        help='FastAPI base URL (default: http://127.0.0.1:7860)'
    )
    
    parser.add_argument(
        '--skip-fastapi',
        action='store_true',
        help='Skip FastAPI query (only measure from load)'
    )
    
    # Other arguments
    parser.add_argument(
        '--settling-time',
        type=float,
        default=2.0,
        metavar='SECONDS',
        help='Wait time after setting current before measuring (default: 2.0s)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    
    args = parser.parse_args()
    
    load = None
    try:
        # Connect to EL34143A
        print_header("KEYSIGHT EL34143A DC ELECTRONIC LOAD TEST")
        
        print(f"{Fore.YELLOW}Connecting to EL34143A...{Style.RESET_ALL}")
        
        try:
            if args.address:
                load = KeysightEL34143A(address=args.address, debug=args.debug)
            else:
                load = KeysightEL34143A(ip_address=args.ip, debug=args.debug)
        except ConnectionError as e:
            print(f"\n{Fore.RED}Connection failed: {e}{Style.RESET_ALL}")
            sys.exit(1)
        
        # Get instrument information
        idn = load.get_idn()
        if idn:
            print_measurement("Instrument ID", idn.replace(',', ' - '), color=Fore.CYAN)
        print_measurement("VISA Address", load.address, color=Fore.CYAN)
        
        # Set current
        print_header("SETTING LOAD CURRENT")
        print(f"{Fore.YELLOW}Setting current to {args.set_current} A...{Style.RESET_ALL}")
        load.set_current(args.set_current)
        
        # Enable output if requested
        if args.enable:
            print(f"{Fore.YELLOW}Enabling load output...{Style.RESET_ALL}")
            load.enable_output()
            print(f"{Fore.GREEN}✓ Output enabled{Style.RESET_ALL}")
        
        # Wait for settling
        print(f"{Fore.YELLOW}Waiting {args.settling_time}s for load to settle...{Style.RESET_ALL}")
        time.sleep(args.settling_time)
        
        # Verify setpoint
        setpoint = load.get_current_setpoint()
        print_measurement("Current setpoint", setpoint, "A")
        
        # Measure from load
        print_header("EL34143A LOAD MEASUREMENTS")
        
        output_enabled = load.is_output_enabled()
        print_measurement("Output status", "ENABLED" if output_enabled else "DISABLED",
                         color=Fore.GREEN if output_enabled else Fore.YELLOW)
        
        if not output_enabled:
            print(f"{Fore.YELLOW}Note: Output is disabled. Measurements may not reflect active load.{Style.RESET_ALL}")
        
        voltage_load = load.measure_voltage()
        current_load = load.measure_current()
        power_load = load.measure_power()
        
        print()
        print_measurement("Voltage", voltage_load, "V")
        print_measurement("Current (measured)", current_load, "A")
        print_measurement("Power", power_load, "W")
        
        if voltage_load is not None and current_load is not None and power_load is not None:
            expected_power = voltage_load * current_load
            power_error = abs(power_load - expected_power) / expected_power * 100 if expected_power > 0 else 0
            print_measurement("Calculated power", expected_power, "W", Fore.CYAN)
            print_measurement("Power error", f"{power_error:.2f}%", "", Fore.CYAN)
        
        # Query FastAPI
        avdd_current = None
        if not args.skip_fastapi:
            print_header("FASTAPI AVDD1_0 CURRENT")
            
            print(f"{Fore.YELLOW}Querying {args.base_url}/state...{Style.RESET_ALL}")
            avdd_current = get_fastapi_avdd_current(args.base_url)
            
            if avdd_current is not None:
                print_measurement("AVDD1_0 current", avdd_current, "A")
            else:
                print(f"{Fore.RED}✗ Could not retrieve AVDD1_0 current from FastAPI{Style.RESET_ALL}")
        
        # Comparison
        if current_load is not None and avdd_current is not None:
            print_header("COMPARISON")
            
            print_measurement("EL34143A measured current", current_load, "A")
            print_measurement("FastAPI AVDD1_0 current", avdd_current, "A")
            
            diff = current_load - avdd_current
            diff_percent = (diff / avdd_current * 100) if avdd_current != 0 else 0
            
            print()
            print_measurement("Difference (Load - API)", diff, "A", 
                             Fore.GREEN if abs(diff) < 0.001 else Fore.YELLOW)
            print_measurement("Difference percentage", f"{diff_percent:.2f}%", "",
                             Fore.GREEN if abs(diff_percent) < 5 else Fore.YELLOW)
            
            # Agreement assessment
            print()
            if abs(diff_percent) < 1:
                print(f"{Fore.GREEN}✓ Excellent agreement (< 1% difference){Style.RESET_ALL}")
            elif abs(diff_percent) < 5:
                print(f"{Fore.YELLOW}⚠ Good agreement (< 5% difference){Style.RESET_ALL}")
            elif abs(diff_percent) < 10:
                print(f"{Fore.YELLOW}⚠ Fair agreement (< 10% difference){Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Poor agreement (> 10% difference){Style.RESET_ALL}")
        
        # Disable output if requested
        if args.disable_after:
            print_header("DISABLING OUTPUT")
            print(f"{Fore.YELLOW}Disabling load output...{Style.RESET_ALL}")
            load.disable_output()
            print(f"{Fore.GREEN}✓ Output disabled{Style.RESET_ALL}")
        
        # Disconnect
        print(f"\n{Fore.YELLOW}Disconnecting...{Style.RESET_ALL}")
        load.disconnect()
        print(f"{Fore.GREEN}✓ Test complete{Style.RESET_ALL}\n")
        
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Test cancelled by user{Style.RESET_ALL}")
        if load:
            load.disconnect()
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        if args.debug:
            import traceback
            traceback.print_exc()
        if load:
            load.disconnect()
        sys.exit(1)


if __name__ == "__main__":
    main()
