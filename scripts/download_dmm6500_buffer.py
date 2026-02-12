#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_dmm6500_buffer.py

Script to download the buffer from the DMM6500 digital multimeter.

USAGE
-----
The script supports multiple connection modes:

1. **Auto-connect (USB/Ethernet auto-detection)**:
   ```bash
   python scripts/download_dmm6500_buffer.py
   ```
   Automatically searches for DMM6500 on any available interface

2. **Connect via IP address**:
   ```bash
   python scripts/download_dmm6500_buffer.py --ip 169.254.233.96
   ```
   Connects to DMM6500 at the specified IP address via Ethernet/LAN

3. **Connect via explicit VISA address**:
   ```bash
   python scripts/download_dmm6500_buffer.py --address "USB0::0x05E6::0x6500::04492372::INSTR"
   ```
   Connects using a specific VISA resource string

4. **Specify buffer name and output file**:
   ```bash
   python scripts/download_dmm6500_buffer.py --buffer defbuffer1 --output my_data.csv
   ```
   Download from a specific buffer and save to a specific file

5. **Add metadata message**:
   ```bash
   python scripts/download_dmm6500_buffer.py -m "Test run #5 with 10V range"
   ```
   Add a descriptive message to the output file header

COMMAND LINE OPTIONS
--------------------
  --ip IP_ADDRESS          IP address for ethernet connection
  --address VISA_ADDRESS   Full VISA resource string (USB or TCPIP)
  --buffer BUFFER_NAME     Buffer name to download (default: defbuffer1)
  --output OUTPUT_FILE     Output CSV filename (default: auto-generated in output/ directory)
  -m, --message MESSAGE    Optional message/metadata to include in file header and filename
  --chunk CHUNK_SIZE       Points per fetch operation (default: 50000)
  --debug                  Enable verbose SCPI logging
  --plot                   Plot the downloaded data after saving
  --help, -h              Show this help message

OUTPUT FILES
------------
Files are automatically saved to the output/ directory with the format:
  output/yyyymmdd_hhmmss-dmm6500_buffer-buffername[-message].csv

For example:
  output/20260212_140120-dmm6500_buffer-defbuffer1-voltage_test.csv

EXAMPLES
--------

Example 1: Quick download with auto-detection
```bash
python scripts/download_dmm6500_buffer.py
```

Example 2: Download from specific IP with metadata
```bash
python scripts/download_dmm6500_buffer.py --ip 169.254.233.96 -m "Voltage stability test"
```

Example 3: Download and plot
```bash
python scripts/download_dmm6500_buffer.py --plot
```

Example 4: Specify all parameters
```bash
python scripts/download_dmm6500_buffer.py --address "TCPIP0::169.254.233.96::inst0::INSTR" \
    --buffer defbuffer1 --output voltage_test.csv -m "10V range, 1 NPLC" --plot
```
"""

import argparse
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.DMM6500 import DMM6500

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # Fallback no-op objects
    class _NoColor:
        def __getattr__(self, name):
            return ''
    Fore = Style = _NoColor()


def print_header(text: str):
    """Print a formatted header."""
    if HAS_COLORAMA:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
        print(f"{text}")
        print(f"{'='*70}{Style.RESET_ALL}\n")
    else:
        print(f"\n{'='*70}")
        print(f"{text}")
        print(f"{'='*70}\n")


def print_success(text: str):
    """Print a success message."""
    if HAS_COLORAMA:
        print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")
    else:
        print(f"✓ {text}")


def print_error(text: str):
    """Print an error message."""
    if HAS_COLORAMA:
        print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")
    else:
        print(f"✗ {text}")


def print_info(text: str):
    """Print an info message."""
    if HAS_COLORAMA:
        print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")
    else:
        print(f"ℹ {text}")


def calculate_statistics(values: List[float]) -> Tuple[float, float, float, float]:
    """
    Calculate statistics for a list of values.
    
    Args:
        values: List of measurement values
        
    Returns:
        Tuple of (mean, stdev, min, max)
    """
    if not values:
        return 0.0, 0.0, 0.0, 0.0
    
    mean = statistics.mean(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0.0
    min_val = min(values)
    max_val = max(values)
    
    return mean, stdev, min_val, max_val


def generate_filename(buffer_name: str = "defbuffer1", message: str = None) -> str:
    """
    Generate a timestamped filename for the output.
    
    Args:
        buffer_name: Name of the buffer
        message: Optional message to include in filename
        
    Returns:
        Full path to output file in format: output/yyyymmdd_hhmmss-dmm6500_buffer_buffername[-message].csv
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Clean buffer name for filename (remove any special characters)
    clean_buffer = buffer_name.replace("'", "").replace('"', '')
    
    # Build filename components
    filename_parts = [timestamp, "dmm6500_buffer", clean_buffer]
    
    # Add message if provided (clean it for filename use)
    if message:
        # Clean message: remove/replace problematic characters
        clean_message = message.replace('/', '_').replace('\\', '_').replace(':', '_').replace('"', '').replace("'", '')
        # Replace spaces with underscores and limit length
        clean_message = clean_message.replace(' ', '_')[:50]
        filename_parts.append(clean_message)
    
    # Join with hyphens and add extension
    filename = '-'.join(filename_parts) + '.csv'
    
    # Return path in output directory
    return f"output/{filename}"


def save_buffer_to_csv(filename: str, values: list, buffer_name: str, message: str = None):
    """
    Save buffer data to a CSV file.
    
    Args:
        filename: Output filename
        values: List of measurement values
        buffer_name: Name of the buffer that was downloaded
        message: Optional metadata message
    """
    with open(filename, 'w') as f:
        # Write header with metadata
        f.write(f"# DMM6500 Buffer Download\n")
        f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"# Buffer: {buffer_name}\n")
        f.write(f"# Samples: {len(values)}\n")
        if message:
            f.write(f"# Message: {message}\n")
        f.write(f"#\n")
        f.write("Index,Value\n")
        
        # Write data
        for i, value in enumerate(values, start=1):
            f.write(f"{i},{value}\n")


