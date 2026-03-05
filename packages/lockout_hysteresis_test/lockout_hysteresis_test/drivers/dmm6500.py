#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keithley/Tektronix DMM6500 6.5-Digit Multimeter Driver (Standalone)
===================================================================

Standalone version of the DMM6500 driver for the lockout_hysteresis_test package.
"""

from __future__ import annotations

import struct
import time
import statistics as stats
from typing import Optional, Tuple, List, Literal

import pyvisa
from colorama import init, Fore, Style

# Simple loading indicator stub (since we can't import from main project)
class _LoadingStub:
    def delay_with_loading_indicator(self, seconds: float) -> None:
        time.sleep(seconds)

# --- Console styles ---
_ERROR_STYLE   = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_DELAY         = 0.1


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s


class DMM6500:
    """
    Simple SCPI wrapper for Keithley/Tektronix DMM6500.

    Example:
        mm = DMM6500()                           # auto-detect using '6500'
        mm.configure("RESISTANCE", 1000.0, 1e-6)
        r = mm.measure_resistance()
        print("R =", r)
        mm.disconnect()
    """

    def __init__(self, auto_connect: bool = True, address: Optional[str] = None, 
                 ip_address: Optional[str] = None, debug: bool = False):
        init(autoreset=True)

        self.rm = pyvisa.ResourceManager()
        self.address: Optional[str] = None
        self.instrument: Optional[pyvisa.resources.MessageBasedResource] = None
        self.loading = _LoadingStub()
        self.status = "Not Connected"
        self._idn: Optional[str] = None
        self._address_hint = address
        self._ip_address = ip_address
        self.debug = debug

        if auto_connect:
            self.connect(address=self._address_hint, ip_address=self._ip_address)

    def connect(self, address: Optional[str] = None, ip_address: Optional[str] = None):
        """Establish a connection via USB or Ethernet."""
        # IP address connection
        ip = ip_address or self._ip_address
        if ip and not address and not self._address_hint:
            tcpip_address = f"TCPIP0::{ip}::inst0::INSTR"
            try:
                inst = self.rm.open_resource(tcpip_address)
                inst.read_termination = '\n'
                inst.write_termination = '\n'
                inst.timeout = 20000
                idn = inst.query("*IDN?").strip()
                if "DMM6500" in idn:
                    self.instrument = inst
                    self.address = tcpip_address
                    self._idn = idn
                    self.status = "Connected"
                    print(_SUCCESS_STYLE + f"Connected to DMM6500 via Ethernet at {ip} [{self._idn}]")
                    return
                else:
                    inst.close()
                    raise ConnectionError(_ERROR_STYLE +
                        f"Device at '{ip}' is not a DMM6500 (IDN='{idn}').")
            except Exception as e:
                raise ConnectionError(_ERROR_STYLE +
                    f"Failed to connect to DMM6500 at IP '{ip}': {e}")
        
        # Explicit address
        explicit = address or self._address_hint
        if explicit:
            try:
                inst = self.rm.open_resource(explicit)
                inst.read_termination = '\n'
                inst.write_termination = '\n'
                inst.timeout = 20000
                idn = inst.query("*IDN?").strip()
                if "DMM6500" in idn:
                    self.instrument = inst
                    self.address = explicit
                else:
                    inst.close()
                    raise ConnectionError(_ERROR_STYLE +
                        f"Resource '{explicit}' is not a DMM6500 (IDN='{idn}').")
            except Exception as e:
                raise ConnectionError(_ERROR_STYLE +
                    f"Failed to open explicit address '{explicit}': {e}")

        # Auto-detect
        if self.instrument is None:
            resources = self.rm.list_resources()
            
            for resource in resources:
                if resource.startswith("TCPIP") or "6500" in resource:
                    try:
                        inst = self.rm.open_resource(resource)
                        inst.read_termination = '\n'
                        inst.write_termination = '\n'
                        inst.timeout = 20000
                        idn = inst.query("*IDN?").strip()
                        if "DMM6500" in idn:
                            self.instrument = inst
                            self.address = resource
                            break
                        inst.close()
                    except Exception:
                        continue

        if self.instrument is None:
            raise ConnectionError(_ERROR_STYLE + "Keithley DMM6500 not found.")

        try:
            self.instrument.write("*CLS")
        except Exception:
            pass
        try:
            self._idn = self.instrument.query("*IDN?").strip()
        except Exception:
            self._idn = "Keithley DMM6500"

        self.status = "Connected"
        print(_SUCCESS_STYLE + f"Connected to DMM6500 at {self.address} [{self._idn}]")

    def disconnect(self):
        """Close the VISA session."""
        if self.instrument is not None:
            try:
                self.instrument.close()
            finally:
                print(f"\rDisconnected from DMM6500 at {self.address}")
        self.status = "Not Connected"
        self.instrument = None
        self.address = None

    def _chk(self):
        if self.status != "Connected" or self.instrument is None:
            raise ConnectionError(_ERROR_STYLE + "Not connected to DMM6500.")

    def _read_float_query(self, q: str) -> float:
        self._chk()
        return float(self.instrument.query(q))

    def measure_voltage(self) -> float:
        """DC voltage via MEASure:VOLTage:DC?"""
        self._chk()
        self.instrument.write("SENSe:FUNCtion 'VOLT:DC'")
        time.sleep(_DELAY)
        return self._read_float_query("MEASure:VOLTage:DC?")

    def measure_current(self) -> float:
        """DC current via MEASure:CURRent:DC?"""
        self._chk()
        self.instrument.write("SENSe:FUNCtion 'CURR:DC'")
        time.sleep(_DELAY)
        return self._read_float_query("MEASure:CURRent:DC?")

    def get(self, item: str):
        k = item.strip().lower()
        if   k == "voltage":    return self.measure_voltage()
        elif k == "current":    return self.measure_current()
        else:
            raise ValueError(_ERROR_STYLE + f"Invalid item: {item}")
