#!/usr/bin/env python3
"""
test_msox4154a_simple.py

Lab Data Logging - Simple Test Script for Keysight MSOX4154A Oscilloscope

This script demonstrates how to use the Keysight MSOX4154A oscilloscope with the 
data_logger framework to collect basic measurement statistics.

Usage:
    python test_msox4154a_simple.py

Requirements:
    - Python 3.x
    - Virtual environment with dependencies installed (see requirements.txt)
    - Keysight MSOX4154A oscilloscope connected via USB/LAN
    - Signal connected to oscilloscope channels for meaningful measurements

Author: Redlen Technologies Lab Automation Team
Date: 2024-09
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add current directory to path for data_logger import
sys.path.append('.')
from data_logger import data_logger

def main():
    """Main test execution using data_logger framework."""
    
    print("Keysight MSOX4154A Statistics Test (data_logger framework)")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("captures")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize data logger
    logger = data_logger()
    
    try:
        # Create timestamped output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"msox4154a_measurements_{timestamp}.txt"
        logger.new_file(str(output_file))
        
        # Connect to oscilloscope
        print("Connecting to Keysight MSOX4154A...")
        osc = logger.connect("msox4154a")
        
        # Add various measurements to the logger
        # These will be collected each time get_data() is called
        
        print("Setting up measurements...")
        
        # Channel 1 measurements
        logger.add("CH1_Statistics", osc, "statistics", channel=1)
        logger.add("CH1_Voltage", osc, "voltage", channel=1)
        logger.add("CH1_Voltage_RMS", osc, "voltage_rms", channel=1)
        logger.add("CH1_Voltage_PP", osc, "voltage_pp", channel=1)
        logger.add("CH1_Frequency", osc, "frequency", channel=1)
        
        # Channel 2 measurements (if signal present)
        logger.add("CH2_Statistics", osc, "statistics", channel=2)
        logger.add("CH2_Voltage", osc, "voltage", channel=2)
        logger.add("CH2_Voltage_RMS", osc, "voltage_rms", channel=2)
        
        # Collect measurements multiple times
        num_measurements = 5
        print(f"\nCollecting {num_measurements} sets of measurements...")
        
        for i in range(num_measurements):
            print(f"\nMeasurement {i+1}/{num_measurements}:")
            measurements = logger.get_data()
            
            # Display some key measurements
            ch1_voltage = measurements.get("CH1_Voltage", "N/A")
            ch1_freq = measurements.get("CH1_Frequency", "N/A")
            ch2_voltage = measurements.get("CH2_Voltage", "N/A")
            
            if isinstance(ch1_voltage, float) and not (ch1_voltage != ch1_voltage):  # Check not NaN
                print(f"  CH1 Voltage: {ch1_voltage:.4f} V")
            if isinstance(ch1_freq, float) and not (ch1_freq != ch1_freq):  # Check not NaN
                print(f"  CH1 Frequency: {ch1_freq:.2f} Hz")
            if isinstance(ch2_voltage, float) and not (ch2_voltage != ch2_voltage):  # Check not NaN
                print(f"  CH2 Voltage: {ch2_voltage:.4f} V")
            
            # Wait before next measurement
            if i < num_measurements - 1:
                time.sleep(2)
        
        # Close the output file
        logger.close_file()
        
        print(f"\nMeasurements saved to: {output_file}")
        print("\nTest completed successfully!")
        
        # Display some usage examples
        print("\n" + "="*60)
        print("USAGE EXAMPLES:")
        print("="*60)
        print("\n1. Basic oscilloscope connection:")
        print("   osc = logger.connect('msox4154a')")
        print("\n2. Get statistics (returns [avg, std_dev, min, max]):")
        print("   stats = osc.get('statistics', channel=1)")
        print("\n3. Get individual measurements:")
        print("   voltage = osc.get('voltage', channel=1)")
        print("   frequency = osc.get('frequency', channel=1)")
        print("   rms = osc.get('voltage_rms', channel=1)")
        print("\n4. Available measurements:")
        print("   - statistics, voltage, voltage_rms, voltage_pp")
        print("   - frequency, period")
        print("   - VPP, VMAX, VMIN, VRMS, VAVerage")
        print("   - FREQuency, PERiod, RISetime, FALLtime")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Ensure file is closed
        try:
            if logger.file_open:
                logger.close_file()
        except:
            pass
            
    print("\nTest script finished.")


if __name__ == "__main__":
    main()