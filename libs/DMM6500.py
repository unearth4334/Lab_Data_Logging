#   @file DMM6500.py 
#   @brief Establishes a connection to the Keysight DMM6500 Multimeter
#       and provides methods for interfacing with the device.
#   @date 5-Dec-2024
#   @author GitHub Copilot
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
import inspect
import re
import pyvisa
from enum import Enum
from typing import Callable
from colorama import init, Fore, Style
try:
    from .loading import *
except:
    from loading import *

# Constants and global variables
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT  + "\r"
_DELAY = 0.1


class Function(Enum):
    DC_VOLTAGE = 'VOLT:DC'
    AC_VOLTAGE = 'VOLT:AC'
    DC_CURRENT = 'CURR:DC'
    AC_CURRENT = 'CURR:AC'
    RESISTANCE = 'RES'
    FOUR_WIRE_RESISTANCE = 'FRES'
    DIODE = 'DIO'
    CAPACITANCE = 'CAP'
    TEMPERATURE = 'TEMP'
    CONTINUITY = 'CON'
    FREQUENCY = 'FREQ'
    PERIOD = 'PER'
    VOLTAGE_RATIO = 'VOLT:RAT'

    def __str__(self):
        return self.value


class Screen(Enum):
    HOME = 'HOME'
    HOME_LARGE = 'HOME_LARGE_READING'
    READING_TABLE = 'READING_TABLE'
    GRAPH = 'GRAPH'
    HISTOGRAM = 'HISTOGRAM'
    SWIPE_FUNCTIONS = 'SWIPE_FUNCTIONS'
    SWIPE_GRAPH = 'SWIPE_GRAPH'
    SWIPE_SECONDARY = 'SWIPE_SECONDARY'
    SWIPE_SETTINGS = 'SWIPE_SETTINGS'
    SWIPE_STATISTICS = 'SWIPE_STATISTICS'
    SWIPE_USER = 'SWIPE_USER'
    SWIPE_CHANNEL = 'SWIPE_CHANNEL'
    SWIPE_NONSWITCH = 'SWIPE_NONSWITCH'
    SWIPE_SCAN = 'SWIPE_SCAN'
    CHANNEL_CONTROL = 'CHANNEL_CONTROL'
    CHANNEL_SETTINGS = 'CHANNEL_SETTINGS'
    CHANNEL_SCAN = 'CHANNEL_SCAN'
    PROCESSING = 'PROCESSING'

    def __str__(self):
        return self.value


query_templates = {
    # commands
    'reset':                    ['*RST'],
    'measure':                  [':MEAS?', lambda s: float(s)],

    'clear_log':                [':SYST:CLEAR'],
    'system_error_next':        [':SYST:ERR:NEXT?', lambda s: _parse_log_event(s)],

    'clear_user_screen':        [':DISP:CLEAR'],
    'display_user_text':        [lambda line, text: f':DISP:USER{line}:TEXT "{text}"',
                                 lambda line: line if line in {1, 2} else None,
                                 lambda text: str(text)],

    # simple queries
    'detected_line_frequency':  [':SYST:LFR?', float],

    # setting of settings
    'set_function':             [':SENS:FUNC "{0}"', lambda val: str(val) if str(val) in list(map(str, Function)) else None],
    'set_screen':               [':DISP:SCREEN {0}', lambda val: str(val) if str(val) in list(map(str, Screen)) else None],

    'set_range':                [lambda v, mm_func: f':SENS:{mm_func}:RANG {v}' if v != 'auto' else f':SENS:{mm_func}:RANG:AUTO ON',
                                 lambda val: val if val == 'auto' or isinstance(val, (float, int)) else None],
}

sense_queries = {
    'set_auto_zero':            ['AZER {0}', lambda val: {False: 'OFF', True: 'ON'}.get(val, None)],
    'set_nplc':                 ['NPLC {0}', lambda val: float(val) if (0.0005 <= float(val) <= 12.0) else None],
}


