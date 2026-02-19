#!/usr/bin/env python
"""
Copy el34143a_sweep files to output directory with standardized naming.

Converts:
  el34143a_sweep_20260219_122448_ch1_045695-1_00004.csv
To:
  20260219_122448-el34143a_sweep_045695-1_00004_AVDD1_MM1.csv

For VDDIO channels:
  el34143a_sweep_20260219_130713_chvddio_l_045695-1_00004_slow.csv
To:
  20260219_130713-el34143a_sweep_045695-1_00004_slow_VDDIO_L.csv
"""

import os
import shutil
import re
from pathlib import Path

def parse_filename(filename):
    """
    Parse el34143a_sweep filename to extract timestamp, channel, and message.
    
    Returns: (timestamp, channel_str, message) or None if parsing fails
    """
    # Pattern: el34143a_sweep_<YYYYMMDD_HHMMSS>_ch<X>_<message>.csv
    # or: el34143a_sweep_<YYYYMMDD_HHMMSS>_chvddio_l_<message>.csv
    # or: el34143a_sweep_<YYYYMMDD_HHMMSS>_chvddio_r_<message>.csv
    
    # Try VDDIO pattern first (more specific)
    vddio_pattern = r'el34143a_sweep_(\d{8}_\d{6})_chvddio_([lr])_(.+)\.csv'
    match = re.match(vddio_pattern, filename)
    if match:
        timestamp = match.group(1)
        vddio_side = match.group(2)  # 'l' or 'r'
        message = match.group(3)
        channel_str = f"vddio_{vddio_side}"
        return timestamp, channel_str, message
    
    # Try standard channel pattern
    pattern = r'el34143a_sweep_(\d{8}_\d{6})_ch([^_]+)_(.+)\.csv'
    match = re.match(pattern, filename)
    if match:
        timestamp = match.group(1)
        channel_str = match.group(2)
        message = match.group(3)
        return timestamp, channel_str, message
    
    return None

def get_channel_suffix(channel_str):
    """
    Convert channel string to appropriate suffix.
    
    Args:
        channel_str: Channel identifier (e.g., "1", "15", "vddio_l", "vddio_r", "-1", "-2")
    
    Returns:
        Suffix string (e.g., "AVDD1_MM1", "VDDIO_L", "VDDIO_R")
    """
    if channel_str == "vddio_l" or channel_str == "-1":
        return "VDDIO_L"
    elif channel_str == "vddio_r" or channel_str == "-2":
        return "VDDIO_R"
    else:
        # Numeric channel (AVDD)
        try:
            channel_num = int(channel_str)
            return f"AVDD1_MM{channel_num}"
        except ValueError:
            return f"CHANNEL_{channel_str}"

def main():
    """Copy and rename all el34143a_sweep files to output directory."""
    # Get current directory and output directory
    current_dir = Path.cwd()
    output_dir = current_dir / "output"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Find all el34143a_sweep CSV files in current directory
    sweep_files = list(current_dir.glob("el34143a_sweep_*.csv"))
    
    if not sweep_files:
        print("No el34143a_sweep_*.csv files found in current directory")
        return
    
    print(f"Found {len(sweep_files)} sweep files to process\n")
    
    copied_count = 0
    skipped_count = 0
    
    for file_path in sorted(sweep_files):
        filename = file_path.name
        
        # Parse filename
        parsed = parse_filename(filename)
        if not parsed:
            print(f"⚠ Skipping (unable to parse): {filename}")
            skipped_count += 1
            continue
        
        timestamp, channel_str, message = parsed
        
        # Get channel suffix
        channel_suffix = get_channel_suffix(channel_str)
        
        # Construct new filename
        # Format: <timestamp>-el34143a_sweep_<message>_<channel_suffix>.csv
        new_filename = f"{timestamp}-el34143a_sweep_{message}_{channel_suffix}.csv"
        new_path = output_dir / new_filename
        
        # Copy file
        try:
            shutil.copy2(file_path, new_path)
            print(f"✓ {filename}")
            print(f"  → {new_filename}\n")
            copied_count += 1
        except Exception as e:
            print(f"✗ Error copying {filename}: {e}\n")
            skipped_count += 1
    
    print(f"\nSummary:")
    print(f"  Copied: {copied_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Output directory: {output_dir}")

if __name__ == "__main__":
    main()
