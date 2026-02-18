#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MSOX4154A Oscilloscope Ethernet Connection Test Script
======================================================

This script tests the MSOX4154A driver's enhanced Ethernet connectivity capabilities,
demonstrating various connection methods and basic instrument operations.

USAGE
-----
The script supports multiple connection modes:

1. **Auto-connect (USB/Ethernet auto-detection)**:
   ```bash
   python test_msox4154a_ethernet.py
   ```
   Automatically searches for MSOX4154A on any available interface (USB or Ethernet)

2. **Connect via IP address**:
   ```bash
   python test_msox4154a_ethernet.py --ip 192.168.1.100
   ```
   Connects to MSOX4154A at the specified IP address via Ethernet/LAN
   (Find IP on device: Utility > I/O > LAN)

3. **Connect via explicit VISA address**:
   ```bash
   # USB connection
   python test_msox4154a_ethernet.py --address "USB0::0x0957::0x17BC::MY59241237::INSTR"
   
   # Ethernet connection
   python test_msox4154a_ethernet.py --address "TCPIP0::192.168.1.100::inst0::INSTR"
   ```
   Connects using a specific VISA resource string

4. **Interactive mode**:
   ```bash
   python test_msox4154a_ethernet.py --interactive
   ```
   Prompts for connection method and parameters

COMMAND LINE OPTIONS
--------------------
  --ip IP_ADDRESS          IP address for ethernet connection (e.g., 192.168.1.100)
  --address VISA_ADDRESS   Full VISA resource string (USB or TCPIP)
  --interactive, -i        Interactive mode - prompts for connection details
  --debug                  Enable debug output (shows VISA resource scanning details)
  
  Capture options:
  --screenshot             Capture oscilloscope screenshot
  --waveform               Capture waveform data from specified channels
  --properties             Capture oscilloscope properties/settings
  -ch, --channels CHANNELS Comma-separated channel list (e.g., "1,2,3,4") [default: 1]
  -m, --message MESSAGE    Custom message to append to filename
  -o, --output DIR         Output directory [default: output/]
  --preview                Generate and open HTML report of captured data
  
  --help, -h               Show this help message

EXAMPLES
--------

Example 1: Quick test with auto-detection
```bash
python test_msox4154a_ethernet.py
```

Example 2: Connect to specific IP (as shown on MSOX4154A LAN settings)
```bash
python test_msox4154a_ethernet.py --ip 192.168.1.100
```

Example 3: Use the exact VISA string
```bash
python test_msox4154a_ethernet.py --address "TCPIP0::192.168.1.100::inst0::INSTR"
```

Example 4: Connect via USB with explicit address
```bash
python test_msox4154a_ethernet.py --address "USB0::0x0957::0x17BC::MY59241237::INSTR"
```

Example 5: Interactive mode for manual configuration
```bash
python test_msox4154a_ethernet.py --interactive
```

Example 6: Debug mode to see resource scanning
```bash
python test_msox4154a_ethernet.py --debug
```

Example 7: Capture screenshot with custom message
```bash
python test_msox4154a_ethernet.py --ip 192.168.1.100 --screenshot -m "test_setup"
```

Example 8: Capture waveforms from multiple channels
```bash
python test_msox4154a_ethernet.py --waveform -ch 1,2,3,4 -m "four_channel_test"
```

Example 9: Capture everything with custom output directory
```bash
python test_msox4154a_ethernet.py --screenshot --waveform --properties -ch 1,2 -m "complete_capture" -o captures/
```

Example 10: Capture and preview results in HTML report
```bash
python test_msox4154a_ethernet.py --ip 192.168.1.100 --screenshot --waveform -ch 1,2,3,4 --preview -m "test_run"
```

NETWORK CONFIGURATION
---------------------
**Finding the MSOX4154A IP Address:**

