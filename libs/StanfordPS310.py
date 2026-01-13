#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   @file StanfordPS310.py
#   @brief Establishes a connection to the Stanford Research Systems PS310 High Voltage Power Supply
#       via a National Instruments GPIB-USB-HS adapter and provides methods for interfacing with the device.
#   @date 02-Dec-2025
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
Stanford Research Systems PS310 High Voltage Power Supply Driver

This module provides a Python interface for controlling the Stanford PS310
high voltage power supply through a National Instruments GPIB-USB-HS adapter
using PyVISA.

The PS310 is a precision high voltage DC power supply capable of generating
voltages up to ±1250V (1.25 kV) with excellent stability and low noise.

Example usage:
    hvps = StanfordPS310()
    hvps.set_voltage(500.0)  # Set output to 500V
    hvps.set_output_state(True)  # Enable output
    voltage = hvps.measure_voltage()  # Read actual output voltage
    print(f"Output voltage: {voltage} V")
    hvps.set_output_state(False)  # Disable output
    hvps.disconnect()
"""

from __future__ import annotations

import time
from typing import Optional

import pyvisa
from colorama import init, Fore, Style

try:
    from .loading import loading
except ImportError:
    try:
        from loading import loading
    except ImportError:
        class loading:
            """Fallback loading class if module not available."""
            def delay_with_loading_indicator(self, seconds: float) -> None:
                time.sleep(seconds)

# Constants and global variables
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "
_DELAY = 0.1  # seconds

# PS310 specifications
_PS310_MAX_VOLTAGE = 1250.0  # ±1250V max
_PS310_MAX_CURRENT = 0.021   # 21 mA max current


class StanfordPS310:
    """
    Stanford Research Systems PS310 High Voltage Power Supply driver.

    The PS310 provides precision high voltage DC power up to ±1250V with
    excellent stability and low noise. Communication is via GPIB interface.

    Attributes:
        status (str): Connection status ('Connected' or 'Not Connected')
        address (str): VISA resource address when connected
        instrument: PyVISA resource object

    Example:
        >>> hvps = StanfordPS310()  # Auto-connect
        >>> hvps.set_voltage(100.0)
        >>> hvps.set_output_state(True)
        >>> voltage = hvps.measure_voltage()
        >>> hvps.disconnect()
    """

    def __init__(self, auto_connect: bool = True, address: Optional[str] = None):
        """
        Initialize an instance of the StanfordPS310 class.

        Args:
            auto_connect: If True, automatically connect to the device.
            address: Optional VISA resource string. If None, auto-detect.
        """
        init(autoreset=True)

        self.rm = pyvisa.ResourceManager()
        self.address: Optional[str] = None
        self.instrument: Optional[pyvisa.resources.MessageBasedResource] = None
        self.loading = loading()
        self.status = "Not Connected"
        self._address_hint = address
        self._voltage_has_been_set = False

        if auto_connect:
            self.connect(address=self._address_hint)

    def connect(self, address: Optional[str] = None) -> None:
        """
        Establish a connection to the Stanford PS310 High Voltage Power Supply.

        The method first tries the specified address, then scans for GPIB
        resources and verifies the instrument identity via *IDN? query.

        Args:
            address: VISA resource string. If None, auto-detect using GPIB scan.

        Raises:
            ConnectionError: If unable to connect to the PS310.

        Example:
            >>> hvps = StanfordPS310(auto_connect=False)
            >>> hvps.connect("GPIB0::14::INSTR")
        """
        explicit = address or self._address_hint

        # Try explicit address first
        if explicit:
            try:
                inst = self.rm.open_resource(explicit)
                inst.read_termination = '\n'
                inst.write_termination = '\n'
                inst.timeout = 5000
                idn = inst.query("*IDN?").strip()
                if self._is_ps310_device(idn):
                    self.instrument = inst
                    self.address = explicit
                    self._idn = idn
                else:
                    inst.close()
                    raise ConnectionError(
                        _ERROR_STYLE + f"Resource '{explicit}' is not a Stanford PS310 (IDN='{idn}')."
                    )
            except pyvisa.errors.VisaIOError as e:
                raise ConnectionError(
                    _ERROR_STYLE + f"Failed to open explicit address '{explicit}': {e}"
                )

        # Auto-detect by scanning GPIB resources
        if self.instrument is None:
            resources = self.rm.list_resources()
            for resource in resources:
                # Look for GPIB resources (NI GPIB-USB-HS adapter)
                if "GPIB" in resource:
                    try:
                        inst = self.rm.open_resource(resource)
                        inst.read_termination = '\n'
                        inst.write_termination = '\n'
                        inst.timeout = 5000
                        idn = inst.query("*IDN?").strip()
                        if self._is_ps310_device(idn):
                            self.instrument = inst
                            self.address = resource
                            self._idn = idn
                            break
                        inst.close()
                    except Exception:
                        continue

        if self.instrument is None:
            raise ConnectionError(
                _ERROR_STYLE + "Stanford PS310 High Voltage Power Supply not found."
            )

        # Clear status registers
        try:
            self.instrument.write("*CLS")
        except Exception:
            pass

        self.status = "Connected"
        print(_SUCCESS_STYLE + f"Connected to Stanford PS310 at {self.address} with idn {self._idn}")

    def disconnect(self) -> None:
        """
        Disconnect from the Stanford PS310 High Voltage Power Supply.

        Example:
            >>> hvps.disconnect()
        """
        if self.instrument is not None:
            try:
                self.instrument.close()
            finally:
                print(f"\rDisconnected from Stanford PS310 at {self.address}")
        self.status = "Not Connected"
        self.instrument = None
        self.address = None

    def _check_connection(self) -> None:
        """Verify the device is connected before operations."""
        if self.status != "Connected" or self.instrument is None:
            raise ConnectionError(_ERROR_STYLE + "Not connected to Stanford PS310.")

    @staticmethod
    def _is_ps310_device(idn: str) -> bool:
        """
        Check if the IDN response indicates a Stanford PS310 device.

        Args:
            idn: The *IDN? response string from the instrument.

        Returns:
            bool: True if the device appears to be a PS310.
        """
        idn_upper = idn.upper()
        # Check for PS310 model number or Stanford Research Systems with PS3xx pattern
        return "PS310" in idn_upper or (
            "STANFORD" in idn_upper and "PS3" in idn_upper
        )

    def get(self, item: str, channel: Optional[int] = None):
        """
        Retrieve the specified measurement value.

        Args:
            item: The measurement item to retrieve.
                Valid values: 'voltage', 'current', 'set_voltage'
            channel: Not used for PS310 (single channel), included for API compatibility.

        Returns:
            float: The measurement result.

        Raises:
            ValueError: If an invalid item is requested.

        Example:
            >>> voltage = hvps.get("voltage")
        """
        items = {
            "voltage": self.measure_voltage,
            "current": self.measure_current,
            "set_voltage": self.get_voltage,
        }

        item_lower = item.lower()
        if item_lower in items:
            return items[item_lower]()
        else:
            raise ValueError(
                _ERROR_STYLE + f"Invalid item: {item} request to Stanford PS310. "
                f"Valid items: {list(items.keys())}"
            )

    def set_voltage(self, voltage: float) -> None:
        """
        Set the output voltage of the PS310.

        Args:
            voltage: The target voltage in volts. Range: -1250V to +1250V.

        Raises:
            ConnectionError: If not connected to the PS310.
            ValueError: If voltage is out of range.

        Example:
            >>> hvps.set_voltage(500.0)  # Set to 500V
        """
        self._check_connection()

        if not isinstance(voltage, (int, float)):
            raise ValueError(_ERROR_STYLE + "Invalid voltage value. Please provide a numeric value.")

        if abs(voltage) > _PS310_MAX_VOLTAGE:
            raise ValueError(
                _ERROR_STYLE + f"Invalid voltage value '{voltage}'. "
                f"The PS310 accepts voltages between -{_PS310_MAX_VOLTAGE} and +{_PS310_MAX_VOLTAGE} V."
            )

        try:
            # VSET <value> - Set the voltage setpoint (SRS PS310 Programming Manual)
            command = f"VSET {voltage:.3f}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            self._voltage_has_been_set = True
            print(f"\rPS310 voltage set to {voltage:.3f} V")
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to set voltage on Stanford PS310: {e}")

    def get_voltage(self) -> float:
        """
        Get the currently configured (setpoint) voltage.

        Returns:
            float: The configured voltage setpoint in volts.

        Raises:
            ConnectionError: If not connected to the PS310.

        Example:
            >>> setpoint = hvps.get_voltage()
        """
        self._check_connection()

        try:
            # VSET? - Query the voltage setpoint (SRS PS310 Programming Manual)
            response = self.instrument.query("VSET?")
            self.loading.delay_with_loading_indicator(_DELAY)
            return float(response.strip())
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to get voltage setpoint from Stanford PS310: {e}")

    def measure_voltage(self) -> float:
        """
        Measure the actual output voltage.

        Returns:
            float: The measured output voltage in volts.

        Raises:
            ConnectionError: If not connected to the PS310.

        Example:
            >>> voltage = hvps.measure_voltage()
            >>> print(f"Output: {voltage} V")
        """
        self._check_connection()

        try:
            # VOUT? - Query the measured output voltage (SRS PS310 Programming Manual)
            response = self.instrument.query("VOUT?")
            self.loading.delay_with_loading_indicator(_DELAY)
            return float(response.strip())
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to measure voltage from Stanford PS310: {e}")

    def measure_current(self) -> float:
        """
        Measure the actual output current.

        Returns:
            float: The measured output current in amps.

        Raises:
            ConnectionError: If not connected to the PS310.

        Example:
            >>> current = hvps.measure_current()
            >>> print(f"Current: {current * 1000:.3f} mA")
        """
        self._check_connection()

        try:
            # IOUT? - Query the measured output current (SRS PS310 Programming Manual)
            response = self.instrument.query("IOUT?")
            self.loading.delay_with_loading_indicator(_DELAY)
            return float(response.strip())
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to measure current from Stanford PS310: {e}")

    def set_current_limit(self, current: float) -> None:
        """
        Set the current limit (trip point) for the PS310.

        Args:
            current: The current limit in amps. Range: 0 to 0.021 A (21 mA).

        Raises:
            ConnectionError: If not connected to the PS310.
            ValueError: If current is out of range.

        Example:
            >>> hvps.set_current_limit(0.010)  # Set 10 mA limit
        """
        self._check_connection()

        if not isinstance(current, (int, float)):
            raise ValueError(_ERROR_STYLE + "Invalid current value. Please provide a numeric value.")

        if current < 0 or current > _PS310_MAX_CURRENT:
            raise ValueError(
                _ERROR_STYLE + f"Invalid current limit '{current}'. "
                f"The PS310 accepts current limits between 0 and {_PS310_MAX_CURRENT * 1000:.1f} mA."
            )

        try:
            # ILIM <value> - Set the current trip point (SRS PS310 Programming Manual)
            command = f"ILIM {current:.6f}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            print(f"\rPS310 current limit set to {current * 1000:.3f} mA")
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to set current limit on Stanford PS310: {e}")

    def get_current_limit(self) -> float:
        """
        Get the currently configured current limit.

        Returns:
            float: The current limit in amps.

        Raises:
            ConnectionError: If not connected to the PS310.

        Example:
            >>> limit = hvps.get_current_limit()
            >>> print(f"Current limit: {limit * 1000:.3f} mA")
        """
        self._check_connection()

        try:
            # ILIM? - Query the current trip point (SRS PS310 Programming Manual)
            response = self.instrument.query("ILIM?")
            self.loading.delay_with_loading_indicator(_DELAY)
            return float(response.strip())
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to get current limit from Stanford PS310: {e}")

    def set_output_state(self, state: bool) -> None:
        """
        Enable or disable the high voltage output.

        Args:
            state: True to enable output, False to disable.

        Raises:
            ConnectionError: If not connected to the PS310.
            ValueError: If output is enabled without setting voltage first.

        Example:
            >>> hvps.set_output_state(True)   # Enable HV output
            >>> hvps.set_output_state(False)  # Disable HV output
        """
        self._check_connection()

        if state and not self._voltage_has_been_set:
            current_setpoint = self.get_voltage()
            print(
                _WARNING_STYLE + f"Output voltage has not been set in this session. "
                f"Current setpoint: {current_setpoint:.3f} V"
            )

        try:
            if state:
                # HVON - Turn on the high voltage output (SRS PS310 Programming Manual)
                self.instrument.write("HVON")
                self.loading.delay_with_loading_indicator(_DELAY)
                print(f"\r{Fore.GREEN}PS310 High Voltage Output: ON")
            else:
                # HVOF - Turn off the high voltage output (SRS PS310 Programming Manual)
                self.instrument.write("HVOF")
                self.loading.delay_with_loading_indicator(_DELAY)
                print(f"\r{Fore.RED}PS310 High Voltage Output: OFF")
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to set output state on Stanford PS310: {e}")

    def get_output_state(self) -> bool:
        """
        Get the current output state (on/off).

        Returns:
            bool: True if output is enabled, False if disabled.

        Raises:
            ConnectionError: If not connected to the PS310.

        Example:
            >>> if hvps.get_output_state():
            ...     print("HV output is ON")
        """
        self._check_connection()

        try:
            # HVON? - Query output state, returns 1 if on, 0 if off (SRS PS310 Programming Manual)
            response = self.instrument.query("HVON?")
            self.loading.delay_with_loading_indicator(_DELAY)
            return response.strip() == "1"
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to get output state from Stanford PS310: {e}")

    def set_voltage_limit(self, voltage: float) -> None:
        """
        Set the voltage limit (maximum allowed voltage).

        Args:
            voltage: The voltage limit in volts. Range: 0 to 1250V.

        Raises:
            ConnectionError: If not connected to the PS310.
            ValueError: If voltage is out of range.

        Example:
            >>> hvps.set_voltage_limit(1000.0)  # Limit to 1000V max
        """
        self._check_connection()

        if not isinstance(voltage, (int, float)):
            raise ValueError(_ERROR_STYLE + "Invalid voltage limit value. Please provide a numeric value.")

        if voltage < 0 or voltage > _PS310_MAX_VOLTAGE:
            raise ValueError(
                _ERROR_STYLE + f"Invalid voltage limit '{voltage}'. "
                f"The PS310 accepts voltage limits between 0 and {_PS310_MAX_VOLTAGE} V."
            )

        try:
            # VLIM <value> - Set the voltage limit (SRS PS310 Programming Manual)
            command = f"VLIM {voltage:.3f}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            print(f"\rPS310 voltage limit set to {voltage:.3f} V")
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to set voltage limit on Stanford PS310: {e}")

    def get_voltage_limit(self) -> float:
        """
        Get the currently configured voltage limit.

        Returns:
            float: The voltage limit in volts.

        Raises:
            ConnectionError: If not connected to the PS310.

        Example:
            >>> limit = hvps.get_voltage_limit()
        """
        self._check_connection()

        try:
            # VLIM? - Query the voltage limit (SRS PS310 Programming Manual)
            response = self.instrument.query("VLIM?")
            self.loading.delay_with_loading_indicator(_DELAY)
            return float(response.strip())
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to get voltage limit from Stanford PS310: {e}")

    def reset(self) -> None:
        """
        Reset the PS310 to default settings.

        This disables the output and resets configuration.

        Raises:
            ConnectionError: If not connected to the PS310.

        Example:
            >>> hvps.reset()
        """
        self._check_connection()

        try:
            self.instrument.write("*RST")
            self.loading.delay_with_loading_indicator(_DELAY)
            self._voltage_has_been_set = False
            print("\rPS310 reset to default settings")
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to reset Stanford PS310: {e}")

    def get_identification(self) -> str:
        """
        Get the instrument identification string.

        Returns:
            str: The *IDN? response from the instrument.

        Raises:
            ConnectionError: If not connected to the PS310.

        Example:
            >>> idn = hvps.get_identification()
            >>> print(f"Instrument: {idn}")
        """
        self._check_connection()

        try:
            response = self.instrument.query("*IDN?")
            self.loading.delay_with_loading_indicator(_DELAY)
            return response.strip()
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to get identification from Stanford PS310: {e}")

    def clear_status(self) -> None:
        """
        Clear the status registers and error queue.

        Raises:
            ConnectionError: If not connected to the PS310.

        Example:
            >>> hvps.clear_status()
        """
        self._check_connection()

        try:
            self.instrument.write("*CLS")
            self.loading.delay_with_loading_indicator(_DELAY)
        except Exception as e:
            raise ValueError(_ERROR_STYLE + f"Failed to clear status on Stanford PS310: {e}")


# Test code
if __name__ == "__main__":
    print("Stanford PS310 High Voltage Power Supply Test")
    print("=" * 50)

    try:
        # Create instance (auto-connect)
        hvps = StanfordPS310(auto_connect=False)
        print("Note: Auto-connect disabled for testing.")
        print("To test with actual hardware, use: hvps.connect()")

        # Show available methods
        print("\nAvailable methods:")
        methods = [m for m in dir(hvps) if not m.startswith('_') and callable(getattr(hvps, m))]
        for method in methods:
            print(f"  - {method}")

    except Exception as e:
        print(f"Test error: {e}")
