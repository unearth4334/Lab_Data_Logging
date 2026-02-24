# Keysight EL34143A Waveform Capture

This document describes the waveform capture capabilities added to the Keysight EL34143A DC Electronic Load driver.

## Overview

The EL34143A driver now supports capturing voltage and current waveforms using the instrument's built-in digitizer functionality. This allows you to record transient behavior, startup characteristics, and dynamic load responses.

**Connection**: The driver works over both USB (via PyVISA) and Ethernet/TCPIP connections. USB is the primary connection method.

## Features

- **Voltage Waveform Capture**: Record voltage measurements over time
- **Current Waveform Capture**: Record current measurements over time
- **Configurable Sample Rate**: Control the digitizer sample rate
- **Flexible Point Count**: Set the number of samples to capture
- **CSV Export**: Save waveforms directly to CSV files
- **Metadata**: Automatic calculation of statistics and capture parameters

## Quick Start

### Basic Voltage Waveform Capture (USB)

```python
from libs.KeysightEL34143A import KeysightEL34143A

# Auto-connect to load (USB or Ethernet)
load = KeysightEL34143A()

# Capture voltage waveform (10 kHz, 1000 points)
t, v, meta = load.get_waveform("VOLTAGE", sample_rate=10000, points=1000)

print(f"Captured {len(v)} voltage points")
print(f"Mean voltage: {meta['mean']:.6f} V")
print(f"Sample rate: {meta['sample_rate_hz']} Hz")

load.disconnect()
```

### Explicit USB Connection

```python
# If you have multiple instruments, specify USB address
load = KeysightEL34143A(address="USB0::0x0957::0x8C18::MY12345678::INSTR")
```

### Ethernet Connection

```python
# Connect via IP address instead of USB
load = KeysightEL34143A(ip_address="169.254.117.30")
```

### Basic Current Waveform Capture

```python
# Capture current waveform (5 kHz, 500 points)
t, i, meta = load.get_waveform("CURRENT", sample_rate=5000, points=500)

print(f"Captured {len(i)} current points")
print(f"Peak-to-peak: {meta['peak_to_peak']:.6f} A")
```

### Save Waveform to CSV

```python
# Capture and save voltage waveform to CSV file
load.save_waveform("voltage_capture.csv", "VOLTAGE", sample_rate=10000, points=1000)
```

## API Reference

### `get_waveform(measure_type, configure, sample_rate, points, debug)`

Capture and download waveform data from the electronic load.

**Parameters:**
- `measure_type` (str): "VOLTAGE" or "CURRENT" - what to capture
- `configure` (bool): Automatically configure digitizer if True (default: True)
- `sample_rate` (float): Sample rate in Hz (default: 10000)
- `points` (int): Number of points to capture (default: 1000)
- `debug` (bool): Print debug information (default: False)

**Returns:**
- `Tuple[List[float], List[float], Dict[str, Any]]`:
  - `time_array`: List of time values in seconds
  - `data_array`: List of voltage (V) or current (A) values
  - `metadata_dict`: Dictionary with capture parameters

**Metadata Dictionary Keys:**
- `measure_type`: Type of measurement ("VOLTAGE" or "CURRENT")
- `npoints`: Number of points captured
- `sample_rate_hz`: Actual sample rate in Hz
- `dt_s`: Time step between samples (seconds)
- `duration_s`: Total capture duration (seconds)
- `t_start_s`: Start time (0.0)
- `t_stop_s`: End time (seconds)
- `mean`: Average value
- `min`: Minimum value
- `max`: Maximum value
- `peak_to_peak`: Peak-to-peak variation

### `configure_digitizer(measure_type, sample_rate, points, auto_range)`

Configure the electronic load's digitizer for waveform capture.

**Parameters:**
- `measure_type` (str): "VOLTAGE" or "CURRENT"
- `sample_rate` (float): Sample rate in Hz (optional)
- `points` (int): Number of points to capture (optional)
- `auto_range` (bool): Use auto-ranging (default: True)

### `save_waveform(filename, measure_type, sample_rate, points, debug)`

Capture waveform and save to CSV file.

**Parameters:**
- `filename` (str): Output CSV filename
- `measure_type` (str): "VOLTAGE" or "CURRENT"
- `sample_rate` (float): Sample rate in Hz (default: 10000)
- `points` (int): Number of points to capture (default: 1000)
- `debug` (bool): Print debug information (default: False)

**Returns:**
- `bool`: True if successful, False otherwise

## Usage Examples

### Example 1: Capture Load Startup Transient (USB)

```python
from libs.KeysightEL34143A import KeysightEL34143A

# Auto-connect via USB
load = KeysightEL34143A()

# Configure for fast sampling (20 kHz, 2000 points = 100 ms)
load.configure_digitizer("VOLTAGE", sample_rate=20000, points=2000)

# Enable load and capture voltage transient
load.set_current(1.0)
load.enable_output()

# Wait briefly for output to stabilize
import time
time.sleep(0.01)

# Capture waveform
t, v, meta = load.get_waveform("VOLTAGE", configure=False)

# Disable load
load.disable_output()

# Save results
load.save_waveform("startup_transient.csv", "VOLTAGE", 20000, 2000)

load.disconnect()
```

