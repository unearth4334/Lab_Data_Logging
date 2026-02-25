#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   @file RigolDP711.py
#   @brief Driver for Rigol DP711 Power Supply
#   @date 19-Feb-2026
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
Rigol DP711 Programmable DC Power Supply Driver
================================================

This module provides a driver for the Rigol DP711 single-output programmable
DC power supply with RS-232 serial interface (USB-to-RS232 cable).

Features
--------
- **Single Channel**: 0-30V, 0-5A output
- **Serial Interface**: RS-232 communication via USB-to-RS232 adapter
- **Programmable**: Set voltage and current limits
- **Readback**: Measure actual output voltage and current
- **Compact**: Single-channel benchtop power supply

Basic Usage
-----------
```python
from libs.RigolDP711 import RigolDP711

# Connect to power supply
psu = RigolDP711(com_port="COM4")

# Set output voltage and current
psu.set_voltage(12.0)  # 12V
psu.set_current(2.0)   # 2A limit

# Enable output
psu.set_output_state(True)

# Read measurements
voltage = psu.measure_voltage()
current = psu.measure_current()
print(f"V: {voltage:.3f}V, I: {current:.3f}A")

# Disable output
psu.set_output_state(False)
psu.disconnect()
```

Integration with data_logger
-----------------------------
```python
from data_logger import data_logger

logger = data_logger()
logger.new_file("dp711_data.txt")

psu = logger.connect("dp711")

psu.set_voltage(15.0)
psu.set_output_state(True)

logger.add("DP711_Voltage", psu, "voltage")
logger.add("DP711_Current", psu, "current")

for i in range(100):
    logger.get_data()
    
psu.set_output_state(False)
logger.close_file()
```

Supported Measurement Commands (for use with data_logger)
----------------------------------------------------------
The following commands are supported by the `get(item)` method:

- **"voltage"** or **"VOLT"** - Measure actual output voltage in volts
- **"current"** or **"CURR"** - Measure actual output current in amperes

Example:
```python
psu = logger.connect("dp711")
voltage = psu.get("voltage")
current = psu.get("current")
```

Available Methods
-----------------
- `set_voltage(voltage)` - Set output voltage (0-30V)
- `set_current(current)` - Set current limit (0-5A)
- `set_output_state(state)` - Enable/disable output (True/False)
- `get_output_state()` - Query output state
- `measure_voltage()` - Read actual voltage
- `measure_current()` - Read actual current
- `get(item)` - Generic getter (voltage, current)
- `connect(com_port)` - Establish serial connection
- `disconnect()` - Close connection

Technical Specifications
------------------------
- **Voltage Range**: 0-30V
- **Current Range**: 0-5A
- **Power Rating**: 150W
- **Voltage Resolution**: 1mV
- **Current Resolution**: 1mA
- **Interface**: RS-232 serial (via USB-to-RS232 adapter)
- **Baud Rate**: 9600 (default)

