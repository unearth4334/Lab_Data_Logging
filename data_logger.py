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
import os
import traceback
import time
from colorama import init, Fore, Back, Style
from .libs.DL3021 import *
from .libs.DP832 import *
from .libs.DS7034 import *
from .libs.FLUKE45 import *
from .libs.KA3010P import *
from .libs.KS33500B import *
from .libs.Keysight34460A import *
from .libs.U1233A import *
from .libs.DAC import *
from .libs.EPS import *

# Constants and global variables
_MAX_TRIES = 100
_OUTPUT_DIRECTORY = "/path/to/output"
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "

"""
A class for data logging and measurement.

Example usage:

    logger = data_logger()
    logger.new_file("output.txt")
    multimeter = logger.connect("Keysight34460A")
    logger.add("Voltage", multimeter, "voltage")
    logger.add("Current", multimeter, "current")
    logger.get_data()
    logger.close_file()
"""
class data_logger:

    """
    Initializes an instance of the data_logger class.
    """
    def __init__(self):

        init(autoreset=True)
        self.labels   = []
        self.devices  = []
        self.items    = []
        self.channels = []

    """
    Establishes a connection to the specified device.
    
    Args:
        device (str): The name of the device to connect to.
    
    Returns:
        object: The connected device object.
    
    Raises:
        ValueError: If an invalid device name is provided.
    """ 
    def connect(self, device):


        devices = { "DL3021"         : DL3021,
                    "DP832"          : DP832,
                    "DS7034"         : DS7034,
                    "FLUKE45"        : FLUKE45,
                    "KA3010P"        : KA3010P,
                    "KS33500B"       : KS33500B,
                    "Keysight34460A" : Keysight34460A,
                    "U1233A"         : U1233A,
                    "DAC"            : DAC,
                    "EPS"            : EPS,
        }

        try:
            device_object = devices[device]()
            return device_object
        except KeyError:
            error_message = f"Invalid device input: '{device}'. Please provide a valid device name."
            raise ValueError(_ERROR_STYLE + error_message)
        

    """
    Add a device to the data logger.

    Args:
        label (str): The label for the device.
        device_object (object): The device object.
        item (str): The item to be measured.
        channel (int, optional): The channel number. Defaults to 1.

    Raises:
        ValueError: If the device is not connected.
    """
    def add(self, device_object, item, channel=1, label=None ):

        if label is None:
            # Generate label based on device name, item, and channel
            device_name = device_object.__class__.__name__
            label = f"{device_name}_{item}_{channel}"

        if device_object.status != 'Connected':
            error_message = f"Device '{label}' is not connected."
            raise ValueError(_ERROR_STYLE + error_message)
        else:
            self.labels.append(label)
            self.devices.append(device_object)
            self.items.append(item)
            self.channels.append(channel)
            

    """
    Writes the data from connected devices to a file.

    Args:
        print_to_terminal (bool, optional): Specifies whether to print the data to the terminal.
            Defaults to True.

    Raises:
        ValueError: If the file is not open or not writable, or if there is an error writing the data.
    """
    def get_data(self, print_to_terminal=True):
        try:
            if not hasattr(self, 'f') or not self.f.writable():
                print(_WARNING_STYLE + "No file is open...")
                return None

            # Check if the file is empty
            if self.f.tell() == 0:
                self.f.write('')
                for i, label in enumerate(self.labels):
                    self.f.write(f"{label}\t{label}_e")
                    if i != len(self.labels) - 1:
                        self.f.write('\t')
                self.f.write('\n')

            # Write data for each connected device
            for i, device in enumerate(self.devices):
                try:
                    value = device.get(self.items[i], self.channels[i])
                    self.f.write('%.10f\t%.10f' % (value[0], value[1]))
                    if i != len(self.devices) - 1:
                        self.f.write('\t')
                    if print_to_terminal:
                        label_padding = ' ' * (max_label_length - len(self.labels[i]))
                        print(f"{Fore.BLACK}{self.labels[i]}{label_padding}\t{Back.BLUE}{Fore.WHITE} %.4f +/- %.4f "\
                            % (value[0], value[1]))
                except:
                    pass

            self.f.write('\n')
        except IOError:
            error_message = f"Failed to write data to the file '{self.filename}'."
            raise ValueError(_ERROR_STYLE + error_message)
        
    
    def __find_next_filename(self, name, max_tries=_MAX_TRIES):
        """
        Finds the next available filename by appending a number to the base filename.

        Args:
            name (str): The base filename.
            max_tries (int, optional): The maximum number of tries to find an available filename. Defaults to _MAX_TRIES.

        Returns:
            str: The next available filename.

        Raises:
            ValueError: If an available filename cannot be found after the maximum number of tries.
        """

        root, ext = os.path.splitext(name)
        for i in range(max_tries):
            test_name = f"{root}{i+1}{ext}"
            if not os.path.exists(test_name):
                return test_name

        # If an available filename is not found after the maximum number of tries, raise an exception
        error_message = (
            f"Failed to find an available filename after {max_tries} tries. "
            "Please clean up the output files or increase 'max_tries' value."
        )
        raise ValueError(_ERROR_STYLE + error_message)
    
        
    """
    Opens a new file for writing data.

    Args:
        filename (str, optional): The name of the file. Defaults to 'data.txt'.

    Raises:
        ValueError: If there is an error opening the file.
    """
    def new_file(self, filename = 'data.txt'):

        try:
            if hasattr(self, 'f') and self.f.writable():
                self.f.close()
                print(Fore.YELLOW + f"Closed file '{self.filename}'.")

            # Generate a new filename if the provided one already exists
            self.filename = self.__find_next_filename(filename)
            
            # Open the file in write mode
            self.f = open(self.filename, 'w')
            print(Fore.GREEN + f"Opened file '{self.filename}'.")
        except:
            # Raise an exception if there is an error opening the file
            error_message = f"Failed to open file '{self.filename}'."
            raise ValueError(_ERROR_STYLE + error_message)


    """
    Closes the filestream and saves the file.

    If a filestream is available and writable, the function closes the filestream and prints a success message.
    If no filestream is available or it is not writable, a warning message is printed.

    Raises:
        ValueError: If an error occurs while saving the file.
    """
    def close_file(self):

        try:
            if self.f.writable():
                self.f.close()
                print(Fore.GREEN + f"File '{self.filename}' saved.")
            else:
                print(_WARNING_STYLE + "No filestream available to save.")
        except Exception:
            error_message = f"Failed to save file '{self.filename}'."
            raise ValueError(_ERROR_STYLE + error_message)