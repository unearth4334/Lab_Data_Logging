#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core download functionality for DMM6500 buffer downloads.
"""

import statistics
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

from .drivers import DMM6500

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
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
        print(f"\n{'='*70}\n{text}\n{'='*70}\n")


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


def print_progress_bar(current: int, total: int, width: int = 40, prefix: str = ""):
    """Print a Braille block progress bar."""
    braille_blocks = ['⠀', '⣀', '⣄', '⣤', '⣦', '⣶', '⣷', '⣿']
    
    if total == 0:
        percent = 0
    else:
        percent = min(100, int(100 * current / total))
    
    filled_width = (current * width) / total if total > 0 else 0
    full_blocks = int(filled_width)
    partial = filled_width - full_blocks
    
    partial_index = int(partial * (len(braille_blocks) - 1))
    
    bar = braille_blocks[-1] * full_blocks
    if full_blocks < width:
        bar += braille_blocks[partial_index]
        bar += braille_blocks[0] * (width - full_blocks - 1)
    
    if HAS_COLORAMA:
        print(f"\r{Fore.CYAN}{prefix}[{bar}] {percent:3d}% ({current}/{total}){Style.RESET_ALL}", end='', flush=True)
    else:
        print(f"\r{prefix}[{bar}] {percent:3d}% ({current}/{total})", end='', flush=True)


def fetch_trace_with_progress(dmm: DMM6500, buffer: str, chunk: int, debug: bool = False) -> Tuple[List[float], None]:
    """Download buffer data with progress bar."""
    inst = dmm.instrument
    
    # Get buffer count
    try:
        n = int(inst.query(f"TRACe:ACTual? '{buffer}'").strip())
    except Exception:
        n = int(inst.query(f"TRACe:ACTual? {buffer}").strip())
    
    if n <= 0:
        print_info("No points in buffer")
        return [], None
    
    print_info(f"Downloading {n} samples...")
    
    # Read in chunks with progress bar
    values: List[float] = []
    start = 1
    chunk = max(1, int(chunk))
    
    while start <= n:
        stop = min(start + chunk - 1, n)
        
        cmd_q = f"TRACe:DATA? {start},{stop},'{buffer}'"
        cmd_uq = f"TRACe:DATA? {start},{stop},{buffer}"
        
        try:
            raw = inst.query_ascii_values(cmd_q, container=list)
        except Exception:
            raw = inst.query_ascii_values(cmd_uq, container=list)
        
        values.extend(float(v) for v in raw)
        
        print_progress_bar(len(values), n, prefix="Progress: ")
        
        if debug:
            print(f"\n  Chunk [{start}:{stop}] -> {len(raw)} values", end='')
        
        start = stop + 1
    
    print()  # New line after progress bar
    
    return values, None


def calculate_statistics(values: List[float]) -> Tuple[float, float, float, float]:
    """Calculate statistics for a list of values."""
    if not values:
        return 0.0, 0.0, 0.0, 0.0
    
    mean = statistics.mean(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0.0
    min_val = min(values)
    max_val = max(values)
    
    return mean, stdev, min_val, max_val


def generate_filename(buffer_name: str = "defbuffer1", message: Optional[str] = None) -> str:
    """Generate a timestamped filename for the output."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_buffer = buffer_name.replace("'", "").replace('"', '')
    
    filename_parts = [timestamp, "dmm6500_buffer", clean_buffer]
    
    if message:
        clean_message = message.replace('/', '_').replace('\\', '_').replace(':', '_').replace('"', '').replace("'", '')
        clean_message = clean_message.replace(' ', '_')[:50]
        filename_parts.append(clean_message)
    
    filename = '-'.join(filename_parts) + '.csv'
    
    return f"output/{filename}"


def save_buffer_to_csv(filename: str, values: list, buffer_name: str, message: Optional[str] = None):
    """Save buffer data to a CSV file."""
    with open(filename, 'w') as f:
        f.write(f"# DMM6500 Buffer Download\n")
        f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"# Buffer: {buffer_name}\n")
        f.write(f"# Samples: {len(values)}\n")
        if message:
            f.write(f"# Message: {message}\n")
        f.write(f"#\n")
        f.write("Index,Value\n")
        
        for i, value in enumerate(values, start=1):
            f.write(f"{i},{value}\n")


def plot_data(filename: str):
    """Plot the downloaded data using matplotlib."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print_error("matplotlib is required for plotting. Install with: pip install matplotlib")
        return
    
    # Read data from CSV
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


def download_buffer(
    buffer_name: str = 'defbuffer1',
    output_file: Optional[str] = None,
    ip_address: Optional[str] = None,
    visa_address: Optional[str] = None,
    message: Optional[str] = None,
    chunk_size: int = 50000,
    debug: bool = False,
    show_plot: bool = False
) -> List[float]:
    """
    Download buffer data from DMM6500.
    
    Args:
        buffer_name: Name of buffer to download (default: 'defbuffer1')
        output_file: Output CSV filename (default: auto-generated)
        ip_address: IP address for ethernet connection
        visa_address: Full VISA resource string
        message: Optional metadata message
        chunk_size: Points per fetch operation (default: 50000)
        debug: Enable verbose SCPI logging
        show_plot: Plot the data after downloading
        
    Returns:
        List of measurement values
    """
    print_header("DMM6500 Buffer Download")
    
    # Connect to DMM6500
    print_info("Connecting to DMM6500...")
    try:
        dmm = DMM6500(auto_connect=False, debug=debug)
        
        if visa_address:
            print_info(f"Using VISA address: {visa_address}")
            dmm.connect(address=visa_address)
        elif ip_address:
            print_info(f"Using IP address: {ip_address}")
            dmm.connect(ip_address=ip_address)
        else:
            print_info("Auto-detecting DMM6500...")
            dmm.connect()
        
        print_success(f"Connected to: {dmm.address}")
        
    except Exception as e:
        print_error(f"Failed to connect: {e}")
        raise
    
    # Download buffer
    print_header(f"Downloading Buffer: {buffer_name}")
    
    try:
        print_info(f"Chunk size: {chunk_size} points")
        
        values, _ = fetch_trace_with_progress(
            dmm=dmm,
            buffer=buffer_name,
            chunk=chunk_size,
            debug=debug
        )
        
        if not values:
            print_error("No data in buffer")
            dmm.disconnect()
            raise ValueError("Buffer is empty")
        
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
        raise
    
    # Save to file
    print_header("Saving Data")
    
    output = output_file if output_file else generate_filename(buffer_name, message)
    
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        save_buffer_to_csv(output, values, buffer_name, message)
        print_success(f"Data saved to: {output}")
        print_info(f"File size: {output_path.stat().st_size} bytes")
    except Exception as e:
        print_error(f"Failed to save file: {e}")
        dmm.disconnect()
        raise
    
    # Disconnect
    try:
        dmm.disconnect()
        print_success("Disconnected from DMM6500")
    except Exception as e:
        print_error(f"Warning: Failed to disconnect cleanly: {e}")
    
    # Plot if requested
    if show_plot:
        print_header("Plotting Data")
        plot_data(output)
    
    print_header("Download Complete")
    print_success(f"Buffer '{buffer_name}' downloaded successfully")
    print_info(f"Output file: {output}")
    print_info(f"Total samples: {len(values)}")
    
    return values
