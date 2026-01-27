# libs/ Device Driver Quick Reference

This is a quick reference guide for the most common patterns when working with device drivers in the `libs/` directory. For complete details, see [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md).

## Quick Comparison Table

| Feature | ❌ Bad Practice | ✅ Good Practice |
|---------|----------------|------------------|
| **Imports** | `import pyvisa` | `from __future__ import annotations`<br>`from typing import Optional`<br>`import pyvisa` |
| **Exception Handling** | `except:` | `except pyvisa.VisaIOError as e:`<br>`except ConnectionError as e:` |
| **Connection** | `self.ser = serial.Serial('COM10', 9600)` | `def connect(self, address: Optional[str] = None):`<br>with auto-detection |
| **Type Hints** | `def measure():` | `def measure(self) -> float:` |
| **Docstrings** | No docstrings | Comprehensive docstrings with Args, Returns, Raises |
| **Error Messages** | `print("Error")` | `print(_ERROR_STYLE + "Device not found")` |
| **Disconnect** | No disconnect method | `def disconnect(self) -> None:` |
| **Method Names** | `meas()`, `get_val()` | `measure_voltage()`, `measure_current()` |

## Template Files

Use these as references when creating new drivers:
- **Best Overall:** `DMM6500.py` (score: 95/100)
- **Complex Example:** `StanfordPS310.py` (score: 90/100)
- **Oscilloscope:** `KeysightMSOX4154A.py` (score: 85/100)

## File Scores at a Glance

| Score | Status | Files |
|-------|--------|-------|
| 90-100 | ✅ Excellent | DMM6500, StanfordPS310 |
| 70-89 | 🟡 Good | KeysightMSOX4154A, Keysight34460A, RigolDS7034, RigolDP832 |
| 40-69 | 🟠 Fair | U1233A |
| 0-39 | 🔴 Needs Work | KS33500B, DL3021, EPS, FLUKE45, KA3010P, DAC, DP832 |

## Common Patterns

### 1. Connection Pattern (PyVISA)
```python
def connect(self, address: Optional[str] = None) -> None:
    """Connect to device via VISA."""
    # 1. Try explicit address
    if address:
        inst = self.rm.open_resource(address)
        inst.timeout = 20000
        idn = inst.query("*IDN?")
        # Verify device...
        
    # 2. Auto-detect by resource string pattern
    if self.instrument is None:
        for resource in self.rm.list_resources():
            if "DEVICE_ID" in resource:
                # Try connection...
                
    # 3. Fail if not found
    if self.instrument is None:
        raise ConnectionError(_ERROR_STYLE + "Device not found")
```

### 2. Connection Pattern (PySerial)
```python
def connect(self, com_port: Optional[str] = None, baud_rate: int = 9600) -> None:
    """Connect to device via serial."""
    # 1. Try environment variable
    if com_port is None:
        com_port = os.environ.get('DEVICE_COM_PORT')
    
    # 2. Prompt user for port selection
    if com_port is None:
        ports = serial.tools.list_ports.comports()
        # Display selection menu...
        
    # 3. Open connection
    self.ser = serial.Serial(com_port, baud_rate, timeout=5)
    self.ser.write(b'*IDN?\n')
    identity = self.ser.readline().decode('ascii').strip()
    # Verify device...
```

### 3. Measurement Method Pattern
```python
def measure_voltage(self) -> float:
    """Measure DC voltage in volts."""
    self._chk()  # Verify connected
    return float(self.instrument.query("MEASure:VOLTage:DC?"))
```

### 4. get() Method Pattern
```python
def get(self, item: str, channel: Optional[int] = None) -> float:
    """
    Get measurement by name.
    
    Args:
        item: 'voltage', 'current', 'resistance', 'statistics'
        channel: Optional channel number
        
    Returns:
        Measurement value
    """
    self._chk()
    
    handlers = {
        'voltage': self.measure_voltage,
        'current': self.measure_current,
        'statistics': self.calculate_statistics,
    }
    
    item_lower = item.strip().lower()
    if item_lower not in handlers:
        raise ValueError(_ERROR_STYLE + f"Invalid item: {item}")
    
    return handlers[item_lower]()
```

### 5. Statistics Pattern
```python
def calculate_statistics(self, n: int = 100) -> Tuple[float, float, float, float]:
    """
    Calculate statistics over n readings.
    
    Returns:
        Tuple of (mean, stdev, min, max)
    """
    import statistics
    
    values = [self.measure_voltage() for _ in range(n)]
    return (
        statistics.fmean(values),
        statistics.pstdev(values) if len(values) > 1 else 0.0,
        min(values),
        max(values)
    )
```

### 6. Disconnect Pattern
```python
def disconnect(self) -> None:
    """Close connection and clean up resources."""
    if self.instrument is not None:
        try:
            self.instrument.close()
        finally:
            print(f"\rDisconnected from {self.__class__.__name__} at {self.address}")
            self.instrument = None
            self.status = "Not Connected"
            self.address = None
```

