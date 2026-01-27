#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   @file EPS.py
#   @brief Driver for Hercules MCU Environmental Control System
#   @date 27-Jan-2026
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

from __future__ import annotations

import os
import time
from typing import Optional, Tuple

import numpy
import serial
import serial.tools.list_ports
from colorama import init, Fore, Style

# Console output styles
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "

_DELAY = 0.01  # in seconds

# Temperature calibration data for thermistor
TEMPERATURES = [150, 140, 130, 120, 110, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0, -10, -20, -30, -40, -50, -55]
VOLTAGES = [302.785, 358.164, 412.739, 466.76, 520.551, 574.117, 627.49, 680.654, 733.608, 786.36, 838.882, 891.178, 943.227, 995.05, 1046.647, 1097.987, 1149.07, 1199.884, 1250.398, 1300.593, 1350.441, 1375.219]

class EPS:
    """
    Driver for Hercules MCU Environmental Control System.
    
    This class provides methods for connecting to and controlling a
    Hercules MCU-based environmental chamber via RS-232 serial interface.
    
    Attributes:
        ser: Serial connection object
        address: COM port address
        status: Connection status ("Connected" or "Not Connected")
        identity: Device identification string
        debug: Enable/disable debug printing
        
    Example:
        >>> eps = EPS()
        >>> temp = eps.read_temp1()
        >>> eps.heater_on()
        >>> time.sleep(60)
        >>> eps.heater_off()
        >>> eps.disconnect()
    """
    
    def __init__(self, auto_connect: bool = True, com_port: Optional[str] = None, baud_rate: int = 9600, debug: bool = False):
        """
        Initialize EPS driver.
        
        Args:
            auto_connect: Automatically connect to device on initialization
            com_port: Optional explicit COM port (e.g., 'COM16', '/dev/ttyUSB0')
            baud_rate: Serial baud rate (default: 9600)
            debug: Enable debug printing (default: False)
        """
        init(autoreset=True)
        
        self.ser: Optional[serial.Serial] = None
        self.address: Optional[str] = None
        self.status: str = "Not Connected"
        self.identity: Optional[str] = None
        self.debug: bool = debug
        self._com_port_hint: Optional[str] = com_port
        self._baud_rate: int = baud_rate

        if auto_connect:
            self.connect(com_port=com_port, baud_rate=baud_rate)
    
    def connect(self, com_port: Optional[str] = None, baud_rate: int = 9600) -> None:
        """
        Establish connection to Hercules MCU.
        
        Args:
            com_port: Optional COM port (e.g., 'COM16', '/dev/ttyUSB0'). If None, prompt user.
            baud_rate: Serial baud rate (default: 9600)
            
        Raises:
            ConnectionError: If device not found or connection fails.
        """
        # 1) Try explicit COM port first
        explicit_port = com_port or self._com_port_hint
        
        # 2) Try environment variable
        if explicit_port is None:
            try:
                explicit_port = os.environ.get('EPS_COM_PORT')
            except Exception:
                pass
        
        # 3) Prompt user to select COM port
        if explicit_port is None:
            ports = serial.tools.list_ports.comports()
            if not ports:
                raise ConnectionError(_ERROR_STYLE + "No COM ports found")
            
            print("\nAvailable COM ports:")
            for i, port in enumerate(ports, start=1):
                print(f"  {i}. {port.device} - {port.description}")
            
            while True:
                try:
                    selection = int(input("Select COM port for EPS (1, 2, ...): "))
                    if 1 <= selection <= len(ports):
                        explicit_port = ports[selection - 1].device
                        os.environ['EPS_COM_PORT'] = explicit_port
                        break
                    print(_ERROR_STYLE + "Invalid selection")
                except ValueError:
                    print(_ERROR_STYLE + "Invalid input. Enter a number.")
        
        # 4) Open serial connection
        try:
            self.ser = serial.Serial(explicit_port, baud_rate, timeout=1)
            self.address = explicit_port
            
            # Verify device identity
            self.ser.write(str('READ(IDN)\r').encode('ascii'))
            time.sleep(_DELAY)
            self.ser.readline()  # Read first line
            identity_bytes = self.ser.readline()
            device_id = identity_bytes[0:(len(identity_bytes) - 2)].decode('ascii', errors='ignore').strip()
            self.identity = f'Hercules MCU, Device ID: {device_id}'
            
            if len(device_id) < 1:
                raise ConnectionError(_ERROR_STYLE + "Device not responding with valid identity")
            
            self.status = "Connected"
            print(_SUCCESS_STYLE + f"Connected to {self.identity}")
            
        except serial.SerialException as e:
            raise ConnectionError(_ERROR_STYLE + f"Failed to connect to {explicit_port}: {e}")
        except Exception as e:
            raise ConnectionError(_ERROR_STYLE + f"Unexpected error connecting to {explicit_port}: {e}")
    
    def disconnect(self) -> None:
        """Close the serial connection to the device."""
        if self.ser is not None and self.ser.is_open:
            try:
                self.ser.close()
            finally:
                print(f"\rDisconnected from Hercules at {self.address}")
                self.ser = None
        
        self.status = "Not Connected"
        self.address = None
    
    def _chk(self) -> None:
        """Verify device is connected before operations."""
        if self.status != "Connected" or self.ser is None or not self.ser.is_open:
            raise ConnectionError(_ERROR_STYLE + "Not connected to EPS")
    
    def get(self, item: str, channel: int = 1) -> Tuple[float, float]:
        """
        Retrieve measurement value by name.
        
        Args:
            item: Measurement item name (case-sensitive)
                  Valid values: 'READ_TIME', 'READ_TEMP1', 'READ_HEATER1'
            channel: Optional channel number (for compatibility, not used)
            
        Returns:
            Tuple of (measurement_value, error_estimate)
            
        Raises:
            ValueError: If invalid item requested
            ConnectionError: If not connected to device
            
        Example:
            >>> time_val, _ = eps.get('READ_TIME')
            >>> temp_val, _ = eps.get('READ_TEMP1')
        """
        self._chk()

        items = {
            "READ_TIME": self.read_time,
            "READ_TEMP1": self.read_temp1,
            "READ_HEATER1": self.read_heater1
        }
        
        if item not in items:
            raise ValueError(
                _ERROR_STYLE + f"Invalid item '{item}'. "
                f"Valid items: {', '.join(items.keys())}"
            )

        return items[item]()


    def read_time(self) -> Tuple[float, float]:
        """
        Read elapsed time from device.
        
        Returns:
            Tuple of (time_in_seconds, error_estimate=0)
            
        Raises:
            ConnectionError: If not connected to device
            ValueError: If response cannot be parsed
        """
        self._chk()
        
        if self.debug:
            print("READ(TIME)")
        
        command = 'READ(TIME)\r'
        
        try:
            self.ser.write(str(command).encode('ascii'))
            time.sleep(_DELAY)
            self.ser.readline()  # Read first line
            val = self.ser.readline()
            time_ms = float(val[0:(len(val) - 2)])
            return (time_ms / 1000, 0)
        except ValueError as e:
            raise ValueError(_ERROR_STYLE + f"Failed to parse time: {e}")
        except Exception as e:
            raise ConnectionError(_ERROR_STYLE + f"Communication error: {e}")

    def read_temp1(self) -> Tuple[float, float]:
        """
        Read temperature from sensor 1.
        
        Returns:
            Tuple of (temperature_celsius, error_estimate=0)
            
        Raises:
            ConnectionError: If not connected to device
            ValueError: If response cannot be parsed
            
        Note:
            Temperature conversion uses thermistor calibration data.
        """
        self._chk()
        
        if self.debug:
            print("READ(TEMP1)")
        
        command = 'READ(TEMP1)\r'
        
        try:
            self.ser.write(str(command).encode('ascii'))
            time.sleep(_DELAY)
            self.ser.readline()  # Read first line
            val = self.ser.readline()
            
            # Convert ADC reading to voltage and then to temperature
            adc_value = float(val[0:(len(val) - 2)])
            voltage_mv = 1600 * adc_value / 0xFFF
            temperature = numpy.interp(voltage_mv, VOLTAGES, TEMPERATURES)
            
            return (temperature, 0)
        except ValueError as e:
            raise ValueError(_ERROR_STYLE + f"Failed to parse temperature: {e}")
        except Exception as e:
            raise ConnectionError(_ERROR_STYLE + f"Communication error: {e}")
    
    def read_heater1(self) -> Tuple[float, float]:
        """
        Read heater 1 status/value.
        
        Returns:
            Tuple of (heater_value, error_estimate=0)
            
        Raises:
            ConnectionError: If not connected to device
            ValueError: If response cannot be parsed
        """
        self._chk()
        
        if self.debug:
            print("READ(HEATER1)")
        
        command = 'READ(HEATER1)\r'
        
        try:
            self.ser.write(str(command).encode('ascii'))
            time.sleep(_DELAY)
            self.ser.readline()  # Read first line
            val = self.ser.readline()
            heater_value = float(val[0:(len(val) - 2)])
            return (heater_value, 0)
        except ValueError as e:
            raise ValueError(_ERROR_STYLE + f"Failed to parse heater value: {e}")
        except Exception as e:
            raise ConnectionError(_ERROR_STYLE + f"Communication error: {e}")
    
    def heater_on(self) -> None:
        """
        Turn on heater 1.
        
        Raises:
            ConnectionError: If not connected to device
        """
        self._chk()
        
        if self.debug:
            print('WRITE(HEATER1,ON)')
        
        command = 'WRITE(HEATER1,ON)\r'
        
        try:
            self.ser.write(str(command).encode('ascii'))
            time.sleep(_DELAY)
            self.ser.readline()  # Read response
            self.ser.readline()  # Read second line
        except Exception as e:
            raise ConnectionError(_ERROR_STYLE + f"Failed to turn on heater: {e}")

    def heater_off(self) -> None:
        """
        Turn off heater 1.
        
        Raises:
            ConnectionError: If not connected to device
        """
        self._chk()
        
        if self.debug:
            print('WRITE(HEATER1,OFF)')
        
        command = 'WRITE(HEATER1,OFF)\r'
        
        try:
            self.ser.write(str(command).encode('ascii'))
            time.sleep(_DELAY)
            self.ser.readline()  # Read response
            self.ser.readline()  # Read second line
        except Exception as e:
            raise ConnectionError(_ERROR_STYLE + f"Failed to turn off heater: {e}")

