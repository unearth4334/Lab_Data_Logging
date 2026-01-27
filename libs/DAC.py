#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   @file DAC.py
#   @brief Driver for DAC and INA226 through Arduino interface
#   @date 27-Jan-2026
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
DAC and INA226 Arduino Interface Driver
========================================

This module provides a driver for controlling a Digital-to-Analog Converter (DAC)
and reading measurements from an INA226 current/voltage/power sensor through an 
Arduino microcontroller serial interface.

Features
--------
- **DAC Control**: Set analog output voltage via Arduino-connected DAC
- **INA226 Monitoring**: Read voltage, current, and power from INA226 sensor
- **Serial Interface**: RS-232/USB communication with Arduino
- **Precision Measurement**: High-resolution current and voltage sensing
- **Custom Hardware**: Arduino-based measurement system

Basic Usage
-----------
```python
from libs.DAC import DAC

# Connect to Arduino interface
dac = DAC(com_port="COM5")

# Set DAC output voltage
dac.set_voltage(2.5)  # 2.5V output

# Read INA226 measurements
voltage = dac.measure_voltage()
current = dac.measure_current()
power = dac.measure_power()

print(f"V: {voltage:.6f}V")
print(f"I: {current*1e6:.3f}μA")
print(f"P: {power*1e3:.3f}mW")

dac.disconnect()
```

Integration with data_logger
-----------------------------
```python
from data_logger import data_logger

logger = data_logger()
logger.new_file("dac_ina226_data.txt")

dac = logger.connect("dac")

# Set DAC voltage
dac.set_voltage(3.3)

# Log INA226 measurements
logger.add(dac, "voltage", label="INA226_Voltage")
logger.add(dac, "current", label="INA226_Current")
logger.add(dac, "power", label="INA226_Power")

for i in range(100):
    logger.get_data()
    
logger.close_file()
```

DAC Voltage Sweep
-----------------
```python
import time

# Sweep DAC voltage and measure
for v in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
    dac.set_voltage(v)
    time.sleep(0.1)  # Settling time
    
    current = dac.measure_current()
    print(f"V_dac={v:.1f}V, I={current*1e3:.3f}mA")
```

Available Methods
-----------------
DAC Control:
- `set_voltage(voltage)` - Set DAC output voltage

INA226 Measurement:
- `measure_voltage()` - Read bus voltage
- `measure_current()` - Read current
- `measure_power()` - Read power dissipation
- `get(item)` - Generic getter

Connection:
- `connect(com_port)` - Establish serial connection
- `disconnect()` - Close connection

Hardware Requirements
---------------------
- Arduino microcontroller (Uno, Nano, etc.)
- DAC module (e.g., MCP4725)
- INA226 current/voltage sensor
- Custom Arduino firmware for serial protocol

Arduino Communication Protocol
------------------------------
The Arduino firmware should implement serial commands for:
- Setting DAC voltage: `"V<value>"`
- Reading voltage: `"?V"`
- Reading current: `"?I"`
- Reading power: `"?P"`