def plot_data(filename: str):
    """
    Plot the downloaded data using matplotlib.
    
    Args:
        filename: CSV file to plot
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print_error("matplotlib is required for plotting. Install with: pip install matplotlib")
        return
    
    # Read data from CSV (skip header lines starting with #)
    data = []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('#') or line.startswith('Index'):
                continue
            parts = line.strip().split(',')
            if len(parts) == 2:
                try:
                    data.append(float(parts[1]))
                except ValueError:
                    continue
    
    if not data:
        print_error("No data to plot")
        return
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Time series plot
    ax1.plot(data, linewidth=0.5)
    ax1.set_xlabel('Sample Index')
    ax1.set_ylabel('Value')
    ax1.set_title(f'DMM6500 Buffer Data - {Path(filename).name}')
    ax1.grid(True, alpha=0.3)
    
    # Statistics - use helper function
    mean, std, min_val, max_val = calculate_statistics(data)
    
    stats_text = f"Mean: {mean:.6e}\nStd: {std:.6e}\nMin: {min_val:.6e}\nMax: {max_val:.6e}\nSamples: {len(data)}"
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
             fontfamily='monospace')
    
    # Histogram
    ax2.hist(data, bins=50, edgecolor='black', alpha=0.7)
    ax2.set_xlabel('Value')
    ax2.set_ylabel('Count')
    ax2.set_title('Distribution')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Download buffer data from DMM6500 digital multimeter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --ip 169.254.233.96 -m "Voltage test"
  %(prog)s --address "USB0::0x05E6::0x6500::04492372::INSTR" --plot
  %(prog)s --buffer defbuffer1 --output my_data.csv
        """
    )
    
    # Connection options
    parser.add_argument('--ip', type=str, help='IP address for ethernet connection')
    parser.add_argument('--address', type=str, help='Full VISA resource string')
    
    # Buffer and output options
    parser.add_argument('--buffer', type=str, default='defbuffer1',
                        help='Buffer name to download (default: defbuffer1)')
    parser.add_argument('--output', type=str,
                        help='Output CSV filename (default: auto-generated in output/ directory)')
    parser.add_argument('-m', '--message', type=str,
                        help='Optional message/metadata to include in file header and filename')
    
    # Download options
    parser.add_argument('--chunk', type=int, default=50000,
                        help='Points per fetch operation (default: 50000)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable verbose SCPI logging')
    
    # Post-processing options
    parser.add_argument('--plot', action='store_true',
                        help='Plot the downloaded data after saving')
    
    args = parser.parse_args()
    
    print_header("DMM6500 Buffer Download Script")
    
    # Connect to DMM6500
    print_info("Connecting to DMM6500...")
    try:
        dmm = DMM6500(auto_connect=False)
        
        if args.address:
            print_info(f"Using VISA address: {args.address}")
            dmm.connect(address=args.address)
        elif args.ip:
            print_info(f"Using IP address: {args.ip}")
            dmm.connect(ip_address=args.ip)
        else:
            print_info("Auto-detecting DMM6500...")
            dmm.connect()
        
        print_success(f"Connected to: {dmm.instrument.resource_name}")
        
        # Get device identification
        idn = dmm.instrument.query("*IDN?").strip()
        print_info(f"Device: {idn}")
        
    except Exception as e:
        print_error(f"Failed to connect: {e}")
        return 1
    
    # Download buffer
    print_header(f"Downloading Buffer: {args.buffer}")
    
    try:
        debug = args.debug
        step = False  # Never use interactive step-through in CLI tool
        
        print_info(f"Fetching data from '{args.buffer}'...")
        print_info(f"Chunk size: {args.chunk} points")
        
        values, _ = dmm.fetch_trace(
            buffer=args.buffer,
            chunk=args.chunk,
            debug=debug,
            step=step
        )
        
        if not values:
            print_error("No data in buffer")
            dmm.disconnect()
            return 1
        
        print_success(f"Downloaded {len(values)} samples")
        
        # Statistics
        if values:
            mean, stdev, min_val, max_val = calculate_statistics(values)
            
            print_info("Buffer Statistics:")
            print(f"  Mean:   {mean:.6e}")
            print(f"  StdDev: {stdev:.6e}")
            print(f"  Min:    {min_val:.6e}")
            print(f"  Max:    {max_val:.6e}")
            print(f"  Range:  {max_val - min_val:.6e}")
        
    except Exception as e:
        print_error(f"Failed to download buffer: {e}")
        dmm.disconnect()
        return 1
    
    # Save to file
    print_header("Saving Data")
    
    output_file = args.output if args.output else generate_filename(args.buffer, args.message)
    
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        save_buffer_to_csv(output_file, values, args.buffer, args.message)
        print_success(f"Data saved to: {output_file}")
        print_info(f"File size: {output_path.stat().st_size} bytes")
    except Exception as e:
        print_error(f"Failed to save file: {e}")
        dmm.disconnect()
        return 1
    
    # Disconnect
    try:
        dmm.disconnect()
        print_success("Disconnected from DMM6500")
    except Exception as e:
        print_error(f"Warning: Failed to disconnect cleanly: {e}")
    
    # Plot if requested
    if args.plot:
        print_header("Plotting Data")
        plot_data(output_file)
    
    print_header("Download Complete")
    print_success(f"Buffer '{args.buffer}' downloaded successfully")
    print_info(f"Output file: {output_file}")
    print_info(f"Total samples: {len(values)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
