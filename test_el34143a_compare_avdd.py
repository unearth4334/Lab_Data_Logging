#!/usr/bin/env python
"""
Test script to compare EL34143A load measurements with AVDD1_0 current from FastAPI.

This script:
1. Sets a current on the EL34143A electronic load
2. Measures voltage, current, and power from the load
3. Queries AVDD1_0 current from the FastAPI endpoint
4. Compares the measurements
5. Can sweep current from 0 to 2A in 10mA increments and save to CSV

Usage:
    # Single measurement
    python test_el34143a_compare_avdd.py --ip 169.254.117.30 --set-current 0.1
    python test_el34143a_compare_avdd.py --ip 169.254.117.30 --set-current 0.05 --base-url http://127.0.0.1:7860
    
    # Sweep mode (0 to 2A in 10mA steps)
    python test_el34143a_compare_avdd.py --ip 169.254.117.30 --sweep --enable
    python test_el34143a_compare_avdd.py --ip 169.254.117.30 --sweep --start 0 --stop 1 --step 0.05
    python test_el34143a_compare_avdd.py --ip 169.254.117.30 --sweep --enable -m "battery_test_1"
"""

import sys
import argparse
import time
import csv
import os
from datetime import datetime
from colorama import init as colorama_init, Fore, Style
from typing import Dict, Any, Optional, List

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

# Minimum current the load can be set to (12mA)
MIN_CURRENT = 0.012  # Amperes


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


def get_fastapi_avdd_current(base_url: str, channel: int = 0) -> Optional[float]:
    """Query AVDD1_X current from FastAPI endpoint based on channel number.
    
    Args:
        base_url: FastAPI base URL
        channel: Channel number (0 for AVDD1_0, 1 for AVDD1_1, etc.)
    """
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
        # Construct field name based on channel: avdd1_0_current, avdd1_1_current, etc.
        field_name = f"avdd1_{channel}_current"
        value = monitor.get(field_name)
        
        return value
    except requests.exceptions.RequestException as e:
        print(f"{Fore.YELLOW}Warning: Could not connect to FastAPI at {base_url}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Error: {e}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Error parsing FastAPI response: {e}{Style.RESET_ALL}")
        return None


def perform_measurement(load: KeysightEL34143A, base_url: str, channel: int = 0, skip_fastapi: bool = False) -> Dict[str, Any]:
    """
    Perform a single measurement from load and FastAPI.
    
    Args:
        load: EL34143A electronic load instance
        base_url: FastAPI base URL
        channel: AVDD channel number (0, 1, etc.)
        skip_fastapi: Skip FastAPI query if True
    
    Returns dict with keys: voltage, current, power, avdd_current, timestamp
    """
    result = {
        'timestamp': datetime.now().isoformat(),
        'voltage': None,
        'current': None,
        'power': None,
        'avdd_current': None,
        'output_enabled': False
    }
    
    # Check output status
    result['output_enabled'] = load.is_output_enabled()
    
    # Measure from load
    result['voltage'] = load.measure_voltage()
    result['current'] = load.measure_current()
    result['power'] = load.measure_power()
    
    # Query FastAPI
    if not skip_fastapi:
        result['avdd_current'] = get_fastapi_avdd_current(base_url, channel)
    
    return result


