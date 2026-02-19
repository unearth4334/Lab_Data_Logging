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
- **Ethernet Connectivity**: Connect via IP address or VISA address
- **Current Setting**: Set constant current load mode
- **Auto-Detection**: Automatically finds EL34143A on the network
- **Link-Local Support**: Probes link-local IP addresses (169.254.x.x)
- **Connection Caching**: Remembers last successful address
- **VISA Interface**: Uses PyVISA for LAN (TCPIP/HiSLiP) connectivity

Basic Usage
-----------
```python
from libs.KeysightEL34143A import KeysightEL34143A

# Auto-connect to EL34143A
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

Connection via IP Address
--------------------------
```python
# Connect directly via IP address
load = KeysightEL34143A(ip_address="192.168.1.100")

# Or use explicit VISA address
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

Connection Details
------------------
The driver searches for VISA resources containing 'EL34143A' or probes common addresses:
- LAN: `TCPIP0::192.168.1.100::inst0::INSTR`
- HiSLiP: `TCPIP0::a-el34143a-xxxxx.local::hislip0::INSTR`
- Link-Local: `TCPIP0::169.254.x.x::inst0::INSTR`

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
from colorama import Fore, Style
from typing import Optional, List, Dict, Any

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
            self.instrument.timeout = 5000
            
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
        
        # Search TCPIP resources
        tcpip_resources = [r for r in resources if r.startswith("TCPIP")]
        
        for resource in tcpip_resources:
            if self.debug:
                print(f"{_INFO_STYLE}Checking: {resource}{_RESET_STYLE}")
            
            try:
                inst = rm.open_resource(resource)
                inst.timeout = 2000
                idn = inst.query("*IDN?").strip()
                
                if "EL34143A" in idn.upper():
                    self.instrument = inst
                    self.address = resource
                    self.status = "Connected"
                    self._save_last_address(resource)
                    
                    print(f"{_SUCCESS_STYLE}Auto-connected to Keysight EL34143A at {resource}{_RESET_STYLE}")
                    return
                else:
                    inst.close()
            except:
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
        
        raise ConnectionError("Failed to find EL34143A. Please specify IP address or VISA address.")
    
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
        
        Args:
            current: Current in amperes
            
        Example:
            >>> load.set_current(2.5)  # Set to 2.5 A
        """
        if not self.instrument:
            raise ConnectionError("Not connected to instrument")
        
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
