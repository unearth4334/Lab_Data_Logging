#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   @file KeysightMSOX4154A.py
#   @brief Keysight MSOX4154A control (screenshots + single/multi-channel waveform download).
#          This version **only** connects to explicit VISA addresses you pass in.
#   @date 16-Sep-2025

from __future__ import annotations
from typing import Optional, Any, Dict, List, Tuple

import pyvisa
from colorama import init, Fore, Style

_ERROR_STYLE   = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "

class KeysightMSOX4154A:
    """
    Example:
        osc = KeysightMSOX4154A(auto_connect=False)
        osc.connect("USB0::0x0957::0x17BC::MY59241237::INSTR")
        t, y, meta = osc.get_waveform(source="CHAN1")
        osc.disconnect()
    """

    def __init__(self, auto_connect: bool = True, timeout_ms: int = 20000, chunk_size: int = 102_400):
        init(autoreset=True)
        self.rm: pyvisa.ResourceManager = pyvisa.ResourceManager()
        self.address: Optional[str] = None
        self.instrument: Optional[pyvisa.resources.MessageBasedResource] = None
        self.status: str = "Not Connected"
        self._timeout_ms = timeout_ms
        self._chunk_size = chunk_size
        if auto_connect:
            self._auto_connect()

    # ---------- Connect / Disconnect ----------
    def _auto_connect(self):
        """Attempt to auto-detect and connect to Keysight MSOX4154A oscilloscope."""
        try:
            resources = self.rm.list_resources()
            for resource in resources:
                if "0x0957" in resource and "INSTR" in resource:  # Keysight vendor ID
                    try:
                        inst = self.rm.open_resource(resource)
                        inst.timeout = self._timeout_ms
                        idn = inst.query("*IDN?").strip()
                        if "MSOX4154A" in idn or "MSO-X 4154A" in idn:
                            inst.chunk_size = self._chunk_size
                            inst.write_termination = '\n'
                            inst.read_termination = None
                            try:
                                inst.write(":SYSTem:HEADer OFF")
                            except Exception:
                                pass
                            self.instrument = inst
                            self.address = resource
                            self.status = "Connected"
                            print(_SUCCESS_STYLE + f"Auto-connected to Keysight MSOX4154A at {resource}")
                            return
                        else:
                            inst.close()
                    except Exception:
                        try:
                            inst.close()
                        except:
                            pass
                        continue
            raise ConnectionError("No Keysight MSOX4154A oscilloscope found")
        except Exception as e:
            print(_ERROR_STYLE + f"Auto-connect failed: {e}")
            raise

    def connect(self, address: Optional[str] = None):
        """Connect to oscilloscope. If address provided, connect to specific address. Otherwise auto-detect."""
        if address is not None:
            # Connect to specific address
            if "::INSTR" not in address:
                raise ValueError(_ERROR_STYLE + f"Not a VISA INSTR address: {address}")
            try:
                inst = self.rm.open_resource(address)
                inst.timeout = self._timeout_ms
                inst.chunk_size = self._chunk_size
                inst.write_termination = '\n'
                inst.read_termination = None
                try:
                    inst.write(":SYSTem:HEADer OFF")
                except Exception:
                    pass
                self.instrument = inst
                self.address = address
                self.status = "Connected"
                print(_SUCCESS_STYLE + f"Connected to Keysight MSOX4154A Oscilloscope at {self.address}")
            except Exception as e:
                raise ConnectionError(_ERROR_STYLE + f"Failed to open {address}: {e}")
        else:
            # Auto-connect
            self._auto_connect()

    def disconnect(self):
        if self.instrument is not None:
            try:
                self.instrument.close()
            finally:
                print(f"\rDisconnected from Keysight MSOX4154A Oscilloscope at {self.address}")
                self.instrument = None
                self.status = "Not Connected"
                self.address = None

    # ---------- Helpers ----------
    def _chk(self):
        if self.instrument is None:
            raise ConnectionError(_ERROR_STYLE + "Not connected.")

    def get_idn(self) -> str:
        self._chk()
        return self.instrument.query("*IDN?").strip()  # type: ignore

    def is_running(self) -> bool:
        self._chk()
        try:
            return bool(int(self.instrument.query(":ACQuire:STATE?").strip()))  # type: ignore
        except Exception:
            return False

    def stop(self):
        self._chk()
        try: self.instrument.write(":STOP")  # type: ignore
        except Exception: pass

    def run(self):
        self._chk()
        try: 
            self.instrument.write(":RUN")  # type: ignore
            print(_SUCCESS_STYLE + "Oscilloscope acquisition started")
        except Exception: pass

    def save_screenshot(self, filename: str, inksaver: bool = False) -> bool:
        """
        Capture and save a screenshot to file.
        
        Args:
            filename: Output filename (should end with .png)
            inksaver: Use ink-saver mode for printing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            screenshot_data = self.get_screenshot(inksaver=inksaver)
            with open(filename, 'wb') as f:
                f.write(screenshot_data)
            print(_SUCCESS_STYLE + f"Screenshot saved: {filename}")
            return True
        except Exception as e:
            print(_ERROR_STYLE + f"Screenshot failed: {e}")
            return False

    # ---------- Screenshot ----------
    def get_screenshot(self, inksaver: bool = False) -> bytes:
        self._chk()
        inst = self.instrument  # type: ignore
        try:
            if inksaver:
                inst.write(":HARDcopy:INKSaver ON"); mode = "PNG,SCReen,ON,NORMal"
            else:
                inst.write(":HARDcopy:INKSaver OFF"); mode = "PNG,COLor"
            data = inst.query_binary_values(
                f":DISPlay:DATA? {mode}",
                datatype='B', is_big_endian=True,
                container=bytearray, chunk_size=self._chunk_size, delay=0
            )
            return bytes(data)
        except pyvisa.errors.VisaIOError as e:
            raise RuntimeError(_ERROR_STYLE + f"Screenshot failed: {e}")
        except Exception as e:
            raise RuntimeError(_ERROR_STYLE + f"Screenshot failed: {e}")

    # ---------- Waveform: scaled data with real timebase ----------
    def _read_preamble(self) -> Dict[str, float]:
        """
        Reads :WAV:PRE? and parses Keysight 10-field preamble.
        Returns dict with keys shown below.
        """
        self._chk()
        pre = self.instrument.query(":WAVeform:PREamble?").strip()  # type: ignore
        # Format per Keysight MSO-X 4000A:
        # 0:FORMAT, 1:TYPE, 2:POINTS, 3:COUNT, 4:XINCR, 5:XORIG, 6:XREF, 7:YINCR, 8:YORIG, 9:YREF
        parts = [p.strip() for p in pre.split(",")]
        if len(parts) < 10:
            raise RuntimeError(_ERROR_STYLE + f"Unexpected preamble: {pre}")
        return {
            "format": float(parts[0]),
            "type":   float(parts[1]),
            "points": int(float(parts[2])),
            "count":  int(float(parts[3])),
            "xincr":  float(parts[4]),
            "xorig":  float(parts[5]),
            "xref":   float(parts[6]),
            "yincr":  float(parts[7]),
            "yorig":  float(parts[8]),
            "yref":   float(parts[9]),
        }

    def get_waveform(self,
                     source: str = "CHAN1",
                     points_mode: str = "RAW",
                     points: Optional[int] = None,
                     stop_during_read: bool = True,
                     debug: bool = False
                     ) -> Tuple[List[float], List[float], Dict[str, Any]]:
        """
        Returns (t_seconds, volts, meta) using the scope's actual timebase.
        - source: e.g., "CHAN1"
        - points_mode: "RAW" (acquisition memory) or "NORMal"/"MAX" etc.
        - points: optional decimation point count
        - stop_during_read: stop acquisition to avoid buffer changing mid-read
        """
        self._chk()
        inst = self.instrument  # type: ignore


        # Configure waveform transfer
        inst.write(f":WAVeform:SOURce {source}")
        inst.write(":WAVeform:FORMat BYTE")
        inst.write(":WAVeform:BYTeorder LSBFirst")
        inst.write(f":WAVeform:POINts:MODE {points_mode}")
        if points is not None:
            inst.write(f":WAVeform:POINts {int(points)}")

        # Read scaling (preamble)
        meta = self._read_preamble()
        xincr = meta["xincr"]
        xorig = meta["xorig"]
        yincr = meta["yincr"]
        yorig = meta["yorig"]
        yref  = meta["yref"]
        sample_rate = 1.0 / xincr if xincr > 0 else float("nan")
        meta["sample_rate_hz"] = sample_rate

        # Fetch binary data (unsigned bytes 0..255)
        raw: List[int] = inst.query_binary_values(":WAVeform:DATA?",
                                                  datatype='B',
                                                  is_big_endian=False,
                                                  container=list,
                                                  chunk_size=self._chunk_size)

        n = len(raw)
        if debug:
            print(f"[{source}] points={n}, xincr={xincr} s, Fs={sample_rate} Hz")

        # Convert to time and volts
        t = [xorig + i * xincr for i in range(n)]
        y = [(v - yref) * yincr + yorig for v in raw]

        # Add a few more helpful fields
        meta.update({
            "source": source,
            "npoints": n,
            "dt_s": xincr,
            "t_start_s": t[0] if n else None,
            "t_stop_s": t[-1] if n else None,
        })
        return t, y, meta

    # ---------- Measurement Statistics ----------
    def setup_measurements(self, channel: str = "CHAN1"):
        """
        Configure oscilloscope for measurement statistics.
        
        Args:
            channel: Channel to configure (CHAN1, CHAN2, etc.)
        """
        self._chk()
        inst = self.instrument  # type: ignore
        
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
            raise RuntimeError(_ERROR_STYLE + f"Failed to setup measurements: {e}")

    def clear_measurement_statistics(self):
        """Clear measurement statistics counters."""
        self._chk()
        inst = self.instrument  # type: ignore
        
        try:
            inst.write(":MEASure:STATistics:RESet")
            print(_SUCCESS_STYLE + "Measurement statistics cleared")
        except Exception as e:
            print(_ERROR_STYLE + f"Failed to clear statistics: {e}")

    def get_measurement_count(self) -> int:
        """
        Get the current measurement count from statistics.
        
        Returns:
            Number of measurements taken since last statistics reset
        """
        self._chk()
        inst = self.instrument  # type: ignore
        
        try:
            result = inst.query(":MEASure:STATistics:COUNt?").strip()
            return int(float(result))
        except Exception as e:
            print(_ERROR_STYLE + f"Failed to get measurement count: {e}")
            return 0

    def list_configured_measurements(self) -> list:
        """
        Get list of currently configured measurements on oscilloscope.
        
        Returns:
            List of configured measurement names
        """
        self._chk()
        inst = self.instrument  # type: ignore
        
        try:
            # Try different ways to get measurement list
            measurements = []
            
            # Method 1: Query measurement catalog
            try:
                result = inst.query(":MEASure:CATalog?").strip()
                if result and "ERROR" not in result.upper():
                    # Parse the catalog response
                    measurements.extend(result.replace('"', '').split(','))
            except:
                pass
            
            # Method 2: Try common measurements individually
            common_measurements = ['VPP', 'VMAX', 'VMIN', 'VAMP', 'VTOP', 'VBASE', 
                                 'VAVerage', 'VRMS', 'PERiod', 'FREQuency',
                                 'RISetime', 'FALLtime', 'PWIDth', 'NWIDth',
                                 'XMAXimum', 'XMINimum']
            
            for meas in common_measurements:
                try:
                    result = inst.query(f":MEASure:{meas}?").strip()
                    if result and "9.9E+37" not in result and "ERROR" not in result.upper():
                        if meas not in measurements:
                            measurements.append(meas)
                except:
                    pass
            
            return measurements
            
        except Exception as e:
            print(_ERROR_STYLE + f"Failed to list measurements: {e}")
            return []

    def get_measurement_results(self) -> Dict[str, Any]:
        """
        Get results of all continuously displayed measurements using :MEASure:RESults? query.
        
        This method returns the results of all continuous measurements currently displayed.
        The response format depends on the :MEASure:STATistics setting:
        - If statistics are ON: returns label, current, min, max, mean, std dev, count for each measurement
        - If statistics are set to specific mode (CURRent, MIN, MAX, etc.): returns only that statistic
        
        Returns:
            Dictionary containing:
            - 'raw_response': Raw comma-separated response string
            - 'parsed_results': List of dictionaries with measurement data
            - 'statistics_mode': Current statistics mode setting
        """
        self._chk()
        inst = self.instrument  # type: ignore
        
        try:
            # Check current statistics mode
            stats_mode = inst.query(":MEASure:STATistics?").strip()
            
            # Get the raw measurement results
            raw_response = inst.query(":MEASure:RESults?").strip()
            
            if not raw_response:
                print("No measurement results available (empty response)")
                return {
                    'raw_response': '',
                    'parsed_results': [],
                    'statistics_mode': stats_mode
                }
            
            # Parse the results based on statistics mode
            parsed_results = []
            values = raw_response.split(',')
            
            if stats_mode == "1" or stats_mode.upper() == "ON":
                # Full statistics mode: label, current, min, max, mean, std dev, count (7 values per measurement)
                for i in range(0, len(values), 7):
                    if i + 6 < len(values):
                        try:
                            result = {
                                'label': values[i].strip().replace('"', ''),
                                'current': float(values[i+1]) if values[i+1] != '9.9E+37' else float('nan'),
                                'minimum': float(values[i+2]) if values[i+2] != '9.9E+37' else float('nan'),
                                'maximum': float(values[i+3]) if values[i+3] != '9.9E+37' else float('nan'),
                                'mean': float(values[i+4]) if values[i+4] != '9.9E+37' else float('nan'),
                                'std_dev': float(values[i+5]) if values[i+5] != '9.9E+37' else float('nan'),
                                'count': int(float(values[i+6])) if values[i+6] != '9.9E+37' else 0
                            }
                            parsed_results.append(result)
                        except (ValueError, IndexError) as e:
                            print(_WARNING_STYLE + f"Failed to parse measurement {i//7 + 1}: {e}")
            else:
                # Single statistic mode - each value corresponds to one measurement
                # We don't know the labels in this mode, so use generic names
                for i, value in enumerate(values):
                    try:
                        parsed_results.append({
                            'measurement_index': i + 1,
                            'value': float(value) if value != '9.9E+37' else float('nan'),
                            'statistic_type': stats_mode
                        })
                    except ValueError as e:
                        print(_WARNING_STYLE + f"Failed to parse value {i+1}: {e}")
            
            print(_SUCCESS_STYLE + f"Retrieved {len(parsed_results)} measurement results")
            
            return {
                'raw_response': raw_response,
                'parsed_results': parsed_results,
                'statistics_mode': stats_mode
            }
            
        except Exception as e:
            print(_ERROR_STYLE + f"Failed to get measurement results: {e}")
            return {
                'raw_response': '',
                'parsed_results': [],
                'statistics_mode': 'unknown'
            }

    def get_measurement_statistics(self, parameter: str) -> Dict[str, float]:
        """
        Get statistics for a specific measurement parameter.
        
        Args:
            parameter: Measurement parameter (VPP, VAVerage, XMAXimum, etc.)
            
        Returns:
            Dictionary with keys: current, minimum, maximum, mean, std_dev, count
        """
        self._chk()
        inst = self.instrument  # type: ignore
        
        try:
            # First check if statistics are enabled
            stat_state = inst.query(":MEASure:STATistics?").strip()
            if stat_state == "0" or stat_state.upper() == "OFF":
                # Turn on statistics
                inst.write(":MEASure:STATistics ON")
                print("Enabled measurement statistics")
            
            # Get count first to check if any measurements exist
            count = inst.query(f":MEASure:STATistics:COUNt?").strip()
            count_val = float(count) if count else 0
            
            if count_val == 0:
                print(f"No statistics available for {parameter} (count = 0)")
                return {
                    "current": float('nan'),
                    "minimum": float('nan'),
                    "maximum": float('nan'),
                    "mean": float('nan'),
                    "std_dev": float('nan'),
                    "count": 0
                }
            
            # Get all statistics for the parameter with longer timeout
            old_timeout = inst.timeout
            inst.timeout = 10000  # 10 second timeout
            
            current = inst.query(f":MEASure:{parameter}?").strip()
            minimum = inst.query(f":MEASure:{parameter}:MINimum?").strip()
            maximum = inst.query(f":MEASure:{parameter}:MAXimum?").strip()
            mean = inst.query(f":MEASure:{parameter}:MEAN?").strip()
            std_dev = inst.query(f":MEASure:{parameter}:SDEViation?").strip()
            
            # Restore timeout
            inst.timeout = old_timeout
            
            # Convert to float, handling errors
            def safe_float(val):
                try:
                    if "9.9E+37" in val or "ERROR" in val.upper():
                        return float('nan')
                    return float(val)
                except:
                    return float('nan')
            
            result = {
                "current": safe_float(current),
                "minimum": safe_float(minimum), 
                "maximum": safe_float(maximum),
                "mean": safe_float(mean),
                "std_dev": safe_float(std_dev),
                "count": count_val
            }
            
            print(f"Successfully got {parameter} statistics: {count_val} measurements")
            return result
            
        except Exception as e:
            print(_ERROR_STYLE + f"Failed to get statistics for {parameter}: {e}")
            return {
                "current": float('nan'),
                "minimum": float('nan'),
                "maximum": float('nan'), 
                "mean": float('nan'),
                "std_dev": float('nan'),
                "count": 0
            }

    def get_measurement(self, parameter: str, channel: Optional[str] = None) -> float:
        """
        Get a specific measurement from the oscilloscope.
        
        Args:
            parameter: Measurement parameter (VPP, VMAX, VMIN, VRMS, etc.)
            channel: Channel to measure (if None, uses current source)
            
        Returns:
            Measurement value or NaN if measurement failed
        """
        self._chk()
        inst = self.instrument  # type: ignore
        
        try:
            if channel is not None:
                inst.write(f":MEASure:SOURce {channel}")
                
            result = inst.query(f":MEASure:{parameter}?").strip()
            
            # Handle measurement errors (Keysight returns 9.9E+37 for invalid measurements)
            if "9.9E+37" in result or "ERROR" in result.upper():
                return float('nan')
            else:
                return float(result)
                
        except Exception as e:
            print(_ERROR_STYLE + f"Measurement {parameter} failed: {e}")
            return float('nan')

    def get_xat_max(self, channel: str = "CHAN1") -> float:
        """
        Get X@Max measurement (time position of maximum voltage).
        
        Args:
            channel: Channel to measure
            
        Returns:
            Time position of maximum voltage in seconds
        """
        self._chk()
        inst = self.instrument  # type: ignore
        
        try:
            inst.write(f":MEASure:SOURce {channel}")
            # Correct SCPI command for X@Maximum (time at maximum voltage)
            result = inst.query(":MEASure:XMAXimum?").strip()
            
            if "9.9E+37" in result or "ERROR" in result.upper():
                return float('nan')
            else:
                return float(result)
                
        except Exception as e:
            print(_ERROR_STYLE + f"X@Max measurement failed: {e}")
            return float('nan')

    def get_full_screen_average(self, channel: str = "CHAN1") -> float:
        """
        Get full-screen average measurement.
        
        Args:
            channel: Channel to measure
            
        Returns:
            Full-screen average voltage
        """
        return self.get_measurement("VAVerage", channel)

    def get_voltage_measurements(self, channel: str = "CHAN1") -> Dict[str, float]:
        """
        Retrieve comprehensive voltage measurements.
        
        Args:
            channel: Oscilloscope channel (CHAN1, CHAN2, etc.)
            
        Returns:
            Dictionary containing voltage measurements
        """
        self._chk()
        
        voltage_params = ["VPP", "VMAX", "VMIN", "VRMS", "VAVerage", "VTOP", "VBASe", "VAMPlitude"]
        measurements = {}
        
        try:
            self.setup_measurements(channel)
            
            for param in voltage_params:
                measurements[param] = self.get_measurement(param, channel)
                
        except Exception as e:
            raise RuntimeError(_ERROR_STYLE + f"Voltage measurement error: {e}")
            
        return measurements

    def get_timing_measurements(self, channel: str = "CHAN1") -> Dict[str, float]:
        """
        Retrieve timing-related measurements.
        
        Args:
            channel: Oscilloscope channel (CHAN1, CHAN2, etc.)
            
        Returns:
            Dictionary containing timing measurements
        """
        self._chk()
        
        timing_params = ["FREQuency", "PERiod", "RISetime", "FALLtime", "PWIDth", "NWIDth", "DCYCle"]
        measurements = {}
        
        try:
            self.setup_measurements(channel)
            
            for param in timing_params:
                measurements[param] = self.get_measurement(param, channel)
                
        except Exception as e:
            raise RuntimeError(_ERROR_STYLE + f"Timing measurement error: {e}")
            
        return measurements

    def get_statistics(self, channel: str = "CHAN1") -> Dict[str, Any]:
        """
        Get comprehensive measurement statistics compatible with data_logger framework.
        
        This method provides a standardized interface similar to other instruments
        in the lab framework (DMM6500, Keysight34460A, etc.).
        
        Args:
            channel: Oscilloscope channel to measure
            
        Returns:
            Dictionary containing [avg, std_dev, min, max] for key measurements
            plus individual measurement values
        """
        self._chk()
        
        try:
            # Get waveform data for statistical analysis
            t, y, meta = self.get_waveform(source=channel, debug=False)
            
            if not y:
                return {"error": "No waveform data available"}
                
            # Compute basic statistics from waveform
            import statistics as stats
            avg_voltage = stats.mean(y)
            std_dev = stats.stdev(y) if len(y) > 1 else 0
            min_voltage = min(y)
            max_voltage = max(y)
            
            # Get oscilloscope's built-in measurements
            voltage_meas = self.get_voltage_measurements(channel)
            timing_meas = self.get_timing_measurements(channel)
            
            # Return data in format compatible with data_logger framework
            result = {
                # Primary statistics array [avg, std_dev, min, max] - compatible with other devices
                "statistics": [avg_voltage, std_dev, min_voltage, max_voltage],
                
                # Individual measurements
                "voltage": avg_voltage,
                "voltage_rms": voltage_meas.get("VRMS", float('nan')),
                "voltage_pp": voltage_meas.get("VPP", float('nan')),
                "voltage_max": voltage_meas.get("VMAX", float('nan')),
                "voltage_min": voltage_meas.get("VMIN", float('nan')),
                "frequency": timing_meas.get("FREQuency", float('nan')),
                "period": timing_meas.get("PERiod", float('nan')),
                
                # Waveform metadata
                "sample_count": len(y),
                "sample_rate_hz": meta.get("sample_rate_hz", float('nan')),
                "duration_s": t[-1] - t[0] if len(t) > 1 else 0,
                
                # Additional measurements
                "all_voltage_measurements": voltage_meas,
                "all_timing_measurements": timing_meas
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e)}

    def get(self, item: str, channel: int = 1) -> Any:
        """
        Generic measurement interface compatible with data_logger framework.
        
        This method provides the standardized get() interface used by the data_logger
        class for consistent measurement across different instrument types.
        
        Args:
            item: Measurement type ("statistics", "voltage", "frequency", etc.)
            channel: Channel number (1-4, converted to CHAN1-CHAN4)
            
        Returns:
            Measurement value or statistics array depending on item requested
        """
        self._chk()
        
        # Convert channel number to channel string
        channel_str = f"CHAN{channel}"
        
        try:
            if item.lower() == "statistics":
                stats = self.get_statistics(channel_str)
                return stats.get("statistics", [float('nan')] * 4)
                
            elif item.lower() == "voltage":
                stats = self.get_statistics(channel_str)
                return stats.get("voltage", float('nan'))
                
            elif item.lower() == "voltage_rms":
                return self.get_measurement("VRMS", channel_str)
                
            elif item.lower() == "voltage_pp":
                return self.get_measurement("VPP", channel_str)
                
            elif item.lower() == "frequency":
                return self.get_measurement("FREQuency", channel_str)
                
            elif item.lower() == "period":
                return self.get_measurement("PERiod", channel_str)
                
            elif item.lower() == "xat_max" or item.lower() == "x_at_max":
                return self.get_xat_max(channel_str)
                
            elif item.lower() == "full_screen_average" or item.lower() == "vaverage":
                return self.get_full_screen_average(channel_str)
                
            elif item.lower() == "all_measurements":
                return self.get_statistics(channel_str)
                
            else:
                # Try to get the measurement directly
                return self.get_measurement(item.upper(), channel_str)
                
        except Exception as e:
            print(_ERROR_STYLE + f"Measurement '{item}' failed: {e}")
            return float('nan')

    def get_oscilloscope_config(self) -> Dict[str, str]:
        """
        Get current oscilloscope configuration for reporting.
        
        Returns:
            Dictionary with oscilloscope settings
        """
        if self.status != "Connected" or not self.instrument:
            return {}
            
        try:
            config = {}
            inst = self.instrument
            
            # Acquisition settings
            try:
                config['acquisition_mode'] = inst.query(":ACQuire:TYPE?").strip()
            except:
                config['acquisition_mode'] = "Unknown"
                
            try:
                config['time_scale'] = inst.query(":TIMebase:SCALe?").strip()
            except:
                config['time_scale'] = "Unknown"
            
            # CH1 settings
            try:
                config['ch1_scale'] = inst.query(":CHANnel1:SCALe?").strip()
            except:
                config['ch1_scale'] = "Unknown"
                
            try:
                config['ch1_bandwidth_limit'] = inst.query(":CHANnel1:BWLimit?").strip()
            except:
                config['ch1_bandwidth_limit'] = "Unknown"
                
            try:
                config['ch1_coupling'] = inst.query(":CHANnel1:COUPling?").strip()
            except:
                config['ch1_coupling'] = "Unknown"
                
            try:
                config['ch1_offset'] = inst.query(":CHANnel1:OFFSet?").strip()
            except:
                config['ch1_offset'] = "Unknown"
            
            return config
            
        except Exception as e:
            print(_ERROR_STYLE + f"Failed to get oscilloscope config: {e}")
            return {}