### Example 2: Monitor Dynamic Load Response

```python
from libs.KeysightEL34143A import KeysightEL34143A
import time

# Auto-connect via USB
load = KeysightEL34143A()

# Set initial current
load.set_current(0.5)
load.enable_output()

time.sleep(0.5)  # Allow to settle

# Capture baseline current
t1, i1, meta1 = load.get_waveform("CURRENT", sample_rate=1000, points=100)
print(f"Baseline: {meta1['mean']:.6f} A")

# Change current and capture response
load.set_current(1.5)
time.sleep(0.01)  # Brief delay

# Capture transient response (fast sampling)
t2, i2, meta2 = load.get_waveform("CURRENT", sample_rate=10000, points=1000)
print(f"New level: {meta2['mean']:.6f} A")
print(f"Peak-to-peak variation: {meta2['peak_to_peak']:.6f} A")

load.disable_output()
load.disconnect()
```

### Example 3: Characterize PSU Ripple

```python
from libs.KeysightEL34143A import KeysightEL34143A

# Auto-connect via USB
load = KeysightEL34143A()

# Set constant current load
load.set_current(2.0)
load.enable_output()

# Allow time to settle
import time
time.sleep(1.0)

# Capture voltage with high resolution (slow sampling for DC accuracy)
t, v, meta = load.get_waveform("VOLTAGE", sample_rate=1000, points=10000)

# Calculate AC ripple (assuming DC component is the mean)
import numpy as np
v_np = np.array(v)
v_ac = v_np - meta['mean']
ripple_rms = np.sqrt(np.mean(v_ac**2))
ripple_pp = meta['peak_to_peak']

print(f"DC Level: {meta['mean']:.6f} V")
print(f"RMS Ripple: {ripple_rms*1000:.3f} mV")
print(f"Peak-to-Peak Ripple: {ripple_pp*1000:.3f} mV")

load.disable_output()
load.disconnect()
```

## Test Script

A test script is provided at `tests/test_el34143a_waveform.py` to verify the functionality:

```bash
# Auto-connect via USB or Ethernet and test voltage capture
python tests/test_el34143a_waveform.py

# Force specific IP address (Ethernet only)
python tests/test_el34143a_waveform.py --ip 169.254.117.30

# Capture current waveform with custom settings
python tests/test_el34143a_waveform.py --type current --rate 5000 --points 500

# Save to specific file
python tests/test_el34143a_waveform.py --output my_capture.csv --debug
```

## SCPI Commands Used

The implementation attempts multiple SCPI command variations to maximize compatibility:

- `:SENSe:FUNCtion:ON "VOLTAGE"` / `"CURRENT"` - Enable measurement function
- `:SENSe:VOLTAGE:RANGe:AUTO ON` - Enable auto-ranging
- `:SENSe:VOLTAGE:APERture <seconds>` - Set integration time (sample period)
- `:SENSe:VOLTAGE:POINts <count>` - Set number of points
- `:FETCh:ARRay:VOLTAGE?` - Fetch voltage array
- `:FETCh:ARRay:CURRent?` - Fetch current array

Alternative fetch commands tried:
- `:FETCH:ARR:VOLTAGE?` / `:FETCH:ARR:CURRENT?`
- `:MEAS:ARR:VOLTAGE?` / `:MEAS:ARR:CURRENT?`
- `:DATA:ARRay:VOLTAGE?` / `:DATA:ARRay:CURRENT?`
- `READ?` - Single reading (fallback if array commands unavailable)

## Limitations and Notes

1. **Actual Sample Rate**: The actual sample rate may differ from the requested rate due to instrument limitations
2. **Point Count**: Maximum point count depends on instrument memory
3. **Binary vs ASCII**: The driver attempts binary transfer first (faster), then falls back to ASCII if needed
4. **SCPI Compatibility**: Different firmware versions may use different SCPI commands; the driver tries multiple variants
5. **Output State**: Waveform capture can be done with output enabled or disabled depending on your test requirements

## Troubleshooting

### No Data Captured

If you get an error about no data being captured:

1. Verify the instrument has digitizer capability (check firmware version)
2. Enable debug mode: `get_waveform(..., debug=True)`
3. Check which SCPI commands are supported by your instrument
4. Try capturing while output is enabled with a valid load

### Unexpected Sample Rate

The actual sample rate depends on the instrument's aperture time settings. Check the returned metadata:

```python
t, v, meta = load.get_waveform("VOLTAGE", sample_rate=10000, points=1000, debug=True)
print(f"Requested: 10000 Hz, Actual: {meta['sample_rate_hz']:.1f} Hz")
```

### Slow Capture

If captures are taking too long:

1. Reduce the number of points
2. Check if ASCII mode is being used (debug mode will show this)
3. Verify network connection speed
4. Consider using shorter timeout values

## See Also

- [KeysightEL34143A.py](../libs/KeysightEL34143A.py) - Driver source code
- [test_el34143a_waveform.py](../tests/test_el34143a_waveform.py) - Test script
- [Keysight MSOX4154A Driver](../libs/KeysightMSOX4154A.py) - Similar waveform capture for oscilloscopes
- [DMM6500 Driver](../libs/DMM6500.py) - Digitizer functionality for multimeters
