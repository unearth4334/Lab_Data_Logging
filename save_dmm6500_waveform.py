#!/usr/bin/env python3
"""
Script to Save Waveform Data from Keithley DMM6500

This script connects to a Keithley DMM6500 digital multimeter and downloads
waveform data from its internal buffer (defbuffer1) to a CSV file.

The script will:
1. Connect to the DMM6500
2. Check if buffer data exists
3. Download the waveform data using fetch_trace()
4. Save the data to a timestamped CSV file in the captures/ directory

Usage:
    python save_dmm6500_waveform.py [--address VISA_ADDRESS] [--output-dir OUTPUT_DIR] [--buffer BUFFER_NAME]

Requirements:
    - Keithley DMM6500 connected via USB or network
    - PyVISA and other dependencies from requirements.txt
    - Buffer data must be captured before running this script
      (e.g., using digitize mode or TRACe commands)

Example:
    # Save waveform from default buffer
    python save_dmm6500_waveform.py
    
    # Save from specific VISA address
    python save_dmm6500_waveform.py --address "USB0::0x05E6::0x6500::04471234::INSTR"
    
    # Save to custom directory
    python save_dmm6500_waveform.py --output-dir "my_captures"

Author: Lab Automation Team
Date: 2026-01
"""

import sys
import argparse
import csv
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.append('.')
from libs.DMM6500 import DMM6500


def save_dmm6500_waveform(visa_address=None, output_dir="captures", buffer_name="defbuffer1"):
    """
    Download and save waveform data from DMM6500 buffer.
    
    Args:
        visa_address: Optional specific VISA address to connect to
        output_dir: Directory to save waveform CSV file (default: "captures")
        buffer_name: Name of the DMM buffer to read from (default: "defbuffer1")
    """
    
    print("=" * 60)
    print("Keithley DMM6500 Waveform Save Script")
    print("=" * 60)
    print()
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    print(f"Output directory: {output_path.absolute()}")
    print()
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Connect to DMM6500
        print("Connecting to Keithley DMM6500...")
        if visa_address:
            dmm = DMM6500(auto_connect=False, address=visa_address)
            dmm.connect(address=visa_address)
        else:
            dmm = DMM6500(auto_connect=True)
        
        print("Connected successfully!")
        print()
        
        # Query buffer information
        print(f"Querying buffer '{buffer_name}'...")
        try:
            # Check how many points are in the buffer
            buffer_count_cmd = f"TRACe:ACTual? '{buffer_name}'"
            buffer_count = int(dmm.instrument.query(buffer_count_cmd).strip())
            print(f"  Buffer contains {buffer_count} data points")
            
            if buffer_count <= 0:
                print()
                print("ERROR: Buffer is empty!")
                print()
                print("Please capture data first using one of these methods:")
                print("  1. Use DMM6500 digitize mode (e.g., dmm.digitize_current())")
                print("  2. Configure trigger and buffer via SCPI commands")
                print("  3. Run a measurement sequence that fills the buffer")
                print()
                dmm.disconnect()
                return False
                
        except Exception as e:
            print(f"  Error querying buffer: {e}")
            print()
            print(f"Make sure buffer '{buffer_name}' exists and contains data.")
            dmm.disconnect()
            return False
        
        print()
        print("Downloading waveform data...")
        print("  (This may take some time for large buffers)")
        
        # Fetch the waveform data from the buffer
        # fetch_trace returns (values, None) - times not available on this firmware
        values, _ = dmm.fetch_trace(
            buffer=buffer_name,
            chunk=50000,  # Download in chunks of 50k points
            debug=False,  # Set to True for detailed SCPI logging
            step=False    # Set to True for interactive debugging
        )
        
        if not values or len(values) == 0:
            print()
            print("ERROR: No data retrieved from buffer!")
            dmm.disconnect()
            return False
        
        print(f"  Successfully downloaded {len(values)} data points")
        print()
        
        # Generate output filename
        waveform_file = output_path / f"dmm6500_waveform_{timestamp}.csv"
        
        # Save waveform to CSV file
        print(f"Saving waveform to: {waveform_file}")
        with open(waveform_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(["Sample_Index", "Value"])
            
            # Write data rows (sample index and value)
            for i, value in enumerate(values, start=1):
                writer.writerow([i, value])
        
        print()
        print("=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"Waveform saved: {waveform_file}")
        print(f"Total samples: {len(values)}")
        print(f"Value range: {min(values):.6g} to {max(values):.6g}")
        
        # Calculate basic statistics
        import statistics as stats
        mean_val = stats.fmean(values)
        stdev_val = stats.pstdev(values) if len(values) > 1 else 0.0
        print(f"Mean: {mean_val:.6g}")
        print(f"Std Dev: {stdev_val:.6g}")
        print()
        
        # Disconnect
        dmm.disconnect()
        return True
        
    except KeyboardInterrupt:
        print()
        print("Interrupted by user")
        return False
        
    except Exception as e:
        print()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Save waveform data from Keithley DMM6500 buffer to CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Save waveform from default buffer
  python save_dmm6500_waveform.py
  
  # Save from specific VISA address
  python save_dmm6500_waveform.py --address "USB0::0x05E6::0x6500::04471234::INSTR"
  
  # Save to custom directory and buffer
  python save_dmm6500_waveform.py --output-dir "my_data" --buffer "defbuffer2"
  
Note: The DMM6500 buffer must contain data before running this script.
      Capture data using digitize mode or trigger/measurement commands first.
        """
    )
    
    parser.add_argument(
        '--address',
        type=str,
        default=None,
        help='VISA address of the DMM6500 (e.g., "USB0::0x05E6::0x6500::04471234::INSTR"). If not specified, auto-detection is used.'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='captures',
        help='Directory to save the waveform CSV file (default: captures)'
    )
    
    parser.add_argument(
        '--buffer',
        type=str,
        default='defbuffer1',
        help='Name of the DMM buffer to read from (default: defbuffer1)'
    )
    
    args = parser.parse_args()
    
    # Run the waveform save function
    success = save_dmm6500_waveform(
        visa_address=args.address,
        output_dir=args.output_dir,
        buffer_name=args.buffer
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