1. On the MSOX4154A front panel, press **Utility** > **I/O** > **LAN**
2. The LAN configuration screen displays network information:
   ```
   Configuration: DHCP (or Auto IP or Manual)
   IP Address: xxx.xxx.xxx.xxx          <-- Use this IP address
   Subnet Mask: xxx.xxx.xxx.xxx
   Default Gateway: xxx.xxx.xxx.xxx
   ```

3. **Note the IP Address shown** (e.g., 192.168.1.100)
   - Use this with: `python test_msox4154a_ethernet.py --ip 192.168.1.100`
   - Or in code: `KeysightMSOX4154A(ip_address="192.168.1.100")`

**Configuring Network Settings:**

If the MSOX4154A doesn't have an IP address or you need to change it:
1. Press **Utility** > **I/O** > **LAN** > **LAN Config**
2. Select configuration mode:
   - **Auto IP**: Uses link-local address (169.254.x.x)
   - **DHCP**: Automatically obtains IP from network
   - **Manual**: Set static IP address manually
3. If using Manual mode, configure:
   - IP Address
   - Subnet Mask
   - Default Gateway (if needed)
4. Apply settings

**Network Requirements:**
- MSOX4154A must be connected via Ethernet cable
- Computer and MSOX4154A should be on the same network
- Firewall should allow LXI/SCPI communication (typically port 5025)
- For link-local (Auto IP), enable IPv4 Link-Local on your computer

TROUBLESHOOTING
---------------
**Connection Issues:**

1. **Find the actual IP address on the device:**
   - Press Utility > I/O > LAN
   - Look for "IP Address" line (e.g., 192.168.1.100 or 169.254.x.x)

2. **Test network connectivity:**
   ```bash
   ping 192.168.1.100  # Replace with your MSOX4154A IP
   ```

3. **Verify VISA resources are visible:**
   ```bash
   python -c "import pyvisa; rm = pyvisa.ResourceManager(); print(rm.list_resources())"
   ```
   Should show something like: `TCPIP0::192.168.1.100::inst0::INSTR`

4. **Check network settings:**
   - For corporate networks, use DHCP mode or consult IT for static IP configuration
   - Verify Ethernet cable is properly connected (check link lights)
   - For Auto IP (169.254.x.x), ensure computer can reach link-local addresses

For USB connections:
1. Ensure USB cable is connected
2. Check that VISA drivers are installed (Keysight IO Libraries or NI-VISA)
3. List available resources: `python -c "import pyvisa; print(pyvisa.ResourceManager().list_resources())"`

REQUIREMENTS
------------
- Python 3.7+
- pyvisa >= 1.11.0
- colorama >= 0.4.6
- Keysight IO Libraries or NI-VISA

Install dependencies:
```bash
pip install pyvisa colorama
```

ABOUT
-----
Author: Lab Data Logging Project
Date: February 2026
License: Apache 2.0
"""

import argparse
import sys
import time
import os
import csv
import base64
import subprocess
import webbrowser
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    from libs.KeysightMSOX4154A import KeysightMSOX4154A
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError as e:
    print(f"Error: Missing required module: {e}")
    print("Please install dependencies: pip install pyvisa colorama")
    sys.exit(1)


# --- Console formatting ---
_SUCCESS = Fore.GREEN + Style.BRIGHT
_ERROR = Fore.RED + Style.BRIGHT
_WARNING = Fore.YELLOW + Style.BRIGHT
_INFO = Fore.CYAN
_RESET = Style.RESET_ALL


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"{_INFO}{title}{_RESET}")
    print("=" * 70)


def print_test(description: str):
    """Print a test description."""
    print(f"\n{_INFO}>>> {description}...{_RESET}")


def print_success(message: str):
    """Print a success message."""
    print(f"{_SUCCESS}✓ {message}{_RESET}")


def print_error(message: str):
    """Print an error message."""
    print(f"{_ERROR}✗ {message}{_RESET}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{_WARNING}⚠ {message}{_RESET}")


def generate_filename(base_name: str, item: str, message: Optional[str], extension: str) -> str:
    """
    Generate standardized filename: yyyymmdd_hhmmss-msox4154a-<item>-<message>.<ext>
    
    Args:
        base_name: Base instrument name (e.g., "msox4154a")
        item: Measurement item (e.g., "screenshot", "waveform", "properties")
        message: Optional custom message
        extension: File extension (e.g., "png", "csv")
    
    Returns:
        Formatted filename string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parts = [timestamp, base_name, item]
    
    if message:
        # Sanitize message for filename
        safe_message = message.replace(" ", "_").replace("/", "-").replace("\\", "-")
        parts.append(safe_message)
    
    filename = "-".join(parts) + "." + extension
    return filename