def _sense_queries_transform(template):
    format_func = template[0]
    assert isinstance(format_func, str)
    return [':SENS:{mm_func}:' + format_func] + template[1:]


def _combined_queries(queries_templates,
                      _sense_queries):
    result = dict()
    result.update(queries_templates)
    result.update(dict((name, _sense_queries_transform(val)) for name, val in _sense_queries.items()))
    return result


def _parse_log_event(s):
    groups = re.fullmatch(r'([+\-\d]+),"(.+)"', s.strip()).groups()
    return int(groups[0]), groups[1]


def query_text(template, mm_state, values):
    formt = template[0]
    rest = template[1:]

    if isinstance(formt, Callable):
        param_info = inspect.signature(formt).parameters
        requires_mm_state = 'mm_func' in param_info
        no_required_args = len(param_info) - (1 if requires_mm_state else 0)
    else:
        requires_mm_state = formt.count('{mm_func}') == 1
        no_required_args = formt.count('{') - (1 if requires_mm_state else 0)

    parameter_convert_funcs = rest[:no_required_args]

    if no_required_args != len(values):
        raise ValueError

    if len(rest) > no_required_args:
        return_convert = rest[-1]
    else:
        return_convert = None

    query_type = 'write' if return_convert is None else 'query'

    converted_values = [f(v) for f, v in zip(parameter_convert_funcs, values)]
    if None in converted_values:
        raise ValueError

    if isinstance(formt, Callable):
        if requires_mm_state:
            return query_type, formt(*converted_values, mm_func=mm_state), return_convert
        else:
            return query_type, formt(*converted_values), return_convert
    else:
        return query_type, formt.format(*converted_values, mm_func=mm_state), return_convert


all_query_templates = _combined_queries(query_templates, sense_queries)


