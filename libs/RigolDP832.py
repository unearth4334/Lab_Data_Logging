#   @file RigolDS7034.py
#   @brief Establishes a connection to the Rigol DP832 Power Supply 
#       and provides methods for interacting with the device.
#   @date 22-May-2023
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

# Imports
import pyvisa
from colorama import init, Fore, Back, Style
try:
    from .loading import *
except:
    from loading import *

# Constants and global variables
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT  + "\r"
_DELAY = 0.05 #seconds

"""
Establishes a connection to the Rigol DP832 Power Supply

Example usage:
"""
class RigolDP832:

    """
    Initializes an instance of the RigolDP832 class.
    """
    def __init__(self,auto_connect=True):

        init(autoreset=True)    

        self.rm = pyvisa.ResourceManager()
        self.address = None
        self.instrument = None
        self.loading = loading()
        self.voltage_has_been_configured = [False,False,False]
        self.current_has_been_configured = [False,False,False]

        self.status = "Not Connected"

        if auto_connect:
            self.connect()

    """
    Establishes a connection to the Rigol DP832 Power Supply.

    Raises:
        ConnectionError: If unable to connect to Rigol DP832 Power Supply.

    Example usage:
        power_supply.connect()
    """
    def connect(self):

        resources = self.rm.list_resources()
        for resource in resources:
            if 'DP8' in resource:
                self.address = resource
                break

        if self.address is None:
            error_message = "Rigol DP832 Power Supply not found."
            raise ConnectionError(_ERROR_STYLE + error_message)
            return None

        try:
            self.instrument = self.rm.open_resource(self.address)
            self.instrument.read_termination = '\n'
            self.status = "Connected"
            success_message = f"Connected to Rigol DP832 Power Supply at {self.address}"
            print(_SUCCESS_STYLE + success_message)

        except Exception as e:
            error_message = f"Failed to connect to Rigol DP832 Power Supply at {self.address}: {e}"
            raise ConnectionError(_ERROR_STYLE + error_message)
        
    """
    Disconnects from the Rigol DP832 Power Supply.

    Example usage:
        power_supply.disconnect()
    """
    def disconnect(self):
        if self.instrument is not None:
            self.instrument.close()
            print(f"\rDisconnected from Rigol DP832 Power Supply at {self.address}")
            self.status = "Not Connected"

    """
    Retrieves the specified value.
    
    Args:
        item (str): The measurement item to retrieve. Valid values are "STAT", "CURR", or "VOLT".
    
    Returns:
        The measurement result corresponding to the specified item and channel.

    Raises:
        ValueError: If an invalid item is requested.
    
    Example usage:
        voltage = multimeter.get("VOLT")
        print(f"Voltage: {voltage} V")
    """
    def get(self, item):
    
        items = {
            "current": self.measure_current,
            "voltage": self.measure_voltage,
            "power": self.measure_power
        }

        if item.lower() in items:
            result = items[item]()
            return result
        else:
            error_message = f"Invalid item: {item} request to Keysight 34460A Multimeter"
            raise ValueError(_ERROR_STYLE + error_message)
        
    """
    Selects the active output channel of the Rigol DP832 Power Supply.

    Parameters:
        channel (int): The channel number to select (1, 2, or 3).

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number is provided.

    Example usage:
        power_supply.select_channel(2)
    """
    def select_channel(self, channel):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        try:
            command = f":INSTrument:NSELect {channel}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
        except Exception as e:
            error_message = f"Failed to select channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)
        

    """
    Gets the currently selected channel on the Rigol DP832 Power Supply.

    Returns:
        int: The channel number (1, 2, or 3) currently selected.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number is received from the instrument.
    """
    def get_selected_channel(self):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        try:
            response = self.instrument.query(":INSTrument:NSELect?")
            self.loading.delay_with_loading_indicator(_DELAY)
            channel = int(response)
            if channel < 1 or channel > 3:
                raise ValueError(_ERROR_STYLE + "Invalid channel number received from the instrument.")
            return channel
        except Exception as e:
            error_message = f"Failed to get selected channel on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

        
    """
    Turns the output of the specified channel on or off.

    Parameters:
        channel (int): The channel number to control (1, 2, or 3).
        state (bool or str): The state to set for the channel.
            - True or "ON" to turn on the output.
            - False or "OFF" to turn off the output.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number or state is provided.

    Example usage:
        # Turn on channel 2
        power_supply.set_output_state(2, True)

        # Turn off channel 1
        power_supply.set_output_state(1, False)
    """
    def set_output_state(self, channel, state):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        if state in [1,"ON",True]:
            if self.voltage_has_been_configured[channel-1] == False:
                warning_message = f"Output voltage has not been set for channel {channel}. The currently configured value is {self.get_output_voltage(channel)} V. Do you want to continue? (y/n): "
                print(_WARNING_STYLE + warning_message)
                if not input() == "y":
                    raise ValueError(_ERROR_STYLE + "User cancelled operation.")
            if self.current_has_been_configured[channel-1] == False:
                warning_message = f"Output current has not been set for channel {channel}. The currently configured value is {self.get_output_current(channel)} A. Do you want to continue? (y/n): "
                print(_WARNING_STYLE + warning_message)
                if not input() == "y":
                    raise ValueError(_ERROR_STYLE + "User cancelled operation.")
            print(f"\rRigol DP832 Power Supply Channel {channel}:\t{Back.GREEN} ON {Back.BLUE} {Fore.WHITE} {self.get_output_voltage(channel)} V | {self.get_output_current(channel)} A   ")
            command = f":OUTPut{channel}:STATe ON"
        elif state in [0,"OFF",False]:
            # Rewritten more compactly
            print(f"\rRigol DP832 Power Supply Channel {channel}:\t{Back.RED} OFF ")
            command = f":OUTPut{channel}:STATe OFF"
        else:
            raise ValueError(_ERROR_STYLE + "Invalid state type. Please provide either bool or str.")

        try:
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
        except Exception as e:
            error_message = f"Failed to set output state of channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)
        
        

    """
    Sets the output voltage of the specified channel.

    Parameters:
        channel (int): The channel number to control (1, 2, or 3).
        voltage (float): The voltage value to set.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number or voltage value is provided.

    Example usage:
        # Set voltage of channel 1 to 5.0V
        power_supply.set_output_voltage(1, 5.0)

        # Set voltage of channel 2 to 3.3V
        power_supply.set_output_voltage(2, 3.3)
    """
    def set_output_voltage(self, channel, voltage):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        if not isinstance(voltage, (int, float)):
            raise ValueError(_ERROR_STYLE + "Invalid voltage value. Please provide a numeric value.")

        if channel in [1, 2] and (voltage < 0 or voltage > 30):
            raise ValueError(_ERROR_STYLE + "Invalid voltage value. Channel 1 and 2 accept voltages between 0 and 30 V.")

        if channel == 3 and (voltage < 0 or voltage > 5):
            raise ValueError(_ERROR_STYLE + "Invalid voltage value. Channel 3 accepts voltages between 0 and 5 V.")

        try:
            currently_selected_channel = self.get_selected_channel()
            if not currently_selected_channel == channel:
                self.select_channel(channel)
            command = f":VOLT {voltage:.3f}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            if not currently_selected_channel == channel:
                self.select_channel(currently_selected_channel) # Return to the previously selected channel
            self.voltage_has_been_configured[channel-1] = True
        except Exception as e:
            error_message = f"Failed to set output voltage of channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)
        

    """
    Sets the output current of the specified channel.

    Parameters:
        channel (int): The channel number to control (1, 2, or 3).
        current (float): The current value to set.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number or current value is provided.

    Example usage:
        # Set current of channel 1 to 2.0A
        power_supply.set_output_current(1, 2.0)

        # Set current of channel 2 to 1.5A
        power_supply.set_output_current(2, 1.5)
    """
    def set_output_current(self, channel, current):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        if not isinstance(current, (int, float)):
            raise ValueError(_ERROR_STYLE + "Invalid current value. Please provide a numeric value.")

        if current < 0 or current > 3:
            raise ValueError(_ERROR_STYLE + "Invalid current value. The current must be between 0 and 3 A.")

        try:
            currently_selected_channel = self.get_selected_channel()
            if not currently_selected_channel == channel:
                self.select_channel(channel)
            command = f":CURR {current:.3f}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            if not currently_selected_channel == channel:
                self.select_channel(currently_selected_channel) # Return to the previously selected channel
            self.current_has_been_configured[channel-1] = True
        except Exception as e:
            error_message = f"Failed to set output current of channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    
    """
    Get the currently configured voltage of the Rigol DP832 Power Supply.

    Parameters:
        channel (int): The channel number to retrieve the voltage from (1, 2, or 3).

    Returns:
        float: The currently configured voltage of the specified channel.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number is provided.

    Example usage:
        # Get voltage of channel 1
        voltage = power_supply.get_output_voltage(1)

        # Get voltage of channel 2
        voltage = power_supply.get_output_voltage(2)
    """
    def get_output_voltage(self, channel):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        try:
            command = f":SOURce{channel}:VOLTage:LEVel:IMMediate:AMPLitude?"
            response = self.instrument.query(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            voltage = float(response)
            return voltage
        except Exception as e:
            error_message = f"Failed to get output voltage of channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Get the currently configured output current of the Rigol DP832 Power Supply.

    Parameters:
        channel (int): The channel number to retrieve the current from (1, 2, or 3).

    Returns:
        float: The currently configured output current of the specified channel.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number is provided.

    Example usage:
        # Get current of channel 1
        current = power_supply.get_output_current(1)

        # Get current of channel 2
        current = power_supply.get_output_current(2)
    """
    def get_output_current(self, channel):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        try:
            command = f":SOURce{channel}:CURRent:LEVel:IMMediate:AMPLitude?"
            response = self.instrument.query(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            current = float(response)
            return current
        except Exception as e:
            error_message = f"Failed to get output current of channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)


    """
    Retrieves the voltage measurement result of the specified channel.

    Parameters:
        channel (int): The channel number to retrieve the voltage measurement from (1, 2, or 3).

    Returns:
        float: The voltage measurement result of the specified channel.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number is provided.

    Example usage:
        # Get voltage measurement of channel 1
        voltage_measurement = power_supply.measure_voltage(1)

        # Get voltage measurement of channel 2
        voltage_measurement = power_supply.measure_voltage(2)
    """
    def measure_voltage(self, channel):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        try:
            command = f":MEASure:VOLTage:DC? CHANnel{channel}"
            response = self.instrument.query(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            voltage_measurement = float(response)
            return voltage_measurement
        except Exception as e:
            error_message = f"Failed to get voltage measurement of channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)
    
    """
    Retrieves the current measurement result of the specified channel.

    Parameters:
        channel (int): The channel number to retrieve the current measurement from (1, 2, or 3).

    Returns:
        float: The current measurement result of the specified channel.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number is provided.

    Example usage:
        # Get current measurement of channel 1
        current_measurement = power_supply.measure_current(1)

        # Get current measurement of channel 2
        current_measurement = power_supply.measure_current(2)
    """
    def measure_current(self, channel):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        try:
            command = f":MEASure:CURRent:DC? CHANnel{channel}"
            response = self.instrument.query(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            current_measurement = float(response)
            return current_measurement
        except Exception as e:
            error_message = f"Failed to get current measurement of channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)
    
    """
    Retrieves the power measurement result of the specified channel.

    Parameters:
        channel (int): The channel number to retrieve the power measurement from (1, 2, or 3).

    Returns:
        float: The power measurement result of the specified channel.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number is provided.

    Example usage:
        # Get power measurement of channel 1
        power_measurement = power_supply.get_power_measurement(1)

        # Get power measurement of channel 2
        power_measurement = power_supply.get_power_measurement(2)
    """
    def measure_power(self, channel):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        try:
            command = f":MEASure:POWer? CHANnel{channel}"
            response = self.instrument.query(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            power_measurement = float(response)
            return power_measurement
        except Exception as e:
            error_message = f"Failed to get power measurement of channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)
    
    """
    Set the overcurrent protection threshold of the specified channel.

    Parameters:
        channel (int): The channel number to set the overcurrent protection threshold for (1, 2, or 3).
        threshold (float): The overcurrent protection threshold to set, in amps.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number is provided or the threshold value is out of range.

    Example usage:
        # Set overcurrent protection threshold for channel 1 to 2.5A
        power_supply.set_overcurrent_protection(1, 2.5)

        # Set overcurrent protection threshold for channel 2 to 3A
        power_supply.set_overcurrent_protection(2, 3.0)
    """
    def set_overcurrent_protection(self, channel, threshold):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        if threshold < 0 or threshold > 3.0:
            raise ValueError(_ERROR_STYLE + "Invalid overcurrent protection threshold. Please provide a value between 0 and 3.0.")

        try:
            command = f":SOURce{channel}:CURRent:PROTection:LEVel {threshold:.3f}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
        except Exception as e:
            error_message = f"Failed to set overcurrent protection threshold for channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Set the overvoltage protection threshold of the specified channel.

    Parameters:
        channel (int): The channel number to set the overvoltage protection threshold for (1, 2, or 3).
        threshold (float): The overvoltage protection threshold to set, in volts.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number is provided or the threshold value is out of range.

    Example usage:
        # Set overvoltage protection threshold for channel 1 to 25V
        power_supply.set_overvoltage_protection(1, 25.0)

        # Set overvoltage protection threshold for channel 2 to 28V
        power_supply.set_overvoltage_protection(2, 28.0)
    """
    def set_overvoltage_protection(self, channel, threshold):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        if channel in [1, 2] and (threshold < 0 or threshold > 30.0):
            raise ValueError(_ERROR_STYLE + "Invalid overvoltage protection threshold. Please provide a value between 0 and 30.0 for channels 1 and 2.")

        if channel == 3 and (threshold < 0 or threshold > 5.0):
            raise ValueError(_ERROR_STYLE + "Invalid overvoltage protection threshold. Please provide a value between 0 and 5.0 for channel 3.")

        try:
            command = f":SOURce{channel}:VOLTage:PROTection:LEVel {threshold:.3f}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
        except Exception as e:
            error_message = f"Failed to set overvoltage protection threshold for channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Turn the overcurrent protection of the specified channel on or off.

    Parameters:
        channel (int): The channel number to turn the overcurrent protection for (1, 2, or 3).
        enable (bool): True to enable overcurrent protection, False to disable.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number is provided.

    Example usage:
        # Enable overcurrent protection for channel 1
        power_supply.set_overcurrent_protection_state(1, True)

        # Disable overcurrent protection for channel 2
        power_supply.set_overcurrent_protection_state(2, False)
    """
    def set_overcurrent_protection_state(self, channel, enable):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        state = "ON" if enable else "OFF"

        try:
            command = f":OUTPut{channel}:PROTection:CURRent {state}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
        except Exception as e:
            error_message = f"Failed to turn overcurrent protection {state} for channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Turn the overvoltage protection of the specified channel on or off.

    Parameters:
        channel (int): The channel number to turn the overvoltage protection for (1, 2, or 3).
        enable (bool): True to enable overvoltage protection, False to disable.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.
        ValueError: If an invalid channel number is provided.

    Example usage:
        # Enable overvoltage protection for channel 1
        power_supply.set_overvoltage_protection_state(1, True)

        # Disable overvoltage protection for channel 2
        power_supply.set_overvoltage_protection_state(2, False)
    """
    def set_overvoltage_protection_state(self, channel, enable):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        if channel < 1 or channel > 3:
            raise ValueError(_ERROR_STYLE + "Invalid channel number. Please provide a number between 1 and 3.")

        state = "ON" if enable else "OFF"

        try:
            command = f":OUTPut{channel}:PROTection:VOLTage {state}"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
        except Exception as e:
            error_message = f"Failed to turn overvoltage protection {state} for channel {channel} on Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Reset the Rigol DP832 Power Supply.

    Raises:
        ConnectionError: If not connected to the Rigol DP832 Power Supply.

    Example usage:
        power_supply.reset()
    """
    def reset(self):
        if not self.status == "Connected":
            raise ConnectionError(_ERROR_STYLE + "Not connected to Rigol DP832 Power Supply.")

        try:
            command = "*RST"
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            self.voltage_has_been_configured = [False, False, False]
            self.current_has_been_configured = [False, False, False]
        except Exception as e:
            error_message = f"Failed to reset Rigol DP832 Power Supply: {e}"
            raise ValueError(_ERROR_STYLE + error_message)
        
    def error_handler(self, exception_type, exception, traceback):
        # Custom error handling logic
        print(_ERROR_STYLE + "An error occurred:", exception)

        # Attempt to turn off all output channels
        try:
            for channel in range(1, 4):
                self.set_output_state(channel, False)
        except Exception as e:
            print(_ERROR_STYLE + "Failed to turn off output channels:", e)
        
# Test code
if __name__ == "__main__":
    test_loading = loading()
    power_supply = RigolDP832()
    power_supply.set_output_voltage(channel=1, voltage=3.3)
    power_supply.set_output_current(channel=1, current=0.5)
    power_supply.set_output_voltage(channel=2, voltage=5.0)
    power_supply.set_output_current(channel=2, current=0.6)
    power_supply.set_output_voltage(channel=3, voltage=1.2)
    power_supply.set_output_current(channel=3, current=0.7)
    power_supply.set_overcurrent_protection(1, 0.6)
    power_supply.set_overcurrent_protection(2, 0.6)
    power_supply.set_overcurrent_protection(3, 0.6)
    power_supply.set_overvoltage_protection(1, 5.5)
    power_supply.set_overvoltage_protection(2, 13.5)
    power_supply.set_overvoltage_protection(3, 3.6)
    power_supply.set_overcurrent_protection_state(1, True)
    power_supply.set_overcurrent_protection_state(2, True)
    power_supply.set_overcurrent_protection_state(3, True)
    power_supply.set_overvoltage_protection_state(1, True)
    power_supply.set_overvoltage_protection_state(2, True)
    power_supply.set_overvoltage_protection_state(3, True)
    power_supply.set_output_state(1, True)
    power_supply.set_output_state(2, True)
    power_supply.set_output_state(3, True)
    test_loading.delay_with_loading_bar(5, loading_text="Waiting for 5 seconds...")
    power_supply.set_output_state(1, False)
    power_supply.set_output_state(2, False)
    power_supply.set_output_state(3, False)
    power_supply.disconnect()

