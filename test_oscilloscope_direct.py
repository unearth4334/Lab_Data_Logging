#!/usr/bin/env python3
"""
test_oscilloscope_direct.py

Lab Data Logging - Direct Test of Keysight MSOX4154A Oscilloscope

This script demonstrates direct usage of the KeysightMSOX4154A driver without 
the data_logger framework. Useful for testing specific oscilloscope functionality
and understanding the underlying measurement capabilities.

Usage:
    python test_oscilloscope_direct.py [VISA_ADDRESS]
    
    If no VISA address is provided, the script will attempt auto-detection.
    
    Example with specific address:
    python test_oscilloscope_direct.py "USB0::0x0957::0x17BC::MY59241237::INSTR"

Requirements:
    - Python 3.x
    - Virtual environment with dependencies installed (see requirements.txt)
    - Keysight MSOX4154A oscilloscope connected via USB/LAN

Author: Redlen Technologies Lab Automation Team  
Date: 2024-09
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add libs directory to path
sys.path.append('./libs')
from KeysightMSOX4154A import KeysightMSOX4154A

def test_basic_connection():
    """Test basic connection and identification."""
    print("\n1. Testing Basic Connection")
    print("-" * 40)
    
    osc = KeysightMSOX4154A(auto_connect=False)
    
    if len(sys.argv) > 1:
        # Use provided VISA address
        visa_address = sys.argv[1]
        print(f"Connecting to specific address: {visa_address}")
        osc.connect(visa_address)
    else:
        # Auto-detect
        print("Auto-detecting oscilloscope...")
        osc.connect()
    
    # Get identification
    idn = osc.get_idn()
    print(f"Instrument ID: {idn}")
    
    return osc

def test_measurements(osc):
    """Test various measurement capabilities."""
    print("\n2. Testing Voltage Measurements")
    print("-" * 40)
    
    channels = ["CHAN1", "CHAN2"]
    
    for channel in channels:
        print(f"\n{channel} Measurements:")
        try:
            # Get voltage measurements
            voltage_meas = osc.get_voltage_measurements(channel)
            
            for param, value in voltage_meas.items():
                if not (value != value):  # Check if not NaN
                    print(f"  {param:12s}: {value:10.6f} V")
                else:
                    print(f"  {param:12s}: No signal")
                    
        except Exception as e:
            print(f"  Error measuring {channel}: {e}")
    
    print("\n3. Testing Timing Measurements")  
    print("-" * 40)
    
    for channel in channels:
        print(f"\n{channel} Timing:")
        try:
            # Get timing measurements
            timing_meas = osc.get_timing_measurements(channel)
            
            for param, value in timing_meas.items():
                if not (value != value):  # Check if not NaN
                    if param == "FREQuency":
                        print(f"  {param:12s}: {value:10.2f} Hz")
                    elif param == "PERiod":
                        print(f"  {param:12s}: {value:10.3e} s")
                    elif param == "DCYCle":
                        print(f"  {param:12s}: {value:10.2f} %")
                    else:
                        print(f"  {param:12s}: {value:10.3e} s")
                else:
                    print(f"  {param:12s}: No signal")
                    
        except Exception as e:
            print(f"  Error measuring timing on {channel}: {e}")

def test_statistics_interface(osc):
    """Test the standardized statistics interface."""
    print("\n4. Testing Statistics Interface (data_logger compatible)")
    print("-" * 60)
    
    channels = [1, 2]  # Channel numbers for get() interface
    
    for channel in channels:
        print(f"\nCHAN{channel} Statistics Interface:")
        
        try:
            # Test statistics (returns [avg, std_dev, min, max])
            stats = osc.get("statistics", channel)
            if len(stats) == 4:
                avg, std_dev, min_val, max_val = stats
                print(f"  Statistics: avg={avg:.6f}, std={std_dev:.6f}, min={min_val:.6f}, max={max_val:.6f}")
            else:
                print(f"  Statistics: {stats}")
            
            # Test individual measurements
            voltage = osc.get("voltage", channel)
            voltage_rms = osc.get("voltage_rms", channel)
            frequency = osc.get("frequency", channel)
            
            print(f"  Voltage (avg): {voltage:.6f} V")
            print(f"  Voltage (RMS): {voltage_rms:.6f} V") 
            print(f"  Frequency:     {frequency:.2f} Hz")
            
        except Exception as e:
            print(f"  Error with CHAN{channel}: {e}")

def test_waveform_capture(osc):
    """Test waveform data capture and analysis."""
    print("\n5. Testing Waveform Capture")
    print("-" * 40)
    
    channels = ["CHAN1", "CHAN2"]
    
    for channel in channels:
        print(f"\n{channel} Waveform:")
        try:
            # Capture waveform
            t, y, meta = osc.get_waveform(source=channel, debug=True)
            
            if y:
                print(f"  Samples:      {len(y)}")
                print(f"  Duration:     {t[-1] - t[0]:.6f} s")
                print(f"  Sample Rate:  {meta.get('sample_rate_hz', 0):.0f} Hz")
                print(f"  Voltage Range: {min(y):.6f} to {max(y):.6f} V")
                
                # Calculate some basic statistics
                import statistics as stats
                avg = stats.mean(y)
                std_dev = stats.stdev(y) if len(y) > 1 else 0
                print(f"  Mean:         {avg:.6f} V")
                print(f"  Std Dev:      {std_dev:.6f} V")
            else:
                print(f"  No waveform data available")
                
        except Exception as e:
            print(f"  Error capturing {channel}: {e}")

def save_test_results(osc):
    """Save test results to file.""" 
    print("\n6. Saving Test Results")
    print("-" * 40)
    
    # Create output directory
    output_dir = Path("captures")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Save comprehensive statistics
        results_file = output_dir / f"oscilloscope_test_results_{timestamp}.txt"
        
        with open(results_file, 'w') as f:
            f.write("Keysight MSOX4154A Test Results\n")
            f.write("=" * 50 + "\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Instrument: {osc.get_idn()}\n\n")
            
            # Test each channel
            for channel_num in [1, 2]:
                channel_str = f"CHAN{channel_num}"
                f.write(f"{channel_str} Results:\n")
                f.write("-" * 20 + "\n")
                
                try:
                    # Get all statistics
                    stats = osc.get_statistics(channel_str)
                    
                    for key, value in stats.items():
                        if key != "error":
                            f.write(f"{key}: {value}\n")
                    f.write("\n")
                    
                except Exception as e:
                    f.write(f"Error: {e}\n\n")
        
        print(f"Results saved to: {results_file}")
        
    except Exception as e:
        print(f"Error saving results: {e}")

def main():
    """Main test execution."""
    
    print("Keysight MSOX4154A Direct Test")
    print("=" * 50)
    
    osc = None
    
    try:
        # Test connection
        osc = test_basic_connection()
        
        # Run measurement tests
        test_measurements(osc)
        test_statistics_interface(osc)
        test_waveform_capture(osc)
        save_test_results(osc)
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Disconnect oscilloscope
        if osc is not None:
            try:
                osc.disconnect()
            except:
                pass
                
    print("\nTest finished.")

if __name__ == "__main__":
    main()