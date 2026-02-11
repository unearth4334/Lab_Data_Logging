# DMM6500 Waveform Capture and Save

This guide explains how to capture and save waveform data from the Keithley DMM6500 Digital Multimeter.

## Overview

The DMM6500 can store measurement data in internal buffers. This feature is useful for:
- High-speed data logging
- Waveform capture and analysis
- Time-series measurements
- Statistical analysis of measurement data

## Scripts Provided

### 1. `save_dmm6500_waveform.py` - Main Waveform Export Script

This script downloads data from the DMM6500's internal buffer and saves it to a CSV file.

**Usage:**
```bash
# Basic usage - auto-detect DMM and save from default buffer
python save_dmm6500_waveform.py

# Specify VISA address
python save_dmm6500_waveform.py --address "USB0::0x05E6::0x6500::04471234::INSTR"

# Custom output directory
python save_dmm6500_waveform.py --output-dir "my_measurements"

# Read from a different buffer
python save_dmm6500_waveform.py --buffer "defbuffer2"

# Get help
python save_dmm6500_waveform.py --help
```

**Features:**
- Auto-detects DMM6500 via USB or network
- Downloads data in chunks for efficiency
- Creates timestamped CSV files in `captures/` directory
- Displays statistics (min, max, mean, std dev)
- Handles large buffers gracefully

**Output Format:**
The script creates a CSV file with two columns:
```
Sample_Index,Value
1,0.123456
2,0.123458
3,0.123452
...
```

### 2. `example_dmm6500_capture_and_save.py` - Interactive Examples

This script provides working examples of how to capture data into the DMM6500 buffer before saving it.

**Usage:**
```bash
python example_dmm6500_capture_and_save.py
```

The script presents three example methods:
1. **Manual Buffer Capture** - Uses SCPI trigger commands for precise control
2. **Simple Continuous Readings** - Takes multiple readings that auto-fill the buffer
3. **Capture and Auto-Save** - Complete workflow in one go

## Complete Workflow

### Method 1: Using the Example Script (Recommended for Learning)

```bash
# Run the interactive example script
python example_dmm6500_capture_and_save.py

# Select option 3 for a complete demonstration
# This will capture data and automatically save it
```

### Method 2: Manual Two-Step Process

**Step 1: Capture Data**

You need to fill the DMM6500 buffer with measurement data first. Here are several ways:

**Option A - Using Python with SCPI commands:**
```python
from libs.DMM6500 import DMM6500

# Connect
dmm = DMM6500(auto_connect=True)

# Reset and clear buffer
dmm.instrument.write("*RST")
dmm.instrument.write("TRACe:CLEar 'defbuffer1'")

# Configure measurement
dmm.instrument.write("SENSe:FUNCtion 'VOLT:DC'")
dmm.instrument.write("SENSe:VOLT:DC:RANGe 10")
dmm.instrument.write("SENSe:VOLT:DC:NPLC 0.1")

# Take readings (they auto-store in buffer)
for i in range(100):
    dmm.instrument.query("MEASure:VOLT:DC?")

dmm.disconnect()
```

**Option B - Using the DMM6500 front panel:**
1. Press **MENU**
2. Navigate to **TRACe** → **defbuffer1**
3. Configure trigger or measurement settings
4. Start measurement
5. Wait for data capture to complete

**Option C - Using existing measurement functions:**
```python
from libs.DMM6500 import DMM6500
dmm = DMM6500()

# Configure and take measurements
dmm.configure("VOLTAGE:DC", 10.0, 1e-6)
for i in range(50):
    voltage = dmm.measure_voltage()
    print(f"Reading {i+1}: {voltage} V")

dmm.disconnect()
```

**Step 2: Save the Buffer to CSV**

After capturing data, run the save script:
```bash
python save_dmm6500_waveform.py
```

The script will:
1. Connect to the DMM6500
2. Check the buffer for data
3. Download all data points
4. Save to a timestamped CSV file in `captures/`
5. Display statistics

## Output Files

### File Naming Convention
```
captures/dmm6500_waveform_YYYYMMDD_HHMMSS.csv
```

Example: `captures/dmm6500_waveform_20260120_143022.csv`

### CSV Format
```csv
Sample_Index,Value
1,5.123456
2,5.123498
3,5.123431
...
```

## Troubleshooting

### "Buffer is empty!" Error

This means the DMM6500 buffer doesn't contain any data. Solutions:
1. Capture data first using one of the methods above
2. Check that you're using the correct buffer name (default: `defbuffer1`)
3. Verify measurements are being stored in the buffer

### Connection Issues

If the script can't find the DMM6500:
1. Check USB connection
2. Verify VISA drivers are installed
3. Try specifying the address explicitly with `--address`
4. Run `verify_installation.py` to check dependencies

### Large Buffer Downloads

For buffers with many points (>100k):
- The script downloads in chunks (50k points at a time)
- Be patient - large transfers can take several minutes
- Monitor the console for progress messages

## Advanced Usage

### Using Different Buffers

The DMM6500 supports multiple buffers. To use a custom buffer:

```python
# Create and use a custom buffer
dmm.instrument.write("TRACe:MAKE 'mybuffer', 50000")
dmm.instrument.write("TRACe:CLEar 'mybuffer'")
# ... take measurements ...

# Save from custom buffer
# python save_dmm6500_waveform.py --buffer "mybuffer"
```

### High-Speed Digitizing

For high-speed waveform capture, use fast NPLC settings:

```python
dmm.instrument.write("SENSe:VOLT:DC:NPLC 0.001")  # Very fast (1/1000 of power line cycle)
```

### Batch Processing

To capture and save multiple waveforms:

```bash
# Create a shell script
for i in {1..10}; do
    echo "Capture $i"
    python example_dmm6500_capture_and_save.py  # Automated version
    sleep 1
done
```

## Integration with Data Logger

These scripts complement the main `data_logger` class. For integrated data logging:

```python
from data_logger import data_logger

logger = data_logger()
logger.new_file("measurements.txt")
dmm = logger.connect("dmm6500")
logger.add("Voltage", dmm, "voltage")
measurements = logger.get_data()
logger.close_file()
```

For waveform capture specifically, use the standalone `save_dmm6500_waveform.py` script.

## Related Files

- `libs/DMM6500.py` - DMM6500 device driver class
- `data_logger.py` - Main data logging framework
- `README.md` - General project documentation

## Requirements

- Python 3.6+
- PyVISA
- Keithley DMM6500 connected via USB or network
- See `requirements.txt` for complete dependency list

## Support

For issues or questions:
1. Check that the DMM6500 is properly connected
2. Verify dependencies with `python verify_installation.py`
3. Review the example scripts for usage patterns
4. Check instrument buffer status with front panel or SCPI commands
