#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   @file KS33500B.py
#   @brief Driver for Keysight 33500B Function/Arbitrary Waveform Generator
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

import time
from typing import Optional

import pyvisa
from colorama import init, Fore, Style

# Loading module with fallback
try:
    from .loading import loading
except ImportError:
    try:
        from loading import loading
    except ImportError:
        class loading:
            """Fallback loading class if module unavailable."""
            def delay_with_loading_indicator(self, seconds: float) -> None:
                time.sleep(seconds)

# Console output styles
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "

_DELAY = 0.1

class KS33500B:
    """
    Driver for Keysight 33500B Function/Arbitrary Waveform Generator.
    
    This class provides methods for connecting to and controlling a
    Keysight 33500B waveform generator via VISA interface.
    
    Attributes:
        rm: PyVISA ResourceManager instance
        address: Device VISA address
        instrument: Active connection handle
        status: Connection status ("Connected" or "Not Connected")
        loading: Loading indicator helper
        debug: Enable/disable debug printing
        
    Example:
        >>> gen = KS33500B()
        >>> gen.set_squ_freq(1000, source=1)
        >>> gen.set_squ_amp(5.0, source=1)
        >>> gen.set_squ_dcyc(50.0, source=1)
        >>> gen.disconnect()
    """
    
    def __init__(self, auto_connect: bool = True, address: Optional[str] = None, debug: bool = False):
        """
        Initialize KS33500B driver.
        
        Args:
            auto_connect: Automatically connect to device on initialization
            address: Optional explicit VISA address
            debug: Enable debug printing (default: False)
        """
        init(autoreset=True)
        
        self.rm: Optional[pyvisa.ResourceManager] = pyvisa.ResourceManager()
        self.address: Optional[str] = None
        self.instrument: Optional[pyvisa.resources.MessageBasedResource] = None
        self.status: str = "Not Connected"
        self.loading = loading()
        self.debug: bool = debug
        self._address_hint: Optional[str] = address

        if auto_connect:
            self.connect(address=address)
    
    def connect(self, address: Optional[str] = None) -> None:
        """
        Establish connection to KS33500B waveform generator.
        
        Args:
            address: Optional explicit VISA resource string. If None, auto-detect.
            
        Raises:
            ConnectionError: If device not found or connection fails.
        """
        # 1) Try explicit address first
        explicit = address or self._address_hint
        if explicit:
            try:
                inst = self.rm.open_resource(explicit)
                inst.read_termination = '\n'
                inst.write_termination = '\n'
                inst.timeout = 20000
                
                # Verify device identity
                idn = inst.query("*IDN?").strip()
                if "33500B" not in idn:
                    inst.close()
                    raise ConnectionError(
                        _ERROR_STYLE + f"Device at '{explicit}' is not a KS33500B (IDN='{idn}')."
                    )
                
                self.instrument = inst
                self.address = explicit
            except pyvisa.VisaIOError as e:
                raise ConnectionError(_ERROR_STYLE + f"Failed to connect to '{explicit}': {e}")
            except Exception as e:
                raise ConnectionError(_ERROR_STYLE + f"Unexpected error connecting to '{explicit}': {e}")
        
        # 2) Auto-detect by scanning resources
        if self.instrument is None:
            try:
                resources = self.rm.list_resources()
            except pyvisa.VisaIOError as e:
                raise ConnectionError(_ERROR_STYLE + f"PyVISA is not able to find any devices: {e}")
            
            # Look for MY52 (typical Keysight 33500B identifier)
            ks_resources = [elem for elem in resources if 'MY52' in elem]
            
            if len(ks_resources) == 0:
                raise ConnectionError(_ERROR_STYLE + "KS33500B not found")
            
            try:
                self.address = ks_resources[0]
                inst = self.rm.open_resource(self.address)
                inst.read_termination = '\n'
                inst.write_termination = '\n'
                inst.timeout = 20000
                self.instrument = inst
            except pyvisa.VisaIOError as e:
                raise ConnectionError(_ERROR_STYLE + f"Failed to connect to auto-detected device: {e}")
            except Exception as e:
                raise ConnectionError(_ERROR_STYLE + f"Unexpected error during auto-detection: {e}")
        
        # 3) Initialize device
        if self.instrument is None:
            raise ConnectionError(_ERROR_STYLE + "Failed to establish connection to KS33500B")
        
        self.status = "Connected"
        print(_SUCCESS_STYLE + f"Connected to {self.address}")
    
    def disconnect(self) -> None:
        """Close the connection to the device."""
        if self.instrument is not None:
            try:
                self.instrument.close()
            finally:
                print(f"\rDisconnected from KS33500B at {self.address}")
                self.instrument = None
        
        self.status = "Not Connected"
        self.address = None
    
    def _chk(self) -> None:
        """Verify device is connected before operations."""
        if self.status != "Connected" or self.instrument is None:
            raise ConnectionError(_ERROR_STYLE + "Not connected to KS33500B")

    def set_squ_dcyc(self, dcyc: float, source: int = 1) -> None:
        """
        Set square wave duty cycle.
        
        Args:
            dcyc: Duty cycle percentage (0-100)
            source: Source channel (1 or 2)
            
        Raises:
            ConnectionError: If not connected to device
        """
        self._chk()
        
        command = f'SOUR{source}:FUNC:SQU:DCYC {dcyc}'
        if self.debug:
            print(command)
        self.instrument.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def set_squ_freq(self, freq: float, source: int = 1) -> None:
        """
        Set square wave frequency.
        
        Args:
            freq: Frequency in Hz
            source: Source channel (1 or 2)
            
        Raises:
            ConnectionError: If not connected to device
        """
        self._chk()
        
        command = f'SOUR{source}:FREQ {freq} Hz'
        if self.debug:
            print(command)
        self.instrument.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def set_squ_amp(self, amp: float, source: int = 1) -> None:
        """
        Set square wave amplitude.
        
        Args:
            amp: Amplitude in Vpp (peak-to-peak voltage)
            source: Source channel (1 or 2)
            
        Raises:
            ConnectionError: If not connected to device
        """
        self._chk()
        
        command = f'SOUR{source}:VOLT {amp} Vpp'
        if self.debug:
            print(command)
        self.instrument.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def set_squ_offset(self, offset: float, source: int = 1) -> None:
        """
        Set square wave DC offset.
        
        Args:
            offset: DC offset in volts
            source: Source channel (1 or 2)
            
        Raises:
            ConnectionError: If not connected to device
        """
        self._chk()
        
        command = f'SOUR{source}:VOLT:OFFS {offset} V'
        if self.debug:
            print(command)
        self.instrument.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

