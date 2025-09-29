#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   @file KeysightMSOX4154A.py
#   @brief Keysight MSOX4154A control (screenshots + single/multi-channel waveform download).
#          This version **only** connects to explicit VISA addresses you pass in.
#   @date 16-Sep-2025

from __future__ import annotations
from typing import Optional, Any, Dict, List, Tuple

import pyvisa
from colorama import init, Fore, Style

_ERROR_STYLE   = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"

class KeysightMSOX4154A:
    """
    Example:
        osc = KeysightMSOX4154A(auto_connect=False)
        osc.connect("USB0::0x0957::0x17BC::MY59241237::INSTR")
        t, y, meta = osc.get_waveform(source="CHAN1")
        osc.disconnect()
    """

    def __init__(self, auto_connect: bool = False, timeout_ms: int = 20000, chunk_size: int = 102_400):
        init(autoreset=True)
        self.rm: pyvisa.ResourceManager = pyvisa.ResourceManager()
        self.address: Optional[str] = None
        self.instrument: Optional[pyvisa.resources.MessageBasedResource] = None
        self.status: str = "Not Connected"
        self._timeout_ms = timeout_ms
        self._chunk_size = chunk_size
        if auto_connect:
            raise ValueError("Pass the VISA address explicitly: use osc.connect('<VISA>')")

    # ---------- Connect / Disconnect (exact address only) ----------
    def connect(self, address: str):
        """Open the exact VISA address you pass (no discovery)."""
        if "::INSTR" not in address:
            raise ValueError(_ERROR_STYLE + f"Not a VISA INSTR address: {address}")
        try:
            inst = self.rm.open_resource(address)
            inst.timeout = self._timeout_ms
            inst.chunk_size = self._chunk_size
            inst.write_termination = '\n'
            # Use None for binary block reads; text queries still work via query()/query_binary_values
            inst.read_termination  = None
            try:
                inst.write(":SYSTem:HEADer OFF")
            except Exception:
                pass
            self.instrument = inst
            self.address = address
            self.status = "Connected"
            print(_SUCCESS_STYLE + f"Connected to Keysight MSOX4154A Oscilloscope at {self.address}")
        except Exception as e:
            raise ConnectionError(_ERROR_STYLE + f"Failed to open {address}: {e}")

    def disconnect(self):
        if self.instrument is not None:
            try:
                self.instrument.close()
            finally:
                print(f"\rDisconnected from Keysight MSOX4154A Oscilloscope at {self.address}")
                self.instrument = None
                self.status = "Not Connected"
                self.address = None

    # ---------- Helpers ----------
    def _chk(self):
        if self.instrument is None:
            raise ConnectionError(_ERROR_STYLE + "Not connected.")

    def get_idn(self) -> str:
        self._chk()
        return self.instrument.query("*IDN?").strip()  # type: ignore

    def is_running(self) -> bool:
        self._chk()
        try:
            return bool(int(self.instrument.query(":ACQuire:STATE?").strip()))  # type: ignore
        except Exception:
            return False

    def stop(self):
        self._chk()
        try: self.instrument.write(":STOP")  # type: ignore
        except Exception: pass

    def run(self):
        self._chk()
        try: self.instrument.write(":RUN")  # type: ignore
        except Exception: pass

    # ---------- Screenshot ----------
    def get_screenshot(self, inksaver: bool = False) -> bytes:
        self._chk()
        inst = self.instrument  # type: ignore
        try:
            if inksaver:
                inst.write(":HARDcopy:INKSaver ON"); mode = "PNG,SCReen,ON,NORMal"
            else:
                inst.write(":HARDcopy:INKSaver OFF"); mode = "PNG,COLor"
            data = inst.query_binary_values(
                f":DISPlay:DATA? {mode}",
                datatype='B', is_big_endian=True,
                container=bytearray, chunk_size=self._chunk_size, delay=0
            )
            return bytes(data)
        except pyvisa.errors.VisaIOError as e:
            raise RuntimeError(_ERROR_STYLE + f"Screenshot failed: {e}")
        except Exception as e:
            raise RuntimeError(_ERROR_STYLE + f"Screenshot failed: {e}")

    # ---------- Waveform: scaled data with real timebase ----------
    def _read_preamble(self) -> Dict[str, float]:
        """
        Reads :WAV:PRE? and parses Keysight 10-field preamble.
        Returns dict with keys shown below.
        """
        self._chk()
        pre = self.instrument.query(":WAVeform:PREamble?").strip()  # type: ignore
        # Format per Keysight MSO-X 4000A:
        # 0:FORMAT, 1:TYPE, 2:POINTS, 3:COUNT, 4:XINCR, 5:XORIG, 6:XREF, 7:YINCR, 8:YORIG, 9:YREF
        parts = [p.strip() for p in pre.split(",")]
        if len(parts) < 10:
            raise RuntimeError(_ERROR_STYLE + f"Unexpected preamble: {pre}")
        return {
            "format": float(parts[0]),
            "type":   float(parts[1]),
            "points": int(float(parts[2])),
            "count":  int(float(parts[3])),
            "xincr":  float(parts[4]),
            "xorig":  float(parts[5]),
            "xref":   float(parts[6]),
            "yincr":  float(parts[7]),
            "yorig":  float(parts[8]),
            "yref":   float(parts[9]),
        }

    def get_waveform(self,
                     source: str = "CHAN1",
                     points_mode: str = "RAW",
                     points: Optional[int] = None,
                     stop_during_read: bool = True,
                     debug: bool = False
                     ) -> Tuple[List[float], List[float], Dict[str, Any]]:
        """
        Returns (t_seconds, volts, meta) using the scope's actual timebase.
        - source: e.g., "CHAN1"
        - points_mode: "RAW" (acquisition memory) or "NORMal"/"MAX" etc.
        - points: optional decimation point count
        - stop_during_read: stop acquisition to avoid buffer changing mid-read
        """
        self._chk()
        inst = self.instrument  # type: ignore


        # Configure waveform transfer
        inst.write(f":WAVeform:SOURce {source}")
        inst.write(":WAVeform:FORMat BYTE")
        inst.write(":WAVeform:BYTeorder LSBFirst")
        inst.write(f":WAVeform:POINts:MODE {points_mode}")
        if points is not None:
            inst.write(f":WAVeform:POINts {int(points)}")

        # Read scaling (preamble)
        meta = self._read_preamble()
        xincr = meta["xincr"]
        xorig = meta["xorig"]
        yincr = meta["yincr"]
        yorig = meta["yorig"]
        yref  = meta["yref"]
        sample_rate = 1.0 / xincr if xincr > 0 else float("nan")
        meta["sample_rate_hz"] = sample_rate

        # Fetch binary data (unsigned bytes 0..255)
        raw: List[int] = inst.query_binary_values(":WAVeform:DATA?",
                                                  datatype='B',
                                                  is_big_endian=False,
                                                  container=list,
                                                  chunk_size=self._chunk_size)

        n = len(raw)
        if debug:
            print(f"[{source}] points={n}, xincr={xincr} s, Fs={sample_rate} Hz")

        # Convert to time and volts
        t = [xorig + i * xincr for i in range(n)]
        y = [(v - yref) * yincr + yorig for v in raw]

        # Add a few more helpful fields
        meta.update({
            "source": source,
            "npoints": n,
            "dt_s": xincr,
            "t_start_s": t[0] if n else None,
            "t_stop_s": t[-1] if n else None,
        })
        return t, y, meta