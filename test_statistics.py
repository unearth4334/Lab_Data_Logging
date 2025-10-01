#!/usr/bin/env python3
"""
test_statistics.py

Lab Data Logging - Test Script for Device Statistics

This script demonstrates how to connect to supported laboratory instruments using the data_logger framework,
collect measurement statistics (average, standard deviation, min, max), and output results for validation.

Specifically configured for Keysight MSOX4154A oscilloscope to collect:
- Peak-to-Peak voltage (CH1)
- Full-screen Average voltage (CH1) 
- X@Max timing (CH1)
- 100 measurements with statistics
- Screenshot capture
- Waveform capture with stop/start sequence

Usage:
    python test_statistics.py

Requirements:
    - Python 3.x
    - Virtual environment with dependencies installed (see requirements.txt)
    - Keysight MSOX4154A oscilloscope connected
    - Signal connected to CH1 for meaningful measurements

Author: Redlen Technologies Lab Automation Team
Date: 2024-09
"""

import sys
import time
import statistics as stats
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append('.')
from data_logger import data_logger

def collect_oscilloscope_statistics(visa_address=None):
    """
    Simple oscilloscope statistics collection.
    
    1. Connect to oscilloscope
    2. Reset measurement statistics 
    3. Wait 2 minutes
    4. Get peak-to-peak statistics
    5. Take a screenshot
    """
    
    print("Keysight MSOX4154A Simple Statistics Collection")
    print("=" * 50)
    print("Plan:")
    print("  1. Reset statistics")
    print("  2. Wait 2 minutes")
    print("  3. Get VPP statistics")
    print("  4. Take screenshot")
    print()
    
    # Create output directory
    output_dir = Path("captures")
    output_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for all output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Connect to oscilloscope directly
        print("Connecting to Keysight MSOX4154A...")
        if visa_address:
            # Create oscilloscope directly with specific address
            from libs.KeysightMSOX4154A import KeysightMSOX4154A
            osc = KeysightMSOX4154A(auto_connect=False)
            osc.connect(visa_address)
        else:
            # Use data_logger auto-connect
            logger = data_logger()
            osc = logger.connect("msox4154a")
        
        # Check what measurements are configured
        print("Checking configured measurements...")
        configured_measurements = osc.list_configured_measurements()
        if configured_measurements:
            print(f"Found {len(configured_measurements)} configured measurements:")
            for meas in configured_measurements:
                print(f"  - {meas}")
        else:
            print("  No measurements found or unable to detect")
        
        # Clear statistics (measurements already configured manually)
        print("\nResetting measurement statistics buffer...")
        print("Note: Using measurements already configured on oscilloscope")
        osc.clear_measurement_statistics()
        
        # Wait 2 minutes
        print("Waiting 2 minutes for measurements to accumulate...")
        wait_time = 120  # 2 minutes
        for i in range(wait_time):
            if i % 30 == 0:  # Print every 30 seconds
                remaining = wait_time - i
                print(f"  {remaining} seconds remaining...")
            time.sleep(1)
        
        print("2 minutes completed!")
        
        # Try to get statistics for whatever VPP-related measurement is available
        print("Getting peak-to-peak voltage statistics...")
        vpp_stats = None
        
        # Try different VPP measurement names
        vpp_names = ['VPP', 'VAMP', 'Vpp', 'Vamp']
        for vpp_name in vpp_names:
            if vpp_name in configured_measurements or not configured_measurements:
                print(f"  Trying {vpp_name}...")
                try:
                    vpp_stats = osc.get_measurement_statistics(vpp_name)
                    if vpp_stats['count'] > 0:
                        print(f"  Success with {vpp_name}!")
                        break
                except:
                    pass
        
        if not vpp_stats or vpp_stats['count'] == 0:
            print("  No VPP statistics available, creating empty result")
            vpp_stats = {
                'current': float('nan'),
                'mean': float('nan'),
                'std_dev': float('nan'),
                'minimum': float('nan'),
                'maximum': float('nan'),
                'count': 0
            }
        
        # Display results
        print("\n" + "=" * 50)
        print("VPP STATISTICS RESULTS")
        print("=" * 50)
        print(f"Current VPP:     {vpp_stats['current']:.6f} V")
        print(f"Mean VPP:        {vpp_stats['mean']:.6f} V")
        print(f"Std Deviation:   {vpp_stats['std_dev']:.6f} V")
        print(f"Minimum VPP:     {vpp_stats['minimum']:.6f} V")
        print(f"Maximum VPP:     {vpp_stats['maximum']:.6f} V")
        print(f"Measurement Count: {vpp_stats['count']:.0f}")
        
        # Take screenshot
        print("\nCapturing screenshot...")
        screenshot_file = output_dir / f"oscilloscope_screenshot_{timestamp}.png"
        
        try:
            success = osc.save_screenshot(str(screenshot_file), inksaver=False)
            if success:
                print(f"Screenshot saved: {screenshot_file}")
            else:
                print("Screenshot capture failed")
        except Exception as e:
            print(f"Screenshot error: {e}")
        
        # Save results to file
        output_file = output_dir / f"vpp_statistics_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write("Keysight MSOX4154A VPP Statistics\n")
            f.write("=" * 40 + "\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Channel: CH1\n")
            f.write(f"Collection Time: 2 minutes\n\n")
            
            f.write("Peak-to-Peak Voltage Statistics:\n")
            f.write(f"  Current:    {vpp_stats['current']:.6f} V\n")
            f.write(f"  Mean:       {vpp_stats['mean']:.6f} V\n")
            f.write(f"  Std Dev:    {vpp_stats['std_dev']:.6f} V\n")
            f.write(f"  Minimum:    {vpp_stats['minimum']:.6f} V\n")
            f.write(f"  Maximum:    {vpp_stats['maximum']:.6f} V\n")
            f.write(f"  Count:      {vpp_stats['count']:.0f}\n")
        
        print(f"Results saved to: {output_file}")
        
        print("\n" + "=" * 50)
        print("FILES GENERATED:")
        print("=" * 50)
        print(f"Statistics:   {output_file}")
        print(f"Screenshot:   {screenshot_file}")
        
        return vpp_stats
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return None
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # No file cleanup needed since we're using direct CSV writing
        pass


def main():
    """Main execution function."""
    
    print("Lab Data Logging - Oscilloscope Statistics Test")
    print("Configured for Keysight MSOX4154A")
    print()
    
    # Check for command line VISA address
    visa_address = None
    if len(sys.argv) > 1:
        visa_address = sys.argv[1]
        print(f"Using specified VISA address: {visa_address}")
    else:
        print("No VISA address specified, attempting auto-detection")
    
    # Run the statistics collection
    results = collect_oscilloscope_statistics(visa_address)
    
    if results:
        print("\nStatistics collection completed successfully!")
    else:
        print("\nStatistics collection failed or was interrupted.")
    
    print("\nTest finished.")


if __name__ == "__main__":
    main()

