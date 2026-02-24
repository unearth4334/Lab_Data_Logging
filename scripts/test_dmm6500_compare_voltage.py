#!/usr/bin/env python
"""
Test script to compare DMM6500 voltage measurements with AVDD1 voltage from FastAPI.

This script tests AVDD1 voltage accuracy across different margin bit settings:
- 00 (margin25=0, margin50=0): +0mV   → 1.200V nominal
- 01 (margin25=1, margin50=0): +25mV  → 1.225V nominal
- 10 (margin25=0, margin50=1): +50mV  → 1.250V nominal
- 11 (margin25=1, margin50=1): +75mV  → 1.275V nominal

For each setting:
1. Configures margin bits via FastAPI
2. Waits for settling time
3. Measures voltage using DMM6500
4. Queries AVDD1 voltage from the FastAPI endpoint
5. Compares the measurements and saves to CSV

Usage:
    # Auto-connect to DMM6500 (recommended)
    python test_dmm6500_compare_voltage.py -m "045695-1 00004_VMON" --channel 0 --settling-time 2
    
    # Specify VISA address explicitly
    python test_dmm6500_compare_voltage.py --address "TCPIP0::169.254.66.84::inst0::INSTR" -m "045695-1 00004_VMON" --channel 1
    python test_dmm6500_compare_voltage.py --address "TCPIP0::169.254.66.84::inst0::INSTR" --channel 1 --base-url http://127.0.0.1:7860
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

from DMM6500 import DMM6500

# Check for requests library
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Initialize colorama for Windows color support
colorama_init()

# Margin bit test cases: (margin25, margin50, voltage_offset_mv, label)
MARGIN_TEST_CASES = [
    (False, False, 0, "00_+0mV"),
    (True, False, 25, "01_+25mV"),
    (False, True, 50, "10_+50mV"),
    (True, True, 75, "11_+75mV"),
]


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


def set_margin_bits(base_url: str, channel: int, margin25: bool, margin50: bool, debug: bool = False) -> bool:
    """Set margin bits for specified AVDD1 channel via FastAPI.
    
    Margin channels have a 2:1 relationship with AVDD1 channels:
    - Margin channel 0 → AVDD1 channels 0 and 1
    - Margin channel 1 → AVDD1 channels 2 and 3
    - Margin channel 2 → AVDD1 channels 4 and 5
    - etc.
    
    Args:
        base_url: FastAPI base URL
        channel: AVDD1 channel number (0, 1, 2, etc.)
        margin25: Enable +25mV margin
        margin50: Enable +50mV margin
        debug: Print debug information
    
    Returns:
        True if successful, False otherwise
    """
    if not REQUESTS_AVAILABLE:
        print(f"{Fore.YELLOW}Warning: 'requests' module not installed. Cannot set margin bits.{Style.RESET_ALL}")
        return False
    
    try:
        url = f"{base_url.rstrip('/')}/margin"
        
        # Calculate margin channel from AVDD1 channel (2:1 mapping)
        margin_channel = channel // 2
        
        # Set margin25 bit
        margin25_name = f"margin25_{margin_channel}"
        resp25 = requests.post(url, json={"name": margin25_name, "enable": margin25}, timeout=5)
        resp25.raise_for_status()
        
        # Set margin50 bit
        margin50_name = f"margin50_{margin_channel}"
        resp50 = requests.post(url, json={"name": margin50_name, "enable": margin50}, timeout=5)
        resp50.raise_for_status()
        
        if debug:
            print(f"{Fore.CYAN}Debug: AVDD1 channel {channel} → Margin channel {margin_channel}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Debug: Set {margin25_name}={margin25}, {margin50_name}={margin50}{Style.RESET_ALL}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"{Fore.YELLOW}Warning: Could not set margin bits at {base_url}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Error: {e}{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Error setting margin bits: {e}{Style.RESET_ALL}")
        return False


def get_fastapi_avdd_voltage(base_url: str, channel: int = 0, debug: bool = False) -> Optional[float]:
    """Query AVDD1_X voltage from FastAPI endpoint.
    
    Args:
        base_url: FastAPI base URL
        channel: AVDD1 channel number (0, 1, etc.)
        debug: Print debug information
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
        
        # Construct field name: avdd1_0_voltage, avdd1_1_voltage, etc.
        field_name = f"avdd1_{channel}_voltage"
        
        if debug:
            print(f"{Fore.CYAN}Debug: Looking for field '{field_name}' in monitor_data{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Debug: Available fields: {list(monitor.keys())}{Style.RESET_ALL}")
        
        value = monitor.get(field_name)
        
        if debug:
            print(f"{Fore.CYAN}Debug: Retrieved value: {value}{Style.RESET_ALL}")
        
        return value
    except requests.exceptions.RequestException as e:
        print(f"{Fore.YELLOW}Warning: Could not connect to FastAPI at {base_url}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Error: {e}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Error parsing FastAPI response: {e}{Style.RESET_ALL}")
        return None