## Most Common Issues to Fix

### Issue 1: Bare Except Blocks
❌ **Bad:**
```python
try:
    value = self.instrument.query("*IDN?")
except:
    pass
```

✅ **Good:**
```python
try:
    value = self.instrument.query("*IDN?")
except pyvisa.VisaIOError as e:
    raise ConnectionError(_ERROR_STYLE + f"Communication error: {e}")
except Exception as e:
    raise ConnectionError(_ERROR_STYLE + f"Unexpected error: {e}")
```

### Issue 2: Hardcoded Ports
❌ **Bad:**
```python
def __init__(self):
    self.ser = serial.Serial('COM10', 9600)
```

✅ **Good:**
```python
def __init__(self, auto_connect: bool = True, com_port: Optional[str] = None):
    self.address = None
    self.ser = None
    if auto_connect:
        self.connect(com_port)
```

### Issue 3: No Type Hints
❌ **Bad:**
```python
def measure_voltage(self):
    return float(self.instrument.query("VOLT?"))
```

✅ **Good:**
```python
def measure_voltage(self) -> float:
    """Measure DC voltage in volts."""
    return float(self.instrument.query("VOLT?"))
```

### Issue 4: Missing Docstrings
❌ **Bad:**
```python
def configure(self, type, range, resolution):
    command = f"CONF:{type} {range},{resolution}"
    self.instrument.write(command)
```

✅ **Good:**
```python
def configure(self, measurement_type: str, range_val: float, resolution_val: float) -> None:
    """
    Configure measurement settings.
    
    Args:
        measurement_type: Type of measurement ('VOLTAGE:DC', 'CURRENT:DC', etc.)
        range_val: Measurement range in measurement units
        resolution_val: Resolution in measurement units
    """
    command = f"CONF:{measurement_type} {range_val},{resolution_val}"
    self.instrument.write(command)
```

### Issue 5: No Connection Check
❌ **Bad:**
```python
def measure_voltage(self):
    return float(self.instrument.query("VOLT?"))
```

✅ **Good:**
```python
def _chk(self) -> None:
    """Verify device is connected."""
    if self.status != "Connected" or self.instrument is None:
        raise ConnectionError(_ERROR_STYLE + "Not connected")

def measure_voltage(self) -> float:
    """Measure DC voltage."""
    self._chk()
    return float(self.instrument.query("VOLT?"))
```

## Checklist for New Drivers

When creating a new driver, ensure:

- [ ] File header with license and metadata
- [ ] `from __future__ import annotations` import
- [ ] Type hints on all public methods
- [ ] Docstrings on class and all public methods
- [ ] `__init__` with `auto_connect: bool = True` parameter
- [ ] `connect()` method with auto-detection + explicit address
- [ ] `disconnect()` method with resource cleanup
- [ ] `_chk()` helper for connection verification
- [ ] Specific exceptions (no bare `except:`)
- [ ] Standard console output styles (_ERROR_STYLE, etc.)
- [ ] Standard method names (`measure_*`, not `meas`)
- [ ] `get()` method with dispatch table
- [ ] Loading module fallback pattern
- [ ] No hardcoded addresses/ports
- [ ] Tested with actual hardware (if available)

## Quick Start for Updates

To update an existing driver to meet standards:

1. **Add type hints** to all methods
2. **Replace bare except** with specific exceptions
3. **Add docstrings** to all public methods
4. **Add disconnect()** if missing
5. **Remove hardcoded ports/addresses**
6. **Add auto_connect parameter**
7. **Standardize method names** (meas → measure_*)
8. **Update get() method** for consistency
9. **Test backward compatibility**

## Priority Order for Fixes

High Priority (Do First):
1. Add `disconnect()` method
2. Remove hardcoded COM ports/addresses
3. Replace bare `except:` blocks
4. Add connection check (`_chk()`)

Medium Priority (Do Next):
5. Add type hints
6. Add docstrings
7. Standardize method names
8. Add `auto_connect` parameter

Low Priority (Polish):
9. Improve error messages
10. Add debug logging
11. Optimize performance
12. Add advanced features

## Resources

- **Full Standard:** [DEVICE_DRIVER_STANDARD.md](./DEVICE_DRIVER_STANDARD.md)
- **Implementation Plan:** [LIBS_CONSISTENCY_PLAN.md](./LIBS_CONSISTENCY_PLAN.md)
- **Best Examples:** `libs/DMM6500.py`, `libs/StanfordPS310.py`
- **Python Style:** [PEP 8](https://pep8.org/)
- **Type Hints:** [PEP 484](https://www.python.org/dev/peps/pep-0484/)

---

**Last Updated:** January 2026  
**Quick Reference Version:** 1.0
