#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   @file RSA3030.py
#   @brief Driver for Rigol RSA3030-TG Spectrum Analyzer using SCPI commands.
#   @date 12-Feb-2026

"""
Rigol RSA3030-TG Spectrum Analyzer Driver
=========================================

This module provides a SCPI-based driver for the Rigol RSA3030-TG spectrum analyzer
with support for auto-detection, USB, and Ethernet connectivity.

Features
--------
- **Auto-Detection**: Automatically finds RSA3030 on the VISA bus (USB or Ethernet)
- **Ethernet Support**: Connect via IP address or TCPIP VISA resource string
- **USB Support**: Traditional USB connection via PyVISA
- **Full SCPI Control**: Direct low-level SCPI commands via query/write methods
- **Identity Query**: Retrieve instrument identification information
- **Type Hints**: Full type annotations for improved IDE support

Basic Usage
-----------
```python
from libs.RSA3030 import RSA3030

# Auto-connect (scans for 'RSA3030' in VISA resources)
rsa = RSA3030()

# Get instrument identification
identity = rsa.get_identity()
print(f"Connected to: {identity}")

# Clean up
rsa.disconnect()
```

Explicit Addressing
-------------------
```python
# Connect to specific USB VISA address
rsa = RSA3030(auto_connect=False)
rsa.connect(address="USB0::0x1AB1::0x0960::RSA3XXXXXXXX::INSTR")

# Connect via Ethernet using IP address
rsa = RSA3030(auto_connect=False)
rsa.connect(ip_address="192.168.1.100")

# Or provide IP address at initialization
rsa = RSA3030(ip_address="192.168.1.100")

# Connect to specific TCPIP VISA address
rsa = RSA3030(auto_connect=False)
rsa.connect(address="TCPIP0::192.168.1.100::INSTR")
```

Identity Query
--------------
```python
# Get instrument identification
identity = rsa.get_identity()
print(f"Instrument: {identity}")

# Using the generic get() method
identity = rsa.get("identity")
print(f"Instrument: {identity}")
```

Integration with data_logger
----------------------------
```python
from data_logger import data_logger

logger = data_logger()
logger.new_file("rsa3030_measurements.txt")

rsa = logger.connect("rsa3030")
logger.add(rsa, "identity", label="Instrument_ID")

# Collect measurements
logger.get_data()
    
logger.close_file()
```

Advanced Configuration
----------------------
```python
# Direct SCPI query
idn = rsa.instrument.query("*IDN?")
print(f"Connected to: {idn}")

# Direct SCPI command
rsa.instrument.write(":SYSTem:PRESet")
```

Supported Measurement Commands (for use with data_logger)
----------------------------------------------------------
The following commands are supported by the `get(item)` method:

- **"identity"** - Returns instrument identification string (*IDN? response)

Example:
```python
rsa = logger.connect("rsa3030")
identity = rsa.get("identity")
```

Measurement Functions
---------------------
- `get_identity()` - Retrieve instrument identification
- `get(item)` - Generic measurement getter (identity)

Configuration Functions
-----------------------
- `connect(address, ip_address)` - Establish connection
- `disconnect()` - Close connection

Error Handling
--------------
```python
try:
    rsa = RSA3030(address="WRONG::ADDRESS")
except ConnectionError as e:
    print(f"Connection failed: {e}")

try:
    identity = rsa.get_identity()
except Exception as e:
    print(f"Query failed: {e}")
```

SCPI Command Reference
-----------------------
The RSA3030 uses standard SCPI commands:
- `*IDN?` - Query instrument identification
- `*RST` - Reset instrument to default state
- `*CLS` - Clear status registers

Technical Specifications
------------------------
- **Frequency Range**: 9 kHz to 3 GHz
- **Interface**: USB, Ethernet/LAN via PyVISA
- **Ethernet**: Supports TCPIP connections via IP address (e.g., 192.168.1.100)
- **USB**: Supports standard USB VISA connections (e.g., USB0::0x1AB1::0x0960::...::INSTR)
- **Manufacturer**: Rigol Technologies
- **Model**: RSA3030-TG

Network Configuration
---------------------
**Finding the RSA3030 IP Address:**

1. On the RSA3030 front panel, press **System** or **Menu**
2. Navigate to: **Interface > LAN**
3. Note the displayed IP address

**Configuring Network Settings:**

1. Access the LAN settings menu
2. Configure network mode (DHCP or Static)
3. If using static IP, configure:
   - IP Address
   - Subnet Mask
   - Gateway
4. Apply settings and restart if necessary

**Network Requirements:**
- RSA3030 must be connected via Ethernet cable
- Computer and RSA3030 should be on the same network
- Firewall should allow VISA/LXI communication (typically port 5025)

Testing the Driver
------------------
Use the provided test script to verify connectivity:

```bash
# Auto-connect test
python test_rsa3030.py

# Connect via IP address
python test_rsa3030.py --ip 192.168.1.100

# Connect via explicit VISA address
python test_rsa3030.py --address "TCPIP0::192.168.1.100::INSTR"

# Interactive mode
python test_rsa3030.py --interactive

# Debug mode (shows detailed connection process)
python test_rsa3030.py --debug
```

Troubleshooting
---------------
**Connection Issues:**

1. **Find the actual IP address on the device:**
   - Check System > Interface > LAN settings
   - Verify network connectivity with ping

2. **Test network connectivity:**
   ```bash
   ping 192.168.1.100  # Replace with your RSA3030 IP
   ```

3. **Verify VISA resources are visible:**
   ```bash
   python -c "import pyvisa; rm = pyvisa.ResourceManager(); print(rm.list_resources())"
   ```

4. **Check USB connection:**
   - Ensure USB cable is connected
   - Verify VISA drivers are installed (NI-VISA or similar)

See Also
--------
- DMM6500: Similar connection pattern implementation
- data_logger: Main orchestrator class
- Device driver standard: docs/DEVICE_DRIVER_STANDARD.md
"""

