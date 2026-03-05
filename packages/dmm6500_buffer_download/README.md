# DMM6500 Buffer Download Tool

Command-line tool for downloading and analyzing buffer data from Keithley DMM6500 digital multimeters.

## Installation

```bash
pip install dmm6500-buffer-download-1.0.0-py3-none-any.whl
```

For plotting support:
```bash
pip install dmm6500-buffer-download-1.0.0-py3-none-any.whl[plot]
```

## Hardware Requirements

- **Keithley DMM6500** digital multimeter (USB/Ethernet/GPIB)

## Usage

### Command Line Interface

```bash
# Auto-connect and download default buffer
dmm6500-buffer-download

# Connect via IP address
dmm6500-buffer-download --ip 169.254.233.96

# Connect via explicit VISA address
dmm6500-buffer-download --address "USB0::0x05E6::0x6500::04492372::INSTR"

# Specify buffer name and add metadata
dmm6500-buffer-download --buffer defbuffer1 -m "Voltage stability test"

# Download and plot
dmm6500-buffer-download --plot

# Custom output file
dmm6500-buffer-download --output my_data.csv

# Enable debug mode with custom chunk size
dmm6500-buffer-download --debug --chunk 10000
```

### Command Line Options

- `--ip IP_ADDRESS` - IP address for ethernet connection
- `--address VISA_ADDRESS` - Full VISA resource string (USB or TCPIP)
- `--buffer BUFFER_NAME` - Buffer name to download (default: defbuffer1)
- `--output OUTPUT_FILE` - Output CSV filename (default: auto-generated)
- `-m, --message MESSAGE` - Metadata message for file header
- `--chunk CHUNK_SIZE` - Points per fetch operation (default: 50000)
- `--debug` - Enable verbose SCPI logging
- `--plot` - Plot downloaded data (requires matplotlib)

### Python API

```python
from dmm6500_buffer_download import download_buffer

# Download buffer
data = download_buffer(
    buffer_name='defbuffer1',
    ip_address='169.254.233.96',
    output_file='voltage_data.csv',
    message='Test measurement'
)

print(f"Downloaded {len(data)} samples")
```

## Output Format

Files are saved in CSV format with the following structure:

```csv
# DMM6500 Buffer Download
# Timestamp: 2026-03-05T10:30:45.123456
# Buffer: defbuffer1
# Samples: 10000
# Message: Voltage stability test
#
Index,Value
1,10.000123
2,10.000145
...
```

### Auto-Generated Filenames

When no output file is specified, files are auto-generated in the `output/` directory:

```
output/yyyymmdd_hhmmss-dmm6500_buffer-buffername[-message].csv
```

Example: `output/20260305_103045-dmm6500_buffer-defbuffer1-voltage_test.csv`

## Features

- ✅ **Multiple connection modes** - USB, Ethernet, or auto-detection
- ✅ **Progress bar** - Visual feedback during large downloads
- ✅ **Automatic statistics** - Mean, std dev, min, max calculated
- ✅ **Chunked transfer** - Efficient download of large buffers
- ✅ **Metadata support** - Add descriptive messages to files
- ✅ **Optional plotting** - Visualize time series and distribution
- ✅ **Debug logging** - Verbose SCPI command logging

## Statistics Output

The tool automatically calculates and displays statistics:

```
Buffer Statistics:
  Mean:   1.000234e+01
  StdDev: 5.432100e-05
  Min:    9.999876e+00
  Max:    1.000345e+01
  Range:  4.690000e-04
```

## Plotting

With the `--plot` flag (requires matplotlib), the tool generates:

1. **Time series plot** - Shows values over sample index
2. **Histogram** - Shows value distribution
3. **Statistics overlay** - Mean, std dev, min, max displayed on plot

## Examples

### Example 1: Quick Download
```bash
dmm6500-buffer-download
```

### Example 2: Production Test with Metadata
```bash
dmm6500-buffer-download --ip 169.254.233.96 \
    -m "Board_00123_VDD_stability" --plot
```

### Example 3: Custom Buffer and Output
```bash
dmm6500-buffer-download --buffer defbuffer2 \
    --output measurements/board_test.csv \
    --chunk 100000
```

### Example 4: Debug Mode
```bash
dmm6500-buffer-download --debug --ip 192.168.1.100
```

## Troubleshooting

### Connection Issues

**Can't connect to DMM6500:**
- Verify USB or Ethernet connection
- Check IP address (try ping test)
- Ensure NI-VISA drivers are installed
- Try explicit VISA address with `--address`

**Buffer is empty:**
- Verify measurements have been taken on DMM6500
- Check buffer name matches (e.g., `defbuffer1` vs `defbuffer2`)
- Use DMM6500 front panel to verify buffer contains data

### Performance

**Download is slow:**
- Increase chunk size: `--chunk 100000`
- Use Ethernet connection instead of USB
- Check network latency if using remote connection

### Plotting Issues

**matplotlib not found:**
```bash
pip install matplotlib
```

Or install with plotting support:
```bash
pip install dmm6500-buffer-download[plot]
```

## Database Storage

At **~12 KB**, the wheel file is ideal for database storage in test records systems.

## Uninstallation

```bash
pip uninstall dmm6500-buffer-download
```

## License

Apache License 2.0
