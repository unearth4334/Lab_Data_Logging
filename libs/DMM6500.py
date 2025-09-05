#   @file DMM6500.py 
#   @brief Establishes a connection to the Keithley DMM6500 Digital Multimeter
#       and provides methods for interfacing with the device.
#   @date 11-Dec-2024
#   @author AI Assistant
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
from colorama import init, Fore, Style
try:
    from .loading import loading
except:
    try:
        from loading import loading
    except:
        # Fallback when loading module is not available
        class loading:
            def delay_with_loading_indicator(self, delay):
                time.sleep(delay)

# Constants and global variables
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT  + "\r"
_DELAY = 0.1

"""
Establishes a connection to the Keithley DMM6500 Digital Multimeter and provides methods for interfacing.

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

        try:
            self.rm = pyvisa.ResourceManager()
        except Exception as e:
            # Handle case where VISA is not available (e.g., testing without hardware)
            print(f"Warning: VISA not available: {e}")
            self.rm = None
        
        self.address = None
        self.instrument = None
        self.loading = loading()

        self.status = "Not Connected"
        
        if auto_connect and self.rm is not None:
            self.connect()
        
    """
    Establishes a connection to the Keithley DMM6500 Digital Multimeter.

    Raises:
        ConnectionError: If unable to connect to Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        multimeter.connect()
    """
    def connect(self):
        
        if self.rm is None:
            error_message = "VISA ResourceManager not available."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
        resources = self.rm.list_resources()
        for resource in resources:
            try:
                # Try to connect to each resource and check if it's a DMM6500
                temp_instrument = self.rm.open_resource(resource)
                temp_instrument.read_termination = '\n'
                temp_instrument.write("*IDN?")
                response = temp_instrument.read()
                if 'DMM6500' in response:
                    self.address = resource
                    temp_instrument.close()
                    break
                temp_instrument.close()
            except:
                continue
        
        if self.address is None:
            error_message = "Keithley DMM6500 Digital Multimeter not found."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
        try:
            self.instrument = self.rm.open_resource(self.address)
            self.instrument.read_termination = '\n'
            self.status = "Connected"
            success_message = f"Connected to Keithley DMM6500 Digital Multimeter at {self.address}"
            print(_SUCCESS_STYLE + success_message)

        except Exception as e:
            error_message = f"Failed to connect to Keithley DMM6500 Digital Multimeter at {self.address}: {e}"
            raise ConnectionError(_ERROR_STYLE + error_message)

    """
    Disconnects from the Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        multimeter.disconnect()
    """
    def disconnect(self):
        
        if self.instrument is not None:
            self.instrument.close()
            print(f"\rDisconnected from Keithley DMM6500 Digital Multimeter at {self.address}")
            self.status = "Not Connected"

    """
    Retrieves the specified value.
    
    Args:
        item (str): The measurement item to retrieve. Valid values are "statistics", "current", "voltage", 
                   "resistance", "resistance_4w", "capacitance", "frequency", "period", "temperature".
    
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
            "voltage": self.measure_voltage,
            "resistance": self.measure_resistance,
            "resistance_4w": self.measure_resistance_4w,
            "capacitance": self.measure_capacitance,
            "frequency": self.measure_frequency,
            "period": self.measure_period,
            "temperature": self.measure_temperature
        }

        if item in items:
            result = items[item]()
            return result
        else:
            error_message = f"Invalid item: {item} request to Keithley DMM6500 Digital Multimeter"
            raise ValueError(_ERROR_STYLE + error_message)
        
    """
    Reads and returns the voltage measurement.
    
    Returns:
        float: The measured voltage value.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        voltage = multimeter.measure_voltage()
        print(f"Voltage: {voltage} V")
    """
    def measure_voltage(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write("MEASURE:VOLTAGE:DC?")
        self.loading.delay_with_loading_indicator(_DELAY)
        voltage = self.instrument.read()
        return float(voltage)

    """
    Reads and returns the current measurement.
    
    Returns:
        float: The measured current value.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        current = multimeter.measure_current()
        print(f"Current: {current} A")
    """
    def measure_current(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write("MEASURE:CURRENT:DC?")
        self.loading.delay_with_loading_indicator(_DELAY)
        current = self.instrument.read()
        return float(current)

    """
    Reads and returns the 2-wire resistance measurement.
    
    Returns:
        float: The measured resistance value.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        resistance = multimeter.measure_resistance()
        print(f"Resistance: {resistance} Ohms")
    """
    def measure_resistance(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write("MEASURE:RESISTANCE?")
        self.loading.delay_with_loading_indicator(_DELAY)
        resistance = self.instrument.read()
        return float(resistance)

    """
    Reads and returns the 4-wire resistance measurement.
    
    Returns:
        float: The measured 4-wire resistance value.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        resistance = multimeter.measure_resistance_4w()
        print(f"4-Wire Resistance: {resistance} Ohms")
    """
    def measure_resistance_4w(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write("MEASURE:FRESISTANCE?")
        self.loading.delay_with_loading_indicator(_DELAY)
        resistance = self.instrument.read()
        return float(resistance)

    """
    Reads and returns the capacitance measurement.
    
    Returns:
        float: The measured capacitance value.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        capacitance = multimeter.measure_capacitance()
        print(f"Capacitance: {capacitance} F")
    """
    def measure_capacitance(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write("MEASURE:CAPACITANCE?")
        self.loading.delay_with_loading_indicator(_DELAY)
        capacitance = self.instrument.read()
        return float(capacitance)

    """
    Reads and returns the frequency measurement.
    
    Returns:
        float: The measured frequency value.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        frequency = multimeter.measure_frequency()
        print(f"Frequency: {frequency} Hz")
    """
    def measure_frequency(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write("MEASURE:FREQUENCY?")
        self.loading.delay_with_loading_indicator(_DELAY)
        frequency = self.instrument.read()
        return float(frequency)

    """
    Reads and returns the period measurement.
    
    Returns:
        float: The measured period value.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        period = multimeter.measure_period()
        print(f"Period: {period} s")
    """
    def measure_period(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write("MEASURE:PERIOD?")
        self.loading.delay_with_loading_indicator(_DELAY)
        period = self.instrument.read()
        return float(period)

    """
    Reads and returns the temperature measurement.
    
    Returns:
        float: The measured temperature value.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        temperature = multimeter.measure_temperature()
        print(f"Temperature: {temperature} C")
    """
    def measure_temperature(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write("MEASURE:TEMPERATURE?")
        self.loading.delay_with_loading_indicator(_DELAY)
        temperature = self.instrument.read()
        return float(temperature)
        
    """
    Retrieves the currently set function on the multimeter.

    Returns:
        str: The current function set on the multimeter.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.
    """
    def get_current_function(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write("FUNCTION?")
        self.loading.delay_with_loading_indicator(_DELAY)
        response = self.instrument.read().strip()
        return response.replace('"', '')  # Remove the quotation marks from the response

    """
    Configures the measurement settings.
    
    Args:
        measurement_type (str): The type of measurement to configure, e.g., "VOLTAGE:DC", "CURRENT:DC".
            +--------------------+-----------------+
            |    Function        |     Command     |
            +--------------------+-----------------+
            |  DC Voltage        |   VOLTAGE:DC    |
            |  AC Voltage        |   VOLTAGE:AC    |
            |  DC Current        |   CURRENT:DC    |
            |  AC Current        |   CURRENT:AC    |
            |  2-Wire Resistance |   RESISTANCE    |
            |  4-Wire Resistance |   FRESISTANCE   |
            |  Frequency         |   FREQUENCY     |
            |  Period            |   PERIOD        |
            |  Capacitance       |   CAPACITANCE   |
            |  Temperature       |   TEMPERATURE   |
            +--------------------+-----------------+
        range_val (float): The desired range value for the measurement type, specified in the measurement's units (V, A, Hz, Ohms, etc).
        resolution_val (float): The desired resolution value for the measurement type, specified in the measurement's units (V, A, Hz, Ohms, etc).
    
    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.

    Note:
        The range and resolution values are dependent on the specific capabilities of the Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        # Configure DC voltage measurement with a range of 10V and a resolution of 0.001V. 
        multimeter.configure("VOLTAGE:DC", 10.0, 0.001) 
    
        # Configure DC current measurement with a range of 1A and a resolution of 0.0001A.
        multimeter.configure("CURRENT:DC", 1.0, 0.0001)
    """
    def configure(self, measurement_type, range_val, resolution_val):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        command = f"CONFIGURE:{measurement_type} {range_val},{resolution_val}"
        self.instrument.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)
        print(f"\rConfiguration set for {measurement_type}: Range={range_val}, Resolution={resolution_val} on Keithley DMM6500 Digital Multimeter.")

    """
    Starts a measurement of n readings by enabling statistics, setting the number of readings, and initiating the measurement.
    
    Args:
        n (int): The number of readings to be performed.

    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.
    
    Example usage:
        multimeter.start_measurement(100)
    """
    def start_measurement(self, n):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        # Enable statistics
        self.instrument.write("CALCULATE:AVERAGE:STATE ON")
        self.loading.delay_with_loading_indicator(_DELAY)
        # Set the number of readings
        self.instrument.write(f"SAMPLE:COUNT {n}")
        self.loading.delay_with_loading_indicator(_DELAY)
        # Initiate the measurement
        self.instrument.write("INIT")
        self.loading.delay_with_loading_indicator(_DELAY)
        print(f"\rMeasurement of {n} readings started on Keithley DMM6500 Digital Multimeter.")

    """
    Performs the CALCULATE:AVERAGE:ALL command and returns the result as a list average, standard deviation, minimum, and maximum values.
    
    Returns:
        list: A list containing the average, standard deviation, minimum, and maximum values of the measurement.
    
    Raises:
        ConnectionError: If not connected to Keithley DMM6500 Digital Multimeter.
        
    Example usage:
        result = multimeter.calculate_average_all()
        print(f"Average: {result[0]}, Std Deviation: {result[1]}, Min: {result[2]}, Max: {result[3]}")
    """
    def calculate_statistics(self):

        if not self.status == "Connected":
            error_message = "Not connected to Keithley DMM6500 Digital Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)

        self.instrument.write("CALCULATE:AVERAGE:ALL?")
        self.loading.delay_with_loading_indicator(_DELAY)
        response = self.instrument.read()
        self.loading.delay_with_loading_indicator(_DELAY)
        values = response.split(',')

        result = [float(values[0]), float(values[1]), float(values[2]), float(values[3])]

        return result