from __future__ import annotations

import time
from typing import Optional

import pyvisa
from colorama import init, Fore, Style

# Optional "loading" helper
try:
    from loading import loading
except Exception:
    class loading:
        def delay_with_loading_indicator(self, seconds: float) -> None:
            time.sleep(seconds)

# --- Console styles to match DMM6500 ---
_ERROR_STYLE   = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\r"
_DELAY         = 0.1


class RSA3030:
    """
    SCPI wrapper for Rigol RSA3030-TG Spectrum Analyzer.

    Example:
        rsa = RSA3030()                           # auto-detect
        identity = rsa.get_identity()
        print("Instrument:", identity)
        rsa.disconnect()
    """

    # -----------------------------
    # Init / Connect / Disconnect
    # -----------------------------
    def __init__(self, auto_connect: bool = True, address: Optional[str] = None, 
                 ip_address: Optional[str] = None, debug: bool = False):
        """
        Initialize RSA3030 driver.

        Args:
            auto_connect: If True, automatically connect during initialization.
            address: Explicit VISA resource string (e.g., "USB0::0x1AB1::0x0960::...::INSTR").
            ip_address: IP address for Ethernet connection (e.g., "192.168.1.100").
            debug: Enable debug output showing resource scanning details.
        """
        init(autoreset=True)

        self.rm = pyvisa.ResourceManager()
        self.address: Optional[str] = None
        self.instrument: Optional[pyvisa.resources.MessageBasedResource] = None
        self.loading = loading()
        self.status = "Not Connected"
        self._idn: Optional[str] = None
        self._address_hint = address
        self._ip_address = ip_address
        self.debug = debug

        if auto_connect:
            self.connect(address=self._address_hint, ip_address=self._ip_address)

    def connect(self, address: Optional[str] = None, ip_address: Optional[str] = None):
        """
        Establish a connection via USB or Ethernet.

        Args:
            address: Explicit VISA resource string. If None, auto-detect by scanning
                    USB resources containing 'RSA' or 'RSA3030' and all TCPIP resources,
                    then verify with *IDN? query.
            ip_address: IP address for Ethernet/LAN connection (e.g., "192.168.1.100").
                       If provided, constructs TCPIP resource string automatically.
        """
        # 1) Try IP address connection if provided
        ip = ip_address or self._ip_address
        if ip and not address and not self._address_hint:
            # Construct TCPIP resource string from IP address
            tcpip_address = f"TCPIP0::{ip}::INSTR"
            try:
                inst = self.rm.open_resource(tcpip_address)
                inst.read_termination = '\n'
                inst.write_termination = '\n'
                inst.timeout = 20000
                idn = inst.query("*IDN?").strip()
                if "RSA" in idn.upper() or "RIGOL" in idn.upper():
                    self.instrument = inst
                    self.address = tcpip_address
                    self._idn = idn
                    self.status = "Connected"
                    print(_SUCCESS_STYLE + f"Connected to RSA3030 via Ethernet at {ip} [{self._idn}]")
                    return
                else:
                    inst.close()
                    raise ConnectionError(_ERROR_STYLE +
                        f"Device at '{ip}' is not an RSA3030 (IDN='{idn}').")
            except Exception as e:
                raise ConnectionError(_ERROR_STYLE +
                    f"Failed to connect to RSA3030 at IP '{ip}': {e}")
        
        # 2) Try explicit address first (argument beats ctor hint)
        explicit = address or self._address_hint
        if explicit:
            try:
                inst = self.rm.open_resource(explicit)
                inst.read_termination = '\n'
                inst.write_termination = '\n'
                inst.timeout = 20000
                idn = inst.query("*IDN?").strip()
                if "RSA" in idn.upper() or "RIGOL" in idn.upper():
                    self.instrument = inst
                    self.address = explicit
                    self._idn = idn
                    self.status = "Connected"
                    print(_SUCCESS_STYLE + f"Connected to RSA3030 at {explicit} [{self._idn}]")
                    return
                else:
                    inst.close()
                    raise ConnectionError(_ERROR_STYLE +
                        f"Resource '{explicit}' is not an RSA3030 (IDN='{idn}').")
            except Exception as e:
                raise ConnectionError(_ERROR_STYLE +
                    f"Failed to open explicit address '{explicit}': {e}")

        # 3) Otherwise scan for resources with 'RSA' in the name (USB) or TCPIP resources
        # Note: Scans all TCPIP resources for maximum compatibility. Each resource is
        # verified with *IDN? query to confirm it's an RSA3030. For faster connection,
        # use explicit address or ip_address parameters.
        if self.instrument is None:
            resources = self.rm.list_resources()
            if self.debug:
                print(f"\n[DEBUG] Found {len(resources)} VISA resources:")
                for r in resources:
                    print(f"[DEBUG]   - {r}")
                print()
            
            for resource in resources:
                # Check TCPIP resources or USB resources containing 'RSA' or Rigol vendor ID
                if resource.startswith("TCPIP") or "RSA" in resource.upper() or "0x1AB1" in resource.upper():
                    if self.debug:
                        print(f"[DEBUG] Trying resource: {resource}")
                    try:
                        inst = self.rm.open_resource(resource)
                        inst.read_termination = '\n'
                        inst.write_termination = '\n'
                        inst.timeout = 20000
                        if self.debug:
                            print(f"[DEBUG]   - Opened connection, querying *IDN?...")
                        idn = inst.query("*IDN?").strip()
                        if self.debug:
                            print(f"[DEBUG]   - Response: {idn}")
                        if "RSA" in idn.upper() or "RIGOL" in idn.upper():
                            self.instrument = inst
                            self.address = resource
                            self._idn = idn
                            self.status = "Connected"
                            if self.debug:
                                print(f"[DEBUG]   - ✓ Match! Connected to RSA3030")
                            print(_SUCCESS_STYLE + f"Connected to RSA3030 at {self.address} [{self._idn}]")
                            return
                        else:
                            if self.debug:
                                print(f"[DEBUG]   - Not an RSA3030, closing connection")
                        inst.close()
                    except Exception as e:
                        if self.debug:
                            print(f"[DEBUG]   - Error: {e}")
                        continue
                else:
                    if self.debug:
                        print(f"[DEBUG] Skipping resource (doesn't match filter): {resource}")

        if self.instrument is None:
            raise ConnectionError(_ERROR_STYLE + "Rigol RSA3030 not found. Ensure device is connected and powered on.")

        # Clear status and cache ID
        try:
            self.instrument.write("*CLS")
        except Exception:
            pass

    def disconnect(self):
        """Close the VISA session."""
        if self.instrument is not None:
            try:
                self.instrument.close()
            finally:
                print(f"\rDisconnected from RSA3030 at {self.address}")
        self.status = "Not Connected"
        self.instrument = None
        self.address = None

    # -----------------------------
    # Helpers / SCPI utilities
    # -----------------------------
    def _chk(self):
        """Verify instrument is connected."""
        if self.status != "Connected" or self.instrument is None:
            raise ConnectionError(_ERROR_STYLE + "Not connected to RSA3030.")

    # -----------------------------
    # Measurement functions
    # -----------------------------
    def get_identity(self) -> str:
        """
        Query instrument identification.

        Returns:
            str: Instrument identification string (manufacturer, model, serial, firmware).
        """
        self._chk()
        return self.instrument.query("*IDN?").strip()

    def get(self, item: str):
        """
        Generic measurement getter for data_logger integration.

        Args:
            item: Measurement type to retrieve. Supported values:
                  - "identity": Instrument identification string

        Returns:
            Measurement value appropriate for the requested item.

        Raises:
            ValueError: If invalid item is requested.
        """
        k = item.strip().lower()
        if k == "identity":
            return self.get_identity()
        else:
            raise ValueError(_ERROR_STYLE + f"Invalid item: {item} request to RSA3030")
