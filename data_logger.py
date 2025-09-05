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
from libs.DL3021 import *
from libs.RigolDP832 import *
from libs.RigolDS7034 import *
from libs.FLUKE45 import *
from libs.KA3010P import *
from libs.KS33500B import *
from libs.Keysight34460A import *
from libs.U1233A import *
from libs.DAC import *
from libs.EPS import *
from libs.DMM6500 import *
from libs.loading import *


# Constants and global variables
_MAX_FILENAMES = 100
_VALUE_PADDING = 40
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
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
        self.max_label_length = 0
        self.beginnning_of_file = True
        self.file_open = False
        self.start_time = time.time()
        self.filename_warning_given = False
        self.loading = loading()

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

        devices = { "dl3021"         : DL3021,
                    "rigoldp832"     : RigolDP832,
                    "rigolds7034"    : RigolDS7034,
                    "fluke45"        : FLUKE45,
                    "ka3010p"        : KA3010P,
                    "ks33500b"       : KS33500B,
                    "keysight34460a" : Keysight34460A,
                    "u1233a"         : U1233A,
                    "dac"            : DAC,
                    "eps"            : EPS,
                    "dmm6500"        : DMM6500
        }

        try:
            device_object = devices[device.lower()]()
            return device_object
        except KeyError:
            error_message = f"Invalid device input: '{device}'. Please provide a valid device name. Check the documentation."
            raise ValueError(_ERROR_STYLE + error_message)
        

    """
    Add a device to the data logger.

    Args:
        device_object (object): The device object.
        item (str): The item to be measured.
        channel (int, optional): The channel number. Defaults to None.
        label (str, optional): The label for the data. Defaults to None.
            If no label is provided, the label will be generated based on the device name, item, and channel.

    Raises:
        ConnectionError: If the device is not connected.
        ValueError: If there is an error getting the data.
    """
    def add(self, device_object, item, channel=None, label=None):


        # if beginnning_of_file = False, warn the user that they cannot add measurement items to the open file. Give them the option to save the current file and create a new one, or to cancel the operation.
        if not self.beginnning_of_file:
            warning_message = "Cannot add measurement items to the current file. Would you like to save the current file and create a new one? (y/n)"
            print(_WARNING_STYLE + warning_message)
            user_input = self.loading.input_with_flashing()
            if user_input.lower() == 'y':
                self.new_file()
            else:
                print(_WARNING_STYLE + "Operation cancelled.")

        device_name = device_object.__class__.__name__

        if label is None:
            # Generate label based on device name, item, and channel
            device_name = device_object.__class__.__name__
            
            if device_object is time:
                if item.lower() == "current" and label is None:
                    label = "Current_Time-GMT"
                elif item.lower() == "elapsed" and label is None:
                    label = "Elapsed_Time"
            elif channel is None:
                label = f"{device_name}_{item.upper()}"
            else:
                label = f"{device_name}_{item.upper()}_{str(channel).upper()}"

        if device_object is time:
            self.labels.append(label)
            self.devices.append(time)
            self.items.append(item)
            self.channels.append(None)

        elif device_object.status != 'Connected':
            error_message = f"Device '{device_name}' is not connected."
            raise ConnectionError(_ERROR_STYLE + error_message)
        else:
            self.max_label_length = max(self.max_label_length, len(label))
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
        IOError: If the file is not open or not writable, or if there is an error writing the data.
    """
    def get_data(self, print_to_terminal=True):

        try:
            if not self.file_open:
                warning_message = "No file is open. Would you like to create a new file? (y/n)"
                print(_WARNING_STYLE + warning_message)
                user_input = self.loading.input_with_flashing()
                if user_input.lower() == 'y':
                    self.new_file()            

            new_row = ""

            if self.beginnning_of_file:
                self.start_time = time.time()

            # Print elapsed time
            elapsed_time = time.time() - self.start_time
            elapsed_time = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))+f"{elapsed_time%1:.3f}"[1:]
            print(f"Getting new measurements (Elapsed Time: {elapsed_time})")

            # Write data for each connected device
            for i, device in enumerate(self.devices):
                try:
                    if device is time:
                        if self.items[i] == 'elapsed':
                            value = time.time() - self.start_time
                        else:
                            value = time.time()
                    elif self.channels[i] is None:
                        value = device.get(self.items[i])
                    else:
                        value = device.get(self.items[i], self.channels[i])

                    if self.file_open:

                        if self.beginnning_of_file:
                            if isinstance(value, tuple):
                                self.f.write(f"{self.labels[i]}\t{self.labels[i]}_e")
                            else:
                                self.f.write(f"{self.labels[i]}")
                            if i != len(self.labels) - 1:
                                self.f.write('\t')
                            else:
                                self.f.write('\n')

                        if isinstance(value, tuple):
                            new_row += f"{value[0]:.10f}\t{value[1]:.10f}"
                        else:
                            if isinstance(value, float):
                                new_row += f"{value:.10f}"
                            else:
                                new_row += f"{value}"

                        if i != len(self.devices) - 1:
                            new_row += '\t'

                    if print_to_terminal:
                        label_padding = ' ' * (self.max_label_length - len(self.labels[i]))
                        if device is time:
                            # value to value in HH:MM:SS format with milliseconds
                            value = time.strftime('%H:%M:%S', time.gmtime(value))+f"{value%1:.3f}"[1:]
                            if self.items[i] == 'current':
                                value = value + '-GMT'

                        if isinstance(value, tuple):
                            value_padding = ' ' * max(0,(_VALUE_PADDING - len(f"{value[0]:.4f} ± {value[1]:.4f}")))
                            print(f"\r{Back.WHITE}{Fore.BLACK} {self.labels[i]}{label_padding} {Back.BLUE}{Fore.WHITE} {value[0]:.4f} ± {value[1]:.4f}{value_padding} ")
                        else:
                            if isinstance(value, float):
                                value_padding = ' ' * max(0,(_VALUE_PADDING - len(f"{value:.4f}")))
                                print(f"\r{Back.WHITE}{Fore.BLACK} {self.labels[i]}{label_padding} {Back.BLUE}{Fore.WHITE} {value:.4f}{value_padding} ")
                            else:
                                value_padding = ' ' * max(0,(_VALUE_PADDING - len(f"{value}")))
                                print(f"\r{Back.WHITE}{Fore.BLACK} {self.labels[i]}{label_padding} {Back.BLUE}{Fore.WHITE} {value}{value_padding} ")
                except Exception as e:
                    error_message = f"Error getting data from device '{self.devices[i]}'."
                    raise ValueError(_ERROR_STYLE + error_message + f"\n{e}")

            if self.file_open:
                self.f.write(new_row + '\n')
                self.beginnning_of_file = False
                
        except IOError:
            error_message = f"Failed to write data to the file '{self.filename}'."
            raise IOError(_ERROR_STYLE + error_message)
        
    
    """
    Finds the next available filename by appending a number to the base filename.

    Args:
        name (str): The base filename.
        max_tries (int, optional): The maximum number of tries to find an available filename. Defaults to _MAX_FILENAMES.

    Returns:
        str: The next available filename.

    Raises:
        FileExistsError: If an available filename cannot be found after the maximum number of tries.
    """
    def __find_next_filename(self, name, max_tries=_MAX_FILENAMES):


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
        raise FileExistsError(_ERROR_STYLE + error_message)
    

        
    """
    Opens a new file for writing data.

    Args:
        filename (str, optional): The name of the file. Defaults to 'data.txt'.

    Raises:
        IOError: If there is an error opening the file.
    """
    def new_file(self, filename = None):

        if filename is None:
            if self.filename_warning_given is False:
                self.filename_warning_given = True
                warning_message = (
                    "No file path provided. "
                    "The data will be saved in the current directory with a timestamped filename. "
                    "Use 'set_screenshot_path(\"path/to/save/*\")' or 'set_screenshot_path(\"path/to/save/filename.txt\")' "
                    "to specify a directory to save the data in."
                )
                print(_WARNING_STYLE + warning_message)
        elif filename.endswith("*"):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = filename.replace("*", f"DS7034_screenshot_{timestamp}.png")
        else:
            if not filename.endswith(".txt"):
                filename += ".txt"

        directory = os.path.dirname(filename)
        if not os.path.exists(directory) and not directory == "":
            # Directory doesn't exist, ask the user if they want to create it
            create_directory = self.loading.input_with_flashing(f"The directory \"{directory}/\" does not exist. Create it? (y/n): ")
            if create_directory.lower() == "y":
                os.makedirs(directory)
            else:
                raise FileNotFoundError(_ERROR_STYLE + "Directory does not exist.")

        try:
            if self.file_open:
                self.close_file()

            # Generate a new filename if the provided one already exists
            self.filename = self.__find_next_filename(filename)
            
            # Open the file in write mode
            self.f = open(self.filename, 'w')
            self.beginnning_of_file = True  
            self.file_open = True
            print(_SUCCESS_STYLE + f"Opened file '{self.filename}'.")
        except IOError:
            # Raise an exception if there is an error opening the file
            error_message = f"Failed to open file '{self.filename}'."
            raise IOError(_ERROR_STYLE + error_message)


    """
    Closes the filestream and saves the file.

    If a filestream is available and writable, the function closes the filestream and prints a success message.
    If no filestream is available or it is not writable, a warning message is printed.

    Raises:
        IOError: If an error occurs while saving the file.
    """
    def close_file(self):

        try:
            if self.f.writable():
                self.f.close()
                self.file_open = False
                print(_SUCCESS_STYLE + f"File '{self.filename}' saved.")
            else:
                print(_WARNING_STYLE + "No filestream available to save.")
        except IOError:
            error_message = f"Failed to save file '{self.filename}'."
            raise IOError(_ERROR_STYLE + error_message)
        