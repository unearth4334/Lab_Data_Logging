# Rigol DP711 Power Supply Driver

## Overview

The `RigolDP711` driver provides control and measurement capabilities for the Rigol DP711 single-output programmable DC power supply via RS-232 serial communication (typically through a USB-to-RS232 adapter).

## Hardware Specifications

- **Voltage Range**: 0-30V
- **Current Range**: 0-5A
- **Maximum Power**: 150W
- **Voltage Resolution**: 1mV
- **Current Resolution**: 1mA
- **Interface**: RS-232 serial (via USB-to-RS232 adapter)
- **Baud Rate**: 9600 (default)

## Basic Usage

### Simple On/Off Control

```python
from libs.RigolDP711 import RigolDP711

# Connect to power supply
ps = RigolDP711(com_port="COM4")  # Or let it prompt for COM port

# Set output parameters
ps.set_voltage(12.0)  # 12V
ps.set_current(2.0)   # 2A current limit

# Turn on output
ps.turn_on()

# Turn off output
ps.turn_off()

# Disconnect
ps.disconnect()
```

### Measurements

```python
from libs.RigolDP711 import RigolDP711

ps = RigolDP711()

# Enable output
ps.set_voltage(10.0)
ps.set_current(1.0)
ps.turn_on()

# Read measurements
voltage = ps.measure_voltage()
current = ps.measure_current()
power = ps.measure_power()

print(f"Output: {voltage:.3f}V, {current:.3f}A, {power:.3f}W")

ps.turn_off()
ps.disconnect()
```

### Integration with data_logger

```python
from data_logger import data_logger

logger = data_logger()
logger.new_file("power_supply_test.txt")

# Connect using either alias
ps = logger.connect("dp711")        # Short alias
# ps = logger.connect("rigoldp711")  # Full name

# Configure output
ps.set_voltage(15.0)
ps.set_current(2.0)
ps.turn_on()

# Add measurements to logger
logger.add("PS_Voltage", ps, "voltage")
logger.add("PS_Current", ps, "current")

# Collect data
for i in range(100):
    logger.get_data()
    time.sleep(0.1)

# Cleanup
ps.turn_off()
logger.close_file()
ps.disconnect()
```

## API Reference

### Connection Methods

#### `__init__(auto_connect=True, com_port=None, baud_rate=9600)`

Initialize the driver.

**Parameters:**
- `auto_connect` (bool): Automatically connect on initialization (default: True)
- `com_port` (str): Optional COM port (e.g., "COM4"). If None, prompts user
- `baud_rate` (int): Serial baud rate (default: 9600)

#### `connect(com_port=None, baud_rate=9600)`

Establish connection to the power supply.

**Parameters:**
- `com_port` (str): Optional COM port. If None, checks environment variable `DP711_COM_PORT` or prompts user
- `baud_rate` (int): Serial baud rate (default: 9600)

**Raises:**
- `ConnectionError`: If device not found or connection fails

#### `disconnect()`

Close the serial connection.

### Configuration Methods

#### `set_voltage(voltage)`

Set the output voltage.

**Parameters:**
- `voltage` (float): Voltage in volts (0-30V)

**Raises:**
- `ValueError`: If voltage out of range
- `ConnectionError`: If not connected

#### `set_current(current)`

Set the output current limit.

**Parameters:**
- `current` (float): Current in amperes (0-5A)

**Raises:**
- `ValueError`: If current out of range
- `ConnectionError`: If not connected

#### `get_voltage_setpoint()`

Get the configured voltage setpoint.

**Returns:**
- `float`: Configured voltage in volts

#### `get_current_setpoint()`

Get the configured current limit setpoint.

**Returns:**
- `float`: Configured current in amperes

### Output Control Methods

#### `set_output_state(state)`

Enable or disable the output.

**Parameters:**
- `state` (bool): True to enable, False to disable

#### `get_output_state()`

Query the current output state.

**Returns:**
- `bool`: True if output enabled, False if disabled

#### `turn_on()`

Turn on the power supply output (convenience method).

#### `turn_off()`

Turn off the power supply output (convenience method).

### Measurement Methods

#### `measure_voltage()`

Measure the actual output voltage.

**Returns:**
- `float`: Measured voltage in volts

#### `measure_current()`

Measure the actual output current.

**Returns:**
- `float`: Measured current in amperes

#### `measure_power()`

Measure the actual output power.

**Returns:**
- `float`: Measured power in watts

#### `get(item, channel=1)`

Generic measurement getter (for data_logger compatibility).

**Parameters:**
- `item` (str): Measurement type (case-insensitive):
  - `"voltage"` or `"VOLT"`: Output voltage
  - `"current"` or `"CURR"`: Output current
- `channel` (int): Not used (for compatibility)

**Returns:**
- `float`: Measurement value

**Raises:**
- `ValueError`: If invalid item requested

## Environment Variables

The driver uses the following environment variable for convenience:

- `DP711_COM_PORT`: Default COM port to use (e.g., "COM4")

If the COM port is not specified in code and this environment variable is not set, the driver will prompt the user to select from available ports.

## SCPI Commands

The driver uses the following SCPI commands:

| Command | Description |
|---------|-------------|
| `*IDN?` | Query device identification |
| `:VOLT <value>` | Set voltage |
| `:VOLT?` | Query voltage setpoint |
| `:CURR <value>` | Set current |
| `:CURR?` | Query current setpoint |
| `:OUTP ON` | Enable output |
| `:OUTP OFF` | Disable output |
| `:OUTP?` | Query output state |
| `:MEAS:VOLT?` | Measure output voltage |
| `:MEAS:CURR?` | Measure output current |
| `:MEAS:POW?` | Measure output power |

## Connection Setup

### Windows

1. Connect the Rigol DP711 to your computer using a USB-to-RS232 adapter
2. Note the COM port assigned (check Device Manager → Ports)
3. Use that COM port in your code: `ps = RigolDP711(com_port="COM4")`

### Linux

1. Connect the USB-to-RS232 adapter
2. Check available ports: `ls /dev/ttyUSB*`
3. You may need permissions: `sudo chmod 666 /dev/ttyUSB0`
4. Use that port: `ps = RigolDP711(com_port="/dev/ttyUSB0")`

## Testing

### Quick Test

Run a simple on/off test:

```bash
python tests/test_dp711_quick.py
```

### Full Test Suite

Run comprehensive tests including data_logger integration:

```bash
python tests/test_rigoldp711.py
```

## Troubleshooting

### Device Not Found

- Verify the USB-to-RS232 adapter is connected
- Check Device Manager (Windows) or `dmesg` (Linux) for device registration
- Try unplugging and reconnecting the USB adapter

### Communication Timeout

- Verify the correct COM port is selected
- Check that the baud rate is set to 9600
- Ensure no other software is using the COM port

### Permission Denied (Linux)

Add your user to the dialout group:
```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

## Related Drivers

- **RigolDP832**: Triple-output power supply (USB/VISA)
- **KA3010P**: Similar single-output supply (RS-232)
- **StanfordPS310**: High voltage power supply (GPIB)

## See Also

- [Device Driver Standard](DEVICE_DRIVER_STANDARD.md)
- [Quick Reference](DEVICE_DRIVER_QUICK_REFERENCE.md)
- [data_logger Documentation](../README.md)
