# DMM6500 Buffer Download Tool - Installation & Usage Guide

## Package Contents

Your installable Python package has been created in the `wheels/` directory:

- **Wheel file** (recommended): `dmm6500_buffer_download-1.0.0-py3-none-any.whl` (11.2 KB)
- **Source distribution**: `dmm6500_buffer_download-1.0.0.tar.gz` (11.4 KB)

## Installation

### Install from Wheel File (Recommended)

```bash
pip install dmm6500_buffer_download-1.0.0-py3-none-any.whl
```

### Install with Plotting Support

```bash
pip install dmm6500_buffer_download-1.0.0-py3-none-any.whl[plot]
```

### Verify Installation

```bash
pip show dmm6500-buffer-download
dmm6500-buffer-download --help
```

## Usage

### Command Line Interface

After installation, the `dmm6500-buffer-download` command is available globally:

```bash
# Auto-connect and download
dmm6500-buffer-download

# Connect via IP address
dmm6500-buffer-download --ip 169.254.233.96

# Add metadata message
dmm6500-buffer-download -m "Voltage stability test"

# Download and plot
dmm6500-buffer-download --plot

# Custom buffer and output
dmm6500-buffer-download --buffer defbuffer2 --output voltage_test.csv

# Debug mode with custom chunk size
dmm6500-buffer-download --debug --chunk 10000

# Full example
dmm6500-buffer-download --ip 169.254.233.96 \
    --buffer defbuffer1 \
    --output measurements.csv \
    -m "Board_00123_test" \
    --plot
```

### Python API

```python
from dmm6500_buffer_download import download_buffer, calculate_statistics

# Download buffer
data = download_buffer(
    buffer_name='defbuffer1',
    ip_address='169.254.233.96',
    output_file='voltage_data.csv',
    message='Test measurement',
    show_plot=True
)

# Calculate statistics
mean, stdev, min_val, max_val = calculate_statistics(data)
print(f"Mean: {mean:.6e}, Std: {stdev:.6e}")
```

## Features

✅ **11 KB package** - Perfect for database storage  
✅ **Multiple connection modes** - USB, Ethernet, auto-detection  
✅ **Progress bar** - Visual feedback during downloads  
✅ **Auto statistics** - Mean, std dev, min, max  
✅ **Chunked transfer** - Efficient large buffer handling  
✅ **Metadata support** - Add descriptions to files  
✅ **Optional plotting** - Visualize data with matplotlib  
✅ **Debug logging** - Verbose SCPI command tracking  

## Output Files

Files are auto-generated in the `output/` directory with format:

```
output/yyyymmdd_hhmmss-dmm6500_buffer-buffername[-message].csv
```

Example: `output/20260305_103045-dmm6500_buffer-defbuffer1-voltage_test.csv`

### CSV Format

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

## Statistics Display

The tool automatically calculates and displays:

```
Buffer Statistics:
  Mean:   1.000234e+01
  StdDev: 5.432100e-05
  Min:    9.999876e+00
  Max:    1.000345e+01
  Range:  4.690000e-04
```

## Plotting

With `--plot` flag (requires matplotlib):

- **Time series plot** - Values over sample index
- **Histogram** - Value distribution
- **Statistics overlay** - Mean, std dev, min, max

## Database Storage

The 11 KB wheel file is ideal for storing in test records databases as a BLOB.

Example database schema:
```sql
CREATE TABLE test_tools (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    version VARCHAR(50),
    filename VARCHAR(255),
    file_data BLOB,
    file_size INTEGER,
    upload_date TIMESTAMP,
    description TEXT
);
```

## Troubleshooting

### Connection Issues

**No DMM6500 found:**
- Check USB or Ethernet connection
- Verify NI-VISA drivers installed
- Try explicit address: `--address "USB0::..."`

**Buffer empty:**
- Verify measurements taken on DMM6500
- Check buffer name (defbuffer1 vs defbuffer2)
- Use DMM front panel to confirm data

### Performance

**Slow downloads:**
- Increase chunk size: `--chunk 100000`
- Use Ethernet instead of USB
- Check network latency

### Plotting

**matplotlib not found:**
```bash
pip install matplotlib
# or
pip install dmm6500-buffer-download[plot]
```

## Uninstallation

```bash
pip uninstall dmm6500-buffer-download
```

## Comparison: Wheel vs Script

| Feature | Wheel Package | Original Script |
|---------|---------------|----------------|
| Size | 11 KB | ~30 KB with libs |
| Installation | `pip install` | Manual path setup |
| Command | `dmm6500-buffer-download` | `python scripts/...` |
| Portability | Cross-platform | Requires project structure |
| Updates | Version controlled | Manual file replacement |
| Dependencies | Auto-managed | Manual install |

## License

Apache License 2.0
