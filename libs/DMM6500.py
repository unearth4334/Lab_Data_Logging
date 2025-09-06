#   @file DMM6500.py 
#   @brief Establishes a connection to the Keithley DMM6500 Multimeter
#       and provides methods for interfacing with the device.
#   @date 18-May-2023
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
from colorama import init, Fore, Style
try:
    from .loading import *
except:
    from loading import *

# Constants and global variables
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT  + "\r"
_DELAY = 0.1

"""
Establishes a connection to the Keithley DMM6500 Multimeter and provides methods for interfacing.

Example usage:
    multimeter = DMM6500()
    voltage = multimeter.measure_voltage()
    print(f"Measured voltage: {voltage} V")
"""
class DMM6500:

    """
    Initializes an instance of the DMM6500 class.
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
    Establishes a connection to the Keithley DMM6500 Multimeter.

    Raises:
        ConnectionError: If unable to connect to Keithley DMM6500 Multimeter.
    
    Example usage:
        multimeter.connect()
    """
    def connect(self):
        
        resources = self.rm.list_resources()
        for resource in resources:
            # DMM6500 typically has identifiers like TCPIP, USB, or specific model strings
            if 'DMM6500' in resource or 'Keithley' in resource:
                self.address = resource
                break
        
        if self.address is None:
            error_message = "Keithley DMM6500 Multimeter not found."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
        try:
            self.instrument = self.rm.open_resource(self.address)
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            self.status = "Connected"
            success_message = f"Connected to Keithley DMM6500 Multimeter at {self.address}"
            print(_SUCCESS_STYLE + success_message)

        except Exception as e:
            error_message = f"Failed to connect to Keithley DMM6500 Multimeter at {self.address}: {e}"
            raise ConnectionError(_ERROR_STYLE + error_message)

    """
    Disconnects from the Keithley DMM6500 Multimeter.
    
    Example usage:
        multimeter.disconnect()
    """
    def disconnect(self):
        
        if self.instrument is not None:
            self.instrument.close()
            print(f"\rDisconnected from Keithley DMM6500 Multimeter at {self.address}")
            self.status = "Not Connected"

    """
    Retrieves the specified value.
    
    Args:
        item (str): The measurement item to retrieve. Valid values are "statistics", "current", or "voltage".
    
    Returns:
        The measurement result corresponding to the specified item.

    Raises:
        ValueError: If an invalid item is requested.
    
    Example usage:
        voltage = multimeter.get("voltage")
        print(f"Voltage: {voltage} V")
    """
    def get(self, item):
    
        items = {
            "statistics": self.calculate_statistics,
            "current": self.measure_current,
            "voltage": self.measure_voltage
        }

        if item in items:
            result = items[item]()
            return result
        else:
            error_message = f"Invalid item: {item} request to Keithley DMM6500 Multimeter"
            raise ValueError(_ERROR_STYLE + error_message)
        
    """
    Reads and returns the voltage measurement.
    
    Returns:
        float: The measured voltage value.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Multimeter.
    
    Example usage:
        voltage = multimeter.measure_voltage()
        print(f"Voltage: {voltage} V")
    """
    def measure_voltage(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write(":MEAS:VOLT:DC?")
        self.loading.delay_with_loading_indicator(_DELAY)
        voltage = self.instrument.read()
        return float(voltage)

    """
    Reads and returns the current measurement.
    
    Returns:
        float: The measured current value.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Multimeter.
    
    Example usage:
        current = multimeter.measure_current()
        print(f"Current: {current} A")
    """
    def measure_current(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write(":MEAS:CURR:DC?")
        self.loading.delay_with_loading_indicator(_DELAY)
        current = self.instrument.read()
        return float(current)
        
    """
    Retrieves the currently set function on the multimeter.

    Returns:
        str: The current function set on the multimeter.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Multimeter.
    """
    def get_current_function(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write(":FUNC?")
        self.loading.delay_with_loading_indicator(_DELAY)
        response = self.instrument.read().strip()
        return response.replace('"', '')  # Remove the quotation marks from the response

    """
    Configures the measurement settings.
    
    Args:
        measurement_type (str): The type of measurement to configure, e.g., "VOLT:DC", "CURR:DC".
        range_val (float): The desired range value for the measurement type.
        resolution_val (float): The desired resolution value for the measurement type.
    
    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Multimeter.

    Example usage:
        multimeter.configure("VOLT:DC", 10.0, 0.001) 
    """
    def configure(self, measurement_type, range_val, resolution_val):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        # DMM6500 uses different syntax for configuration
        self.instrument.write(f":FUNC '{measurement_type}'")
        self.loading.delay_with_loading_indicator(_DELAY)
        self.instrument.write(f":{measurement_type}:RANG {range_val}")
        self.loading.delay_with_loading_indicator(_DELAY)
        self.instrument.write(f":{measurement_type}:NPLC {resolution_val}")
        self.loading.delay_with_loading_indicator(_DELAY)
        print(f"\rConfiguration set for {measurement_type}: Range={range_val}, Resolution={resolution_val} on Keithley DMM6500 Multimeter.")

    """
    Starts a measurement of n readings by configuring statistics and initiating the measurement.
    
    Args:
        n (int): The number of readings to be performed.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Multimeter.
    
    Example usage:
        multimeter.start_measurement(100)
    """
    def start_measurement(self, n):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        # Enable statistics on DMM6500
        self.instrument.write(":CALC:STAT:ENAB ON")
        self.loading.delay_with_loading_indicator(_DELAY)
        # Clear previous statistics
        self.instrument.write(":CALC:STAT:CLE")
        self.loading.delay_with_loading_indicator(_DELAY)
        # Set the number of readings
        self.instrument.write(f":SAMP:COUN {n}")
        self.loading.delay_with_loading_indicator(_DELAY)
        # Initiate the measurement
        self.instrument.write(":INIT")
        self.loading.delay_with_loading_indicator(_DELAY)
        print(f"\rMeasurement of {n} readings started on Keithley DMM6500 Multimeter.")

    """
    Retrieves statistics from the DMM6500 and returns them as a list.
    This method uses the correct DMM6500 SCPI commands to avoid SCPI errors.
    
    Returns:
        list: A list containing the average, standard deviation, minimum, and maximum values.
    
    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Multimeter.
        
    Example usage:
        result = multimeter.calculate_statistics()
        print(f"Average: {result[0]}, Std Dev: {result[1]}, Min: {result[2]}, Max: {result[3]}")
    """
    def calculate_statistics(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        # DMM6500 specific statistics commands to fix SCPI error
        try:
            # Get average
            self.instrument.write(":CALC:STAT:AVER?")
            self.loading.delay_with_loading_indicator(_DELAY)
            average = float(self.instrument.read().strip())
            
            # Get standard deviation
            self.instrument.write(":CALC:STAT:SDEV?")
            self.loading.delay_with_loading_indicator(_DELAY)
            std_dev = float(self.instrument.read().strip())
            
            # Get minimum
            self.instrument.write(":CALC:STAT:MIN?")
            self.loading.delay_with_loading_indicator(_DELAY)
            minimum = float(self.instrument.read().strip())
            
            # Get maximum
            self.instrument.write(":CALC:STAT:MAX?")
            self.loading.delay_with_loading_indicator(_DELAY)
            maximum = float(self.instrument.read().strip())
            
            result = [average, std_dev, minimum, maximum]
            return result
            
        except Exception as e:
            error_message = f"Error retrieving statistics from DMM6500: {e}"
            raise ValueError(_ERROR_STYLE + error_message)