def run_sweep(load: KeysightEL34143A, start: float, stop: float, step: float,
              base_url: str, channel: int, skip_fastapi: bool, settling_time: float, 
              output_file: str, enable_output: bool = False):
    """Run current sweep and save results to CSV.
    
    Args:
        load: EL34143A electronic load instance
        start: Starting current in amperes
        stop: Stopping current in amperes
        step: Current step size in amperes
        base_url: FastAPI base URL
        channel: AVDD channel number (0, 1, etc.)
        skip_fastapi: Skip FastAPI query if True
        settling_time: Wait time after setting current
        output_file: CSV output filename
        enable_output: Enable load output if True
    """
    
    # Generate sweep points
    import numpy as np
    currents = np.arange(start, stop + step/2, step)  # Add step/2 to include stop
    total_points = len(currents)
    
    print_header(f"CURRENT SWEEP: {start}A to {stop}A in {step}A steps")
    print(f"Total measurement points: {total_points}")
    print(f"Settling time per point: {settling_time}s")
    print(f"Estimated duration: {total_points * settling_time:.1f}s (~{total_points * settling_time / 60:.1f} minutes)")
    print(f"Output file: {output_file}\n")
    
    # Determine the actual starting current (enforce minimum)
    actual_start = max(start, MIN_CURRENT)
    if start < MIN_CURRENT:
        print(f"{Fore.YELLOW}Note: Start current {start}A is below minimum {MIN_CURRENT}A (12mA){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}First setpoint will be corrected to {MIN_CURRENT}A{Style.RESET_ALL}\n")
    
    # Set initial current before enabling output
    print(f"{Fore.YELLOW}Setting initial current to {actual_start}A...{Style.RESET_ALL}")
    load.set_current(actual_start)
    time.sleep(0.5)  # Brief delay to ensure setpoint is applied
    print(f"{Fore.GREEN}✓ Initial current set{Style.RESET_ALL}\n")
    
    if enable_output:
        print(f"{Fore.YELLOW}Enabling load output...{Style.RESET_ALL}")
        load.enable_output()
        print(f"{Fore.GREEN}✓ Output enabled{Style.RESET_ALL}\n")
    
    # Open CSV file
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'setpoint_current', 'voltage', 'measured_current', 
                     'power', 'avdd_current', 'difference', 'difference_percent', 
                     'output_enabled']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Progress tracking
        start_time = time.time()
        
        for i, current_setpoint in enumerate(currents, 1):
            # Apply minimum current constraint
            actual_current = max(current_setpoint, MIN_CURRENT)
            
            # Set current
            load.set_current(actual_current)
            
            # Wait for settling
            time.sleep(settling_time)
            
            # Perform measurement
            result = perform_measurement(load, base_url, channel, skip_fastapi)
            
            # Calculate difference
            diff = None
            diff_percent = None
            if result['current'] is not None and result['avdd_current'] is not None:
                diff = result['current'] - result['avdd_current']
                diff_percent = (diff / result['avdd_current'] * 100) if result['avdd_current'] != 0 else 0
            
            # Write to CSV
            writer.writerow({
                'timestamp': result['timestamp'],
                'setpoint_current': actual_current,
                'voltage': result['voltage'],
                'measured_current': result['current'],
                'power': result['power'],
                'avdd_current': result['avdd_current'],
                'difference': diff,
                'difference_percent': diff_percent,
                'output_enabled': result['output_enabled']
            })
            
            # Progress update
            elapsed = time.time() - start_time
            eta = (elapsed / i) * (total_points - i)
            
            status_color = Fore.GREEN if result['output_enabled'] else Fore.YELLOW
            print(f"{status_color}[{i}/{total_points}] {actual_current:.4f}A → "
                  f"V={result['voltage']:.4f}V I={result['current']:.4f}A "
                  f"P={result['power']:.4f}W", end="")
            
            if result['avdd_current'] is not None:
                print(f" API={result['avdd_current']:.4f}A diff={diff:.4f}A", end="")
            
            print(f" (ETA: {eta:.0f}s){Style.RESET_ALL}")
    
    elapsed_total = time.time() - start_time
    print(f"\n{Fore.GREEN}✓ Sweep complete!{Style.RESET_ALL}")
    print(f"Total time: {elapsed_total:.1f}s ({elapsed_total/60:.1f} minutes)")
    print(f"Results saved to: {output_file}")


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
    
    # Load control arguments - single measurement
    parser.add_argument(
        '--set-current',
        type=float,
        metavar='AMPS',
        help='Set constant current load value in amperes (e.g., 0.1 for 100mA)'
    )
    
    # Sweep mode arguments
    parser.add_argument(
        '--sweep',
        action='store_true',
        help='Run current sweep mode (0 to 2A in 10mA steps by default)'
    )
    
    parser.add_argument(
        '--start',
        type=float,
        default=0.0,
        metavar='AMPS',
        help='Sweep start current in amperes (default: 0.0)'
    )
    
    parser.add_argument(
        '--stop',
        type=float,
        default=2.0,
        metavar='AMPS',
        help='Sweep stop current in amperes (default: 2.0)'
    )
    
    parser.add_argument(
        '--step',
        type=float,
        default=0.01,
        metavar='AMPS',
        help='Sweep step size in amperes (default: 0.01 = 10mA)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        metavar='FILE',
        help='Output CSV filename (default: auto-generated with timestamp)'
    )
    
    parser.add_argument(
        '-m', '--message',
        type=str,
        metavar='TEXT',
        help='Add message to output filename: el34143a_sweep_TIMESTAMP_message.csv'
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
        '--channel',
        type=int,
        default=0,
        metavar='N',
        help='AVDD channel number to query from API (0=AVDD1_0, 1=AVDD1_1, etc., default: 0)'
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
    
    # Validation
    if not args.sweep and args.set_current is None:
        parser.error("Either --sweep or --set-current must be specified")
    
    if args.sweep and args.set_current is not None:
        parser.error("Cannot use both --sweep and --set-current")
    
    # Import numpy if sweep mode
    if args.sweep:
        try:
            import numpy as np
        except ImportError:
            print(f"{Fore.RED}Error: numpy is required for sweep mode{Style.RESET_ALL}")
            print(f"Install with: pip install numpy")
            sys.exit(1)
    
    load = None
    try:
        # Connect to EL34143A
        header_title = "KEYSIGHT EL34143A SWEEP TEST" if args.sweep else "KEYSIGHT EL34143A DC ELECTRONIC LOAD TEST"
        print_header(header_title)
        
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
        
        # ==================== SWEEP MODE ====================
        if args.sweep:
            # Generate output filename if not provided
            if args.output is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if args.message:
                    # Sanitize message for filename (replace spaces and special chars)
                    safe_message = args.message.replace(' ', '_').replace('/', '-').replace('\\', '-')
                    args.output = f"el34143a_sweep_{timestamp}_ch{args.channel}_{safe_message}.csv"
                else:
                    args.output = f"el34143a_sweep_{timestamp}_ch{args.channel}.csv"
            
            # Run sweep
            run_sweep(
                load=load,
                start=args.start,
                stop=args.stop,
                step=args.step,
                base_url=args.base_url,
                channel=args.channel,
                skip_fastapi=args.skip_fastapi,
                settling_time=args.settling_time,
                output_file=args.output,
                enable_output=args.enable
            )
        
        # ==================== SINGLE MEASUREMENT MODE ====================
        else:
            # Validate and correct minimum current
            if args.set_current < MIN_CURRENT:
                print(f"{Fore.YELLOW}Warning: Requested current {args.set_current}A is below minimum {MIN_CURRENT}A (12mA){Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Correcting current to {MIN_CURRENT}A{Style.RESET_ALL}\n")
                args.set_current = MIN_CURRENT
            
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
                print_header(f"FASTAPI AVDD1_{args.channel} CURRENT")
                
                print(f"{Fore.YELLOW}Querying {args.base_url}/state for AVDD1_{args.channel}...{Style.RESET_ALL}")
                avdd_current = get_fastapi_avdd_current(args.base_url, args.channel)
                
                if avdd_current is not None:
                    print_measurement(f"AVDD1_{args.channel} current", avdd_current, "A")
                else:
                    print(f"{Fore.RED}✗ Could not retrieve AVDD1_{args.channel} current from FastAPI{Style.RESET_ALL}")
            
            # Comparison
            if current_load is not None and avdd_current is not None:
                print_header("COMPARISON")
                
                print_measurement("EL34143A measured current", current_load, "A")
                print_measurement(f"FastAPI AVDD1_{args.channel} current", avdd_current, "A")
                
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