See Also
--------
- RigolDP832: Standard programmable power supply
- data_logger: Main orchestrator class
"""

from __future__ import annotations

import os
import time
from typing import Optional, Tuple

import serial
import serial.tools.list_ports
from colorama import init, Fore, Style


# Console output styles
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "

_DELAY = 1  # in seconds

class DAC:
    """
    Driver for DAC and INA226 through Arduino interface.
    
    This class provides methods for controlling a DAC and reading measurements
    from an INA226 current/voltage sensor through an Arduino serial interface.
    
    Attributes:
        ser: Serial connection object
        address: COM port address
        status: Connection status ("Connected" or "Not Connected")
        
    Example:
        >>> dac = DAC()  # Auto-selects COM port
        >>> dac.set_value("DACA", 1024)
        >>> voltage, error = dac.get("VOLT")
        >>> dac.disconnect()
    """
    
    def __init__(self, auto_connect: bool = True, com_port: Optional[str] = None):
        """
        Initialize DAC driver.
        
        Args:
            auto_connect: Automatically connect to device on initialization
            com_port: Optional explicit COM port (e.g., 'COM10', '/dev/ttyUSB0')
        """
        init(autoreset=True)
        
        self.ser: Optional[serial.Serial] = None
        self.address: Optional[str] = None
        self.status: str = "Not Connected"
        self._com_port_hint: Optional[str] = com_port

        if auto_connect:
            self.connect(com_port=com_port)

    
    def connect(self, com_port: Optional[str] = None, baud_rate: int = 115200) -> None:
        """
        Establish connection to DAC/INA226 Arduino interface.
        
        Args:
            com_port: Optional COM port (e.g., 'COM10', '/dev/ttyUSB0'). If None, prompt user.
            baud_rate: Serial baud rate (default: 115200)
            
        Raises:
            ConnectionError: If device not found or connection fails.
        """
        # 1) Try explicit COM port first
        explicit_port = com_port or self._com_port_hint
        
        # 2) Try environment variable
        if explicit_port is None:
            try:
                explicit_port = os.environ.get('DAC_COM_PORT')
            except Exception:
                pass
        
        # 3) Prompt user to select COM port
        if explicit_port is None:
            ports = serial.tools.list_ports.comports()
            if not ports:
                raise ConnectionError(_ERROR_STYLE + "No COM ports found")
            
            print("\nAvailable COM ports:")
            for i, port in enumerate(ports, start=1):
                print(f"  {i}. {port.device} - {port.description}")
            
            while True:
                try:
                    selection = int(input("Select COM port for DAC/INA226 (1, 2, ...): "))
                    if 1 <= selection <= len(ports):
                        explicit_port = ports[selection - 1].device
                        os.environ['DAC_COM_PORT'] = explicit_port
                        break
                    print(_ERROR_STYLE + "Invalid selection")
                except ValueError:
                    print(_ERROR_STYLE + "Invalid input. Enter a number.")
        
        # 4) Open serial connection
        try:
            self.ser = serial.Serial(explicit_port, baud_rate, timeout=5)
            time.sleep(3)  # Wait for Arduino to initialize
            self.address = explicit_port
            self.status = "Connected"
            
            print(_SUCCESS_STYLE + f"Connected to DAC and INA226 through Arduino on {explicit_port}")
            
        except serial.SerialException as e:
            raise ConnectionError(_ERROR_STYLE + f"Failed to connect to {explicit_port}: {e}")
        except Exception as e:
            raise ConnectionError(_ERROR_STYLE + f"Unexpected error connecting to {explicit_port}: {e}")
    
    def disconnect(self) -> None:
        """Close the serial connection to the device."""
        if self.ser is not None and self.ser.is_open:
            try:
                self.ser.close()
            finally:
                print(f"\rDisconnected from DAC on {self.address}")
                self.ser = None
        
        self.status = "Not Connected"
        self.address = None
    
    def _chk(self) -> None:
        """Verify device is connected before operations."""
        if self.status != "Connected" or self.ser is None or not self.ser.is_open:
            raise ConnectionError(_ERROR_STYLE + "Not connected to DAC")
    
    def set_value(self, item: str, val: int) -> None:
        """
        Set a DAC channel value.
        
        Args:
            item: DAC channel name (e.g., "DACA", "DACB", "DACC", "DACD")
            val: Value to set
            
        Raises:
            ConnectionError: If not connected to device
        """
        self._chk()
        command = f'SET:{item}={val}\n'
        self.ser.write(bytes(command, 'utf-8'))
        time.sleep(_DELAY)
        

    def get(self, item: str, channel: int = 1) -> Tuple[float, float]:
        """
        Retrieve measurement value by name.
        
        Args:
            item: Measurement item name (case-insensitive)
                  Valid values: 'DACA', 'DACB', 'DACC', 'DACD', 'VOLT', 'CURR'
            channel: Optional channel number (for compatibility, not used)
            
        Returns:
            Tuple of (measurement_value, error_estimate)
            
        Raises:
            ValueError: If invalid item requested
            ConnectionError: If not connected to device
            
        Example:
            >>> voltage, error = dac.get('VOLT')
            >>> current, error = dac.get('CURR')
        """
        self._chk()
        
        item_upper = item.strip().upper()
        
        # Valid measurement items
        valid_items = ["DACA", "DACB", "DACC", "DACD", "VOLT", "CURR"]
        
        if item_upper not in valid_items:
            raise ValueError(
                _ERROR_STYLE + f"Invalid item '{item}'. "
                f"Valid items: {', '.join(valid_items)}"
            )
        
        return self.measure_value(item_upper)

    def measure_value(self, item: str) -> Tuple[float, float]:
        """
        Measure a value from the DAC/INA226 interface.
        
        Args:
            item: Measurement item (DACA, DACB, DACC, DACD, VOLT, CURR)
            
        Returns:
            Tuple of (measurement_value, error_estimate=0)
            
        Raises:
            ConnectionError: If not connected to device
            ValueError: If measurement fails or returns invalid data
        """
        self._chk()
        
        command = f'MEAS:{item}?\n'
        
        try:
            self.ser.write(bytes(command, 'utf-8'))
            time.sleep(_DELAY)
            val = self.ser.readline()
            
            if len(val) < 2:
                raise ValueError(_ERROR_STYLE + f"No response from device for '{item}'")
            
            val = val[0:(len(val) - 2)]
            val = float(val)
            return (val, 0)
        except ValueError as e:
            raise ValueError(_ERROR_STYLE + f"Failed to parse measurement for '{item}': {e}")
        except Exception as e:
            raise ConnectionError(_ERROR_STYLE + f"Communication error during measurement: {e}")