#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   @file DMM6500.py
#   @brief Keysight-style wrapper for Keithley/Tektronix DMM6500 using pure SCPI.
#          "Digitize" helpers implemented via regular DMM mode + defbuffer1.
#   @date 15-Sep-2025

"""
Keithley/Tektronix DMM6500 6.5-Digit Multimeter Driver
=======================================================

This module provides a pure SCPI-based driver for the Keithley/Tektronix DMM6500 
digital multimeter with support for standard measurements and high-speed digitizing.

Features
--------
- **Auto-Detection**: Automatically finds DMM6500 on the VISA bus (USB or Ethernet)
- **Ethernet Support**: Connect via IP address or TCPIP VISA resource string
- **USB Support**: Traditional USB connection via PyVISA
- **Full SCPI Control**: Direct low-level SCPI commands via query/write methods
- **Digitizing Mode**: High-speed data acquisition up to 1 MS/s
- **Statistics Support**: Built-in mean, std dev, min, max calculations
- **Multiple Measurement Types**: DC/AC voltage, DC/AC current, resistance, 
  2-wire/4-wire resistance
- **Flexible Configuration**: Explicit range, resolution, and NPLC settings
- **Type Hints**: Full type annotations for improved IDE support

Basic Usage
-----------
```python
from libs.DMM6500 import DMM6500

# Auto-connect (scans for '6500' in VISA resources)
dmm = DMM6500()

# Simple voltage measurement
voltage = dmm.measure_voltage()
print(f"Voltage: {voltage:.6f} V")

# Clean up
dmm.disconnect()
```

Explicit Addressing
-------------------
```python
# Connect to specific USB VISA address
dmm = DMM6500(auto_connect=False)
dmm.connect(address="USB0::0x05E6::0x6500::04492372::INSTR")

# Connect via Ethernet using IP address
dmm = DMM6500(auto_connect=False)
dmm.connect(ip_address="192.168.1.100")

# Or provide IP address at initialization
dmm = DMM6500(ip_address="192.168.1.100")

# Connect to specific TCPIP VISA address
dmm = DMM6500(auto_connect=False)
dmm.connect(address="TCPIP0::192.168.1.100::inst0::INSTR")
```

Configured Measurements
-----------------------
```python
# Configure measurement parameters
dmm.configure("VOLTAGE:DC", max_value=10.0, resolution=1e-6)
voltage = dmm.measure_voltage()

# Configure resistance with 4-wire mode
dmm.configure("RESISTANCE:4W", max_value=1000.0, resolution=0.001)
resistance = dmm.measure_resistance()

# Configure current measurement
dmm.configure("CURRENT:DC", max_value=1.0, resolution=1e-6)
current = dmm.measure_current()
```

High-Speed Digitizing
---------------------
```python
# Capture high-speed voltage data
data = dmm.digitize_voltage(
    duration_s=2.0,      # 2 second capture
    fixed_range=10.0,    # 10V range
    nplc=0.001          # Fast sampling (~100kHz)
)
print(f"Captured {len(data)} samples")
print(f"Mean: {sum(data)/len(data):.6f} V")

# Digitize current
current_data = dmm.digitize_current(
    duration_s=1.0,
    fixed_range=0.1,     # 100mA range
    nplc=0.01
)
```

Statistics Measurements
-----------------------
```python
# Get statistics for voltage
stats = dmm.get("statistics")
# Returns: [mean, std_dev, min, max]
print(f"Mean: {stats[0]:.6f} V")
print(f"Std Dev: {stats[1]:.6f} V")
print(f"Min: {stats[2]:.6f} V")
print(f"Max: {stats[3]:.6f} V")
```

Integration with data_logger
-----------------------------
```python
from data_logger import data_logger

logger = data_logger()
logger.new_file("dmm6500_measurements.txt")

dmm = logger.connect("dmm6500")
logger.add(dmm, "voltage", label="DC_Voltage")
logger.add(dmm, "current", label="DC_Current")
logger.add(dmm, "statistics", label="Voltage_Stats")

# Collect measurements
for i in range(100):
    logger.get_data()
    
logger.close_file()
```

Advanced Configuration
----------------------
```python
# Set integration time (NPLC)
dmm.set_nplc(10)  # 10 power line cycles (slow, high accuracy)

# Set auto-zero mode
dmm.instrument.write(":SENS:VOLT:AZER ON")

# Set trigger model
dmm.instrument.write(":TRIG:LOAD 'Empty'")

# Direct SCPI query
idn = dmm.instrument.query("*IDN?")
print(f"Connected to: {idn}")
```

Supported Measurement Commands (for use with data_logger)
----------------------------------------------------------
The following commands are supported by the `get(item)` method:

- **"voltage"** - DC voltage measurement in volts
- **"current"** - DC current measurement in amperes
- **"resistance"** - 2-wire resistance measurement in ohms
- **"statistics"** - Returns [mean, std_dev, min, max] for current function

Example:
```python
dmm = logger.connect("dmm6500")
voltage = dmm.get("voltage")
stats = dmm.get("statistics")  # Returns: [mean, std_dev, min, max]
```

Measurement Functions
---------------------
- `measure_voltage()` - DC voltage measurement
- `measure_current()` - DC current measurement  
- `measure_resistance()` - 2-wire resistance measurement
- `digitize_voltage()` - High-speed voltage capture
- `digitize_current()` - High-speed current capture
- `get(item)` - Generic measurement getter (voltage, current, resistance, statistics)

Configuration Functions
-----------------------
- `configure(function, max_value, resolution)` - Set measurement parameters
- `set_nplc(nplc)` - Set integration time
- `connect(address)` - Establish connection
- `disconnect()` - Close connection

Buffer Operations
-----------------
```python
# Fetch data from internal buffer (defbuffer1)
data = dmm.fetch_trace()
print(f"Buffer contains {len(data)} readings")
```

Error Handling
--------------
```python
try:
    dmm = DMM6500(address="WRONG::ADDRESS")
except ConnectionError as e:
    print(f"Connection failed: {e}")

try:
    voltage = dmm.measure_voltage()
except Exception as e:
    print(f"Measurement failed: {e}")
```

SCPI Command Reference
-----------------------
The DMM6500 uses standard SCPI commands:
- `:SENS:FUNC "VOLT:DC"` - Select DC voltage function
- `:SENS:VOLT:RANG 10` - Set voltage range
- `:SENS:VOLT:NPLC 1` - Set integration time
- `:READ?` - Trigger and fetch reading
- `:CALC:STAT:AVER?` - Get average from statistics

Technical Specifications
------------------------
- **Resolution**: Up to 6.5 digits
- **Sampling Rate**: Up to 1 MS/s in digitize mode
- **Buffer Size**: 7 million readings in defbuffer1
- **Interface**: USB, Ethernet/LAN, GPIB via PyVISA
- **Supported Functions**: DCV, ACV, DCI, ACI, 2W/4W resistance, frequency, period
- **Ethernet**: Supports TCPIP connections via IP address (e.g., 192.168.1.100)
- **USB**: Supports standard USB VISA connections (e.g., USB0::0x05E6::0x6500::...::INSTR)

See Also
--------
- Keysight34460A: Alternative 6.5-digit DMM driver
- data_logger: Main orchestrator class
- Device driver standard: docs/DEVICE_DRIVER_STANDARD.md
"""

