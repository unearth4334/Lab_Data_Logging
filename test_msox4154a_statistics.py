#!/usr/bin/env python3
"""
test_msox4154a_statistics.py

Lab Data Logging - Test Script for Keysight MSOX4154A Oscilloscope Statistics

This script demonstrates how to connect to the Keysight MSOX4154A oscilloscope using the 
data_logger framework and retrieve measurement statistics including:
- Voltage measurements (Vpp, Vmax, Vmin, Vrms, Vavg)
- Timing measurements (frequency, period, rise time, fall time)
- Advanced measurements (duty cycle, overshoot, preshoot)
- Waveform data with computed statistics

Usage:
    python test_msox4154a_statistics.py <VISA_ADDRESS>
    
    Example:
    python test_msox4154a_statistics.py "USB0::0x0957::0x17BC::MY59241237::INSTR"

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
import statistics as stats
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from colorama import init, Fore, Style

# Add libs directory to path for device imports
sys.path.append('./libs')
from KeysightMSOX4154A import KeysightMSOX4154A

# Console styling to match framework conventions
init(autoreset=True)
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "
_INFO_STYLE = Fore.CYAN + Style.BRIGHT + "\rInfo: "


class MSOX4154A_Statistics:
    """
    Extended wrapper for Keysight MSOX4154A with built-in measurement statistics capabilities.
    
    This class extends the basic KeysightMSOX4154A driver to include comprehensive
    measurement statistics functionality commonly used in laboratory testing.
    """
    
    def __init__(self, visa_address: str):
        """Initialize oscilloscope connection."""
        self.osc = KeysightMSOX4154A(auto_connect=False)
        self.visa_address = visa_address
        self.connected = False
        
    def connect(self):
        """Establish connection to oscilloscope."""
        try:
            self.osc.connect(self.visa_address)
            self.connected = True
            print(_SUCCESS_STYLE + f"Connected to oscilloscope: {self.get_idn()}")
        except Exception as e:
            print(_ERROR_STYLE + f"Failed to connect: {e}")
            raise
            
    def disconnect(self):
        """Close oscilloscope connection."""
        if self.connected:
            self.osc.disconnect()
            self.connected = False
            
    def get_idn(self) -> str:
        """Get instrument identification."""
        return self.osc.get_idn()
        
    def _ensure_connected(self):
        """Check connection status."""
        if not self.connected:
            raise ConnectionError(_ERROR_STYLE + "Oscilloscope not connected")
            
    def setup_measurements(self, channel: str = "CHAN1"):
        """
        Configure oscilloscope for optimal measurement accuracy.
        
        Args:
            channel: Channel to configure (CHAN1, CHAN2, etc.)
        """
        self._ensure_connected()
        inst = self.osc.instrument
        
        try:
            # Clear any existing measurements
            inst.write(":MEASure:CLEar")
            
            # Set measurement source
            inst.write(f":MEASure:SOURce {channel}")
            
            # Configure measurement statistics
            inst.write(":MEASure:STATistics ON")
            inst.write(":MEASure:STATistics:DISPlay ON")
            
            print(_SUCCESS_STYLE + f"Configured measurements for {channel}")
            
        except Exception as e:
            print(_ERROR_STYLE + f"Failed to setup measurements: {e}")
            raise
            
    def get_voltage_measurements(self, channel: str = "CHAN1") -> Dict[str, float]:
        """
        Retrieve comprehensive voltage measurements from specified channel.
        
        Args:
            channel: Oscilloscope channel (CHAN1, CHAN2, etc.)
            
        Returns:
            Dictionary containing voltage measurements with statistics
        """
        self._ensure_connected()
        inst = self.osc.instrument
        
        measurements = {}
        
        # Define voltage measurements to collect
        voltage_params = {
            "VPP": "peak-to-peak voltage",
            "VMAX": "maximum voltage", 
            "VMIN": "minimum voltage",
            "VRMS": "RMS voltage",
            "VAVerage": "average voltage",
            "VTOP": "statistical top voltage",
            "VBASe": "statistical base voltage",
            "VAMPlitude": "amplitude (Vtop - Vbase)"
        }
        
        try:
            inst.write(f":MEASure:SOURce {channel}")
            
            for param, description in voltage_params.items():
                try:
                    # Query measurement value
                    result = inst.query(f":MEASure:{param}?").strip()
                    
                    # Parse result (handle error cases)
                    if "9.9E+37" in result or "ERROR" in result.upper():
                        measurements[param] = float('nan')
                        print(_WARNING_STYLE + f"{param} measurement failed for {channel}")
                    else:
                        measurements[param] = float(result)
                        
                except Exception as e:
                    measurements[param] = float('nan')
                    print(_WARNING_STYLE + f"Failed to measure {param}: {e}")
                    
        except Exception as e:
            print(_ERROR_STYLE + f"Voltage measurement error: {e}")
            raise
            
        return measurements
        
    def get_timing_measurements(self, channel: str = "CHAN1") -> Dict[str, float]:
        """
        Retrieve timing-related measurements from specified channel.
        
        Args:
            channel: Oscilloscope channel (CHAN1, CHAN2, etc.)
            
        Returns:
            Dictionary containing timing measurements
        """
        self._ensure_connected()
        inst = self.osc.instrument
        
        measurements = {}
        
        # Define timing measurements to collect
        timing_params = {
            "FREQuency": "signal frequency",
            "PERiod": "signal period", 
            "RISetime": "10%-90% rise time",
            "FALLtime": "90%-10% fall time",
            "PWIDth": "positive pulse width",
            "NWIDth": "negative pulse width",
            "DCYCle": "duty cycle percentage"
        }
        
        try:
            inst.write(f":MEASure:SOURce {channel}")
            
            for param, description in timing_params.items():
                try:
                    result = inst.query(f":MEASure:{param}?").strip()
                    
                    if "9.9E+37" in result or "ERROR" in result.upper():
                        measurements[param] = float('nan')
                        print(_WARNING_STYLE + f"{param} measurement failed for {channel}")
                    else:
                        measurements[param] = float(result)
                        
                except Exception as e:
                    measurements[param] = float('nan')
                    print(_WARNING_STYLE + f"Failed to measure {param}: {e}")
                    
        except Exception as e:
            print(_ERROR_STYLE + f"Timing measurement error: {e}")
            raise
            
        return measurements
        
    def get_waveform_statistics(self, channel: str = "CHAN1") -> Dict[str, Any]:
        """
        Capture waveform data and compute comprehensive statistics.
        
        Args:
            channel: Oscilloscope channel (CHAN1, CHAN2, etc.)
            
        Returns:
            Dictionary containing waveform data and computed statistics
        """
        self._ensure_connected()
        
        try:
            # Capture waveform data
            t, y, meta = self.osc.get_waveform(source=channel, debug=True)
            
            if not y:
                print(_WARNING_STYLE + f"No waveform data available for {channel}")
                return {}
                
            # Compute statistical measures
            waveform_stats = {
                "samples": len(y),
                "duration_s": t[-1] - t[0] if len(t) > 1 else 0,
                "sample_rate_hz": meta.get("sample_rate_hz", float('nan')),
                "mean_v": stats.mean(y),
                "std_dev_v": stats.stdev(y) if len(y) > 1 else 0,
                "min_v": min(y),
                "max_v": max(y),
                "peak_to_peak_v": max(y) - min(y),
                "rms_v": (sum(val**2 for val in y) / len(y))**0.5,
                "median_v": stats.median(y)
            }
            
            # Add percentile measurements
            sorted_y = sorted(y)
            n = len(sorted_y)
            waveform_stats.update({
                "percentile_10_v": sorted_y[int(0.1 * n)],
                "percentile_90_v": sorted_y[int(0.9 * n)],
                "percentile_25_v": sorted_y[int(0.25 * n)], 
                "percentile_75_v": sorted_y[int(0.75 * n)]
            })
            
            return waveform_stats
            
        except Exception as e:
            print(_ERROR_STYLE + f"Waveform statistics error: {e}")
            raise
            
    def get_all_statistics(self, channels: List[str] = ["CHAN1"]) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve comprehensive statistics from multiple channels.
        
        Args:
            channels: List of channels to measure (e.g., ["CHAN1", "CHAN2"])
            
        Returns:
            Dictionary organized by channel containing all measurement types
        """
        all_stats = {}
        
        for channel in channels:
            print(_INFO_STYLE + f"Collecting statistics for {channel}...")
            
            channel_stats = {
                "voltage_measurements": {},
                "timing_measurements": {},
                "waveform_statistics": {}
            }
            
            try:
                # Setup measurements for this channel
                self.setup_measurements(channel)
                time.sleep(0.5)  # Allow measurements to settle
                
                # Collect all measurement types
                channel_stats["voltage_measurements"] = self.get_voltage_measurements(channel)
                channel_stats["timing_measurements"] = self.get_timing_measurements(channel)
                channel_stats["waveform_statistics"] = self.get_waveform_statistics(channel)
                
            except Exception as e:
                print(_ERROR_STYLE + f"Failed to collect statistics for {channel}: {e}")
                
            all_stats[channel] = channel_stats
            
        return all_stats