See Also
--------
- RigolDP832: Triple-output power supply
- KA3010P: Similar single-output power supply with RS-232
- data_logger: Main orchestrator class
"""

from __future__ import annotations

import os
import time
from typing import Optional

import serial
import serial.tools.list_ports
from colorama import init, Fore, Style


# Console output styles
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "

_DELAY = 0.2   # inter-command delay (s)
_IDN_DELAY = 0.5  # longer wait after *IDN? on first connect

class RigolDP711:
    """
    Driver for Rigol DP711 Programmable DC Power Supply.
    
    This class provides methods for connecting to and controlling a
    DP711 power supply via RS-232 serial interface (USB-to-RS232 adapter).
    
    Attributes:
        ser: Serial connection object
        address: COM port address
        status: Connection status ("Connected" or "Not Connected")
        identity: Device identification string
        
    Example:
        >>> ps = RigolDP711()
        >>> ps.set_voltage(5.0)
        >>> ps.set_current(1.0)
        >>> ps.set_output_state(True)
        >>> voltage = ps.measure_voltage()
        >>> ps.set_output_state(False)
        >>> ps.disconnect()
    """
    
    def __init__(self, auto_connect: bool = True, com_port: Optional[str] = None, baud_rate: int = 9600):
        """
        Initialize RigolDP711 driver.
        
        Args:
            auto_connect: Automatically connect to device on initialization
            com_port: Optional explicit COM port (e.g., 'COM4', '/dev/ttyUSB0')
            baud_rate: Serial baud rate (default: 9600)
        """
        init(autoreset=True)
        
        self.ser: Optional[serial.Serial] = None
        self.address: Optional[str] = None
        self.status: str = "Not Connected"
        self.identity: Optional[str] = None
        self._com_port_hint: Optional[str] = com_port
        self._baud_rate: int = baud_rate

        if auto_connect:
            self.connect(com_port=com_port, baud_rate=baud_rate)
    
    def connect(self, com_port: Optional[str] = None, baud_rate: int = 9600) -> None:
        """
        Establish connection to RigolDP711 power supply.
        
        Args:
            com_port: Optional COM port (e.g., 'COM4', '/dev/ttyUSB0'). If None, prompt user.
            baud_rate: Serial baud rate (default: 9600)
            
        Raises:
            ConnectionError: If device not found or connection fails.
        """
        # 1) Try explicit COM port first
        explicit_port = com_port or self._com_port_hint
        
        # 2) Try environment variable
        if explicit_port is None:
            try:
                explicit_port = os.environ.get('DP711_COM_PORT')
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
                    selection = int(input("Select COM port for Rigol DP711 (1, 2, ...): "))
                    if 1 <= selection <= len(ports):
                        explicit_port = ports[selection - 1].device
                        os.environ['DP711_COM_PORT'] = explicit_port
                        break
                    print(_ERROR_STYLE + "Invalid selection")
                except ValueError:
                    print(_ERROR_STYLE + "Invalid input. Enter a number.")
        
        # 4) Open serial connection
        try:
            self.ser = serial.Serial(
                explicit_port,
                baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
                timeout=2,
            )
            self.address = explicit_port

            # Assert DTR + RTS so the instrument sees "terminal ready"
            self.ser.dtr = True
            self.ser.rts = True
            time.sleep(0.05)

            # Flush any stale bytes left in the hardware buffer
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            time.sleep(0.1)

            # Try \r\n first (Rigol standard), fall back to \n
            self.identity = None
            for terminator in (b'\r\n', b'\n'):
                self.ser.reset_input_buffer()
                self.ser.write(b'*IDN?' + terminator)
                self.ser.flush()
                time.sleep(_IDN_DELAY)

                # Read however many bytes arrived (handles missing \n terminator)
                n = self.ser.in_waiting
                raw = self.ser.read(n) if n > 0 else b''
                candidate = raw.decode('ascii', errors='ignore').strip()
                if len(candidate) >= 5:
                    self.identity = candidate
                    break

            if not self.identity:
                raise ConnectionError(_ERROR_STYLE + "Device not responding with valid identity")

            self.status = "Connected"
            print(_SUCCESS_STYLE + f"Connected to {self.identity}")

        except serial.SerialException as e:
            raise ConnectionError(_ERROR_STYLE + f"Failed to connect to {explicit_port}: {e}")
        except Exception as e:
            raise ConnectionError(_ERROR_STYLE + f"Unexpected error connecting to {explicit_port}: {e}")

    @staticmethod
    def diagnose(com_port: str) -> None:
        """
        Probe a COM port with all common baud rates and terminators to help
        identify the correct settings for the connected device.

        Usage:
            RigolDP711.diagnose("COM15")
        """
        print(f"\n{'='*60}")
        print(f"  Rigol DP711 Serial Diagnostic — {com_port}")
        print(f"{'='*60}")

        # ── Step 1: loopback test (short pin 2 ↔ pin 3 on DB9 for this) ────
        print("\n[1/3] TX→RX loopback test  (short DB9 pins 2↔3 on adapter)")
        print("      If you see 'OK' here, the adapter TX/RX path works.")
        try:
            s = serial.Serial(com_port, 9600, timeout=0.5,
                              xonxoff=False, rtscts=False, dsrdtr=False)
            s.reset_input_buffer()
            test_msg = b'LOOPBACK_TEST\r\n'
            s.write(test_msg)
            s.flush()
            time.sleep(0.3)
            n = s.in_waiting
            echo = s.read(n) if n > 0 else b''
            if test_msg.strip() in echo:
                print("      Loopback: OK — adapter TX→RX path is working")
            else:
                print(f"      Loopback: no echo  rx_bytes={n}  "
                      "(normal if pins 2↔3 NOT shorted — cable path untested)")
            s.close()
        except serial.SerialException as e:
            print(f"      Cannot open port: {e}")
            return

        # ── Step 2: passive listen — does the instrument talk first? ────────
        print("\n[2/3] Passive listen (2 s) — does the instrument send anything?")
        try:
            s = serial.Serial(com_port, 9600, timeout=2,
                              xonxoff=False, rtscts=False, dsrdtr=False)
            s.dtr = True
            s.rts = True
            s.reset_input_buffer()
            time.sleep(2.0)
            n = s.in_waiting
            raw = s.read(n) if n > 0 else b''
            if n > 0:
                print(f"      Received {n} bytes: {raw!r}")
            else:
                print("      Nothing received (instrument does not auto-transmit)")
            s.close()
        except serial.SerialException as e:
            print(f"      Error: {e}")

        # ── Step 3: active SCPI probe — all baud rates / terminators ────────
        print("\n[3/3] Active *IDN? probe (DTR+RTS asserted)")
        baud_rates  = [9600, 19200, 4800, 38400, 57600, 115200]
        terminators = [(b'\r\n', r'\r\n'), (b'\n', r'\n'), (b'\r', r'\r')]
        found = False
        for baud in baud_rates:
            try:
                s = serial.Serial(com_port, baud, timeout=1,
                                  xonxoff=False, rtscts=False, dsrdtr=False)
            except serial.SerialException as e:
                print(f"  {baud:>6} baud: cannot open – {e}")
                break
            s.dtr = True
            s.rts = True
            time.sleep(0.05)
            for term_bytes, term_label in terminators:
                s.reset_input_buffer()
                s.write(b'*IDN?' + term_bytes)
                s.flush()
                time.sleep(0.8)
                n = s.in_waiting
                raw = s.read(n) if n > 0 else b''
                decoded = raw.decode('ascii', errors='replace').strip()
                if len(decoded) >= 5:
                    marker = " ← RESPONSE"
                    found = True
                else:
                    marker = ""
                print(f"  {baud:>6} baud  term={term_label:<6}  "
                      f"rx={n:>3}  '{decoded[:60]}'{marker}")
            s.close()

        print()
        if not found:
            print("  No response from instrument. Most likely causes:")
            print("  1. TX/RX wires crossed — try a null-modem cable instead of")
            print("     straight-through (or vice versa)")
            print("  2. Wrong COM port — confirm by unplugging the FTDI adapter")
            print("     and checking which port disappears in Device Manager")
            print("  3. DP711 in LOCAL mode — the RS-232 port may need the front")
            print("     panel set to 'Remote' or the unit may need a power cycle")
        print(f"{'='*60}\n")

    def disconnect(self) -> None:
        """Close the serial connection to the device."""
        if self.ser is not None and self.ser.is_open:
            try:
                self.ser.close()
            finally:
                print(f"\rDisconnected from Rigol DP711 at {self.address}")
                self.ser = None
        
        self.status = "Not Connected"
        self.address = None
    
    def _chk(self) -> None:
        """Verify device is connected before operations."""
        if self.status != "Connected" or self.ser is None or not self.ser.is_open:
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP711")
    
    def _write(self, command: str) -> None:
        """Write a command to the device."""
        self._chk()
        self.ser.write(f"{command}\r\n".encode('ascii'))
        self.ser.flush()
        time.sleep(_DELAY)
    
    def _query(self, command: str) -> str:
        """Query the device and return the response."""
        self._chk()
        self.ser.reset_input_buffer()
        self.ser.write(f"{command}\r\n".encode('ascii'))
        self.ser.flush()
        time.sleep(_DELAY)
        n = self.ser.in_waiting
        raw = self.ser.read(n) if n > 0 else b''
        return raw.decode('ascii', errors='ignore').strip()
    
    def get(self, item: str, channel: int = 1) -> float:
        """
        Retrieve measurement value by name.
        
        Args:
            item: Measurement item name (case-insensitive)
                  Valid values: 'voltage', 'VOLT', 'current', 'CURR'
            channel: Optional channel number (for compatibility, not used)
            
        Returns:
            Measurement value
            
        Raises:
            ValueError: If invalid item requested
            ConnectionError: If not connected to device
            
        Example:
            >>> voltage = ps.get('voltage')
            >>> current = ps.get('CURR')
        """
        self._chk()

        item_upper = item.strip().upper()
        
        items = {
            "CURR": self.measure_current,
            "CURRENT": self.measure_current,
            "VOLT": self.measure_voltage,
            "VOLTAGE": self.measure_voltage
        }
        
        if item_upper not in items:
            raise ValueError(
                _ERROR_STYLE + f"Invalid item '{item}'. "
                f"Valid items: {', '.join(items.keys())}"
            )

        return items[item_upper]()

    def set_voltage(self, voltage: float) -> None:
        """
        Set the output voltage.
        
        Args:
            voltage: Voltage value to set (0-30V)
            
        Raises:
            ConnectionError: If not connected to device
            ValueError: If voltage out of range
        """
        self._chk()
        
        if not 0 <= voltage <= 30:
            raise ValueError(_ERROR_STYLE + f"Voltage {voltage}V out of range (0-30V)")
        
        command = f':VOLT {voltage:.3f}'
        self._write(command)

    def set_current(self, current: float) -> None:
        """
        Set the output current limit.
        
        Args:
            current: Current value to set (0-5A)
            
        Raises:
            ConnectionError: If not connected to device
            ValueError: If current out of range
        """
        self._chk()
        
        if not 0 <= current <= 5:
            raise ValueError(_ERROR_STYLE + f"Current {current}A out of range (0-5A)")
        
        command = f':CURR {current:.3f}'
        self._write(command)

    def get_voltage_setpoint(self) -> float:
        """
        Get the configured voltage setpoint.
        
        Returns:
            Configured voltage value
            
        Raises:
            ConnectionError: If not connected to device
            ValueError: If response cannot be parsed
        """
        try:
            response = self._query(':VOLT?')
            return float(response)
        except ValueError as e:
            raise ValueError(_ERROR_STYLE + f"Failed to parse voltage setpoint: {e}")

    def get_current_setpoint(self) -> float:
        """
        Get the configured current limit setpoint.
        
        Returns:
            Configured current value
            
        Raises:
            ConnectionError: If not connected to device
            ValueError: If response cannot be parsed
        """
        try:
            response = self._query(':CURR?')
            return float(response)
        except ValueError as e:
            raise ValueError(_ERROR_STYLE + f"Failed to parse current setpoint: {e}")
    
    def measure_voltage(self) -> float:
        """
        Measure the actual output voltage.
        
        Returns:
            Measured voltage value
            
        Raises:
            ConnectionError: If not connected to device
            ValueError: If response cannot be parsed
        """
        try:
            response = self._query(':MEAS:VOLT?')
            return float(response)
        except ValueError as e:
            raise ValueError(_ERROR_STYLE + f"Failed to parse voltage measurement: {e}")

    def measure_current(self) -> float:
        """
        Measure the actual output current.
        
        Returns:
            Measured current value
            
        Raises:
            ConnectionError: If not connected to device
            ValueError: If response cannot be parsed
        """
        try:
            response = self._query(':MEAS:CURR?')
            return float(response)
        except ValueError as e:
            raise ValueError(_ERROR_STYLE + f"Failed to parse current measurement: {e}")

    def measure_power(self) -> float:
        """
        Measure the actual output power.
        
        Returns:
            Measured power value in watts
            
        Raises:
            ConnectionError: If not connected to device
            ValueError: If response cannot be parsed
        """
        try:
            response = self._query(':MEAS:POW?')
            return float(response)
        except ValueError as e:
            raise ValueError(_ERROR_STYLE + f"Failed to parse power measurement: {e}")

    def set_output_state(self, state: bool) -> None:
        """
        Enable or disable the power supply output.
        
        Args:
            state: True to enable output, False to disable
            
        Raises:
            ConnectionError: If not connected to device
        """
        self._chk()
        
        if state:
            command = ':OUTP ON'
            print(_SUCCESS_STYLE + "Rigol DP711 output: ON")
        else:
            command = ':OUTP OFF'
            print(_SUCCESS_STYLE + "Rigol DP711 output: OFF")
        
        self._write(command)

    def get_output_state(self) -> bool:
        """
        Query the current output state.
        
        Returns:
            True if output is enabled, False if disabled
            
        Raises:
            ConnectionError: If not connected to device
        """
        try:
            response = self._query(':OUTP?')
            # Response should be 'ON' or 'OFF', or '1' or '0'
            return response.upper() in ['ON', '1']
        except Exception as e:
            raise ConnectionError(_ERROR_STYLE + f"Failed to query output state: {e}")

    def turn_on(self) -> None:
        """
        Turn on the power supply output.
        
        Raises:
            ConnectionError: If not connected to device
        """
        self.set_output_state(True)

    def turn_off(self) -> None:
        """
        Turn off the power supply output.
        
        Raises:
            ConnectionError: If not connected to device
        """
        self.set_output_state(False)


if __name__ == "__main__":
    """Test script for Rigol DP711"""
    
    print("Rigol DP711 Driver Test")
    print("=" * 50)
    
    try:
        # Connect to power supply
        ps = RigolDP711()
        
        print(f"\nIdentity: {ps.identity}")
        print(f"Address: {ps.address}")
        
        # Read current settings
        print("\nCurrent Settings:")
        print(f"  Voltage setpoint: {ps.get_voltage_setpoint():.3f}V")
        print(f"  Current setpoint: {ps.get_current_setpoint():.3f}A")
        print(f"  Output state: {ps.get_output_state()}")
        
        # Set voltage and current
        print("\nSetting voltage to 5.0V and current to 1.0A...")
        ps.set_voltage(5.0)
        ps.set_current(1.0)
        
        # Turn on output
        print("\nTurning output ON...")
        ps.turn_on()
        time.sleep(1)
        
        # Measure output
        print("\nMeasurements:")
        print(f"  Voltage: {ps.measure_voltage():.3f}V")
        print(f"  Current: {ps.measure_current():.3f}A")
        print(f"  Power: {ps.measure_power():.3f}W")
        
        # Turn off output
        print("\nTurning output OFF...")
        ps.turn_off()
        
        # Disconnect
        ps.disconnect()
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
