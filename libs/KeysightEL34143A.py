#   @file KeysightEL34143A.py 
#   @brief Establishes a connection to the Keysight EL34143A DC Electronic Load
#       and provides methods for interfacing with the device.
#   @date 18-Feb-2026
#   @author Stefan Damkjar
#
#   Licensed to the Apache Software Foundation (ASF) under one
#   or more contributor license agreements.  See the NOTICE file
#   distributed with this work for additional information
#   regarding copyright ownership.  The ASF licenses this file
#   to you under the Apache License, Version 2.0 (the
#   "License"); you may not use this file except in compliance
#   with the License.  You may obtain a copy of the License at
#   
#     http://www.apache.org/licenses/LICENSE-2.0
#   
#   Unless required by applicable law or agreed to in writing,
#   software distributed under the License is distributed on an
#   "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#   KIND, either express or implied.  See the License for the
#   specific language governing permissions and limitations
#   under the License. 

"""
Keysight EL34143A DC Electronic Load Driver
============================================

This module provides a driver for the Keysight EL34143A DC electronic load,
a programmable DC electronic load with VISA connectivity over Ethernet/LAN.

Features
--------
- **USB Connectivity**: Connect via PyVISA over USB (primary)
- **Ethernet Connectivity**: Also supports TCPIP/HiSLiP connections
- **Current Setting**: Set constant current load mode
- **Waveform Capture**: Download voltage and current waveforms
- **Digitizer Support**: Configure sample rate and capture points
- **Auto-Detection**: Automatically finds EL34143A via USB or network
- **Link-Local Support**: Probes link-local IP addresses (169.254.x.x)
- **Connection Caching**: Remembers last successful address
- **VISA Interface**: Uses PyVISA for USB, LAN (TCPIP/HiSLiP) connectivity

Basic Usage
-----------
```python
from libs.KeysightEL34143A import KeysightEL34143A

# Auto-connect to EL34143A (finds USB or Ethernet automatically)
load = KeysightEL34143A()

# Set current level to 1.5 A
load.set_current(1.5)

# Enable the load
load.enable_output()

# Read back current and voltage
current = load.measure_current()
voltage = load.measure_voltage()
print(f"Load: {current:.3f} A at {voltage:.3f} V")

# Disable when done
load.disable_output()
load.disconnect()
```

Connection Methods
------------------
```python
# Auto-connect (recommended for USB - finds USB or Ethernet automatically)
load = KeysightEL34143A()

# Connect via explicit USB VISA address
load = KeysightEL34143A(address="USB0::0x0957::0x8C18::MY12345678::INSTR")

# Connect via IP address (for Ethernet)
load = KeysightEL34143A(ip_address="192.168.1.100")

# Or use explicit TCPIP VISA address
load = KeysightEL34143A(address="TCPIP0::192.168.1.100::inst0::INSTR")
```

Current Setting Examples
-------------------------
```python
# Set to constant current mode at 2.5 A
load.set_current(2.5)
load.enable_output()

# Check if output is enabled
if load.is_output_enabled():
    print("Load is active")

# Disable output
load.disable_output()
```

Measurement Examples
--------------------
```python
# Measure current being drawn
current = load.measure_current()

# Measure voltage across load
voltage = load.measure_voltage()

# Measure power dissipation
power = load.measure_power()
```

Waveform Capture Examples (USB or Ethernet)
--------------------------------------------
```python
# Auto-connect via USB and capture voltage waveform
load = KeysightEL34143A()  # Finds USB device automatically
t, v, meta = load.get_waveform("VOLTAGE", sample_rate=10000, points=1000)
print(f"Captured {len(v)} voltage points at {meta['sample_rate_hz']} Hz")

# Capture current waveform
t, i, meta = load.get_waveform("CURRENT", sample_rate=5000, points=500)
print(f"Mean current: {meta['mean']:.6f} A")

# Save waveform to CSV
load.save_waveform("voltage_capture.csv", "VOLTAGE", 10000, 1000)

# Manual digitizer configuration
load.configure_digitizer("VOLTAGE", sample_rate=20000, points=2000)
t, v, meta = load.get_waveform("VOLTAGE", configure=False)
```

Integration with data_logger
-----------------------------
```python
from data_logger import data_logger

logger = data_logger()
logger.new_file("load_test.txt")

# Connect via data_logger
load = logger.connect("keysightel34143a")

# Set load current
load.set_current(1.0)
load.enable_output()

# Add measurements to log
logger.add(load, "current", label="Load_Current")
logger.add(load, "voltage", label="Load_Voltage")
logger.add(load, "power", label="Load_Power")

# Collect data
for i in range(100):
    logger.get_data()
    
load.disable_output()
logger.close_file()
```

Direct SCPI Commands
--------------------
```python
# Query instrument identification
idn = load.instrument.query("*IDN?")
print(f"Connected to: {idn}")

# Set current manually via SCPI
load.instrument.write("CURR 2.5")

# Read measured values
current = float(load.instrument.query("MEAS:CURR?"))
voltage = float(load.instrument.query("MEAS:VOLT?"))
```

Supported Measurement Commands (for use with data_logger)
----------------------------------------------------------
The following commands are supported by the `get(item)` method:

- **"current"** - Measured current in amperes
- **"voltage"** - Measured voltage in volts
- **"power"** - Measured power in watts

Example:
```python
load = logger.connect("keysightel34143a")
current = load.get("current")
voltage = load.get("voltage")
power = load.get("power")
```

Waveform Capture Methods
-------------------------
The following methods are available for waveform capture:

- **`get_waveform(measure_type, sample_rate, points)`** - Capture waveform data
- **`configure_digitizer(measure_type, sample_rate, points)`** - Configure digitizer settings
- **`save_waveform(filename, measure_type, sample_rate, points)`** - Capture and save to CSV

Example:
```python
# Capture voltage transient
t, v, meta = load.get_waveform("VOLTAGE", sample_rate=10000, points=1000)

# Capture current transient
t, i, meta = load.get_waveform("CURRENT", sample_rate=5000, points=500)

# Save directly to file
load.save_waveform("load_startup.csv", "VOLTAGE", 10000, 2000)
```

Connection Details
------------------
The driver searches for VISA resources and automatically finds EL34143A via:
- **USB**: `USB0::0x0957::0x8C18::<serial>::INSTR` (Keysight vendor ID 0x0957)
- **LAN**: `TCPIP0::192.168.1.100::inst0::INSTR`
- **HiSLiP**: `TCPIP0::a-el34143a-xxxxx.local::hislip0::INSTR`
- **Link-Local**: `TCPIP0::169.254.x.x::inst0::INSTR`

For USB connection, ensure Keysight IO Libraries are installed with USB drivers.

Error Handling
--------------
```python
try:
    load = KeysightEL34143A(ip_address="192.168.1.100")
    load.set_current(1.5)
    load.enable_output()
except ConnectionError as e:
    print(f"Failed to connect: {e}")
except Exception as e:
    print(f"Error: {e}")
finally:
    if load:
        load.disable_output()
        load.disconnect()
```

Safety Notes
------------
- Always disable output before disconnecting
- Be aware of maximum current and power ratings
- Ensure proper cooling and ventilation
- Monitor temperature during high-power operation

Requirements
------------
- Python 3.7+
- pyvisa >= 1.11.0
- colorama >= 0.4.6
- Keysight IO Libraries Suite (includes VISA drivers)

"""

