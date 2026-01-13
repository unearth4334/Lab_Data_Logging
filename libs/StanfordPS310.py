#   @file StanfordPS310.py
#   @brief Establishes a connection to the Stanford PS310 Power Supply (Negative Model)
#       and provides methods for interacting with the device.
#   @date 13-Jan-2026
#   @author Copilot
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

# Imports
import pyvisa
import time
from colorama import init, Fore, Back, Style

try:
    from .loading import *
except (ImportError, ModuleNotFoundError):
    from loading import *

# Constants and global variables
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_DELAY = 0.1  # seconds

"""
Establishes a connection to the Stanford PS310 Power Supply (Negative Model)

This is for the negative model of the Stanford PS310, which requires
negative voltage values.

Example usage:
    power_supply = StanfordPS310()
    power_supply.set_voltage(-5.0)  # Negative voltage required
    voltage = power_supply.measure_voltage()
"""
class StanfordPS310:

    """
    Initializes an instance of the StanfordPS310 class.
    """
    def __init__(self, auto_connect=True):

        init(autoreset=True)
        
        self.rm = pyvisa.ResourceManager()
        self.address = None
        self.instrument = None
        self.loading = loading()
        self.status = "Not Connected"

        if auto_connect:
            self.connect()

    """
    Establishes a connection to the Stanford PS310 Power Supply.

    Raises:
        ConnectionError: If unable to connect to Stanford PS310 Power Supply.

    Example usage:
        power_supply.connect()
    """
    def connect(self):

        resources = self.rm.list_resources()
        for resource in resources:
            if 'PS310' in resource or 'PS 310' in resource:
                self.address = resource
                break

        if self.address is None:
            error_message = "Stanford PS310 Power Supply not found."
            raise ConnectionError(_ERROR_STYLE + error_message)

        try:
            self.instrument = self.rm.open_resource(self.address)
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            self.status = "Connected"
            success_message = f"Connected to Stanford PS310 Power Supply at {self.address}"
            print(_SUCCESS_STYLE + success_message)

        except Exception as e:
            error_message = f"Failed to connect to Stanford PS310 Power Supply at {self.address}: {e}"
            raise ConnectionError(_ERROR_STYLE + error_message)

    """
    Disconnects from the Stanford PS310 Power Supply.

    Example usage:
        power_supply.disconnect()
    """
    def disconnect(self):
        if self.instrument is not None:
            self.instrument.close()
            self.status = "Not Connected"
            print(_SUCCESS_STYLE + "Disconnected from Stanford PS310 Power Supply")

    """
    Generic get method for measurements.

    Parameters:
        item (str): The measurement type to retrieve (e.g., "VOLT", "CURR").
        channel (int, optional): The channel number (not used for single-channel devices).

    Returns:
        tuple: A tuple containing the measurement value and error (0 if no error).

    Example usage:
        voltage = power_supply.get("VOLT")
    """
    def get(self, item, channel=1):

        items = {
            "VOLT": self.measure_voltage,
            "CURR": self.measure_current
        }

        result = items[item]()
        return (result, 0)

    """
    Sets the output voltage of the power supply.

    **IMPORTANT: This is a negative model power supply. Only negative voltage values are accepted.**

    Parameters:
        voltage (float): The voltage value to set. Must be negative.

    Raises:
        ConnectionError: If not connected to the Stanford PS310 Power Supply.
        ValueError: If voltage is not negative or not a valid numeric value.

    Example usage:
        # Correct usage for negative model
        power_supply.set_voltage(-5.0)
        
        # This will raise an error
        # power_supply.set_voltage(5.0)  # ValueError: voltage must be negative
    """
    def set_voltage(self, voltage):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Stanford PS310 Power Supply.")

        if not isinstance(voltage, (int, float)):
            raise ValueError(_ERROR_STYLE + "Invalid voltage value. Please provide a numeric value.")

        # Check for negative voltage requirement (negative model)
        if voltage >= 0:
            raise ValueError(_ERROR_STYLE + f"Invalid voltage value \"{voltage}\". This is a negative model Stanford PS310 - voltage must be negative (e.g., -5.0 V).")

        try:
            command = f"VOLT {voltage:.3f}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
        except Exception as e:
            error_message = f"Failed to set output voltage on Stanford PS310 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Sets the output current limit of the power supply.

    Parameters:
        current (float): The current limit value to set in amperes.

    Raises:
        ConnectionError: If not connected to the Stanford PS310 Power Supply.
        ValueError: If current is not a valid numeric value or is negative.

    Example usage:
        power_supply.set_current(1.0)  # Set current limit to 1.0 A
    """
    def set_current(self, current):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Stanford PS310 Power Supply.")

        if not isinstance(current, (int, float)):
            raise ValueError(_ERROR_STYLE + "Invalid current value. Please provide a numeric value.")

        if current < 0:
            raise ValueError(_ERROR_STYLE + "Invalid current value. Current must be positive.")

        try:
            command = f"CURR {current:.3f}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
        except Exception as e:
            error_message = f"Failed to set output current on Stanford PS310 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Measures the output voltage of the power supply.

    Returns:
        float: The measured voltage in volts.

    Raises:
        ConnectionError: If not connected to the Stanford PS310 Power Supply.

    Example usage:
        voltage = power_supply.measure_voltage()
    """
    def measure_voltage(self):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Stanford PS310 Power Supply.")

        try:
            command = "MEAS:VOLT?"
            result = self.instrument.query(command)
            voltage = float(result)
            self.loading.delay_with_loading_indicator(_DELAY)
            return voltage
        except Exception as e:
            error_message = f"Failed to measure voltage on Stanford PS310 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Measures the output current of the power supply.

    Returns:
        float: The measured current in amperes.

    Raises:
        ConnectionError: If not connected to the Stanford PS310 Power Supply.

    Example usage:
        current = power_supply.measure_current()
    """
    def measure_current(self):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Stanford PS310 Power Supply.")

        try:
            command = "MEAS:CURR?"
            result = self.instrument.query(command)
            current = float(result)
            self.loading.delay_with_loading_indicator(_DELAY)
            return current
        except Exception as e:
            error_message = f"Failed to measure current on Stanford PS310 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Turns the output on or off.

    Parameters:
        state (bool or str): The state to set for the output.
            - True or "ON" to turn on the output.
            - False or "OFF" to turn off the output.

    Raises:
        ConnectionError: If not connected to the Stanford PS310 Power Supply.
        ValueError: If an invalid state is provided.

    Example usage:
        power_supply.set_output_state(True)   # Turn on
        power_supply.set_output_state(False)  # Turn off
    """
    def set_output_state(self, state):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Stanford PS310 Power Supply.")

        if state in [1, "ON", True]:
            print(f"\r{Back.GREEN} Stanford PS310 Power Supply: ON ")
            command = "OUTP ON"
        elif state in [0, "OFF", False]:
            print(f"\r{Back.RED} Stanford PS310 Power Supply: OFF ")
            command = "OUTP OFF"
        else:
            raise ValueError(_ERROR_STYLE + "Invalid state type. Please provide either bool or str.")

        try:
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
        except Exception as e:
            error_message = f"Failed to set output state on Stanford PS310 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Gets the current output state.

    Returns:
        bool: True if output is on, False if output is off.

    Raises:
        ConnectionError: If not connected to the Stanford PS310 Power Supply.

    Example usage:
        is_on = power_supply.get_output_state()
    """
    def get_output_state(self):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Stanford PS310 Power Supply.")

        try:
            command = "OUTP?"
            result = self.instrument.query(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            return result.strip() == "1" or result.strip().upper() == "ON"
        except Exception as e:
            error_message = f"Failed to get output state on Stanford PS310 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)
