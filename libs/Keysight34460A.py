#   @file Keysight34460A.py 
#   @brief Establishes a connection to the Keysight 34460A Multimeter and provides methods for interfacing.
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

"""
Establishes a connection to the Keysight 34460A Multimeter and provides methods for interfacing.

Example usage:
    multimeter = Keysight34460A("TCPIP0::192.168.1.1::INSTR")
    multimeter.connect()
    voltage = multimeter.measure_voltage()
    print(f"Measured voltage: {voltage} V")
"""
class Keysight34460A:

    """
    Initializes an instance of the Keysight34460A class.
    
    Example usage:
        multimeter = Keysight34460A()
    """
    def __init__(self, auto_connect=True):
        
        color = init(autoreset=True)

        self.rm = pyvisa.ResourceManager()
        self.address = None
        self.instrument = None

        self.status = "Not Connected"
        
        if auto_connect:
            self.connect()
        
    """
    Establishes a connection to the Keysight 34460A Multimeter.
    
    Example usage:
        multimeter.connect()
    """
    def connect(self):
        
        resources = self.rm.list_resources()
        for resource in resources:
            if 'MY59' in resource:
                self.address = resource
                break
        
        if self.address is None:
            print(Fore.RED + "Keysight 34460A Multimeter not found." + Style.RESET_ALL)
            return
        
        try:
            self.instrument = self.rm.open_resource(self.address)
            self.instrument.read_termination = '\n'
            print(Fore.GREEN + f"Connected to Keysight 34460A Multimeter at {self.address}" + Style.RESET_ALL)
            self.status = "Connected"
        except pyvisa.Error as e:
            print(Fore.RED + f"Error! Failed to connect to Keysight 34460A Multimeter at {self.address}: {e}" + Style.RESET_ALL)
            
    """
    Disconnects from the Keysight 34460A Multimeter.
    
    Example usage:
        multimeter.disconnect()
    """
    def disconnect(self):
        
        if self.instrument is not None:
            self.instrument.close()
            print(f"Disconnected from Keysight 34460A Multimeter at {self.address}")
            self.status = "Not Connected"

    """
    Retrieves the specified value.
    
    Args:
        item (str): The measurement item to retrieve. Valid values are "STAT", "CURR", or "VOLT".
        channel (int, optional): The channel number for the measurement.
           Defaults to 1.
    
    Returns:
        The measurement result corresponding to the specified item and channel.
    
    Example usage:
        voltage = multimeter.get("VOLT", channel=2)
        print(f"Voltage on channel 2: {voltage} V")
    """
    def get(self, item, channel=1):
    
        items = {
            "statistics": self.calculate_statistics,
            "current": self.read_current,
            "voltage": self.read_voltage
        }

        if item in items:
            result = items[item](channel)
            return result
        else:
            print(Fore.RED + f"Error! Invalid item: {item} request to Keysight 34460A Multimeter")
            return None
        
    """
    Reads and returns the voltage measurement.
    
    Returns:
        float: The measured voltage value.
    
    Example usage:
        voltage = multimeter.read_voltage()
        print(f"Voltage: {voltage} V")
    """
    def read_voltage(self):

        if self.instrument is not None:
            self.instrument.write("MEASURE:VOLTAGE:DC?")
            voltage = self.instrument.read()
            return float(voltage)
        else:
            print(Fore.RED +"Error! Not connected to Keysight 34460A Multimeter.")
            return None

    """
    Reads and returns the current measurement.
    
    Returns:
        float: The measured current value.
    
    Example usage:
        current = multimeter.current()
        print(f"Current: {current} A")
    """
    def read_current(self):

        if self.instrument is not None:
            self.instrument.write("MEASURE:CURRENT:DC?")
            current = self.instrument.read()
            return float(current)
        else:
            print(Fore.RED +"Error! Not connected to Keysight 34460A Multimeter.")
            return None
        
    """
    Disables the autorange feature for voltage and current measurements.
    
    Example usage:
        multimeter.disable_autorange()
    """
    def disable_autorange(self):

        if self.instrument is not None:
            self.instrument.write("VOLTAGE:DC:RANGE:AUTO OFF")
            self.instrument.write("CURRENT:DC:RANGE:AUTO OFF")
            print("Autorange disabled on Keysight 34460A Multimeter.")
        else:
            print(Fore.RED +"Error! Not connected to Keysight 34460A Multimeter.")

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
            |  Frequency         |   FREQUENCY     |
            |  Period            |   PERIOD        |
            |  Capacitance       |   CAPACITANCE   |
            |  Diode Test        |   DIODE         |
            |  Temperature       |   TEMPERATURE   |
            +--------------------+-----------------+
        range_val (float): The desired range value for the measurement type, specified in the measurement's units (V, A, Hz, Ohms, etc).
        resolution_val (float): The desired resolution value for the measurement type, specified in the measurement's units (V, A, Hz, Ohms, etc).
    
    Note:
        The range and resolution values are dependent on the specific capabilities of the Keysight 34460A Multimeter.
    
    Example usage:
        # Configure DC voltage measurement with a range of 10V and a resolution of 0.001V. 
        multimeter.configure("VOLTAGE:DC", 10.0, 0.001) 
    
        # Configure DC current measurement with a range of 1A and a resolution of 0.0001A.
        multimeter.configure("CURRENT:DC", 1.0, 0.0001)
    """
    def configure(self, measurement_type, range_val, resolution_val):

        if self.instrument is not None:
            command = f"CONFIGURE:{measurement_type} {range_val},{resolution_val}"
            self.instrument.write(command)
            print(f"Configuration set for {measurement_type}: Range={range_val}, Resolution={resolution_val} on Keysight 34460A Multimeter.")
        else:
            print(Fore.RED +"Error! Not connected to Keysight 34460A Multimeter.")

    """
    Starts a measurement of n readings by enabling statistics, setting the number of readings, and initiating the measurement.
    
    Args:
        n (int): The number of readings to be performed.
    
    Example usage:
        multimeter.start_measurement(100)
    """
    def start_measurement(self, n):

        if self.instrument is not None:
            # Enable statistics
            self.instrument.write("CALCulate:AVERage:STAT ON")
            # Set the number of readings
            self.instrument.write(f"SAMPle:COUNt {n}")
            # Initiate the measurement
            self.instrument.write("INIT")
            print(f"Measurement of {n} readings started on Keysight 34460A Multimeter.")
        else:
            print(Fore.RED +"Error! Not connected to Keysight 34460A Multimeter.")

    """
    Performs the CALCulate:AVERage:ALL command and returns the result as a namedtuple with average, standard deviation, minimum, and maximum values.
    
    Returns:
        namedtuple: An namedtuple with the calculated average, standard deviation, minimum, and maximum values.
    
    Example usage:
        result = multimeter.calculate_average_all()
        print(f"Average: {result.Average}, Std Deviation: {result.StdDev}, Min: {result.Min}, Max: {result.Max}")
    """
    def calculate_statistics(self):

        if self.instrument is not None:
            self.instrument.write("CALCulate:AVERage:ALL?")
            response = self.instrument.read()
            values = response.split(',')

            # Create a namedtuple to store the result values
            Result = namedtuple('Result', ['Average', 'StdDev', 'Min', 'Max'])
            result = Result(float(values[0]), float(values[1]), float(values[2]), float(values[3]))

            return result
        else:
            print(Fore.RED +"Error! Not connected to Keysight 34460A Multimeter.")
            return None