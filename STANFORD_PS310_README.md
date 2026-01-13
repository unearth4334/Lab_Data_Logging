# Stanford PS310 Power Supply (Negative Model) - Usage Guide

## Overview

The `StanfordPS310` library provides an interface for controlling the Stanford PS310 Power Supply negative model. This particular model requires **negative voltage values** for the `set_voltage()` method.

## Key Features

- **Negative Voltage Validation**: The library enforces that all voltage values must be negative (< 0)
- **PyVISA Communication**: Uses PyVISA for VISA instrument communication
- **Colorama Output**: Provides colored terminal output for better user experience
- **Error Handling**: Comprehensive error handling with descriptive messages

## Installation

The library is already integrated into the Lab Data Logging framework. Ensure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

## Usage Examples

### Basic Usage with data_logger

```python
from data_logger import data_logger

# Create data logger instance
logger = data_logger()

# Connect to Stanford PS310
ps310 = logger.connect("stanfordps310")

# Set negative voltage (required for negative model)
ps310.set_voltage(-5.0)  # ✓ Valid: negative voltage

# Measure voltage and current
voltage = ps310.measure_voltage()
current = ps310.measure_current()

# Control output
ps310.set_output_state(True)   # Turn on
ps310.set_output_state(False)  # Turn off
```

### Direct Usage

```python
from libs.StanfordPS310 import StanfordPS310

# Create instance (auto-connects by default)
power_supply = StanfordPS310()

# Set negative voltage
power_supply.set_voltage(-10.5)  # ✓ Valid

# Set current limit
power_supply.set_current(1.0)

# Measure values
voltage = power_supply.measure_voltage()
current = power_supply.measure_current()

# Disconnect
power_supply.disconnect()
```

## Important: Negative Voltage Requirement

This is a **negative model** Stanford PS310 power supply. The `set_voltage()` method **only accepts negative values**:

### ✓ Valid Examples
```python
ps310.set_voltage(-5.0)   # OK
ps310.set_voltage(-10.5)  # OK
ps310.set_voltage(-0.5)   # OK
```

### ✗ Invalid Examples (Will Raise ValueError)
```python
ps310.set_voltage(5.0)    # ERROR: Must be negative
ps310.set_voltage(0.0)    # ERROR: Must be negative
ps310.set_voltage(10.5)   # ERROR: Must be negative
```

## Error Messages

If you attempt to set a non-negative voltage, you will receive an error message like:

```
Error! Invalid voltage value "5.0". This is a negative model Stanford PS310 - voltage must be negative (e.g., -5.0 V).
```

## Methods

### Connection Methods
- `__init__(auto_connect=True)`: Initialize the power supply
- `connect()`: Manually connect to the device
- `disconnect()`: Disconnect from the device

### Control Methods
- `set_voltage(voltage)`: Set output voltage (must be negative)
- `set_current(current)`: Set current limit (positive value)
- `set_output_state(state)`: Turn output on/off

### Measurement Methods
- `measure_voltage()`: Measure output voltage
- `measure_current()`: Measure output current
- `get(item, channel=1)`: Generic measurement interface

### Status Methods
- `get_output_state()`: Check if output is on or off

## Testing

A comprehensive test suite is provided in `test_stanfordps310.py`:

```bash
python3 test_stanfordps310.py
```

This test validates:
1. Negative voltage acceptance
2. Positive voltage rejection
3. Zero voltage rejection
4. Non-numeric input rejection
5. Proper error messages

## Device Connection

The library automatically detects Stanford PS310 devices by searching for 'PS310' or 'PS 310' in the VISA resource names. Ensure your device is:

1. Properly connected via USB/GPIB/Ethernet
2. Powered on
3. Visible to PyVISA (check with `pyvisa-info`)

## Troubleshooting

### "Stanford PS310 Power Supply not found"
- Verify the device is powered on and connected
- Run `pyvisa-info` to check if the device is visible
- Ensure proper drivers are installed

### "voltage must be negative" error
- This is expected behavior for the negative model
- Use negative values: `set_voltage(-5.0)` instead of `set_voltage(5.0)`

## Related Files

- `libs/StanfordPS310.py`: Main library implementation
- `test_stanfordps310.py`: Test suite
- `data_logger.py`: Integration with data logging framework
