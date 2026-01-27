# Device Driver Gold Standard

This document defines the gold standard for all device driver files in the `libs/` directory. All new drivers MUST follow these standards, and existing drivers SHOULD be updated to comply.

## Table of Contents
1. [File Structure](#file-structure)
2. [Imports and Dependencies](#imports-and-dependencies)
3. [Class Structure](#class-structure)
4. [Connection Management](#connection-management)
5. [Error Handling](#error-handling)
6. [Console Output](#console-output)
7. [Measurement Methods](#measurement-methods)
8. [API Interface (get method)](#api-interface-get-method)
9. [Type Hints](#type-hints)
10. [Documentation](#documentation)
11. [Examples](#examples)

---

## File Structure

### Header Template
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   @file YourDevice.py
#   @brief Brief description of the device and its purpose
#   @date DD-Mon-YYYY
#   @author Your Name
#
#   Licensed to the Apache Software Foundation (ASF) under one
#   or more contributor license agreements. [... standard Apache 2.0 header ...]
```

### Required Sections
1. **Header**: File metadata, author, license
2. **Imports**: Standard library → Third-party → Local
3. **Constants**: Module-level configuration
4. **Class Definition**: Main device class
5. **Test Code**: `if __name__ == "__main__":` block (optional)

---

## Imports and Dependencies

### Standard Import Pattern

#### For PyVISA Devices
```python
from __future__ import annotations

import time
from typing import Optional, Tuple, List, Dict, Literal

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
```

#### For PySerial Devices
```python
from __future__ import annotations

import os
import time
from typing import Optional, Tuple, List

import serial
import serial.tools.list_ports
from colorama import init, Fore, Style

# Same loading fallback pattern as above
```

### Constants
```python
# Console output styles
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "

# Timing
_DELAY = 0.1  # seconds
_CONNECTION_TIMEOUT = 5  # seconds
```

---

## Class Structure

### Required Attributes
```python
class DeviceName:
    """
    Brief description of the device.
    
    Attributes:
        rm: PyVISA ResourceManager (for VISA devices) or None (for serial)
        address: Device address/COM port (str or None)
        instrument: Active connection handle
        status: Connection status ("Connected" or "Not Connected")
        loading: Loading indicator helper
        
    Example:
        device = DeviceName()
        voltage = device.measure_voltage()
        device.disconnect()
    """
    
    def __init__(self, auto_connect: bool = True, address: Optional[str] = None):
        """
        Initialize device driver.
        
        Args:
            auto_connect: Automatically connect to device on initialization
            address: Optional explicit address (VISA resource string or COM port)
        """
        init(autoreset=True)
        
        # PyVISA devices
        self.rm: Optional[pyvisa.ResourceManager] = pyvisa.ResourceManager()
        # OR for serial devices:
        # self.rm = None
        
        self.address: Optional[str] = None
        self.instrument: Optional[pyvisa.resources.MessageBasedResource] = None
        self.status: str = "Not Connected"
        self.loading = loading()
        self._address_hint: Optional[str] = address
        
        if auto_connect:
            self.connect(address=address)
```

---

## Connection Management

### PyVISA Connection Pattern

```python
def connect(self, address: Optional[str] = None) -> None:
    """
    Establish connection to device.
    
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
            inst.timeout = 20000  # milliseconds
            
            # Verify device identity
            idn = inst.query("*IDN?").strip()
            if "EXPECTED_DEVICE_ID" not in idn:
                inst.close()
                raise ConnectionError(
                    _ERROR_STYLE + f"Device at '{explicit}' is not a {self.__class__.__name__}"
                )
            
            self.instrument = inst
            self.address = explicit
        except Exception as e:
            raise ConnectionError(
                _ERROR_STYLE + f"Failed to connect to '{explicit}': {e}"
            )
    
    # 2) Auto-detect by scanning resources
    if self.instrument is None:
        resources = self.rm.list_resources()
        for resource in resources:
            if "DEVICE_IDENTIFIER" in resource:  # e.g., "6500", "MY59"
                try:
                    inst = self.rm.open_resource(resource)
                    inst.read_termination = '\n'
                    inst.write_termination = '\n'
                    inst.timeout = 20000
                    
                    idn = inst.query("*IDN?").strip()
                    if "EXPECTED_DEVICE_ID" in idn:
                        self.instrument = inst
                        self.address = resource
                        break
                    inst.close()
                except Exception:
                    continue
    
    # 3) Fail if no device found
    if self.instrument is None:
        raise ConnectionError(_ERROR_STYLE + f"{self.__class__.__name__} not found")
    
    # 4) Initialize device
    try:
        self.instrument.write("*CLS")  # Clear status
    except Exception:
        pass
    
    self.status = "Connected"
    print(_SUCCESS_STYLE + f"Connected to {self.__class__.__name__} at {self.address}")
```

### PySerial Connection Pattern

```python
def connect(self, com_port: Optional[str] = None, baud_rate: int = 9600) -> None:
    """
    Establish connection to serial device.
    
    Args:
        com_port: Optional COM port (e.g., 'COM3', '/dev/ttyUSB0'). If None, prompt user.
        baud_rate: Serial baud rate (default: 9600)
        
    Raises:
        ConnectionError: If device not found or connection fails.
    """
    # 1) Try environment variable
    if com_port is None:
        try:
            com_port = os.environ.get('DEVICE_COM_PORT_ENV_VAR')
        except Exception:
            pass
    
    # 2) Prompt user to select COM port
    if com_port is None:
        ports = serial.tools.list_ports.comports()
        if not ports:
            raise ConnectionError(_ERROR_STYLE + "No COM ports found")
        
        print("\nAvailable COM ports:")
        for i, port in enumerate(ports, start=1):
            print(f"  {i}. {port.device} - {port.description}")
        
        while True:
            try:
                selection = int(input("Select COM port (1, 2, ...): "))
                if 1 <= selection <= len(ports):
                    com_port = ports[selection - 1].device
                    os.environ['DEVICE_COM_PORT_ENV_VAR'] = com_port
                    break
                print(_ERROR_STYLE + "Invalid selection")
            except ValueError:
                print(_ERROR_STYLE + "Invalid input. Enter a number.")
    
    # 3) Open serial connection
    try:
        self.ser = serial.Serial(com_port, baud_rate, timeout=5)
        self.address = com_port
        self.status = "Connected"
        
        # Verify device identity
        self.ser.write(b'*IDN?\n')
        time.sleep(0.1)
        identity = self.ser.readline().decode('ascii').strip()
        
        if len(identity) < 5:
            raise ConnectionError("Device not responding")
        
        print(_SUCCESS_STYLE + f"Connected to {identity} on {com_port}")
        
    except Exception as e:
        raise ConnectionError(_ERROR_STYLE + f"Failed to connect to {com_port}: {e}")
```

### Disconnect Pattern

```python
def disconnect(self) -> None:
    """Close the connection to the device."""
    if self.instrument is not None:  # For VISA devices
        try:
            self.instrument.close()
        finally:
            print(f"\rDisconnected from {self.__class__.__name__} at {self.address}")
            self.instrument = None
    
    # For serial devices, use:
    # if self.ser is not None and self.ser.is_open:
    #     self.ser.close()
    #     print(f"\rDisconnected from {self.__class__.__name__} on {self.address}")
    #     self.ser = None
    
    self.status = "Not Connected"
    self.address = None
```

---

## Error Handling

### ❌ NEVER Use Bare Except
```python
# BAD - catches everything including KeyboardInterrupt
try:
    result = self.instrument.query("*IDN?")
except:
    pass
```

### ✅ ALWAYS Use Specific Exceptions
```python
# GOOD - catches specific errors
try:
    result = self.instrument.query("*IDN?")
except pyvisa.VisaIOError as e:
    raise ConnectionError(_ERROR_STYLE + f"VISA communication error: {e}")
except Exception as e:
    raise ConnectionError(_ERROR_STYLE + f"Unexpected error: {e}")
```

### Connection Check Helper
```python
def _chk(self) -> None:
    """Verify device is connected before operations."""
    if self.status != "Connected" or self.instrument is None:
        raise ConnectionError(_ERROR_STYLE + f"Not connected to {self.__class__.__name__}")
```

---

## Console Output

### Standard Messages
```python
# Success (green)
print(_SUCCESS_STYLE + "Operation completed successfully")

# Error (red, with 'Error! ' prefix)
print(_ERROR_STYLE + "Connection failed: timeout")

# Warning (yellow, with 'Warning! ' prefix)
print(_WARNING_STYLE + "Auto-range disabled may affect accuracy")

# Info (no color)
print(f"\rConfiguration set: Range={range_val}, Resolution={resolution_val}")
```

### Logging for Debug Mode
```python
def __init__(self, auto_connect: bool = True, debug: bool = False):
    # ...
    self._debug = debug

def _log(self, message: str) -> None:
    """Log debug message if debug mode enabled."""
    if self._debug:
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")
```

---

## Measurement Methods

### Standard Method Naming
```python
def measure_voltage(self) -> float:
    """Measure DC voltage."""
    self._chk()
    return float(self.instrument.query("MEASure:VOLTage:DC?"))

def measure_current(self) -> float:
    """Measure DC current."""
    self._chk()
    return float(self.instrument.query("MEASure:CURRent:DC?"))

def measure_resistance(self, four_wire: bool = False) -> float:
    """
    Measure resistance.
    
    Args:
        four_wire: Use 4-wire (True) or 2-wire (False) measurement
        
    Returns:
        Resistance in ohms
    """
    self._chk()
    if four_wire:
        return float(self.instrument.query("MEASure:FRESistance?"))
    return float(self.instrument.query("MEASure:RESistance?"))
```

### Statistics Methods
```python
def calculate_statistics(
    self,
    n: int = 100,
    measurement_type: Optional[str] = None,
    delay_s: float = 0.0
) -> Tuple[float, float, float, float]:
    """
    Collect multiple readings and calculate statistics.
    
    Args:
        n: Number of readings to collect
        measurement_type: Type of measurement ('voltage', 'current', etc.). If None, use current function.
        delay_s: Delay between readings in seconds
        
    Returns:
        Tuple of (mean, stdev, min, max)
    """
    import statistics
    
    self._chk()
    
    values: List[float] = []
    for _ in range(max(1, int(n))):
        if measurement_type == 'voltage':
            values.append(self.measure_voltage())
        elif measurement_type == 'current':
            values.append(self.measure_current())
        # ... add other types
        
        if delay_s > 0:
            time.sleep(delay_s)
    
    mean = statistics.fmean(values)
    stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
    return mean, stdev, min(values), max(values)
```

---

## API Interface (get method)

### Standard get() Method
```python
def get(self, item: str, channel: Optional[int] = None) -> float:
    """
    Retrieve measurement value by name.
    
    Args:
        item: Measurement item name (case-insensitive)
              Valid values: 'voltage', 'current', 'resistance', 'statistics'
        channel: Optional channel number for multi-channel devices
        
    Returns:
        Measurement value or statistics tuple
        
    Raises:
        ValueError: If invalid item requested
        ConnectionError: If not connected to device
        
    Example:
        voltage = device.get('voltage')
        mean, stdev, min, max = device.get('statistics')
    """
    self._chk()
    
    item_lower = item.strip().lower()
    
    # Dispatch table
    handlers = {
        'voltage': self.measure_voltage,
        'current': self.measure_current,
        'resistance': lambda: self.measure_resistance(False),
        'statistics': lambda: self.calculate_statistics(),
    }
    
    if item_lower not in handlers:
        raise ValueError(
            _ERROR_STYLE + f"Invalid item '{item}'. "
            f"Valid items: {', '.join(handlers.keys())}"
        )
    
    return handlers[item_lower]()
```

### Multi-Channel Devices
```python
def get(self, item: str, channel: int = 1) -> float:
    """Get measurement from specified channel."""
    self._chk()
    
    if not (1 <= channel <= self.num_channels):
        raise ValueError(
            _ERROR_STYLE + f"Invalid channel {channel}. "
            f"Valid range: 1-{self.num_channels}"
        )
    
    # ... rest of implementation
```

---

## Type Hints

### Required Type Hints
- **All public methods**: Parameters and return types
- **Constructor**: All parameters
- **Class attributes**: In docstring or as annotations
- **Complex return types**: Use `Tuple`, `List`, `Dict`, `Optional`

### Examples
```python
from typing import Optional, Tuple, List, Dict, Literal

def configure(
    self,
    measurement_type: Literal["voltage", "current", "resistance"],
    range_val: float,
    resolution_val: float
) -> None:
    """Configure measurement settings."""
    pass

def get_waveform(self, source: str = "CHAN1") -> Tuple[List[float], List[float], Dict[str, float]]:
    """
    Capture waveform data.
    
    Returns:
        Tuple of (time_array, voltage_array, metadata_dict)
    """
    pass
```

---

## Documentation

### Class Docstring Template
```python
class DeviceName:
    """
    Driver for [Manufacturer] [Model] [Type].
    
    This class provides methods for connecting to and controlling a
    [brief description of device capabilities].
    
    Attributes:
        rm: PyVISA ResourceManager instance
        address: Device VISA address or COM port
        instrument: Active connection handle
        status: Connection status string
        
    Example:
        >>> device = DeviceName()
        >>> device.configure('voltage', 10.0, 0.001)
        >>> voltage = device.measure_voltage()
        >>> print(f"Voltage: {voltage:.4f} V")
        >>> device.disconnect()
        
    Note:
        This driver requires [specific dependencies or hardware setup].
    """
```

### Method Docstring Template
```python
def method_name(self, param1: str, param2: Optional[float] = None) -> float:
    """
    Brief one-line description.
    
    Detailed explanation of what the method does, including any important
    behavior, side effects, or state changes.
    
    Args:
        param1: Description of first parameter
        param2: Description of optional second parameter. Defaults to None.
        
    Returns:
        Description of return value
        
    Raises:
        ConnectionError: If device is not connected
        ValueError: If invalid parameter provided
        
    Example:
        >>> result = device.method_name("test", 3.14)
        >>> print(f"Result: {result}")
        
    Note:
        Any additional information, warnings, or caveats.
    """
```

---

## Examples

### Complete Modern Driver Template

See `libs/DMM6500.py` for a comprehensive example following all standards.

**Key features of DMM6500.py:**
- ✅ Full type hints with `from __future__ import annotations`
- ✅ Structured error handling (no bare except)
- ✅ Auto-connect with optional explicit addressing
- ✅ Comprehensive docstrings
- ✅ Standard console output styles
- ✅ Helper methods for common operations
- ✅ Statistics support
- ✅ Proper disconnect handling

### Minimal Compliant Driver

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional
import pyvisa
from colorama import init, Fore, Style

_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"

class MinimalDevice:
    """Minimal compliant device driver example."""
    
    def __init__(self, auto_connect: bool = True, address: Optional[str] = None):
        init(autoreset=True)
        self.rm = pyvisa.ResourceManager()
        self.address: Optional[str] = None
        self.instrument: Optional[pyvisa.resources.MessageBasedResource] = None
        self.status = "Not Connected"
        
        if auto_connect:
            self.connect(address)
    
    def connect(self, address: Optional[str] = None) -> None:
        """Establish connection to device."""
        # Implementation here
        pass
    
    def disconnect(self) -> None:
        """Close connection to device."""
        if self.instrument is not None:
            try:
                self.instrument.close()
            finally:
                self.instrument = None
                self.status = "Not Connected"
    
    def _chk(self) -> None:
        """Verify device is connected."""
        if self.status != "Connected" or self.instrument is None:
            raise ConnectionError(_ERROR_STYLE + "Not connected")
    
    def measure_voltage(self) -> float:
        """Measure voltage."""
        self._chk()
        return float(self.instrument.query("MEASure:VOLTage:DC?"))
    
    def get(self, item: str) -> float:
        """Get measurement by name."""
        self._chk()
        if item.lower() == 'voltage':
            return self.measure_voltage()
        raise ValueError(_ERROR_STYLE + f"Invalid item: {item}")
```

---

## Migration Checklist

When updating an existing driver to comply with this standard:

- [ ] Add file header with Apache 2.0 license
- [ ] Add `from __future__ import annotations`
- [ ] Add type hints to all public methods
- [ ] Replace bare `except:` with specific exceptions
- [ ] Add `auto_connect` parameter to `__init__`
- [ ] Remove hardcoded COM ports/addresses
- [ ] Add `disconnect()` method
- [ ] Add comprehensive docstrings
- [ ] Standardize console output styles
- [ ] Implement standard `get()` method interface
- [ ] Add `_chk()` helper for connection verification
- [ ] Update method names to `measure_*` convention
- [ ] Add loading module fallback pattern
- [ ] Test backward compatibility with data_logger.py

---

## References

- **Best Examples**: `DMM6500.py`, `StanfordPS310.py`, `KeysightMSOX4154A.py`
- **PEP 8**: Python Style Guide
- **PEP 484**: Type Hints
- **PEP 257**: Docstring Conventions

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Maintainer**: Lab Data Logging Team