def perform_measurement(dmm: DMM6500, base_url: str, channel: int = 0, 
                       margin25: bool = False, margin50: bool = False,
                       skip_fastapi: bool = False, debug: bool = False) -> Dict[str, Any]:
    """
    Perform a single voltage measurement from DMM6500 and FastAPI.
    
    Args:
        dmm: DMM6500 multimeter instance
        base_url: FastAPI base URL
        channel: AVDD channel number (0, 1, etc.)
        margin25: Margin25 bit setting
        margin50: Margin50 bit setting
        skip_fastapi: Skip FastAPI query if True
        debug: Enable debug output
    
    Returns dict with keys: voltage, avdd_voltage, margin25, margin50, timestamp
    """
    result = {
        'timestamp': datetime.now().isoformat(),
        'voltage': None,
        'avdd_voltage': None,
        'margin25': margin25,
        'margin50': margin50
    }
    
    # Measure voltage from DMM6500
    result['voltage'] = dmm.measure_voltage()
    
    # Query FastAPI
    if not skip_fastapi:
        result['avdd_voltage'] = get_fastapi_avdd_voltage(base_url, channel, debug)
    
    return result


def run_margin_test(dmm: DMM6500, base_url: str, channel: int, 
                    skip_fastapi: bool, settling_time: float, output_file: str, 
                    debug: bool = False):
    """Run margin bit voltage test and save results to CSV.
    
    Args:
        dmm: DMM6500 multimeter instance
        base_url: FastAPI base URL
        channel: AVDD channel number (0, 1, etc.)
        skip_fastapi: Skip FastAPI query if True
        settling_time: Wait time after setting margin bits
        output_file: CSV output filename
        debug: Enable debug output
    """
    
    total_points = len(MARGIN_TEST_CASES)
    
    print_header(f"AVDD1 VOLTAGE MARGIN TEST - Channel {channel}")
    print(f"Test cases: {total_points} margin bit combinations")
    print(f"Settling time per test: {settling_time}s")
    print(f"Estimated duration: {total_points * settling_time:.1f}s")
    print(f"Output file: {output_file}\n")
    
    # Open CSV file
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'margin25', 'margin50', 'voltage_offset_mv', 'case_label',
                     'measured_voltage', 'avdd_voltage', 'difference', 'difference_percent']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Progress tracking
        start_time = time.time()
        
        for i, (margin25, margin50, offset_mv, label) in enumerate(MARGIN_TEST_CASES, 1):
            print(f"{Fore.CYAN}[{i}/{total_points}] Testing case: {label} "
                  f"(margin25={margin25}, margin50={margin50}){Style.RESET_ALL}")
            
            # Set margin bits
            if not skip_fastapi:
                if not set_margin_bits(base_url, channel, margin25, margin50, debug):
                    print(f"{Fore.RED}Failed to set margin bits, continuing anyway...{Style.RESET_ALL}")
            
            # Wait for settling
            print(f"  Waiting {settling_time}s for settling...")
            time.sleep(settling_time)
            
            # Perform measurement
            result = perform_measurement(dmm, base_url, channel, margin25, margin50, skip_fastapi, debug)
            
            # Calculate difference
            diff = None
            diff_percent = None
            if result['voltage'] is not None and result['avdd_voltage'] is not None:
                diff = result['voltage'] - result['avdd_voltage']
                diff_percent = (diff / result['avdd_voltage'] * 100) if result['avdd_voltage'] != 0 else 0
            
            # Write to CSV
            writer.writerow({
                'timestamp': result['timestamp'],
                'margin25': margin25,
                'margin50': margin50,
                'voltage_offset_mv': offset_mv,
                'case_label': label,
                'measured_voltage': result['voltage'],
                'avdd_voltage': result['avdd_voltage'],
                'difference': diff,
                'difference_percent': diff_percent
            })
            
            # Display results
            print(f"{Fore.GREEN}  DMM: V={result['voltage']:.6f}V", end="")
            
            if result['avdd_voltage'] is not None:
                print(f" | API: V={result['avdd_voltage']:.6f}V | "
                      f"Δ={diff:.6f}V ({diff_percent:.4f}%)", end="")
            
            print(f"{Style.RESET_ALL}\n")
    
    # Reset margin bits to 00 after test
    if not skip_fastapi:
        print(f"{Fore.YELLOW}Resetting margin bits to 00...{Style.RESET_ALL}")
        if set_margin_bits(base_url, channel, False, False, debug):
            print(f"{Fore.GREEN}✓ Margin bits reset{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to reset margin bits{Style.RESET_ALL}")
    
    elapsed_total = time.time() - start_time
    print(f"\n{Fore.GREEN}✓ Margin test complete!{Style.RESET_ALL}")
    print(f"Total time: {elapsed_total:.1f}s")
    print(f"Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Compare DMM6500 voltage measurements with FastAPI AVDD1 voltage across margin bit settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Connection arguments
    parser.add_argument(
        '--address',
        type=str,
        default=None,
        help='VISA address of DMM6500 (e.g., "TCPIP0::169.254.66.84::inst0::INSTR"). If not provided, auto-connect will be used.'
    )
    
    # Test arguments
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
        help='Add message to output filename: dmm6500_voltage_TIMESTAMP_chX_message.csv'
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
        help='AVDD1 channel number (0, 1, 2, etc.) (default: 0)'
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
        help='Wait time after setting margin bits before measuring (default: 2.0s)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    
    args = parser.parse_args()
    
    dmm = None
    try:
        # Connect to DMM6500
        print_header("KEITHLEY DMM6500 VOLTAGE MARGIN TEST")
        
        if args.address:
            print(f"{Fore.YELLOW}Connecting to DMM6500 at {args.address}...{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Auto-connecting to DMM6500...{Style.RESET_ALL}")
        
        try:
            if args.address:
                dmm = DMM6500(address=args.address, debug=args.debug)
            else:
                dmm = DMM6500(auto_connect=True, debug=args.debug)
        except Exception as e:
            print(f"\n{Fore.RED}Connection failed: {e}{Style.RESET_ALL}")
            sys.exit(1)
        
        # Generate output filename if not provided
        if args.output is None:
            # Create output directory
            output_dir = os.path.join("output", "ELE-11 (AVDD1 and VDDIO Voltage Sensor Test)")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if args.message:
                # Sanitize message for filename
                safe_message = args.message.replace(' ', '_').replace('/', '-').replace('\\', '-')
                filename = f"{timestamp}_ELE-11-dmm6500_{safe_message}_AVDD1_MM{args.channel}.csv"
            else:
                filename = f"{timestamp}_ELE-11-dmm6500_AVDD1_MM{args.channel}.csv"
            
            args.output = os.path.join(output_dir, filename)
        
        # Run margin test
        run_margin_test(
            dmm=dmm,
            base_url=args.base_url,
            channel=args.channel,
            skip_fastapi=args.skip_fastapi,
            settling_time=args.settling_time,
            output_file=args.output,
            debug=args.debug
        )
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Cleanup
        if dmm is not None:
            try:
                dmm.disconnect()
                print(f"\n{Fore.GREEN}✓ Disconnected from DMM6500{Style.RESET_ALL}")
            except:
                pass


if __name__ == "__main__":
    main()
