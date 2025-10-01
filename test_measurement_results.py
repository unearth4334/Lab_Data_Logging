#!/usr/bin/env python3
"""
Test Script for Keysight MSOX4154A Measurement Results Query

This script demonstrates the :MEASure:RESults? query functionality which returns
the results of all continuously displayed measurements on the oscilloscope.

The script will:
1. Connect to the oscilloscope
2. Check current measurement statistics mode
3. Query all measurement results using :MEASure:RESults?
4. Parse and display the results in a readable format
5. Save results to a file
6. Take a screenshot

Usage:
    python test_measurement_results.py [VISA_ADDRESS] [--output-dir OUTPUT_DIR]

Requirements:
    - Keysight MSOX4154A oscilloscope connected
    - Measurements configured on the oscilloscope (manually or via software)
    - Signal present for meaningful measurements

Author: Redlen Technologies Lab Automation Team
Date: 2025-10
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add current directory to path for imports
sys.path.append('.')
from libs.KeysightMSOX4154A import KeysightMSOX4154A

def test_measurement_results(visa_address=None, output_dir="captures"):
    """
    Test the measurement results query functionality.
    
    Args:
        visa_address: Optional specific VISA address to connect to
        output_dir: Directory to save results (default: "captures")
    """
    
    print("Keysight MSOX4154A Measurement Results Test")
    print("=" * 50)
    print("Testing :MEASure:RESults? query functionality")
    print()
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    print(f"Output directory: {output_path.absolute()}")
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    waveforms_saved = []  # Initialize waveform save list
    
    try:
        # Connect to oscilloscope
        print("\nConnecting to Keysight MSOX4154A...")
        if visa_address:
            osc = KeysightMSOX4154A(auto_connect=False)
            osc.connect(visa_address)
        else:
            osc = KeysightMSOX4154A()
        
        print("Connected successfully!")
        
        # Stop oscilloscope acquisition
        print("\nStopping oscilloscope acquisition...")
        osc.stop()
        
        # Get measurement results
        print("Querying measurement results using :MEASure:RESults?...")
        results = osc.get_measurement_results()
        
        # Display results
        print("\n" + "=" * 60)
        print("MEASUREMENT RESULTS")
        print("=" * 60)
        
        print(f"Statistics Mode: {results['statistics_mode']}")
        print(f"Raw Response: {results['raw_response']}")
        print()
        
        if results['parsed_results']:
            print(f"Found {len(results['parsed_results'])} measurement(s):")
            print()
            
            # Display based on statistics mode
            if results['statistics_mode'] == "1" or results['statistics_mode'].upper() == "ON":
                # Full statistics mode
                for i, measurement in enumerate(results['parsed_results'], 1):
                    print(f"Measurement {i}: {measurement['label']}")
                    print(f"  Current:    {measurement['current']:.6f}")
                    print(f"  Minimum:    {measurement['minimum']:.6f}")
                    print(f"  Maximum:    {measurement['maximum']:.6f}")
                    print(f"  Mean:       {measurement['mean']:.6f}")
                    print(f"  Std Dev:    {measurement['std_dev']:.6f}")
                    print(f"  Count:      {measurement['count']}")
                    print()
            else:
                # Single statistic mode
                print(f"Single statistic mode: {results['statistics_mode']}")
                for measurement in results['parsed_results']:
                    print(f"  Measurement {measurement['measurement_index']}: {measurement['value']:.6f}")
        else:
            print("No measurement results available")
            print("Make sure measurements are configured and running on the oscilloscope")
        
        # Save results to file
        output_file = output_path / f"measurement_results_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write("Keysight MSOX4154A Measurement Results\n")
            f.write("=" * 50 + "\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Statistics Mode: {results['statistics_mode']}\n")
            f.write(f"Raw Response: {results['raw_response']}\n\n")
            
            if results['parsed_results']:
                f.write(f"Parsed Results ({len(results['parsed_results'])} measurements):\n")
                f.write("-" * 40 + "\n")
                
                if results['statistics_mode'] == "1" or results['statistics_mode'].upper() == "ON":
                    for i, measurement in enumerate(results['parsed_results'], 1):
                        f.write(f"\nMeasurement {i}: {measurement['label']}\n")
                        f.write(f"  Current:    {measurement['current']:.6f}\n")
                        f.write(f"  Minimum:    {measurement['minimum']:.6f}\n")
                        f.write(f"  Maximum:    {measurement['maximum']:.6f}\n")
                        f.write(f"  Mean:       {measurement['mean']:.6f}\n")
                        f.write(f"  Std Dev:    {measurement['std_dev']:.6f}\n")
                        f.write(f"  Count:      {measurement['count']}\n")
                else:
                    for measurement in results['parsed_results']:
                        f.write(f"  Measurement {measurement['measurement_index']}: {measurement['value']:.6f}\n")
            else:
                f.write("No measurement results available\n")
        
        print(f"Results saved to: {output_file}")
        
        # Take screenshot
        print("\nCapturing screenshot...")
        screenshot_file = output_path / f"measurement_results_screenshot_{timestamp}.png"
        
        try:
            success = osc.save_screenshot(str(screenshot_file), inksaver=False)
            if success:
                print(f"Screenshot saved: {screenshot_file}")
            else:
                print("Screenshot capture failed")
        except Exception as e:
            print(f"Screenshot error: {e}")
        
        # Capture waveforms
        print("\nCapturing waveform data...")
        waveforms_saved = []
        
        # Capture CH1 waveform
        print("  Capturing CH1...")
        ch1_waveform_file = output_path / f"ch1_waveform_{timestamp}.csv"
        
        try:
            t, y, meta = osc.get_waveform(source="CHAN1", debug=True)
            
            if y and len(y) > 0:
                # Save waveform to CSV
                import csv
                with open(ch1_waveform_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Time_s", "Voltage_V"])
                    writer.writerows(zip(t, y))
                
                print(f"    CH1 saved: {ch1_waveform_file}")
                print(f"    Samples: {len(y)}, Duration: {t[-1] - t[0]:.6f} s, Rate: {meta.get('sample_rate_hz', 0):.0f} Hz")
                waveforms_saved.append(('CH1', ch1_waveform_file))
            else:
                print("    No CH1 waveform data available")
                
        except Exception as e:
            print(f"    CH1 waveform capture failed: {e}")
        
        # Capture M1 waveform
        print("  Capturing M1 (Math1)...")
        m1_waveform_file = output_path / f"m1_waveform_{timestamp}.csv"
        
        try:
            t, y, meta = osc.get_waveform(source="MATH1", debug=True)
            
            if y and len(y) > 0:
                # Save waveform to CSV
                import csv
                with open(m1_waveform_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Time_s", "Value"])
                    writer.writerows(zip(t, y))
                
                print(f"    M1 saved: {m1_waveform_file}")
                print(f"    Samples: {len(y)}, Duration: {t[-1] - t[0]:.6f} s, Rate: {meta.get('sample_rate_hz', 0):.0f} Hz")
                waveforms_saved.append(('M1', m1_waveform_file))
            else:
                print("    No M1 waveform data available")
                
        except Exception as e:
            print(f"    M1 waveform capture failed: {e}")
        
        waveform_saved = len(waveforms_saved) > 0
        
        # Restart oscilloscope acquisition
        print("\nRestarting oscilloscope acquisition...")
        osc.run()
        
        # Disconnect
        osc.disconnect()
        print("Disconnected from oscilloscope")
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Statistics Mode: {results['statistics_mode']}")
        print(f"Measurements Found: {len(results['parsed_results'])}")
        print(f"Raw Response Length: {len(results['raw_response'])} chars")
        
        print("\nFiles Generated:")
        print(f"  Results:    {output_file}")
        print(f"  Screenshot: {screenshot_file}")
        if waveforms_saved:
            print(f"  Waveforms:  {len(waveforms_saved)} files saved")
            for source, filepath in waveforms_saved:
                print(f"    {source}: {filepath}")
        else:
            print(f"  Waveforms:  (none saved)")
        
        return results
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to restart oscilloscope before failing
        try:
            if 'osc' in locals():
                print("Attempting to restart oscilloscope before exit...")
                osc.run()
        except:
            pass
            
        return None

def main():
    """Main execution function."""
    
    print("Keysight MSOX4154A - Measurement Results Query Test")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Test :MEASure:RESults? query on Keysight MSOX4154A oscilloscope",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script tests the :MEASure:RESults? query which returns results of all
continuously displayed measurements. The response format depends on the
:MEASure:STATistics setting:

- Statistics ON: Returns label, current, min, max, mean, std dev, count
- Statistics set to specific mode: Returns only that statistic value

Examples:
  python test_measurement_results.py
  python test_measurement_results.py "USB0::0x0957::0x17BC::MY56310625::INSTR"
  python test_measurement_results.py --output-dir ./results
        """
    )
    
    parser.add_argument(
        "visa_address",
        nargs="?",
        help="VISA address of the oscilloscope (optional, will auto-detect if not provided)"
    )
    
    parser.add_argument(
        "-o", "--output-dir",
        default="captures",
        help="Output directory for results and screenshots (default: captures)"
    )
    
    args = parser.parse_args()
    
    print()
    
    if args.visa_address:
        print(f"Using specified VISA address: {args.visa_address}")
    else:
        print("Using auto-detection for VISA address")
    
    print(f"Output directory: {args.output_dir}")
    print()
    
    # Run the test
    results = test_measurement_results(args.visa_address, args.output_dir)
    
    if results:
        print("\nMeasurement results test completed successfully!")
    else:
        print("\nMeasurement results test failed!")
    
    print("\nTest finished.")

if __name__ == "__main__":
    main()