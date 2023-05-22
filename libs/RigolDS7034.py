#   @file RigolDS7034.py
#   @brief Establishes a connection to the Rigol DS7034 Oscilloscope
#       and provides methods for interacting with the device.
#   @date 21-May-2023
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
import time
import statistics
import numpy
from colorama import init, Fore, Back, Style
from .loading import *

# Constants and global variables
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_DELAY = 0.1 #seconds

class RigolDS7034:

    """
    Initializes an instance of the RigolDS7034 class.
    """
    def __init__(self, auto_connect=True):
        
        init(autoreset=True)

        self.rm = pyvisa.ResourceManager()
        self.address = None
        self.instrument = None

        self.status = "Not Connected"
        
        if auto_connect:
            self.connect()

    """
    Establishes a connection to the Rigol DS7034 Oscilloscope.

    Raises:
        ConnectionError: If unable to connect to Rigol DS7034 Oscilloscope.
    
    Example usage:
        oscilloscope.connect()
    """
    def connect(self):

        resources = self.rm.list_resources()
        for resource in resources:
            if 'DS7' in resource:
                self.address = resource
                break

        if self.address is None:
            error_message = "Rigol DS7034 Oscilloscope not found."
            raise ConnectionError(_ERROR_STYLE + error_message)

        try:
            self.instrument = self.rm.open_resource(self.address)
            self.instrument.read_termination = '\n'
            self.status = "Connected"
            success_message = f"Connected to Rigol DS7034 Oscilloscope at {self.address}"
            print(_SUCCESS_STYLE + success_message)

        except pyvisa.Error as e:
            error_message = f"Error! Failed to connect to Rigol DS7034 Oscilloscope at {self.address}: {e}"
            raise ConnectionError(_ERROR_STYLE + error_message)

    
    """
    Disconnects from the Rigol DS7034 Oscilloscope.
    
    Example usage:
        oscilloscope.disconnect()
    """
    def disconnect(self):
        
        if self.instrument is not None:
            self.instrument.close()
            print(f"\rDisconnected from Rigol DS7034 Oscilloscope at {self.address}")
            self.status = "Not Connected"

    """
    Retrieves the specified value.
    
    Args:
        item (str): The measurement item to retrieve.
        channel (int, optional): The channel number for the measurement.
           Defaults to 1.
    
    Returns:
        The measurement result corresponding to the specified item and channel.

    Raises:
        ValueError: If an invalid item is requested.
    
    Example usage:
        measurement = oscilloscope.get("VAVG", channel=2)
        print(f"Measurement for VAVG on channel 2: {measurement}")
    """
    def get(self,item,channel=1):

        items = { "VAVG"        :self.read_item,
                  "VMAX"        :self.read_item,
                  "VMIN"        :self.read_item,
                  "VAVG_STAT"   :self.read_stat,
                  "VMAX_STAT"   :self.read_stat,
                  "VPP_STAT"    :self.read_stat,
                  "PDUT_STAT"   :self.read_stat,
                  "FREQ_STAT"   :self.read_stat,
                  "RFD_STAT"    :self.read_stat,
                  "RRD_STAT"    :self.read_stat,
                  "VMIN_STAT"   :self.read_stat,
                  "PSL_STAT"    :self.read_stat,
                  "NSL_STAT"    :self.read_stat,
                  "VTOP_STAT"   :self.read_stat,
                  "VBAS_STAT"   :self.read_stat 
        }

        if item in items:
            if "_STAT" in item:
                item_x = item[:item.find("_STAT")]
                result = items[item](item_x, f'CHAN{channel}')
            else:
                result = items[item](item, f'CHAN{channel}')
            return result
        else:
            error_message = f"Invalid item: {item} request to Rigol DS7034 oscilloscope"
            raise ValueError(_ERROR_STYLE + error_message)
        

        
    """
    Measures the waveform parameter of the specified source.

    Args:
        item (str): The measurement item to retrieve.
            +----------+-----------------------+    +---------+--------------------------+
            |   Item   |      Description      |    |  Item   |       Description        |
            +==========+=======================+    +=========+==========================+
            |   VMAX   | Maximum voltage       |    | RRDelay | Rising-to-rising delay   |
            |   VMIN   | Minimum voltage       |    | RFDelay | Rising-to-falling delay  |
            |   VPP    | Peak-to-peak voltage  |    | FRDelay | Falling-to-rising delay  |
            |   VTOP   | Top voltage           |    | FFDelay | Falling-to-falling delay |
            |   VBASE  | Base voltage          |    | RRPHase | Rising-to-rising phase   |
            |   VAMP   | Amplitude voltage     |    | RFPHase | Rising-to-falling phase  |
            |   VAVG   | Average voltage       |    | FRPHase | Falling-to-rising phase  |
            |   VRMS   | RMS voltage           |    | FFPHase | Falling-to-falling phase |
            +----------+-----------------------+    +---------+--------------------------+
        source (str): The source to measure.
            +----------+-----------------------+
            |  Source  |      Description      |
            +----------+-----------------------+
            | D0       | Digital 0             |
            | D1       | Digital 1             |
            | D2       | Digital 2             |
            | ...      | ...                   |
            | D15      | Digital 15            |
            | CHANnel1 | Channel 1             |
            | CHANnel2 | Channel 2             |
            | CHANnel3 | Channel 3             |
            | CHANnel4 | Channel 4             |
            | MATH1    | Math 1                |
            | MATH2    | Math 2                |
            | MATH3    | Math 3                |
            | MATH4    | Math 4                |
            +----------+-----------------------+

    Returns:
        The measurement result corresponding to the specified item and source.

    Raises:
        ConnectionError: If not connected to Rigol DS7034 Oscilloscope.
        ValueError: If an invalid item or source is requested.

    Example usage:
        voltage = oscilloscope.measure_item()
        print(f"Voltage: {voltage} V")
    """
    def read_item(self, item, source):

        if isinstance(source, int) and 1 <= source <= 4:
            source = f"CHANnel{source}"
        elif not isinstance(source, str):
            raise ValueError("Invalid source. Must be a string or an integer between 1 and 4.")

        if self.instrument is not None:
            command = f"MEASURE:ITEM? {item},{source}"
            value = self.instrument.read()
            print(value)
            return float(value)
        else:
            error_message = "Not connected to Rigol DS7034 Oscilloscope."
            raise ConnectionError(_ERROR_STYLE + error_message)