import pyvisa
import time
import os
import json
import struct
from colorama import Fore, Style
from typing import Optional, List, Dict, Any, Tuple

# Console output styles
_ERROR_STYLE = Fore.RED + Style.BRIGHT
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT
_INFO_STYLE = Fore.CYAN
_RESET_STYLE = Style.RESET_ALL


class KeysightEL34143A:
    """
    Keysight EL34143A DC Electronic Load driver.
    
    Provides methods for connecting to and controlling the Keysight EL34143A
    DC electronic load via VISA (Ethernet/LAN).
    
    Attributes:
        status (str): Connection status ("Connected", "Disconnected", or error message)
        address (str): VISA resource address of the connected instrument
        instrument: PyVISA instrument resource object
    """
    
    # Minimum current the load can be set to (12mA)
    MIN_CURRENT = 0.012  # Amperes
    
    # Chunk size for binary data transfer
    _chunk_size = 102400
    
    def __init__(self, 
                 ip_address: Optional[str] = None,
                 address: Optional[str] = None,
                 debug: bool = False):
        """
        Initialize Keysight EL34143A Electronic Load.
        
        Args:
            ip_address: IP address for Ethernet connection (e.g., "192.168.1.100")
            address: Explicit VISA resource address (overrides ip_address if both provided)
            debug: Enable debug output showing resource scanning
            
        Examples:
            >>> load = KeysightEL34143A()  # Auto-connect
            >>> load = KeysightEL34143A(ip_address="192.168.1.100")  # Via IP
            >>> load = KeysightEL34143A(address="TCPIP0::192.168.1.100::inst0::INSTR")  # Via VISA address
        """
        self.status = "Disconnected"
        self.address = None
        self.instrument = None
        self.debug = debug
        
        # Auto-connect if not explicitly disabled
        try:
            if address:
                self._connect_explicit(address)
            elif ip_address:
                self._connect_ip(ip_address)
            else:
                self._auto_connect()
        except Exception as e:
            self.status = f"Connection failed: {e}"
            if self.debug:
                import traceback
                traceback.print_exc()
            # Re-raise the exception so caller knows connection failed
            raise ConnectionError(f"Failed to connect to EL34143A: {e}") from e
    
    def _connect_explicit(self, address: str):
        """Connect using explicit VISA address."""
        if self.debug:
            print(f"{_INFO_STYLE}Connecting to explicit address: {address}{_RESET_STYLE}")
        
        rm = pyvisa.ResourceManager()
        try:
            self.instrument = rm.open_resource(address)
            # Use longer timeout for USB devices
            if address.startswith("USB"):
                self.instrument.timeout = 10000  # 10 seconds for USB
            else:
                self.instrument.timeout = 5000  # 5 seconds for network
            
            # Set termination characters (important for proper communication)
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            
            # Verify it's an EL34143A
            try:
                idn = self.instrument.query("*IDN?").strip()
                if self.debug:
                    print(f"{_INFO_STYLE}Device IDN: {idn}{_RESET_STYLE}")
                if "EL34143A" not in idn.upper():
                    self.instrument.close()
                    raise ConnectionError(f"Device is not an EL34143A: {idn}")
            except pyvisa.errors.VisaIOError as e:
                self.instrument.close()
                raise ConnectionError(f"Could not communicate with device at {address}: {e}")
            
            self.address = address
            self.status = "Connected"
            self._save_last_address(address)
            
            if self.debug:
                print(f"{_SUCCESS_STYLE}Connected to EL34143A at {address}{_RESET_STYLE}")
                
        except pyvisa.errors.VisaIOError as e:
            raise ConnectionError(f"VISA error connecting to {address}: {e}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {address}: {e}")
    
    def _connect_ip(self, ip_address: str):
        """Connect using IP address."""
        # Try standard TCPIP address
        address = f"TCPIP0::{ip_address}::inst0::INSTR"
        
        if self.debug:
            print(f"{_INFO_STYLE}Connecting via IP: {ip_address}{_RESET_STYLE}")
            print(f"{_INFO_STYLE}Trying address: {address}{_RESET_STYLE}")
        
        try:
            self._connect_explicit(address)
            return
        except:
            pass
        
        # Try HiSLiP
        address = f"TCPIP0::{ip_address}::hislip0::INSTR"
        if self.debug:
            print(f"{_INFO_STYLE}Trying HiSLiP: {address}{_RESET_STYLE}")
        
        try:
            self._connect_explicit(address)
            return
        except:
            pass
        
        raise ConnectionError(f"Failed to connect to EL34143A at IP {ip_address}")
    
    def _auto_connect(self):
        """Automatically search for and connect to EL34143A."""
        if self.debug:
            print(f"{_INFO_STYLE}Auto-connecting to EL34143A...{_RESET_STYLE}")
        
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        
        if self.debug:
            print(f"{_INFO_STYLE}Found {len(resources)} VISA resources{_RESET_STYLE}")
            for r in resources:
                print(f"{_INFO_STYLE}  - {r}{_RESET_STYLE}")
        
        # First, try cached address
        cached_address = self._load_last_address()
        if cached_address:
            if self.debug:
                print(f"{_INFO_STYLE}Trying cached address: {cached_address}{_RESET_STYLE}")
            try:
                self._connect_explicit(cached_address)
                return
            except:
                if self.debug:
                    print(f"{_WARNING_STYLE}Cached address failed{_RESET_STYLE}")
        
        # Search USB resources first (primary connection method)
        usb_resources = [r for r in resources if r.startswith("USB")]
        
        for resource in usb_resources:
            if self.debug:
                print(f"{_INFO_STYLE}Checking USB: {resource}{_RESET_STYLE}")
            
            try:
                inst = rm.open_resource(resource)
                inst.timeout = 10000  # 10 second timeout for USB (some devices are slow)
                inst.read_termination = '\n'
                inst.write_termination = '\n'
                idn = inst.query("*IDN?").strip()
                
                if self.debug:
                    print(f"{_INFO_STYLE}  IDN: {idn}{_RESET_STYLE}")
                
                if "EL34143A" in idn.upper():
                    self.instrument = inst
                    self.address = resource
                    self.status = "Connected"
                    self._save_last_address(resource)
                    
                    print(f"{_SUCCESS_STYLE}Auto-connected to Keysight EL34143A at {resource}{_RESET_STYLE}")
                    return
                else:
                    inst.close()
            except Exception as e:
                if self.debug:
                    print(f"{_WARNING_STYLE}  Failed: {e}{_RESET_STYLE}")
                continue
        
        # Search TCPIP resources
        tcpip_resources = [r for r in resources if r.startswith("TCPIP")]
        
        for resource in tcpip_resources:
            if self.debug:
                print(f"{_INFO_STYLE}Checking TCPIP: {resource}{_RESET_STYLE}")
            
            try:
                inst.read_termination = '\n'
                inst.write_termination = '\n'
                inst = rm.open_resource(resource)
                inst.timeout = 2000
                idn = inst.query("*IDN?").strip()
                
                if self.debug:
                    print(f"{_INFO_STYLE}  IDN: {idn}{_RESET_STYLE}")
                
                if "EL34143A" in idn.upper():
                    self.instrument = inst
                    self.address = resource
                    self.status = "Connected"
                    self._save_last_address(resource)
                    
                    print(f"{_SUCCESS_STYLE}Auto-connected to Keysight EL34143A at {resource}{_RESET_STYLE}")
                    return
                else:
                    inst.close()
            except Exception as e:
                if self.debug:
                    print(f"{_WARNING_STYLE}  Failed: {e}{_RESET_STYLE}")
                continue
        
        # If not found, try probing link-local IPs
        if self.debug:
            print(f"{_INFO_STYLE}Probing link-local IP addresses...{_RESET_STYLE}")
        
        link_local_ips = self._probe_link_local_ips()
        for ip in link_local_ips:
            try:
                self._connect_ip(ip)
                return
            except:
                continue
        
        raise ConnectionError("Failed to find EL34143A. Please specify USB or TCPIP address via address= or ip_address= parameter.")
    
    def _probe_link_local_ips(self) -> List[str]:
        """Probe common link-local IP addresses for EL34143A."""
        # Common link-local IP range
        candidate_ips = []
        
        # Generate some common link-local addresses to try
        for i in [1, 2, 3, 4, 5, 10, 20, 50, 100]:
            candidate_ips.append(f"169.254.{i}.{i}")
        
        return candidate_ips
    
    def _save_last_address(self, address: str):
        """Save last successful address to cache file."""
        try:
            cache_dir = os.path.expanduser("~/.lab_data_logging")
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, "el34143a_last_address.json")
            
            with open(cache_file, 'w') as f:
                json.dump({"address": address}, f)
        except:
            pass  # Silently fail if can't save cache
    
    def _load_last_address(self) -> Optional[str]:
        """Load last successful address from cache file."""
        try:
            cache_file = os.path.expanduser("~/.lab_data_logging/el34143a_last_address.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return data.get("address")
        except:
            pass
        return None
    
    def connect(self):
        """
        Manual connection method (for compatibility with data_logger).
        
        Note: Connection is typically established automatically during __init__().
        This method is provided for manual reconnection if needed.
        """
        if self.status == "Connected" and self.instrument:
            return
        
        self._auto_connect()
    
    def disconnect(self):
        """
        Disconnect from the electronic load.
        
        Always call this before exiting to properly close the VISA connection.
        """
        if self.instrument:
            try:
                # Make sure output is off before disconnecting
                self.disable_output()
                self.instrument.close()
                print(f"Disconnected from Keysight EL34143A Electronic Load at {self.address}")
            except:
                pass
            finally:
                self.instrument = None
                self.status = "Disconnected"
                self.address = None
    
    def get_idn(self) -> str:
        """
        Query instrument identification string.
        
        Returns:
            Identification string from *IDN? query
            
        Example:
            >>> load = KeysightEL34143A()
            >>> print(load.get_idn())
            KEYSIGHT TECHNOLOGIES,EL34143A,MY12345678,A.01.02
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        return self.instrument.query("*IDN?").strip()
    
    def reset(self):
        """
        Reset the instrument to default settings.
        
        Warning: This will disable output and reset all settings.
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        self.instrument.write("*RST")
        time.sleep(1)  # Allow time for reset
    
    def set_current(self, current: float):
        """
        Set the constant current load value.
        
        The minimum current is 12mA (0.012A). Values below this will be
        silently corrected to the minimum.
        
        Args:
            current: Current in amperes (minimum 0.012A / 12mA)
            
        Example:
            >>> load.set_current(2.5)  # Set to 2.5 A
            >>> load.set_current(0.005)  # Will be silently corrected to 0.012 A (12mA)
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        # Enforce minimum current (silent correction for safety)
        if current < self.MIN_CURRENT:
            current = self.MIN_CURRENT
        
        self.instrument.write(f"CURR {current}")
    
    def get_current_setpoint(self) -> float:
        """
        Query the current setpoint.
        
        Returns:
            Current setpoint in amperes
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        return float(self.instrument.query("CURR?"))
    
    def measure_current(self) -> float:
        """
        Measure the actual current being drawn.
        
        Returns:
            Measured current in amperes
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        return float(self.instrument.query("MEAS:CURR?"))
    
    def measure_voltage(self) -> float:
        """
        Measure the voltage across the load.
        
        Returns:
            Measured voltage in volts
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        return float(self.instrument.query("MEAS:VOLT?"))
    
    def measure_power(self) -> float:
        """
        Measure the power being dissipated.
        
        Returns:
            Measured power in watts
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        return float(self.instrument.query("MEAS:POW?"))
    
    def enable_output(self):
        """
        Enable the electronic load output (start sinking current).
        
        Warning: Ensure proper connections before enabling output.
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        self.instrument.write("INP ON")
    
    def disable_output(self):
        """
        Disable the electronic load output (stop sinking current).
        
        Always call this before disconnecting or when done with measurements.
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        self.instrument.write("INP OFF")
    
    def is_output_enabled(self) -> bool:
        """
        Check if output is currently enabled.
        
        Returns:
            True if output is enabled, False otherwise
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        response = self.instrument.query("INP?").strip()
        return response in ["1", "ON"]

    def set_sense_mode(self, remote: bool = True) -> None:
        """
        Set the voltage sense mode.

        Args:
            remote: True for 4-wire remote sense (EXT), False for 2-wire local sense (INT).

        Example:
            >>> load.set_sense_mode(True)   # 4-wire remote sense
            >>> load.set_sense_mode(False)  # 2-wire local sense
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")

        mode = "EXT" if remote else "INT"
        self.instrument.write(f"VOLT:SENS {mode}")

    def get_sense_mode(self) -> str:
        """
        Query the current voltage sense mode.

        Returns:
            "EXT" for 4-wire remote sense, "INT" for 2-wire local sense.
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")

        return self.instrument.query("VOLT:SENS?").strip()

    def sequencer_stop(self) -> None:
        """
        Exit list mode and switch to fixed CC mode (CURR:MODE FIX).

        Must be called before changing the current setpoint while the
        sequencer is active.  Using CURR:MODE FIX is the correct method
        on firmware 1.2.9 — ABOR causes a VISA session abort that poisons
        subsequent queries.  After this call the instrument accepts plain
        CURR writes immediately.
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")

        self.instrument.write("CURR:MODE FIX")

    def sequencer_start(self) -> None:
        """
        Re-enter list mode and start execution (CURR:MODE LIST + INIT).

        Call after the current setpoint has been changed to resume the
        previously configured list sequence.
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")

        self.instrument.write("CURR:MODE LIST")
        self.instrument.write("INIT")

    def get(self, item: str) -> Any:
        """
        Generic measurement method (for data_logger compatibility).
        
        Args:
            item: Measurement type ("current", "voltage", "power")
            
        Returns:
            Measurement value
            
        Example:
            >>> load.get("current")
            1.523
            >>> load.get("voltage")
            12.045
        """
        item_lower = item.lower()
        
        if item_lower == "current":
            return self.measure_current()
        elif item_lower == "voltage":
            return self.measure_voltage()
        elif item_lower == "power":
            return self.measure_power()
        else:
            raise ValueError(f"Unknown measurement item: {item}. Supported: current, voltage, power")
    
    # ===== Waveform Capture Methods =====
    
    def configure_digitizer(self, 
                           measure_type: str = "VOLTAGE",
                           sample_rate: Optional[float] = None,
                           points: Optional[int] = None,
                           auto_range: bool = True):
        """
        Configure the electronic load's digitizer for waveform capture.
        
        Args:
            measure_type: "VOLTAGE" or "CURRENT" - what to digitize
            sample_rate: Sample rate in Hz (e.g., 10000 for 10 kS/s)
            points: Number of points to capture
            auto_range: Use auto-ranging if True
            
        Example:
            >>> load.configure_digitizer("VOLTAGE", sample_rate=10000, points=1000)
            >>> load.configure_digitizer("CURRENT", sample_rate=5000, points=500)
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        measure_type = measure_type.upper()
        if measure_type not in ["VOLTAGE", "CURRENT"]:
            raise ValueError("measure_type must be 'VOLTAGE' or 'CURRENT'")
        
        # Configure measurement mode
        self.instrument.write(f":SENSe:FUNCtion:ON \"{measure_type}\"")
        
        # Set auto-range
        if auto_range:
            self.instrument.write(f":SENSe:{measure_type}:RANGe:AUTO ON")
        
        # Configure sample rate if specified
        if sample_rate is not None:
            # Convert to sample period (seconds)
            sample_period = 1.0 / sample_rate
            self.instrument.write(f":SENSe:{measure_type}:APERture {sample_period}")
        
        # Configure number of points if specified
        if points is not None:
            self.instrument.write(f":SENSe:{measure_type}:POINts {int(points)}")
    
    def get_waveform(self, 
                    measure_type: str = "VOLTAGE",
                    configure: bool = True,
                    sample_rate: Optional[float] = 10000,
                    points: Optional[int] = 1000,
                    debug: bool = False
                    ) -> Tuple[List[float], List[float], Dict[str, Any]]:
        """
        Capture and download waveform data from the electronic load.
        
        Args:
            measure_type: "VOLTAGE" or "CURRENT" - what to capture
            configure: Automatically configure digitizer if True
            sample_rate: Sample rate in Hz (used if configure=True)
            points: Number of points (used if configure=True)
            debug: Print debug information
            
        Returns:
            Tuple of (time_array, data_array, metadata_dict)
            - time_array: List of time values in seconds
            - data_array: List of voltage (V) or current (A) values
            - metadata_dict: Dictionary with capture parameters
            
        Example:
            >>> # Capture voltage waveform
            >>> t, v, meta = load.get_waveform("VOLTAGE", sample_rate=10000, points=1000)
            >>> print(f"Captured {len(v)} voltage points")
            >>> print(f"Sample rate: {meta['sample_rate_hz']} Hz")
            
            >>> # Capture current waveform
            >>> t, i, meta = load.get_waveform("CURRENT", sample_rate=5000, points=500)
            >>> print(f"Captured {len(i)} current points")
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
        measure_type = measure_type.upper()
        if measure_type not in ["VOLTAGE", "CURRENT"]:
            raise ValueError("measure_type must be 'VOLTAGE' or 'CURRENT'")
        
        # Configure digitizer if requested
        if configure:
            self.configure_digitizer(measure_type, sample_rate, points, auto_range=True)
            time.sleep(0.1)  # Allow settings to apply
        
        # Query actual settings
        try:
            actual_points = int(float(self.instrument.query(f":SENSe:{measure_type}:POINts?")))
            aperture = float(self.instrument.query(f":SENSe:{measure_type}:APERture?"))
            actual_sample_rate = 1.0 / aperture if aperture > 0 else 0
        except Exception as e:
            if debug:
                print(f"{_WARNING_STYLE}Could not query digitizer settings: {e}{_RESET_STYLE}")
            actual_points = points if points else 1000
            actual_sample_rate = sample_rate if sample_rate else 10000
        
        # Initiate measurement and fetch data
        # The EL34143A requires initiating the measurement before fetching
        data = None
        
        try:
            # Initiate the measurement array capture
            if debug:
                print(f"{_INFO_STYLE}Initiating measurement...{_RESET_STYLE}")
            
            self.instrument.write("INIT")
            
            # Wait for completion with *OPC? (operation complete query)
            if debug:
                print(f"{_INFO_STYLE}Waiting for measurement to complete...{_RESET_STYLE}")
            
            self.instrument.query("*OPC?")  # Blocks until operation complete
            
            # Now fetch the array data
            if measure_type == "VOLTAGE":
                cmd = "FETC:ARR:VOLT?"
            else:  # CURRENT
                cmd = "FETC:ARR:CURR?"
            
            if debug:
                print(f"{_INFO_STYLE}Fetching data with: {cmd}{_RESET_STYLE}")
            
            # Try to fetch as ASCII (more reliable)
            response = self.instrument.query(cmd)
            data = [float(x) for x in response.strip().split(',')]
            
            if debug:
                print(f"{_SUCCESS_STYLE}Successfully fetched {len(data)} points{_RESET_STYLE}")
                
        except Exception as e:
            if debug:
                print(f"{_WARNING_STYLE}Failed to capture with INIT/FETC:ARR: {e}{_RESET_STYLE}")
                print(f"{_INFO_STYLE}Trying alternative methods...{_RESET_STYLE}")
            
            # Fall back to trying different command variations
            if measure_type == "VOLTAGE":
                fetch_commands = [
                    "FETC:ARR:VOLT?",
                    ":FETCh:ARRay:VOLTage?",
                    ":FETCH:ARR:VOLT?",
                ]
            else:  # CURRENT
                fetch_commands = [
                    "FETC:ARR:CURR?",
                    ":FETCh:ARRay:CURRent?",
                    ":FETCH:ARR:CURR?",
                ]
            
            for cmd in fetch_commands:
                try:
                    if debug:
                        print(f"{_INFO_STYLE}Trying command: {cmd}{_RESET_STYLE}")
                    
                    response = self.instrument.query(cmd)
                    data = [float(x) for x in response.strip().split(',')]
                    
                    if data and len(data) > 0:
                        if debug:
                            print(f"{_SUCCESS_STYLE}Successfully fetched {len(data)} points using {cmd}{_RESET_STYLE}")
                        break
                except Exception as e2:
                    if debug:
                        print(f"{_WARNING_STYLE}Failed with {cmd}: {e2}{_RESET_STYLE}")
                    continue
        
        # If standard commands fail, try simple READ?
        if not data or len(data) == 0:
            try:
                if debug:
                    print(f"{_INFO_STYLE}Trying simple READ? command{_RESET_STYLE}")
                # Take multiple readings
                data = []
                for i in range(actual_points):
                    val = float(self.instrument.query("READ?"))
                    data.append(val)
                    if debug and i % 100 == 0:
                        print(f"{_INFO_STYLE}Captured {i}/{actual_points} points{_RESET_STYLE}")
            except Exception as e:
                raise RuntimeError(f"Failed to capture waveform data: {e}")
        
        n = len(data)
        
        # Generate time array
        dt = 1.0 / actual_sample_rate
        time_array = [i * dt for i in range(n)]
        
        # Build metadata
        metadata = {
            "measure_type": measure_type,
            "npoints": n,
            "sample_rate_hz": actual_sample_rate,
            "dt_s": dt,
            "duration_s": (n - 1) * dt if n > 1 else 0,
            "t_start_s": 0.0,
            "t_stop_s": (n - 1) * dt if n > 1 else 0,
        }
        
        # Add statistics
        if len(data) > 0:
            metadata["mean"] = sum(data) / len(data)
            metadata["min"] = min(data)
            metadata["max"] = max(data)
            metadata["peak_to_peak"] = max(data) - min(data)
        
        if debug:
            print(f"{_SUCCESS_STYLE}Waveform capture complete:{_RESET_STYLE}")
            print(f"  Points: {n}")
            print(f"  Sample rate: {actual_sample_rate:.1f} Hz")
            print(f"  Duration: {metadata['duration_s']:.6f} s")
            if 'mean' in metadata:
                print(f"  Mean: {metadata['mean']:.6f} {measure_type[0]}")
                print(f"  Range: {metadata['min']:.6f} to {metadata['max']:.6f} {measure_type[0]}")
        
        return time_array, data, metadata
    
    def save_waveform(self, 
                     filename: str,
                     measure_type: str = "VOLTAGE",
                     sample_rate: Optional[float] = 10000,
                     points: Optional[int] = 1000,
                     debug: bool = False) -> bool:
        """
        Capture waveform and save to CSV file.
        
        Args:
            filename: Output CSV filename (relative or absolute path)
                     If no path specified, saves to output/el34143a_waveforms/
            measure_type: "VOLTAGE" or "CURRENT"
            sample_rate: Sample rate in Hz
            points: Number of points to capture
            debug: Print debug information
            
        Returns:
            True if successful, False otherwise
            
        Example:
            >>> load.save_waveform("voltage_capture.csv", "VOLTAGE", 10000, 1000)
            >>> load.save_waveform("current_capture.csv", "CURRENT", 5000, 500)
        """
        try:
            # If filename has no path, use default output directory
            if not os.path.dirname(filename):
                output_dir = os.path.join("output", "el34143a_waveforms")
                os.makedirs(output_dir, exist_ok=True)
                filename = os.path.join(output_dir, filename)
            else:
                # Ensure the specified directory exists
                os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Capture waveform
            time_array, data_array, metadata = self.get_waveform(
                measure_type, True, sample_rate, points, debug
            )
            
            # Write to CSV
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header with metadata
                writer.writerow([f"# Keysight EL34143A Waveform Capture"])
                writer.writerow([f"# Measure Type: {metadata['measure_type']}"])
                writer.writerow([f"# Sample Rate: {metadata['sample_rate_hz']} Hz"])
                writer.writerow([f"# Points: {metadata['npoints']}"])
                writer.writerow([f"# Duration: {metadata['duration_s']} s"])
                writer.writerow([])
                
                # Write column headers
                unit = "V" if measure_type == "VOLTAGE" else "A"
                writer.writerow(["Time (s)", f"{measure_type.capitalize()} ({unit})"])
                
                # Write data
                for t, val in zip(time_array, data_array):
                    writer.writerow([f"{t:.9f}", f"{val:.9f}"])
            
            print(f"{_SUCCESS_STYLE}Waveform saved to: {filename}{_RESET_STYLE}")
            return True
            
        except Exception as e:
            print(f"{_ERROR_STYLE}Failed to save waveform: {e}{_RESET_STYLE}")
            if debug:
                import traceback
                traceback.print_exc()
            return False


# Example usage
if __name__ == "__main__":
    print("Keysight EL34143A Electronic Load Test\n")
    
    try:
        # Auto-connect
        load = KeysightEL34143A(debug=True)
        
        print(f"\nConnected to: {load.get_idn()}")
        
        # Set current (but don't enable yet)
        load.set_current(1.0)
        print(f"Current setpoint: {load.get_current_setpoint():.3f} A")
        
        # Example: Enable output (uncomment if safe to do so)
        # load.enable_output()
        # time.sleep(1)
        # 
        # current = load.measure_current()
        # voltage = load.measure_voltage()
        # power = load.measure_power()
        # 
        # print(f"\nMeasurements:")
        # print(f"  Current: {current:.3f} A")
        # print(f"  Voltage: {voltage:.3f} V")
        # print(f"  Power:   {power:.3f} W")
        # 
        # load.disable_output()
        
        print("\nTest complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'load' in locals():
            load.disconnect()