def ensure_output_dir(output_dir: str) -> str:
    """
    Ensure output directory exists.
    
    Args:
        output_dir: Path to output directory
    
    Returns:
        Absolute path to output directory
    """
    os.makedirs(output_dir, exist_ok=True)
    return os.path.abspath(output_dir)


def get_property_units(property_name: str) -> str:
    """Get the units for a given property name.
    
    Args:
        property_name: The name of the property
        
    Returns:
        Unit string for the property
    """
    prop_lower = property_name.lower()
    
    # Units mapping
    if 'scale' in prop_lower and 'time' not in prop_lower:
        return 'V/div'
    elif 'time scale' in prop_lower:
        return 's/div'
    elif 'offset' in prop_lower:
        return 'V'
    elif 'probe gain' in prop_lower:
        return 'X'
    elif 'coupling' in prop_lower:
        return ''
    elif 'impedance' in prop_lower:
        return ''
    elif 'bandwidth limit' in prop_lower:
        return ''
    elif 'display' in prop_lower:
        return ''
    else:
        return ''


def generate_html_report(captured_files: Dict[str, Any], output_dir: str, message: Optional[str]) -> str:
    """
    Generate HTML report with captured data.
    
    Args:
        captured_files: Dictionary with captured file information
        output_dir: Output directory path
        message: Optional message for filename
    
    Returns:
        Path to generated HTML file
    """
    # Generate filename for report
    filename = generate_filename("msox4154a", "report", message, "html")
    filepath = os.path.join(output_dir, filename)
    
    # Start HTML document
    html_parts = []
    html_parts.append('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MSOX4154A Capture Report</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #0066cc;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
            margin-top: 0;
        }
        h2 {
            color: #0066cc;
            margin-top: 30px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 8px;
        }
        .metadata {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #0066cc;
        }
        .metadata table {
            width: 100%;
            border-collapse: collapse;
        }
        .metadata td {
            padding: 5px;
            border: none;
        }
        .metadata td:first-child {
            font-weight: bold;
            width: 200px;
            color: #666;
        }
        .screenshot-container {
            text-align: center;
            margin: 20px 0;
            background-color: #000;
            padding: 20px;
            border-radius: 5px;
        }
        .screenshot-container img {
            max-width: 100%;
            height: auto;
            border: 2px solid #444;
            border-radius: 3px;
        }
        .waveform-plot {
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            background-color: white;
        }
        .properties-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .properties-table th,
        .properties-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .properties-table th {
            background-color: #0066cc;
            color: white;
            font-weight: 600;
        }
        .properties-table tr:hover {
            background-color: #f5f5f5;
        }
        .section {
            margin-bottom: 40px;
        }
        .timestamp {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #28a745;
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
        }
        .stat-card .value {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }
        .stat-card .unit {
            font-size: 0.8em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
''')
    
    # Header
    html_parts.append(f'''        <h1>MSOX4154A Oscilloscope Capture Report</h1>
        <div class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
''')
    
    # Metadata section
    if message or 'address' in captured_files:
        html_parts.append('        <div class="metadata"><table>')
        if message:
            html_parts.append(f'            <tr><td>Capture ID:</td><td>{message}</td></tr>')
        if 'address' in captured_files:
            html_parts.append(f'            <tr><td>Oscilloscope:</td><td>{captured_files["address"]}</td></tr>')
        if 'identity' in captured_files:
            html_parts.append(f'            <tr><td>Instrument:</td><td>{captured_files["identity"]}</td></tr>')
        html_parts.append('        </table></div>')
    
    # Properties section
    if 'properties' in captured_files:
        html_parts.append('        <div class="section">')
        html_parts.append('            <h2>Oscilloscope Properties</h2>')
        props = captured_files['properties']
        html_parts.append('            <table class="properties-table">')
        html_parts.append('                <tr><th>Property</th><th>Value</th><th>Units</th></tr>')
        for key, value in props.items():
            units = get_property_units(key)
            html_parts.append(f'                <tr><td>{key}</td><td>{value}</td><td>{units}</td></tr>')
        html_parts.append('            </table>')
        html_parts.append('        </div>')
    
    # Screenshot section
    if 'screenshot' in captured_files:
        html_parts.append('        <div class="section">')
        html_parts.append('            <h2>Screenshot</h2>')
        html_parts.append('            <div class="screenshot-container">')
        
        # Read and encode screenshot
        screenshot_path = captured_files['screenshot']
        try:
            with open(screenshot_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            html_parts.append(f'                <img src="data:image/png;base64,{img_data}" alt="Oscilloscope Screenshot">')
        except Exception as e:
            html_parts.append(f'                <p style="color: red;">Error loading screenshot: {e}</p>')
        
        html_parts.append('            </div>')
        html_parts.append('        </div>')
    
    # Waveforms section
    if 'waveforms' in captured_files and captured_files['waveforms']:
        html_parts.append('        <div class="section">')
        html_parts.append('            <h2>Waveforms</h2>')
        
        for ch_num, wf_data in captured_files['waveforms'].items():
            html_parts.append(f'            <h3>Channel {ch_num}</h3>')
            
            # Statistics cards
            if 'stats' in wf_data:
                stats = wf_data['stats']
                html_parts.append('            <div class="stats-grid">')
                if 'mean' in stats:
                    html_parts.append(f'''                <div class="stat-card">
                    <h3>Mean Voltage</h3>
                    <div class="value">{stats["mean"]:.6f} <span class="unit">V</span></div>
                </div>''')
                if 'vpp' in stats:
                    html_parts.append(f'''                <div class="stat-card">
                    <h3>Peak-to-Peak</h3>
                    <div class="value">{stats["vpp"]:.6f} <span class="unit">V</span></div>
                </div>''')
                if 'sample_rate' in stats:
                    html_parts.append(f'''                <div class="stat-card">
                    <h3>Sample Rate</h3>
                    <div class="value">{stats["sample_rate"]/1e6:.3f} <span class="unit">MS/s</span></div>
                </div>''')
                if 'points' in stats:
                    html_parts.append(f'''                <div class="stat-card">
                    <h3>Data Points</h3>
                    <div class="value">{stats["points"]:,}</div>
                </div>''')
                html_parts.append('            </div>')
            
            # Read waveform CSV
            try:
                times = []
                voltages = []
                with open(wf_data['file'], 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and not row[0].startswith('#') and row[0] != 'Time (s)':
                            try:
                                times.append(float(row[0]))
                                voltages.append(float(row[1]))
                            except ValueError:
                                continue
                
                # Create plotly graph
                plot_id = f'waveform_ch{ch_num}'
                html_parts.append(f'            <div id="{plot_id}" class="waveform-plot"></div>')
                html_parts.append('            <script>')
                html_parts.append(f'''                var trace_{ch_num} = {{
                    x: {times},
                    y: {voltages},
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Channel {ch_num}',
                    line: {{
                        color: 'rgb(0, 102, 204)',
                        width: 1
                    }}
                }};
                var layout_{ch_num} = {{
                    title: 'Channel {ch_num} Waveform',
                    xaxis: {{
                        title: 'Time (s)',
                        gridcolor: '#e0e0e0'
                    }},
                    yaxis: {{
                        title: 'Voltage (V)',
                        gridcolor: '#e0e0e0'
                    }},
                    plot_bgcolor: '#fafafa',
                    paper_bgcolor: 'white',
                    hovermode: 'closest'
                }};
                Plotly.newPlot('{plot_id}', [trace_{ch_num}], layout_{ch_num}, {{responsive: true}});''')
                html_parts.append('            </script>')
            except Exception as e:
                html_parts.append(f'            <p style="color: red;">Error loading waveform: {e}</p>')
    
    # Footer
    html_parts.append('''    </div>
</body>
</html>''')
    
    # Write HTML file
    with open(filepath, 'w') as f:
        f.write('\n'.join(html_parts))
    
    print_success(f"HTML report generated ({os.path.getsize(filepath)} bytes)")
    print(f"  File: {filepath}")
    
    return filepath


def open_with_electron(html_path: str) -> bool:
    """
    Open HTML file with default browser or electron app framework.
    
    Args:
        html_path: Path to HTML file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        import webbrowser
        
        # Convert to absolute path with proper file:// URL
        abs_path = os.path.abspath(html_path)
        
        # On Windows, use file:/// with forward slashes
        if sys.platform == 'win32':
            abs_path = abs_path.replace('\\', '/')
            file_url = f'file:///{abs_path}'
        else:
            file_url = f'file://{abs_path}'
        
        # Try to open in default browser
        success = webbrowser.open(file_url)
        
        if success:
            print_success(f"Opening report in default browser...")
            print(f"  URL: {file_url}")
            print(f"  If browser doesn't open, manually navigate to: {abs_path}")
        else:
            print_warning("Could not open browser automatically")
            print(f"  Please open this file manually: {abs_path}")
        
        return success
        
    except Exception as e:
        print_error(f"Failed to open HTML: {e}")
        print(f"  Please open this file manually: {os.path.abspath(html_path)}")
        return False


def capture_properties(scope: KeysightMSOX4154A, output_dir: str, message: Optional[str] = None) -> Optional[Dict[str, str]]:
    """Capture oscilloscope properties and settings.
    
    Args:
        scope: Connected MSOX4154A instance
        output_dir: Output directory path
        message: Optional message for filename
    
    Returns:
        Dictionary of properties if successful, None otherwise
    """
    print_header("Properties Capture")
    
    try:
        print_test("Capturing oscilloscope properties")
        
        # Generate filename
        filename = generate_filename("msox4154a", "properties", message, "txt")
        filepath = os.path.join(output_dir, filename)
        
        # Collect properties (channel settings only)
        props = {}
        
        # Get oscilloscope configuration (includes channel settings)
        try:
            config = scope.get_oscilloscope_config()
            for key, value in config.items():
                # Format the key for better readability
                formatted_key = key.replace('_', ' ').title()
                props[formatted_key] = value
        except Exception as e:
            props['Config Error'] = f"ERROR - {e}"
        
        # Write to file
        with open(filepath, 'w') as f:
            f.write("MSOX4154A Oscilloscope Properties\n")
            f.write("=" * 70 + "\n\n")
            for key, value in props.items():
                f.write(f"{key}: {value}\n")
            f.write("\n" + "=" * 70 + "\n")
            f.write("Properties captured successfully\n")
        
        file_size = os.path.getsize(filepath)
        print_success(f"Properties captured ({file_size} bytes)")
        print(f"  File: {filepath}")
        
        return props
        
    except Exception as e:
        print_error(f"Properties capture failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_identity_query(scope: KeysightMSOX4154A) -> bool:
    """Test instrument identification query."""
    print_header("Identity Query Test")
    
    try:
        print_test("Querying instrument identification")
        identity = scope.get_idn()
        print_success(f"Instrument Identity: {identity}")
        
        # Verify it's the correct model
        if "MSOX4154A" in identity or "MSO-X 4154A" in identity:
            print_success("Confirmed MSOX4154A model")
        else:
            print_warning(f"Unexpected model in identity string")
        
        return True
        
    except Exception as e:
        print_error(f"Identity query failed: {e}")
        return False


def capture_screenshot(scope: KeysightMSOX4154A, output_dir: str, message: Optional[str] = None) -> Optional[str]:
    """Capture oscilloscope screenshot.
    
    Args:
        scope: Connected MSOX4154A instance
        output_dir: Output directory path
        message: Optional message for filename
    
    Returns:
        Path to screenshot file if successful, None otherwise
    """
    print_header("Screenshot Capture")
    
    try:
        # Generate filename
        filename = generate_filename("msox4154a", "screenshot", message, "png")
        filepath = os.path.join(output_dir, filename)
        
        print_test("Capturing oscilloscope screenshot")
        success = scope.save_screenshot(filepath)
        
        if success and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print_success(f"Screenshot captured successfully ({file_size} bytes)")
            print(f"  File: {filepath}")
            return filepath
        else:
            print_error("Screenshot capture failed")
            return None
        
    except Exception as e:
        print_error(f"Screenshot capture failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def capture_waveforms(scope: KeysightMSOX4154A, channels: List[int], output_dir: str, 
                     message: Optional[str] = None) -> Dict[int, Dict[str, Any]]:
    """Capture waveforms from specified channels.
    
    Args:
        scope: Connected MSOX4154A instance
        channels: List of channel numbers to capture
        output_dir: Output directory path
        message: Optional message for filename
    
    Returns:
        Dictionary mapping channel numbers to waveform data and metadata
    """
    print_header("Waveform Capture")
    
    success_count = 0
    waveform_dict = {}
    
    for ch_num in channels:
        try:
            source = f"CHAN{ch_num}"
            print_test(f"Capturing waveform from Channel {ch_num}")
            
            time_data, voltage_data, metadata = scope.get_waveform(source=source)
            
            # Generate filename
            item = f"waveform-ch{ch_num}"
            filename = generate_filename("msox4154a", item, message, "csv")
            filepath = os.path.join(output_dir, filename)
            
            # Save to CSV
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header with metadata
                writer.writerow([f"# MSOX4154A Waveform Data - Channel {ch_num}"])
                writer.writerow([f"# Captured: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([f"# Points: {len(time_data)}"])
                
                if 'x_increment' in metadata:
                    sample_rate = 1.0 / metadata['x_increment']
                    writer.writerow([f"# Sample Rate: {sample_rate/1e6:.3f} MS/s"])
                
                if 'vpp' in metadata:
                    writer.writerow([f"# Peak-to-Peak: {metadata['vpp']:.6f} V"])
                
                if 'mean' in metadata:
                    writer.writerow([f"# Mean: {metadata['mean']:.6f} V"])
                
                writer.writerow([])  # Blank line
                writer.writerow(["Time (s)", "Voltage (V)"])
                
                # Write data
                for t, v in zip(time_data, voltage_data):
                    writer.writerow([f"{t:.12e}", f"{v:.12e}"])
            
            file_size = os.path.getsize(filepath)
            print_success(f"Captured {len(time_data)} points ({file_size} bytes)")
            print(f"  File: {filepath}")
            
            # Display quick stats
            print(f"  Time range: {time_data[0]:.9f} to {time_data[-1]:.9f} s")
            print(f"  Voltage range: {min(voltage_data):.6f} to {max(voltage_data):.6f} V")
            
            if 'x_increment' in metadata:
                sample_rate = 1.0 / metadata['x_increment']
                print(f"  Sample rate: {sample_rate/1e6:.3f} MS/s")
            
            # Store waveform data for report
            wf_data = {
                'file': filepath,
                'points': len(time_data),
                'stats': {}
            }
            if 'x_increment' in metadata:
                wf_data['stats']['sample_rate'] = 1.0 / metadata['x_increment']
            if 'vpp' in metadata:
                wf_data['stats']['vpp'] = metadata['vpp']
            if 'mean' in metadata:
                wf_data['stats']['mean'] = metadata['mean']
            wf_data['stats']['points'] = len(time_data)
            
            waveform_dict[ch_num] = wf_data
            success_count += 1
            
        except Exception as e:
            print_error(f"Channel {ch_num} capture failed: {e}")
            import traceback
            traceback.print_exc()
    
    if success_count == len(channels):
        print_success(f"All {success_count} channel(s) captured successfully")
    elif success_count > 0:
        print_warning(f"Partial success: {success_count}/{len(channels)} channels captured")
    else:
        print_error("All channel captures failed")
    
    return waveform_dict


def test_connection_methods(args) -> bool:
    """Test various connection methods based on command line arguments."""
    print_header("MSOX4154A Connection and Capture")
    
    scope = None
    
    try:
        # Ensure output directory exists
        output_dir = ensure_output_dir(args.output)
        print(f"Output directory: {output_dir}\n")
        
        # Parse channels
        channels = [int(ch.strip()) for ch in args.channels.split(',')]
        print(f"Channels to capture: {', '.join(map(str, channels))}")
        if args.message:
            print(f"Filename message: {args.message}")
        print()
        
        # Test the specified connection method
        if args.ip:
            print_test(f"Connecting via IP address: {args.ip}")
            scope = KeysightMSOX4154A(ip_address=args.ip, debug=args.debug)
        elif args.address:
            print_test(f"Connecting via explicit address: {args.address}")
            scope = KeysightMSOX4154A(address=args.address, debug=args.debug)
        else:
            print_test("Searching for MSOX4154A (auto-connect)")
            scope = KeysightMSOX4154A(debug=args.debug)
        
        print_success(f"Successfully connected to MSOX4154A")
        print(f"  Address: {scope.address}")
        print(f"  Status: {scope.status}")
        
        # Run identity query test
        if not test_identity_query(scope):
            return False
        
        # Determine what to capture
        capture_items = []
        if args.screenshot:
            capture_items.append("screenshot")
        if args.waveform:
            capture_items.append("waveform")
        if args.properties:
            capture_items.append("properties")
        
        # If no specific items requested, just test connection
        if not capture_items:
            print_warning("No capture items requested (use --screenshot, --waveform, or --properties)")
            print_warning("Connection test successful. Use capture flags to save data.")
            return True
        
        print(f"\nCapture items: {', '.join(capture_items)}\n")
        
        # Perform captures
        success = True
        captured_data = {
            'address': scope.address,
            'identity': scope.get_idn() if scope.instrument else 'Unknown'
        }
        
        if args.screenshot:
            screenshot_path = capture_screenshot(scope, output_dir, args.message)
            if screenshot_path:
                captured_data['screenshot'] = screenshot_path
            else:
                print_warning("Screenshot capture failed")
                success = False
        
        if args.waveform:
            waveforms = capture_waveforms(scope, channels, output_dir, args.message)
            if waveforms:
                captured_data['waveforms'] = waveforms
            else:
                print_warning("Waveform capture failed")
                success = False
        
        if args.properties:
            props = capture_properties(scope, output_dir, args.message)
            if props:
                captured_data['properties'] = props
            else:
                print_warning("Properties capture failed")
                success = False
        
        # Generate HTML report if requested
        if args.preview and (args.screenshot or args.waveform or args.properties):
            print_header("Generating HTML Report")
            try:
                html_path = generate_html_report(captured_data, output_dir, args.message)
                open_with_electron(html_path)
            except Exception as e:
                print_error(f"Failed to generate HTML report: {e}")
                import traceback
                traceback.print_exc()
        
        return success
        
    except ConnectionError as e:
        print_error(f"Connection failed: {e}")
        print_warning("Troubleshooting tips:")
        print("  1. Check that MSOX4154A is powered on")
        print("  2. Verify USB cable connection (if using USB)")
        print("  3. Check network connectivity: ping [IP_ADDRESS]")
        print("  4. Verify VISA drivers are installed (Keysight IO Libraries)")
        print("  5. List resources: python -c \"import pyvisa; print(pyvisa.ResourceManager().list_resources())\"")
        print("  6. Check IP address: Utility > I/O > LAN on the MSOX4154A")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if scope:
            print_test("Disconnecting from MSOX4154A")
            scope.disconnect()
            print_success("Disconnected successfully")


def interactive_mode() -> argparse.Namespace:
    """Interactive mode - prompt user for connection details."""
    print_header("MSOX4154A Interactive Connection Mode")
    
    print("\nSelect connection method:")
    print("  1. Auto-connect (search USB and Ethernet)")
    print("  2. Connect via IP address")
    print("  3. Connect via explicit VISA address")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    args = argparse.Namespace()
    args.debug = False
    args.ip = None
    args.address = None
    args.screenshot = False
    args.waveform = False
    args.properties = False
    args.channels = "1"
    args.message = None
    args.output = "output"
    args.preview = False
    
    if choice == "1":
        print("\nUsing auto-connect mode...")
        enable_debug = input("Enable debug output? (y/n): ").strip().lower()
        args.debug = (enable_debug == 'y')
    elif choice == "2":
        ip = input("\nEnter IP address (e.g., 192.168.1.100): ").strip()
        args.ip = ip
        enable_debug = input("Enable debug output? (y/n): ").strip().lower()
        args.debug = (enable_debug == 'y')
    elif choice == "3":
        address = input("\nEnter VISA address (e.g., USB0::0x0957::...::INSTR): ").strip()
        args.address = address
        enable_debug = input("Enable debug output? (y/n): ").strip().lower()
        args.debug = (enable_debug == 'y')
    else:
        print_error("Invalid choice. Using auto-connect mode.")
    
    return args


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test Keysight MSOX4154A Oscilloscope Ethernet connectivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_msox4154a_ethernet.py                              # Auto-connect
  python test_msox4154a_ethernet.py --ip 192.168.1.100          # Connect via IP
  python test_msox4154a_ethernet.py --address "TCPIP0::192.168.1.100::inst0::INSTR"  # Explicit address
  python test_msox4154a_ethernet.py --interactive                # Interactive mode
  python test_msox4154a_ethernet.py --debug                      # Debug mode
        """
    )
    
    # Connection options
    parser.add_argument('--ip', type=str, help='IP address for Ethernet connection')
    parser.add_argument('--address', type=str, help='Explicit VISA resource address')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug output (shows resource scanning)')
    
    # Capture options
    parser.add_argument('--screenshot', action='store_true',
                       help='Capture oscilloscope screenshot')
    parser.add_argument('--waveform', action='store_true',
                       help='Capture waveform data from specified channels')
    parser.add_argument('--properties', action='store_true',
                       help='Capture oscilloscope properties/settings')
    parser.add_argument('-ch', '--channels', type=str, default='1',
                       help='Comma-separated channel list (e.g., "1,2,3,4") [default: 1]')
    parser.add_argument('-m', '--message', type=str,
                       help='Custom message to append to filename')
    parser.add_argument('-o', '--output', type=str, default='output',
                       help='Output directory [default: output/]')
    parser.add_argument('--preview', action='store_true',
                       help='Generate and open HTML report of captured data')
    
    args = parser.parse_args()
    
    # Handle interactive mode
    if args.interactive:
        args = interactive_mode()
    
    # Run connection tests
    print_header("Keysight MSOX4154A Oscilloscope Ethernet Test Suite")
    print(f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    success = test_connection_methods(args)
    
    # Print summary
    print_header("Summary")
    if success:
        print_success("Operation completed successfully!")
        print("\nNext steps:")
        print("  - Use the KeysightMSOX4154A class with ip_address parameter in your scripts")
        print("  - Integrate with data_logger for automated data collection")
        print("  - Refer to libs/KeysightMSOX4154A.py docstring for usage examples")
        print("\nCapture examples:")
        print("  python test_msox4154a_ethernet.py --ip 192.168.1.100 --screenshot -m \"test1\"")
        print("  python test_msox4154a_ethernet.py --waveform -ch 1,2,3,4 -m \"multichannel\"")
        print("  python test_msox4154a_ethernet.py --screenshot --waveform --properties -ch 1,2")
        return 0
    else:
        print_error("Some operations failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
