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
from colorama import init, Fore
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

        error_message = f"Failed to connect to Rigol DS7034 Oscilloscope at {self.address}: {e}"
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