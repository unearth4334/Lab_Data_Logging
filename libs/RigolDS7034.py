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

        items = { "VAVG"        :self.measure_item,
                  "VMAX"        :self.measure_item,
                  "VMIN"        :self.measure_item,
                  "VAVG_STAT"   :self.measure_statistic_item,
                  "VMAX_STAT"   :self.measure_statistic_item,
                  "VPP_STAT"    :self.measure_statistic_item,
                  "PDUT_STAT"   :self.measure_statistic_item,
                  "FREQ_STAT"   :self.measure_statistic_item,
                  "RFD_STAT"    :self.measure_statistic_item,
                  "RRD_STAT"    :self.measure_statistic_item,
                  "VMIN_STAT"   :self.measure_statistic_item,
                  "PSL_STAT"    :self.measure_statistic_item,
                  "NSL_STAT"    :self.measure_statistic_item,
                  "VTOP_STAT"   :self.measure_statistic_item,
                  "VBAS_STAT"   :self.measure_statistic_item 
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
    Determines if the specified item is a valid measurement item.

    Args:
        item (str): The measurement item to check. Valid items are:
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

    Returns:
        True if the item is valid, False otherwise.
    """
    def __is_valid_item(self,item):

        valid_items = ["VMAX", "VMIN", "VPP", "VTOP", "VBASE", "VAMP", "VAVG", "VRMS",
                    "OVERshoot", "PREShoot", "MARea", "MPARea", "PERiod", "FREQuency",
                    "RTIMe", "FTIMe", "PWIDth", "NWIDth", "PDUTy", "NDUTy", "TVMax",
                    "TVMin", "PSLewrate", "NSLewrate", "VUPPer", "VMID", "VLOWer",
                    "VARiance", "PVRMs", "PPULses", "NPULses", "PEDGes", "NEDGes",
                    "RRDelay", "RFDelay", "FRDelay", "FFDelay", "RRPHase", "RFPHase",
                    "FRPHase", "FFPHase"]
        
        item_upper = item.upper()
        
        # Check if the item is a valid item or its alias
        for valid_item in valid_items:
            if item_upper == valid_item.upper() or (valid_item.startswith(item_upper) and valid_item[len(item_upper)].islower() ): 
                return True

        return False

    """
    Determines if the specified source is a valid source.

    Args:
        source (str): The source to check. Valid sources are:
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
        True if the source is valid, False otherwise.
    """
    def __is_valid_source(self, source):
        valid_sources = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9",
                        "D10", "D11", "D12", "D13", "D14", "D15", "CHANNEL1","CHAN1" "CHANNEL2","CHAN2"
                        "CHANNEL3","CHAN3" "CHANNEL4","CHAN4" "MATH1", "MATH2", "MATH3", "MATH4"]

        if source.upper() in valid_sources:
            return True
        
        return False
    
    """
    Determines if the specified statistic type is valid.

    Args:
        type (str): The statistic type to check. Valid statistic types are:
            +-----------+-----------------------+
            |  Type     |      Description      |
            +-----------+-----------------------+
            | MAXimum   | Maximum               |
            | MINimum   | Minimum               |
            | CURRent   | Current               |
            | AVERages  | Average               |
            | DEViation | Standard deviation    |
            +-----------+-----------------------+
    Returns:
        True if the statistic type is valid, False otherwise.
    """
    def __is_valid_statistic_type(self, type):
        valid_types = ["MAXimum", "MINimum", "CURRent", "AVERages", "DEViation"]

        type_upper = type.upper()
        
        # Check if the item is a valid statistic type or its alias
        for valid_type in valid_types:
            if type_upper == valid_type.upper() or (valid_type.startswith(type_upper) and valid_type[len(type_upper)].islower() ):
                return True

        return False
        

    """
    Measures the waveform parameter of the specified source.

    Args:
        item (str): The measurement item to retrieve.
        source (str): The source to measure.

    Returns:
        The measurement result corresponding to the specified item and source.

    Raises:
        ConnectionError: If not connected to Rigol DS7034 Oscilloscope.
        ValueError: If an invalid item or source is requested.

    Example usage:
        voltage = oscilloscope.measure_item()
        print(f"Voltage: {voltage} V")
    """
    def measure_item(self, item, source):

        if isinstance(source, int) and 1 <= source <= 4:
            source = f"CHANnel{source}"
        
        if not self.__is_valid_item(item):
            error_message = f"Invalid item: \"{item}\" request to Rigol DS7034 Oscilloscope. Check the documentation."
            raise ValueError(_ERROR_STYLE + error_message)
        
        if not self.__is_valid_source(source):
            error_message = f"Invalid source: \"{source}\" request to Rigol DS7034 Oscilloscope. Check the documentation."
            raise ValueError(_ERROR_STYLE + error_message)

        if self.instrument is not None:
            command = f"MEASURE:ITEM? {item},{source}"
            value = self.instrument.query(command)
            return float(value)
        else:
            error_message = "Not connected to Rigol DS7034 Oscilloscope."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
    """
    Returns the specified measurement statistics of the specified waveform parameter.

    Args:
        item (str): The measurement item to retrieve.
        source (str): The source to measure.
        types (set): The set of statistic types to retrieve.

    Returns:
        The measurement result corresponding to the specified item and source.

    Raises:
        ConnectionError: If not connected to Rigol DS7034 Oscilloscope.
        ValueError: If an invalid item, source, or statistic type is requested.
    """
    def measure_statistic_item(self, item, source, types = {"AVERages","DEViation"}):
            
            if isinstance(source, int) and 1 <= source <= 4:
                source = f"CHANnel{source}"
            
            if not self.__is_valid_item(item):
                error_message = f"Invalid item: \"{item}\" request to Rigol DS7034 Oscilloscope. Check the documentation."
                raise ValueError(_ERROR_STYLE + error_message)
            
            if not self.__is_valid_source(source):
                error_message = f"Invalid source: \"{source}\" request to Rigol DS7034 Oscilloscope. Check the documentation."
                raise ValueError(_ERROR_STYLE + error_message)

            if self.instrument is not None:
                values = []
                for type in types:
                    if not self.__is_valid_statistic_type(type):
                        error_message = f"Invalid statistic type: \"{type}\" request to Rigol DS7034 Oscilloscope. Check the documentation."
                        raise ValueError(_ERROR_STYLE + error_message)

                    command = f"MEASURE:STAT:ITEM? {type},{item},{source}"
                    value = self.instrument.query(command)
                    values.append(float(value))
                return values
            else:
                error_message = "Not connected to Rigol DS7034 Oscilloscope."
                raise ConnectionError(_ERROR_STYLE + error_message)


    """
    Enables statistics for the specified waveform parameter of the specified source.

    Args:
        item (str): The measurement item to retrieve.
        source (str): The source to measure.

    Raises:
        ConnectionError: If not connected to Rigol DS7034 Oscilloscope.
        ValueError: If an invalid item or source is requested.
    """
    def enable_statistic_item(self, item, source):

        if isinstance(source, int) and 1 <= source <= 4:
            source = f"CHANnel{source}"
        
        if not self.__is_valid_item(item):
            error_message = f"Invalid item: \"{item}\" request to Rigol DS7034 Oscilloscope. Check the documentation."
            raise ValueError(_ERROR_STYLE + error_message)
        
        if not self.__is_valid_source(source):
            error_message = f"Invalid source: \"{source}\" request to Rigol DS7034 Oscilloscope. Check the documentation."
            raise ValueError(_ERROR_STYLE + error_message)

        if self.instrument is not None:
            command = f"MEASURE:STAT:ITEM {item},{source}"
            self.instrument.write(command)
        else:
            error_message = "Not connected to Rigol DS7034 Oscilloscope."
            raise ConnectionError(_ERROR_STYLE + error_message)

    """
    Resets the statistics for all measurement items.

    Raises:
        ConnectionError: If not connected to Rigol DS7034 Oscilloscope.
    """
    def reset_statistics(self):
        if self.instrument is not None:
            command = "MEASURE:STAT:RESET"
            self.instrument.write(command)
        else:
            error_message = "Not connected to Rigol DS7034 Oscilloscope."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
    """
    Clears any one or all 10 of the measurement items that have been turned on.

    Args:
        item_n (str): The measurement item to clear.
    
    Raises:
        ConnectionError: If not connected to Rigol DS7034 Oscilloscope.
        ValueError: If an invalid item is requested.
    """
    def clear_measure_item(self, item_n):
        # item_n : {ITEM1|ITEM2|ITEM3|ITEM4|ITEM5|ITEM6|ITEM7|ITEM8|ITEM9|ITEM10|ALL}
        if isinstance(item_n, int) and 1 <= item_n <= 10:
            item_n = f"ITEM{item_n}"
        item_n_upper = item_n.upper()
        if item_n_upper in {"ITEM1","ITEM2","ITEM3","ITEM4","ITEM5","ITEM6","ITEM7","ITEM8","ITEM9","ITEM10","ALL"}:
            if self.instrument is not None:
                command = f"MEASURE:CLE {item_n}"
                self.instrument.write(command)
            else:
                error_message = "Not connected to Rigol DS7034 Oscilloscope."
                raise ConnectionError(_ERROR_STYLE + error_message)
        else:
            error_message = f"Invalid item: \"{item_n}\" request to Rigol DS7034 Oscilloscope. Check the documentation."
            raise ValueError(_ERROR_STYLE + error_message)