def format_statistics_report(stats: Dict[str, Dict[str, Any]]) -> str:
    """Format statistics data into a readable report."""
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("KEYSIGHT MSOX4154A OSCILLOSCOPE STATISTICS REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    for channel, channel_data in stats.items():
        report_lines.append(f"\n{channel.upper()} MEASUREMENTS")
        report_lines.append("-" * 40)
        
        # Voltage measurements section
        voltage_data = channel_data.get("voltage_measurements", {})
        if voltage_data:
            report_lines.append("\nVoltage Measurements:")
            for param, value in voltage_data.items():
                if not (value != value):  # Check for NaN
                    if "VPP" in param or "VMAX" in param or "VMIN" in param or "VRMS" in param:
                        report_lines.append(f"  {param:12s}: {value:8.4f} V")
                    else:
                        report_lines.append(f"  {param:12s}: {value:8.6f} V")
                        
        # Timing measurements section  
        timing_data = channel_data.get("timing_measurements", {})
        if timing_data:
            report_lines.append("\nTiming Measurements:")
            for param, value in timing_data.items():
                if not (value != value):  # Check for NaN
                    if param == "FREQuency":
                        report_lines.append(f"  {param:12s}: {value:8.2f} Hz")
                    elif param == "PERiod":
                        report_lines.append(f"  {param:12s}: {value:8.6f} s")
                    elif "time" in param.lower():
                        report_lines.append(f"  {param:12s}: {value:8.3e} s")
                    elif param == "DCYCle":
                        report_lines.append(f"  {param:12s}: {value:8.2f} %")
                    else:
                        report_lines.append(f"  {param:12s}: {value:8.3e}")
                        
        # Waveform statistics section
        waveform_data = channel_data.get("waveform_statistics", {})
        if waveform_data:
            report_lines.append("\nWaveform Statistics:")
            report_lines.append(f"  {'Samples':12s}: {waveform_data.get('samples', 0):8d}")
            report_lines.append(f"  {'Duration':12s}: {waveform_data.get('duration_s', 0):8.6f} s")
            report_lines.append(f"  {'Sample Rate':12s}: {waveform_data.get('sample_rate_hz', 0):8.0f} Hz")
            report_lines.append(f"  {'Mean':12s}: {waveform_data.get('mean_v', 0):8.6f} V")
            report_lines.append(f"  {'Std Dev':12s}: {waveform_data.get('std_dev_v', 0):8.6f} V")
            report_lines.append(f"  {'Min/Max':12s}: {waveform_data.get('min_v', 0):8.6f} / {waveform_data.get('max_v', 0):8.6f} V")
            report_lines.append(f"  {'Peak-Peak':12s}: {waveform_data.get('peak_to_peak_v', 0):8.6f} V")
            report_lines.append(f"  {'RMS':12s}: {waveform_data.get('rms_v', 0):8.6f} V")
            
    report_lines.append("\n" + "=" * 80)
    return "\n".join(report_lines)


def save_statistics_csv(stats: Dict[str, Dict[str, Any]], filename: str):
    """Save statistics to CSV file for further analysis."""
    
    import csv
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(["Channel", "Measurement_Type", "Parameter", "Value", "Unit"])
        
        for channel, channel_data in stats.items():
            # Voltage measurements
            for param, value in channel_data.get("voltage_measurements", {}).items():
                if not (value != value):  # Skip NaN values
                    writer.writerow([channel, "Voltage", param, f"{value:.6f}", "V"])
                    
            # Timing measurements  
            for param, value in channel_data.get("timing_measurements", {}).items():
                if not (value != value):  # Skip NaN values
                    unit = "Hz" if param == "FREQuency" else "s" if param != "DCYCle" else "%"
                    writer.writerow([channel, "Timing", param, f"{value:.6e}", unit])
                    
            # Waveform statistics
            waveform_data = channel_data.get("waveform_statistics", {})
            for param, value in waveform_data.items():
                if param == "samples":
                    writer.writerow([channel, "Waveform", param, str(value), "count"])
                elif "_hz" in param:
                    writer.writerow([channel, "Waveform", param, f"{value:.2f}", "Hz"])
                elif "_s" in param:
                    writer.writerow([channel, "Waveform", param, f"{value:.6e}", "s"])
                elif "_v" in param:
                    writer.writerow([channel, "Waveform", param, f"{value:.6f}", "V"])


def main():
    """Main test execution function."""
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python test_msox4154a_statistics.py <VISA_ADDRESS>")
        print('Example: python test_msox4154a_statistics.py "USB0::0x0957::0x17BC::MY59241237::INSTR"')
        sys.exit(1)
        
    visa_address = sys.argv[1]
    
    print(_INFO_STYLE + "Keysight MSOX4154A Statistics Test")
    print("=" * 50)
    print(f"VISA Address: {visa_address}")
    print()
    
    # Create output directory
    output_dir = Path("captures")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize oscilloscope
    osc_stats = MSOX4154A_Statistics(visa_address)
    
    try:
        # Connect to oscilloscope
        osc_stats.connect()
        
        # Define channels to test (modify as needed)
        channels_to_test = ["CHAN1", "CHAN2"]  # Add more channels as needed
        
        print(_INFO_STYLE + f"Testing channels: {', '.join(channels_to_test)}")
        print()
        
        # Collect comprehensive statistics
        all_statistics = osc_stats.get_all_statistics(channels_to_test)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create and display report
        report = format_statistics_report(all_statistics)
        print(report)
        
        # Save results
        report_file = output_dir / f"msox4154a_statistics_report_{timestamp}.txt"
        csv_file = output_dir / f"msox4154a_statistics_data_{timestamp}.csv"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            
        save_statistics_csv(all_statistics, csv_file)
        
        print(_SUCCESS_STYLE + f"Statistics saved to:")
        print(f"  Report: {report_file}")
        print(f"  Data:   {csv_file}")
        
    except KeyboardInterrupt:
        print(_WARNING_STYLE + "Test interrupted by user")
        
    except Exception as e:
        print(_ERROR_STYLE + f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Ensure oscilloscope is disconnected
        try:
            osc_stats.disconnect()
        except:
            pass
            
    print(_INFO_STYLE + "Test completed")


if __name__ == "__main__":
    main()