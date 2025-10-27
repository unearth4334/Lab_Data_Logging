#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   @file DMM6500.py
#   @brief Keysight-style wrapper for Keithley/Tektronix DMM6500 using pure SCPI.
#          "Digitize" helpers implemented via regular DMM mode + defbuffer1.
#   @date 15-Sep-2025

from __future__ import annotations

import struct
import time
import statistics as stats
from typing import Optional, Tuple, List, Literal

import pyvisa
from colorama import init, Fore, Style

# Optional "loading" helper to mirror your Keysight class UX
try:
    from loading import loading
except Exception:
    class loading:
        def delay_with_loading_indicator(self, seconds: float) -> None:
            time.sleep(seconds)

# --- Console styles to match your Keysight code ---
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

    "Digitize" helpers:
        data = mm.digitize_current(duration_s=2.0, fixed_range=0.1, nplc=0.001)
        print(len(data), "samples")
    """

    # -----------------------------
    # Init / Connect / Disconnect
    # -----------------------------
    def __init__(self, auto_connect: bool = True, address: Optional[str] = None):
        init(autoreset=True)

        self.rm = pyvisa.ResourceManager()
        self.address: Optional[str] = None
        self.instrument: Optional[pyvisa.resources.MessageBasedResource] = None
        self.loading = loading()
        self.status = "Not Connected"
        self._idn: Optional[str] = None
        self._address_hint = address

        if auto_connect:
            self.connect(address=self._address_hint)

    def connect(self, address: Optional[str] = None):
        """
        Establish a connection.

        Args:
            address: explicit VISA resource string. If None, auto-detect using
                     entries containing '6500', then verify with *IDN?.
        """
        # 1) Try explicit address first (argument beats ctor hint)
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

        # 2) Otherwise scan for resources with '6500' in the name
        if self.instrument is None:
            for resource in self.rm.list_resources():
                if "6500" in resource:
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

        # Clear status and cache ID
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

    # -----------------------------
    # Helpers / SCPI utilities
    # -----------------------------
    def _chk(self):
        if self.status != "Connected" or self.instrument is None:
            raise ConnectionError(_ERROR_STYLE + "Not connected to DMM6500.")

    def get_current_function(self) -> str:
        """Return active function (VOLT:DC | CURR:DC | RES | FRES), sans quotes."""
        self._chk()
        self.instrument.write("SENSe:FUNCtion?")
        return _strip_quotes(self.instrument.read())

    def _ensure_function(self, fn: str) -> None:
        """Set function if not already active. fn like 'VOLT:DC','CURR:DC','RES','FRES'."""
        cur = self.get_current_function().upper()
        if fn.upper() not in cur:
            self.instrument.write(f"SENSe:FUNCtion '{fn}'")
            self.loading.delay_with_loading_indicator(_DELAY)

    def _read_float_query(self, q: str) -> float:
        self._chk()
        return float(self.instrument.query(q))

    # -----------------------------
    # Core configuration helpers
    # -----------------------------
    def set_terminals(self, where: str = "FRONt") -> None:
        """Select FRONt or REAR terminals."""
        self._chk()
        w = where.strip().upper()
        if w.startswith("FRON"):
            self.instrument.write("ROUTe:TERMinals FRONt")
        elif w == "REAR":
            self.instrument.write("ROUTe:TERMinals REAR")
        else:
            raise ValueError("Terminals must be 'FRONt' or 'REAR'.")

    def disable_autorange(self, function: Optional[str] = None) -> None:
        """Disable autorange for specified (or current) function."""
        self._chk()
        fn = (function or self.get_current_function()).upper()
        if "VOLT" in fn:
            node = "VOLT:DC"
        elif "CURR" in fn:
            node = "CURR:DC"
        elif "FRES" in fn:
            node = "FRES"
        else:
            node = "RES"
        self.instrument.write(f"SENSe:{node}:RANGe:AUTO OFF")
        print(f"\rAutorange disabled for {node}.")

    def set_nplc(self, nplc: float, function: Optional[str] = None) -> None:
        """Set integration time (power-line cycles) for the given/current function."""
        self._chk()
        fn = (function or self.get_current_function()).upper()
        if "VOLT" in fn:
            node = "VOLT:DC"
        elif "CURR" in fn:
            node = "CURR:DC"
        elif "FRES" in fn:
            node = "FRES"
        else:
            node = "RES"
        # Correct header: NPLC
        self.instrument.write(f"SENSe:{node}:NPLC {float(nplc)}")

    def set_autozero(self, state: str = "OFF") -> None:
        """Set autozero ON/OFF for active function context."""
        self._chk()
        st = state.strip().upper()
        if st not in ("ON", "OFF"):
            raise ValueError("Autozero must be 'ON' or 'OFF'.")
        self.instrument.write(f"SENSe:AZERo {st}")

    def configure(self, measurement_type: str, range_val: float, resolution_val: float) -> None:
        """
        Configure via CONFigure:
          VOLTAGE:DC  -> CONFigure:VOLTage:DC <range>,<resolution>
          CURRENT:DC  -> CONFigure:CURRent:DC <range>,<resolution>
          RESISTANCE  -> CONFigure:RESistance <range>,<resolution>
          FRESISTANCE -> CONFigure:FRESistance <range>,<resolution>
        """
        self._chk()
        mt = measurement_type.strip().upper()
        if mt in ("VOLTAGE:DC", "VOLT:DC"):
            self.instrument.write(f"CONFigure:VOLTage:DC {range_val},{resolution_val}")
            self.instrument.write("SENSe:FUNCtion 'VOLT:DC'")
        elif mt in ("CURRENT:DC", "CURR:DC"):
            self.instrument.write(f"CONFigure:CURRent:DC {range_val},{resolution_val}")
            self.instrument.write("SENSe:FUNCtion 'CURR:DC'")
        elif mt in ("FRESISTANCE", "FRES"):
            self.instrument.write(f"CONFigure:FRESistance {range_val},{resolution_val}")
            self.instrument.write("SENSe:FUNCtion 'FRES'")
        elif mt in ("RESISTANCE", "RES"):
            self.instrument.write(f"CONFigure:RESistance {range_val},{resolution_val}")
            self.instrument.write("SENSe:FUNCtion 'RES'")
        else:
            raise ValueError(_ERROR_STYLE + f"Unsupported measurement_type: {measurement_type}")
        print(f"\rConfigured {mt} Range={range_val}, Resolution={resolution_val}")

    # -----------------------------
    # One-shot DC measurements
    # -----------------------------
    def measure_voltage(self) -> float:
        """DC voltage via MEASure:VOLTage:DC?"""
        self._ensure_function("VOLT:DC")
        return self._read_float_query("MEASure:VOLTage:DC?")

    def measure_current(self) -> float:
        """DC current via MEASure:CURRent:DC?"""
        self._ensure_function("CURR:DC")
        return self._read_float_query("MEASure:CURRent:DC?")

    def measure_resistance(self, four_wire: bool = False) -> float:
        """2-wire by default; 4-wire if four_wire=True."""
        if four_wire:
            self._ensure_function("FRES")
            return self._read_float_query("MEASure:FRESistance?")
        else:
            self._ensure_function("RES")
            return self._read_float_query("MEASure:RESistance?")

    # -----------------------------
    # High-level dispatcher (compat)
    # -----------------------------
    def get(self, item: str):
        k = item.strip().lower()
        if   k == "voltage":    return self.measure_voltage()
        elif k == "current":    return self.measure_current()
        elif k == "resistance": return self.measure_resistance(False)
        elif k == "statistics": return self.calculate_statistics()
        else:
            raise ValueError(_ERROR_STYLE + f"Invalid item: {item} request to DMM6500")

    # -----------------------------
    # Host-side statistics
    # -----------------------------
    def calculate_statistics(self,
                             n: int = 100,
                             measurement_type: Optional[str] = None,
                             delay_s: float = 0.0) -> Tuple[float, float, float, float]:
        """
        Collect n readings via MEASure:...?, then compute (mean, stdev, min, max).
        measurement_type: VOLTAGE:DC | CURRENT:DC | RESISTANCE | FRESISTANCE | None(current)
        """
        self._chk()

        def oneshot() -> float:
            if measurement_type is None:
                fn = self.get_current_function().upper()
                if   "VOLT" in fn: return self.measure_voltage()
                elif "CURR" in fn: return self.measure_current()
                elif "FRES" in fn: return self.measure_resistance(True)
                else:              return self.measure_resistance(False)
            mt = measurement_type.strip().upper()
            if   mt in ("VOLTAGE:DC", "VOLT:DC"): return self.measure_voltage()
            if   mt in ("CURRENT:DC", "CURR:DC"):  return self.measure_current()
            if   mt in ("FRESISTANCE", "FRES"):    return self.measure_resistance(True)
            if   mt in ("RESISTANCE", "RES"):      return self.measure_resistance(False)
            raise ValueError(_ERROR_STYLE + f"Unsupported measurement_type: {measurement_type}")

        vals: List[float] = []
        for _ in range(max(1, int(n))):
            vals.append(oneshot())
            if delay_s > 0:
                time.sleep(delay_s)

        mean = stats.fmean(vals)
        stdev = stats.pstdev(vals) if len(vals) > 1 else 0.0
        vmin = min(vals)
        vmax = max(vals)
        return mean, stdev, vmin, vmax

    def fetch_trace(self,
                    buffer: str = "defbuffer1",
                    chunk: int = 50000,
                    debug: bool = True,
                    step: bool = True):
        """
        Download existing readings (values only) from a DMM buffer (no re-config, no trigger).
        Returns a 2-tuple: (values, None) to be drop-in compatible with code that unpacks
        (vals, times) even though TIME output isn't supported on this firmware.

        Args:
            buffer: buffer name, e.g. 'defbuffer1'
            chunk:  points per TRACe:DATA? fetch (avoid huge single transfers)
            debug:  verbose logging of every SCPI call
            step:   prompt 'Press Enter to continue...' after each I/O

        Returns:
            (values, None)  # times are not available on this unit
        """
        self._chk()
        inst = self.instrument

        # -------- local helpers --------
        import datetime
        def _now():
            return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

        def _pause(where: str):
            if not step:
                return
            try:
                input(f"[{_now()}] {where}  —  press Enter to continue...")
            except Exception:
                pass

        def _log(msg: str):
            if debug:
                print(f"[{_now()}] {msg}")

        def _write(cmd: str):
            _log(f"WRITE: {cmd}")
            inst.write(cmd)
            _pause(f"Wrote: {cmd}")

        def _query(cmd: str) -> str:
            _log(f"QUERY: {cmd}")
            rsp = inst.query(cmd).strip()
            _log(f"  -> '{rsp}'")
            _pause(f"Query: {cmd}")
            return rsp

        def _query_ascii(cmd: str):
            _log(f"QUERY_ASCII: {cmd}")
            vals = inst.query_ascii_values(cmd, container=list)
            _log(f"  -> {len(vals)} numbers")
            _pause(f"Query ASCII: {cmd}")
            return vals


        # -------- how many points exist now? --------
        try:
            n = int(_query(f"TRACe:ACTual? '{buffer}'"))
        except Exception as e1:
            _log(f"ACTual? with quoted buffer failed ({e1}); trying unquoted…")
            n = int(_query(f"TRACe:ACTual? {buffer}"))

        _log(f"BUFFER COUNT: {n}")
        if n <= 0:
            _log("No points in buffer; returning empty lists.")
            return [], None

        # -------- read in chunks --------
        values: List[float] = []
        start = 1
        chunk = max(1, int(chunk))

        while start <= n:
            stop = min(start + chunk - 1, n)

            cmd_q  = f"TRACe:DATA? {start},{stop},'{buffer}'"
            cmd_uq = f"TRACe:DATA? {start},{stop},{buffer}"
            try:
                raw = _query_ascii(cmd_q)
            except Exception as e_q:
                _log(f"DATA? quoted failed ({e_q}); trying unquoted…")
                raw = _query_ascii(cmd_uq)

            values.extend(float(v) for v in raw)
            _log(f"CHUNK [{start}:{stop}] -> {len(raw)} values "
                f"(total {len(values)} of {n})")
            if raw:
                _log(f"  first={raw[0]:.6g}, last={raw[-1]:.6g}")

            start = stop + 1

        _log(f"DONE: fetched {len(values)} values from '{buffer}'.")
        # Return (values, None) so callers that unpack (vals, times) keep working.
        return values, None