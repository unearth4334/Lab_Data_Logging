# DMM6500 Ethernet Connection Guide

This guide explains how to use the new ethernet/LAN connectivity features for the Keithley DMM6500.

## Overview

The DMM6500 driver now supports three connection methods:
1. **USB** - Traditional USB connection (existing functionality)
2. **Ethernet/LAN via IP address** - Simple connection using IP address
3. **Explicit VISA address** - Full control with VISA resource string (USB or TCPIP)

## Network Setup

### Configure DMM6500 Network Settings

1. On the DMM6500 front panel, press **MENU**
2. Navigate to **System → Communications → LAN**
3. Configure the network settings:
   - **DHCP** (automatic IP) or **Static** (manual IP)
   - Note the IP address displayed
4. Ensure the DMM6500 and your computer are on the same network

### Verify Network Connection

Test the connection from your computer:
```bash
ping 192.168.1.100  # Replace with your DMM6500's IP
```

## Basic Usage

### Method 1: Connect via IP Address (Simplest)

```python
from libs.DMM6500 import DMM6500

# Connect using IP address
dmm = DMM6500(ip_address="192.168.1.100")

# Take measurements
voltage = dmm.measure_voltage()
print(f"Voltage: {voltage:.6f} V")

# Disconnect
dmm.disconnect()
```

### Method 2: Manual Connection

```python
from libs.DMM6500 import DMM6500

# Create instance without auto-connecting
dmm = DMM6500(auto_connect=False)

# Connect to specific IP
dmm.connect(ip_address="192.168.1.100")

# Or connect with explicit VISA address
# dmm.connect(address="TCPIP0::192.168.1.100::inst0::INSTR")

# Take measurements
voltage = dmm.measure_voltage()
print(f"Voltage: {voltage:.6f} V")

dmm.disconnect()
```

### Method 3: Auto-Detection (Works with USB or Ethernet)

```python
from libs.DMM6500 import DMM6500

# Auto-detect any DMM6500 (searches USB and TCPIP resources)
dmm = DMM6500()

# Take measurements
voltage = dmm.measure_voltage()
print(f"Voltage: {voltage:.6f} V")

dmm.disconnect()
```

## Test Script

A comprehensive test script is provided: `test_dmm6500_ethernet.py`

### Quick Test

```bash
# Auto-detect connection
python test_dmm6500_ethernet.py

# Connect via IP address
python test_dmm6500_ethernet.py --ip 192.168.1.100

# Interactive mode
python test_dmm6500_ethernet.py --interactive
```

### Command Line Options

```
--ip IP_ADDRESS          Connect via IP address
--address VISA_ADDRESS   Use explicit VISA resource string
--interactive, -i        Interactive mode with prompts
--skip-statistics        Skip statistics test (faster)
--skip-digitize         Skip digitize test (faster)
--help, -h              Show full help
```

### Full Test Suite

```bash
# Run all tests via ethernet
python test_dmm6500_ethernet.py --ip 192.168.1.100

# Quick voltage-only test
python test_dmm6500_ethernet.py --ip 192.168.1.100 --skip-statistics --skip-digitize
```

## Integration with data_logger

The ethernet support works seamlessly with the existing data_logger framework:

```python
from data_logger import data_logger

# Create logger and output file
logger = data_logger()
logger.new_file("measurements.txt")

# Option 1: Let data_logger auto-connect (will find USB or Ethernet)
dmm = logger.connect("dmm6500")

# Option 2: Connect manually first with IP, then use with logger
from libs.DMM6500 import DMM6500
dmm = DMM6500(ip_address="192.168.1.100")

# Add measurements
logger.add(dmm, "voltage", label="Input_Voltage")
logger.add(dmm, "current", label="Load_Current")
logger.add(dmm, "statistics", label="Voltage_Stats")

# Collect data
for i in range(100):
    logger.get_data()

# Clean up
logger.close_file()
dmm.disconnect()
```

## Troubleshooting

### Connection Fails

1. **Check Power and Network**
   - Verify DMM6500 is powered on
   - Check ethernet cable is connected
   - Look for link lights on ethernet port

2. **Verify IP Address**
   - Check IP on DMM6500: Menu → System → LAN
   - Ensure IP is accessible: `ping <IP_ADDRESS>`
   - Verify computer and DMM are on same network

3. **Test VISA Backend**
   ```python
   import pyvisa
   rm = pyvisa.ResourceManager()
   print(rm.list_resources())  # Should show TCPIP resources
   ```

4. **Firewall Issues**
   - Ensure port 5025 (LXI/VXI-11) is not blocked
   - Temporarily disable firewall to test

### "Device not found" Error

```python
# Try explicit VISA address
dmm = DMM6500(auto_connect=False)
dmm.connect(address="TCPIP0::192.168.1.100::inst0::INSTR")
```

### Slow Connection

- Increase timeout if needed (default is 20 seconds):
  ```python
  dmm = DMM6500(ip_address="192.168.1.100")
  dmm.instrument.timeout = 30000  # 30 seconds
  ```

### USB Still Preferred

The ethernet support is fully backward compatible. Existing USB code continues to work:

```python
# This still works as before
dmm = DMM6500()  # Auto-detects USB first, then ethernet
```

## VISA Resource String Format

For ethernet connections, the VISA resource string format is:
```
TCPIP0::<IP_ADDRESS>::inst0::INSTR
```

Examples:
- `TCPIP0::192.168.1.100::inst0::INSTR`
- `TCPIP0::10.0.0.50::inst0::INSTR`

When you provide just an IP address, the driver automatically constructs this format.

## Advanced Usage

### Specify Both USB and Ethernet Fallback

```python
from libs.DMM6500 import DMM6500

# Try ethernet first
try:
    dmm = DMM6500(ip_address="192.168.1.100")
    print("Connected via Ethernet")
except:
    # Fall back to USB
    dmm = DMM6500()
    print("Connected via USB")
```

### Multiple DMM6500 Devices

```python
# Connect to multiple DMMs
dmm1 = DMM6500(ip_address="192.168.1.100")
dmm2 = DMM6500(ip_address="192.168.1.101")

# Use them independently
v1 = dmm1.measure_voltage()
v2 = dmm2.measure_voltage()

print(f"DMM1: {v1:.6f} V")
print(f"DMM2: {v2:.6f} V")

dmm1.disconnect()
dmm2.disconnect()
```

## Performance Notes

- **USB**: Typically faster for single measurements
- **Ethernet**: Better for remote operation and multiple devices
- **Auto-detection**: Searches all interfaces (may be slower on first connect)

## Requirements

- Python 3.7+
- pyvisa >= 1.11.0
- colorama >= 0.4.6
- numpy >= 1.21.0
- NI-VISA or compatible VISA backend installed

## See Also

- `test_dmm6500_ethernet.py` - Comprehensive test script
- `libs/DMM6500.py` - Driver source code with full documentation
- `data_logger.py` - Main data logging framework
