#!/usr/bin/env python3
"""
Simple Keysight MSOX4154A Screenshot Capture
Just connects and takes a screenshot - no statistics or measurements.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from libs.KeysightMSOX4154A import KeysightMSOX4154A

def take_screenshot(visa_address=None, output_dir="captures"):
    """
    Simple screenshot capture from Keysight MSOX4154A.
    
    Args:
        visa_address: Optional specific VISA address to connect to
        output_dir: Directory to save screenshot (default: "captures")
    """
    
    print("Keysight MSOX4154A Screenshot Capture")
    print("=" * 40)
    print()
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    print(f"Output directory: {output_path.absolute()}")
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Connect to oscilloscope
        print("Connecting to Keysight MSOX4154A...")
        if visa_address:
            osc = KeysightMSOX4154A(auto_connect=False)
            osc.connect(visa_address)
        else:
            osc = KeysightMSOX4154A()
        
        print("Connected successfully!")
        
        # Take screenshot
        print("Capturing screenshot...")
        screenshot_file = output_path / f"oscilloscope_screenshot_{timestamp}.png"
        
        success = osc.save_screenshot(str(screenshot_file), inksaver=False)
        
        if success:
            print(f"Screenshot saved: {screenshot_file}")
        else:
            print("Screenshot capture failed")
        
        # Disconnect
        osc.disconnect()
        print("Disconnected from oscilloscope")
        
        return success
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Simple Oscilloscope Screenshot Tool")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Capture screenshot from Keysight MSOX4154A oscilloscope",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python simple_screenshot.py
  python simple_screenshot.py "USB0::0x0957::0x17BC::MY56310625::INSTR"
  python simple_screenshot.py --output-dir ./screenshots
  python simple_screenshot.py "USB0::0x0957::0x17BC::MY56310625::INSTR" --output-dir ./screenshots
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
        help="Output directory for screenshots (default: captures)"
    )
    
    args = parser.parse_args()
    
    print()
    
    if args.visa_address:
        print(f"Using specified VISA address: {args.visa_address}")
    else:
        print("Using auto-detection for VISA address")
    
    print(f"Output directory: {args.output_dir}")
    print()
    
    # Take the screenshot
    success = take_screenshot(args.visa_address, args.output_dir)
    
    if success:
        print("\nScreenshot capture completed successfully!")
    else:
        print("\nScreenshot capture failed!")
    
    print("\nDone.")