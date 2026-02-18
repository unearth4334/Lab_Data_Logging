# Rigol RSA3030-TG Spectrum Analyzer Driver

## Overview

The RSA3030 driver provides comprehensive support for the Rigol RSA3030-TG spectrum analyzer in the Lab Data Logging framework. It follows the same design patterns as other device drivers (e.g., DMM6500) and supports both USB and Ethernet connectivity.

## Quick Start

### Basic Usage

```python
from libs.RSA3030 import RSA3030

# Auto-connect to RSA3030
rsa = RSA3030()

# Get instrument identification
identity = rsa.get_identity()
print(f"Connected to: {identity}")

# Clean up
rsa.disconnect()
```

### Integration with data_logger

```python
from data_logger import data_logger

logger = data_logger()
logger.new_file("measurements.txt")

# Connect to RSA3030
rsa = logger.connect("rsa3030")

# Add measurements
logger.add(rsa, "identity", label="Instrument_ID")

# Collect data
logger.get_data()

# Clean up
logger.close_file()
rsa.disconnect()
```

## Connection Methods

### 1. Auto-Detection

```python
# Automatically finds RSA3030 on USB or Ethernet
rsa = RSA3030()
```

### 2. IP Address Connection

```python
# Connect via Ethernet using IP address
rsa = RSA3030(ip_address="192.168.1.100")

# Or specify during initialization
rsa = RSA3030(auto_connect=False)
rsa.connect(ip_address="192.168.1.100")
```

### 3. Explicit VISA Address

```python
# USB connection
rsa = RSA3030(address="USB0::0x1AB1::0x0960::RSA3XXXXXXXX::INSTR")

# Ethernet connection
rsa = RSA3030(address="TCPIP0::192.168.1.100::INSTR")
```

## Testing

### Comprehensive Test Suite

The `test_rsa3030.py` script provides extensive testing capabilities:

```bash
# Auto-connect test
python test_rsa3030.py

# Connect via IP address
python test_rsa3030.py --ip 192.168.1.100

# Connect via explicit VISA address
python test_rsa3030.py --address "TCPIP0::192.168.1.100::INSTR"

# Interactive mode (prompts for connection details)
python test_rsa3030.py --interactive

# Debug mode (shows detailed connection process)
python test_rsa3030.py --debug
```

### Example Script

Run the example script for guided demonstrations:

```bash
python example_rsa3030.py
```

## Network Configuration

### Finding the RSA3030 IP Address

1. Press **System** or **Menu** on the RSA3030 front panel
2. Navigate to: **Interface > LAN**
3. Note the displayed IP address

### Configuring Network Settings

1. Access the LAN settings menu on the device
2. Select **Config Mode**:
   - **DHCP**: Automatically obtains IP from network
   - **Static**: Set static IP address manually
3. If using Static mode, configure:
   - IP Address
   - Subnet Mask
   - Gateway
4. Apply settings and restart if necessary

## Supported Commands

The RSA3030 driver currently supports the following commands via the `get(item)` method:

- **"identity"**: Returns instrument identification string (*IDN? response)

### Example

```python
rsa = RSA3030()
identity = rsa.get("identity")
print(f"Instrument: {identity}")
```

## Troubleshooting

### Connection Issues

1. **Verify device is powered on**
   - Check that the RSA3030 is turned on and initialized

2. **Check network connectivity** (for Ethernet)
   ```bash
   ping 192.168.1.100  # Replace with your RSA3030 IP
   ```

3. **Verify VISA resources**
   ```bash
   python -c "import pyvisa; rm = pyvisa.ResourceManager(); print(rm.list_resources())"
   ```

4. **Check USB connection**
   - Ensure USB cable is properly connected
   - Verify VISA drivers are installed (NI-VISA or similar)

5. **Use debug mode**
   ```bash
   python test_rsa3030.py --debug
   ```
   This shows detailed information about resource scanning and connection attempts.

### Common Error Messages

- **"Rigol RSA3030 not found"**: No RSA3030 detected on any interface. Check power, cables, and network connectivity.
- **"Device at 'X' is not an RSA3030"**: Device found but not identified as RSA3030. Verify correct IP/address.
- **"Failed to connect to RSA3030 at IP"**: Network connectivity issue. Check network settings and firewall.

## Technical Specifications

- **Frequency Range**: 9 kHz to 3 GHz
- **Interfaces Supported**: USB, Ethernet/LAN
- **Communication Protocol**: SCPI over VISA
- **Manufacturer**: Rigol Technologies
- **Model**: RSA3030-TG

## Device Driver Architecture

The RSA3030 driver follows the standard device driver pattern:

1. **Connection Management**
   - Auto-detection via VISA resource scanning
   - Support for multiple connection types (USB, Ethernet)
   - Proper error handling and user feedback

2. **SCPI Communication**
   - Direct query/write methods via PyVISA
   - Standardized command interface
   - Connection status tracking

3. **Integration Interface**
   - Generic `get(item)` method for data_logger compatibility
   - Consistent error handling across all operations
   - Type hints for improved IDE support

## Requirements

- Python 3.7+
- pyvisa >= 1.11.0
- colorama >= 0.4.6
- NI-VISA or compatible VISA backend (e.g., pyvisa-py)

Install dependencies:
```bash
pip install pyvisa colorama
```

## Files

- **libs/RSA3030.py**: Main driver implementation with comprehensive documentation
- **test_rsa3030.py**: Comprehensive test suite with multiple connection modes
- **example_rsa3030.py**: Example usage scripts for common scenarios
- **docs/RSA3030_README.md**: This documentation file

## See Also

- **DMM6500 Driver**: Similar implementation pattern for reference
- **DEVICE_DRIVER_STANDARD.md**: General device driver standards
- **data_logger Documentation**: Main framework documentation

## Future Enhancements

Potential future additions to the RSA3030 driver:

1. **Spectrum Measurements**
   - Frequency sweep data capture
   - Peak detection
   - Marker measurements

2. **Configuration Control**
   - Center frequency and span settings
   - Resolution bandwidth configuration
   - Amplitude settings

3. **Data Analysis**
   - Trace capture and analysis
   - Statistical measurements
   - Multi-trace support

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the comprehensive documentation in libs/RSA3030.py
3. Run tests with `--debug` flag for detailed diagnostics
4. Refer to the Rigol RSA3030 programming manual for SCPI command details