from __future__ import annotations

import ipaddress
import re
import socket
import struct
import subprocess
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


def _parse_tcpip_address(address: str) -> Tuple[Optional[str], Optional[int], bool]:
    """Return (host, port, is_socket_resource) for TCPIP VISA strings."""
    match = re.match(
        r"^TCPIP\d*::(?P<host>[^:]+)::(?:(?P<inst>inst\d+)::INSTR|(?P<port>\d+)::SOCKET)$",
        address,
        flags=re.IGNORECASE,
    )
    if not match:
        return None, None, False
    host = match.group("host")
    port = int(match.group("port")) if match.group("port") else 5025
    return host, port, bool(match.group("port"))


def _is_link_local_ipv4(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_link_local
    except ValueError:
        return False


def _same_link_local_subnet(ip_a: str, ip_b: str) -> bool:
    try:
        a = ipaddress.ip_address(ip_a)
        b = ipaddress.ip_address(ip_b)
    except ValueError:
        return False
    if not (a.is_link_local and b.is_link_local):
        return False
    return str(a).split('.')[:2] == str(b).split('.')[:2]


def _list_local_ipv4_addresses() -> List[str]:
    addresses: List[str] = []

    try:
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        matches = re.findall(r"(?:Autoconfiguration )?IPv4 Address[^:]*:\s*(\d+\.\d+\.\d+\.\d+)", result.stdout)
        for ip in matches:
            if ip not in addresses:
                addresses.append(ip)
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
            ip = info[4][0]
            if ip not in addresses:
                addresses.append(ip)
    except Exception:
        pass

    return addresses


def _select_source_ips(target_ip: str, requested_local_ip: Optional[str] = None) -> List[Optional[str]]:
    candidates: List[Optional[str]] = []

    if requested_local_ip:
        candidates.append(requested_local_ip)

    if _is_link_local_ipv4(target_ip):
        local_ips = [ip for ip in _list_local_ipv4_addresses() if _is_link_local_ipv4(ip)]
        preferred = [ip for ip in local_ips if _same_link_local_subnet(ip, target_ip)]
        fallback = [ip for ip in local_ips if ip not in preferred]
        for ip in preferred + fallback:
            if ip not in candidates:
                candidates.append(ip)

    if None not in candidates:
        candidates.append(None)

    return candidates


class _SocketSCPIResource:
    """Minimal SCPI-over-socket resource compatible with the driver methods used here."""

    def __init__(
        self,
        host: str,
        port: int = 5025,
        timeout_ms: int = 20000,
        source_ip: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self._timeout_ms = timeout_ms
        self.read_termination = '\n'
        self.write_termination = '\n'
        self._buffer = b''
        source_address = (source_ip, 0) if source_ip else None
        self._sock = socket.create_connection((host, port), timeout=timeout_ms / 1000.0, source_address=source_address)
        self._sock.settimeout(timeout_ms / 1000.0)

    @property
    def timeout(self) -> int:
        return self._timeout_ms

    @timeout.setter
    def timeout(self, value: int) -> None:
        self._timeout_ms = int(value)
        self._sock.settimeout(self._timeout_ms / 1000.0)

    def write(self, command: str) -> None:
        payload = command
        if self.write_termination and not payload.endswith(self.write_termination):
            payload += self.write_termination
        self._sock.sendall(payload.encode("ascii"))

    def _read_until_termination(self) -> str:
        terminator = (self.read_termination or '\n').encode("ascii")
        while terminator not in self._buffer:
            chunk = self._sock.recv(4096)
            if not chunk:
                break
            self._buffer += chunk

        if terminator in self._buffer:
            raw, self._buffer = self._buffer.split(terminator, 1)
        else:
            raw, self._buffer = self._buffer, b''
        return raw.decode("ascii", errors="replace").strip()

    def read(self) -> str:
        return self._read_until_termination()

    def query(self, command: str) -> str:
        self.write(command)
        return self.read()

    def query_ascii_values(self, command: str, container=list):
        response = self.query(command)
        if not response:
            return container()
        return container(float(part.strip()) for part in response.split(',') if part.strip())

    def close(self) -> None:
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        self._sock.close()


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
    def __init__(self, auto_connect: bool = True, address: Optional[str] = None, ip_address: Optional[str] = None, local_ip: Optional[str] = None, debug: bool = False):
        init(autoreset=True)

        self.rm = pyvisa.ResourceManager()
        self.address: Optional[str] = None
        self.instrument: Optional[object] = None
        self.loading = loading()
        self.status = "Not Connected"
        self._idn: Optional[str] = None
        self._address_hint = address
        self._ip_address = ip_address
        self._local_ip = local_ip
        self.debug = debug

        if auto_connect:
            self.connect(address=self._address_hint, ip_address=self._ip_address, local_ip=self._local_ip)

    def _configure_instrument(self, inst: object, timeout_ms: int = 20000) -> None:
        inst.read_termination = '\n'
        inst.write_termination = '\n'
        inst.timeout = timeout_ms

    def _finalize_connection(self, inst: object, address: str, idn: str) -> None:
        self.instrument = inst
        self.address = address
        self._idn = idn
        self.status = "Connected"

    def _connect_socket_fallback(self, host: str, port: int, requested_local_ip: Optional[str] = None) -> Tuple[object, str, Optional[str]]:
        attempts = []
        for source_ip in _select_source_ips(host, requested_local_ip):
            try:
                inst = _SocketSCPIResource(host=host, port=port, timeout_ms=20000, source_ip=source_ip)
                idn = inst.query("*IDN?").strip()
                if "DMM6500" not in idn:
                    inst.close()
                    raise ConnectionError(f"Device at '{host}:{port}' is not a DMM6500 (IDN='{idn}').")
                socket_address = f"TCPIP0::{host}::{port}::SOCKET"
                return inst, socket_address, source_ip
            except Exception as exc:
                label = source_ip or "default route"
                attempts.append(f"{label}: {exc}")

        detail = "; ".join(attempts) if attempts else "no socket attempts made"
        raise ConnectionError(f"Socket fallback failed for {host}:{port}: {detail}")

    def _build_link_local_hint(self, host: str, requested_local_ip: Optional[str] = None) -> str:
        if not _is_link_local_ipv4(host):
            return ""

        local_ips = [ip for ip in _list_local_ipv4_addresses() if _is_link_local_ipv4(ip)]
        if requested_local_ip and requested_local_ip not in local_ips:
            local_ips.insert(0, requested_local_ip)

        if local_ips:
            return (
                f" Link-local target {host} detected. Available local link-local IPv4 addresses: "
                f"{', '.join(local_ips)}. If Windows is routing over the wrong NIC, pass local_ip or --local-ip "
                f"to bind the connection to the correct adapter."
            )

        return (
            f" Link-local target {host} detected, but no local 169.254.x.x IPv4 address was found. "
            f"Configure the Ethernet adapter connected to the instrument with a 169.254.x.x address first."
        )

    def _connect_by_tcpip_host(self, host: str, requested_local_ip: Optional[str] = None) -> Tuple[object, str, Optional[str]]:
        visa_address = f"TCPIP0::{host}::inst0::INSTR"
        visa_error: Optional[Exception] = None

        try:
            inst = self.rm.open_resource(visa_address)
            self._configure_instrument(inst)
            idn = inst.query("*IDN?").strip()
            if "DMM6500" not in idn:
                inst.close()
                raise ConnectionError(f"Device at '{host}' is not a DMM6500 (IDN='{idn}').")
            return inst, visa_address, None
        except Exception as exc:
            visa_error = exc
            if self.debug:
                print(f"[DEBUG] VISA TCPIP connection failed for {visa_address}: {exc}")

        try:
            return self._connect_socket_fallback(host, 5025, requested_local_ip=requested_local_ip)
        except Exception as socket_exc:
            hint = self._build_link_local_hint(host, requested_local_ip=requested_local_ip)
            raise ConnectionError(
                _ERROR_STYLE +
                f"Failed to connect to DMM6500 at IP '{host}'. VISA error: {visa_error}. "
                f"Socket fallback error: {socket_exc}.{hint}"
            )

    def connect(self, address: Optional[str] = None, ip_address: Optional[str] = None, local_ip: Optional[str] = None):
        """
        Establish a connection via USB or Ethernet.

        Args:
            address: explicit VISA resource string. If None, auto-detect by scanning
                     USB resources containing '6500' and all TCPIP resources, then
                     verify with *IDN? query.
            ip_address: IP address for ethernet/LAN connection (e.g., "192.168.1.100").
                       If provided, constructs TCPIP resource string automatically.
            local_ip: Optional local IPv4 address to bind for Ethernet socket fallback.
                     Useful when multiple Ethernet adapters are present and Windows picks
                     the wrong route for a link-local instrument.
        """
        # 1) Try IP address connection if provided
        ip = ip_address or self._ip_address
        preferred_local_ip = local_ip or self._local_ip
        if ip and not address and not self._address_hint:
            inst, connected_address, bound_local_ip = self._connect_by_tcpip_host(ip, requested_local_ip=preferred_local_ip)
            self._finalize_connection(inst, connected_address, inst.query("*IDN?").strip())
            source_note = f" via local IP {bound_local_ip}" if bound_local_ip else ""
            print(_SUCCESS_STYLE + f"Connected to DMM6500 via Ethernet at {ip}{source_note} [{self._idn}]")
            return
        
        # 2) Try explicit address first (argument beats ctor hint)
        explicit = address or self._address_hint
        if explicit:
            host, port, is_socket_resource = _parse_tcpip_address(explicit)
            if host and _is_link_local_ipv4(host):
                try:
                    if is_socket_resource:
                        inst, connected_address, bound_local_ip = self._connect_socket_fallback(host, port or 5025, requested_local_ip=preferred_local_ip)
                    else:
                        inst, connected_address, bound_local_ip = self._connect_by_tcpip_host(host, requested_local_ip=preferred_local_ip)
                    self._finalize_connection(inst, connected_address, inst.query("*IDN?").strip())
                    source_note = f" via local IP {bound_local_ip}" if bound_local_ip else ""
                    print(_SUCCESS_STYLE + f"Connected to DMM6500 at {self.address}{source_note} [{self._idn}]")
                    return
                except Exception as exc:
                    raise ConnectionError(_ERROR_STYLE + f"Failed to open explicit address '{explicit}': {exc}")

            try:
                inst = self.rm.open_resource(explicit)
                self._configure_instrument(inst)
                idn = inst.query("*IDN?").strip()
                if "DMM6500" in idn:
                    self._finalize_connection(inst, explicit, idn)
                else:
                    inst.close()
                    raise ConnectionError(_ERROR_STYLE +
                        f"Resource '{explicit}' is not a DMM6500 (IDN='{idn}').")
            except Exception as e:
                raise ConnectionError(_ERROR_STYLE +
                    f"Failed to open explicit address '{explicit}': {e}")

        # 3) Otherwise scan for resources with '6500' in the name (USB) or TCPIP resources
        # Note: Scans all TCPIP resources for maximum compatibility. Each resource is
        # verified with *IDN? query to confirm it's a DMM6500. For faster connection,
        # use explicit address or ip_address parameters.
        if self.instrument is None:
            resources = self.rm.list_resources()
            if self.debug:
                print(f"\n[DEBUG] Found {len(resources)} VISA resources:")
                for r in resources:
                    print(f"[DEBUG]   - {r}")
                print()
            
            for resource in resources:
                # Check TCPIP resources or USB resources containing '6500'
                if resource.startswith("TCPIP") or "6500" in resource:
                    if self.debug:
                        print(f"[DEBUG] Trying resource: {resource}")
                    try:
                        inst = self.rm.open_resource(resource)
                        self._configure_instrument(inst)
                        if self.debug:
                            print(f"[DEBUG]   - Opened connection, querying *IDN?...")
                        idn = inst.query("*IDN?").strip()
                        if self.debug:
                            print(f"[DEBUG]   - Response: {idn}")
                        if "DMM6500" in idn:
                            self._finalize_connection(inst, resource, idn)
                            if self.debug:
                                print(f"[DEBUG]   - ✓ Match! Connected to DMM6500")
                            break
                        else:
                            if self.debug:
                                print(f"[DEBUG]   - Not a DMM6500, closing connection")
                        inst.close()
                    except Exception as e:
                        if self.debug:
                            print(f"[DEBUG]   - Error: {e}")
                        continue
                else:
                    if self.debug:
                        print(f"[DEBUG] Skipping resource (doesn't match filter): {resource}")

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