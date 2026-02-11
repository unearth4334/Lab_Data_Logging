#!/usr/bin/env python3
"""
Example Script: Capture and Save DMM6500 Waveform

This example demonstrates the complete workflow for capturing waveform data
from the Keithley DMM6500 and saving it to a CSV file.

The workflow is:
1. Connect to the DMM6500
2. Configure measurement settings (optional)
3. Capture data using buffer or digitize mode
4. Use save_dmm6500_waveform.py to export the data to CSV

This script provides two example methods:
- Method 1: Manual buffer capture using SCPI commands
- Method 2: Using the digitize_current() helper method (if available)

Author: Lab Automation Team
Date: 2026-01
"""

import sys
import time
import subprocess
from pathlib import Path

# Add current directory to path for imports
sys.path.append('.')
from libs.DMM6500 import DMM6500


def example_buffer_capture():
    """
    Example 1: Manually configure DMM6500 to capture data into buffer.
    
    This method uses SCPI commands to configure triggered measurements
    that fill the buffer with data.
    """
    print("=" * 60)
    print("Example 1: Manual Buffer Capture")
    print("=" * 60)
    print()
    
    try:
        # Connect to DMM6500
        print("Connecting to DMM6500...")
        dmm = DMM6500(auto_connect=True)
        print()
        
        # Configure for DC voltage measurement
        print("Configuring measurement...")
        dmm.instrument.write("*RST")  # Reset to known state
        time.sleep(1)
        
        # Set up DC voltage measurement
        dmm.instrument.write("SENSe:FUNCtion 'VOLT:DC'")
        dmm.instrument.write("SENSe:VOLT:DC:RANGe 10")  # 10V range
        dmm.instrument.write("SENSe:VOLT:DC:NPLC 0.1")  # Fast integration
        
        # Clear and configure buffer
        dmm.instrument.write("TRACe:CLEar 'defbuffer1'")
        dmm.instrument.write("TRACe:MAKE 'defbuffer1', 10000")  # 10k point buffer
        
        # Configure simple timer trigger for continuous acquisition
        print("Starting data capture...")
        print("  Capturing 100 voltage readings...")
        
        # Simple method: use INITiate with COUNt
        dmm.instrument.write("SENSe:VOLT:DC:RANGe:AUTO OFF")
        dmm.instrument.write("TRIGger:COUNt 100")  # Capture 100 readings
        dmm.instrument.write("TRIGger:DELay 0.01")  # 10ms between readings
        dmm.instrument.write("INITiate")
        
        # Wait for completion
        print("  Waiting for capture to complete...")
        time.sleep(3)  # Wait for 100 readings @ 10ms each + overhead
        
        # Check how many points were captured
        count = int(dmm.instrument.query("TRACe:ACTual? 'defbuffer1'").strip())
        print(f"  Captured {count} data points")
        print()
        
        if count > 0:
            print("SUCCESS! Buffer contains data.")
            print()
            print("Now run the save script to export this data:")
            print("  python save_dmm6500_waveform.py")
            print()
        else:
            print("WARNING: No data captured!")
        
        dmm.disconnect()
        return count > 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def example_simple_capture():
    """
    Example 2: Simple approach - just take multiple readings.
    
    This is the simplest method: configure the DMM and take multiple
    readings that automatically fill the buffer.
    """
    print("=" * 60)
    print("Example 2: Simple Continuous Readings")
    print("=" * 60)
    print()
    
    try:
        # Connect to DMM6500
        print("Connecting to DMM6500...")
        dmm = DMM6500(auto_connect=True)
        print()
        
        # Configure measurement
        print("Configuring DC voltage measurement...")
        dmm.instrument.write("*RST")
        time.sleep(1)
        
        # Clear buffer
        dmm.instrument.write("TRACe:CLEar 'defbuffer1'")
        
        # Configure function
        dmm.instrument.write("SENSe:FUNCtion 'VOLT:DC'")
        dmm.instrument.write("SENSe:VOLT:DC:RANGe:AUTO ON")
        dmm.instrument.write("SENSe:VOLT:DC:NPLC 1")
        
        # Take multiple readings (they auto-store in buffer)
        print("Taking 50 voltage readings...")
        for i in range(50):
            reading = dmm.instrument.query("MEASure:VOLT:DC?")
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/50 readings")
        
        # Check buffer
        count = int(dmm.instrument.query("TRACe:ACTual? 'defbuffer1'").strip())
        print(f"  Buffer now contains {count} data points")
        print()
        
        if count > 0:
            print("SUCCESS! Buffer contains data.")
            print()
            print("Now run the save script to export this data:")
            print("  python save_dmm6500_waveform.py")
            print()
        else:
            print("WARNING: No data in buffer!")
        
        dmm.disconnect()
        return count > 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def example_with_auto_save():
    """
    Example 3: Complete workflow - capture data and automatically save it.
    
    This method captures data and then calls the save script automatically.
    """
    print("=" * 60)
    print("Example 3: Capture and Auto-Save")
    print("=" * 60)
    print()
    
    try:
        # Connect to DMM6500
        print("Connecting to DMM6500...")
        dmm = DMM6500(auto_connect=True)
        print()
        
        # Quick capture
        print("Capturing 30 voltage readings...")
        dmm.instrument.write("*RST")
        time.sleep(1)
        dmm.instrument.write("TRACe:CLEar 'defbuffer1'")
        dmm.instrument.write("SENSe:FUNCtion 'VOLT:DC'")
        
        for i in range(30):
            dmm.instrument.query("MEASure:VOLT:DC?")
            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/30 readings")
        
        count = int(dmm.instrument.query("TRACe:ACTual? 'defbuffer1'").strip())
        print(f"  Captured {count} data points")
        print()
        
        dmm.disconnect()
        
        if count > 0:
            # Automatically call the save script
            print("Calling save script...")
            print()
            result = subprocess.run(
                [sys.executable, "save_dmm6500_waveform.py"]
            )
            
            return result.returncode == 0
        else:
            print("ERROR: No data captured!")
            return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main menu for example selection."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║  DMM6500 Waveform Capture and Save - Example Script     ║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("This script demonstrates how to capture waveform data from")
    print("the DMM6500 and save it using save_dmm6500_waveform.py")
    print()
    print("Choose an example:")
    print()
    print("  1) Manual buffer capture using SCPI triggers")
    print("  2) Simple continuous readings approach")
    print("  3) Capture and auto-save in one go")
    print()
    print("  q) Quit")
    print()
    
    choice = input("Enter your choice (1-3 or q): ").strip().lower()
    print()
    
    if choice == '1':
        success = example_buffer_capture()
    elif choice == '2':
        success = example_simple_capture()
    elif choice == '3':
        success = example_with_auto_save()
    elif choice == 'q':
        print("Exiting...")
        return
    else:
        print("Invalid choice!")
        return
    
    if success:
        print()
        print("=" * 60)
        print("Example completed successfully!")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("Example completed with errors.")
        print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Interrupted by user")