"""
Establishes a connection to the Keysight DMM6500 Multimeter and provides methods for interfacing.

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
        self.current_function = Function.DC_VOLTAGE

        self.status = "Not Connected"
        
        if auto_connect:
            self.connect()
        
    """
    Establishes a connection to the Keysight DMM6500 Multimeter.

    Raises:
        ConnectionError: If unable to connect to Keysight DMM6500 Multimeter.
    
    Example usage:
        multimeter.connect()
    """
    def connect(self):
        
        resources = self.rm.list_resources()
        for resource in resources:
            if 'DMM6500' in resource or '6500' in resource:
                self.address = resource
                break
        
        if self.address is None:
            error_message = "Keysight DMM6500 Multimeter not found."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
        try:
            self.instrument = self.rm.open_resource(self.address)
            self.instrument.read_termination = '\n'
            self.status = "Connected"
            success_message = f"Connected to Keysight DMM6500 Multimeter at {self.address}"
            print(_SUCCESS_STYLE + success_message)

        except Exception as e:
            error_message = f"Failed to connect to Keysight DMM6500 Multimeter at {self.address}: {e}"
            raise ConnectionError(_ERROR_STYLE + error_message)

    """
    Disconnects from the Keysight DMM6500 Multimeter.
    
    Example usage:
        multimeter.disconnect()
    """
    def disconnect(self):
        
        if self.instrument is not None:
            self.instrument.close()
            print(f"\rDisconnected from Keysight DMM6500 Multimeter at {self.address}")
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
            error_message = f"Invalid item: {item} request to Keysight DMM6500 Multimeter"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Executes a query using the template system and returns the result.
    
    Args:
        query_name (str): The name of the query template to use.
        *values: Values to pass to the query template.
    
    Returns:
        The result of the query, processed according to the template.
    
    Raises:
        ConnectionError: If not connected to the multimeter.
        ValueError: If the query is invalid.
    """
    def execute_query(self, query_name, *values):
        
        if not self.status == "Connected":
            error_message = "Not connected to Keysight DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
        if query_name not in all_query_templates:
            error_message = f"Unknown query: {query_name}"
            raise ValueError(_ERROR_STYLE + error_message)
        
        template = all_query_templates[query_name]
        query_type, command, return_convert = query_text(template, str(self.current_function), values)
        
        if query_type == 'write':
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            return None
        else:
            self.instrument.write(command)
            self.loading.delay_with_loading_indicator(_DELAY)
            response = self.instrument.read().strip()
            
            if return_convert:
                return return_convert(response)
            else:
                return response

    """
    Measures the current voltage.
    
    Returns:
        float: The measured voltage value.
    
    Raises:
        ConnectionError: If not connected to the multimeter.
    """
    def measure_voltage(self):
        
        if not self.status == "Connected":
            error_message = "Not connected to Keysight DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
        # Set function to DC voltage if not already set
        self.current_function = Function.DC_VOLTAGE
        self.execute_query('set_function', str(self.current_function))
        
        # Measure voltage
        result = self.execute_query('measure')
        return result

    """
    Measures the current.
    
    Returns:
        float: The measured current value.
    
    Raises:
        ConnectionError: If not connected to the multimeter.
    """
    def measure_current(self):
        
        if not self.status == "Connected":
            error_message = "Not connected to Keysight DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
        # Set function to DC current if not already set
        self.current_function = Function.DC_CURRENT
        self.execute_query('set_function', str(self.current_function))
        
        # Measure current
        result = self.execute_query('measure')
        return result

    """
    Calculates statistics for the current measurements.
    
    Returns:
        list: A list containing [average, std_dev, min, max] values.
    
    Raises:
        ConnectionError: If not connected to the multimeter.
    """
    def calculate_statistics(self):
        
        if not self.status == "Connected":
            error_message = "Not connected to Keysight DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
        # For DMM6500, use proper SCPI commands for statistics
        # This fixes the SCPI error by using the correct command syntax
        try:
            self.instrument.write(":CALC:AVER:ALL?")
            self.loading.delay_with_loading_indicator(_DELAY)
            response = self.instrument.read().strip()
            
            values = response.split(',')
            if len(values) >= 4:
                result = [float(values[0]), float(values[1]), float(values[2]), float(values[3])]
                return result
            else:
                # Fallback to individual queries if combined query fails
                self.instrument.write(":CALC:AVER:AVER?")
                self.loading.delay_with_loading_indicator(_DELAY)
                avg = float(self.instrument.read().strip())
                
                self.instrument.write(":CALC:AVER:SDEV?")
                self.loading.delay_with_loading_indicator(_DELAY)
                sdev = float(self.instrument.read().strip())
                
                self.instrument.write(":CALC:AVER:MIN?")
                self.loading.delay_with_loading_indicator(_DELAY)
                min_val = float(self.instrument.read().strip())
                
                self.instrument.write(":CALC:AVER:MAX?")
                self.loading.delay_with_loading_indicator(_DELAY)
                max_val = float(self.instrument.read().strip())
                
                return [avg, sdev, min_val, max_val]
                
        except Exception as e:
            error_message = f"Error retrieving statistics: {e}"
            raise ValueError(_ERROR_STYLE + error_message)

    """
    Sets the measurement function.
    
    Args:
        function (Function): The measurement function to set.
    
    Raises:
        ConnectionError: If not connected to the multimeter.
    """
    def set_function(self, function):
        
        if not self.status == "Connected":
            error_message = "Not connected to Keysight DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
        self.current_function = function
        self.execute_query('set_function', str(function))

    """
    Resets the instrument to its default state.
    
    Raises:
        ConnectionError: If not connected to the multimeter.
    """
    def reset(self):
        
        if not self.status == "Connected":
            error_message = "Not connected to Keysight DMM6500 Multimeter."
            raise ConnectionError(_ERROR_STYLE + error_message)
        
        self.execute_query('reset')
        self.current_function = Function.DC_VOLTAGE