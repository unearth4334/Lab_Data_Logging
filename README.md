# Lab Data Logging
Python project for interfacing with test equipment for automated testing and data-logging.

## Repository Structure

```
Lab_Data_Logging/
├── data_logger.py          # Core data logging orchestrator
├── libs/                   # Device driver libraries
│   ├── DMM6500.py         # Keithley DMM6500 driver
│   ├── KeysightMSOX4154A.py  # Oscilloscope driver
│   ├── StanfordPS310.py   # High voltage power supply driver
│   └── ...                # Other instrument drivers
├── apps/                   # GUI applications
│   ├── MSOX4154A/         # Oscilloscope measurement GUI
│   │   └── measurement_gui.py
│   └── PS310/             # High voltage power supply GUI
│       ├── stanfordps310_gui.py
│       ├── stanfordps310_gui_desktop.py
│       ├── stanfordps310_gui_example.py
│       └── quickstart_ps310_desktop.py
├── scripts/                # Utility scripts
│   ├── verify_installation.py
│   ├── lab_cli.py
│   └── generate_report.py
├── config/                 # Configuration files
│   ├── defaults.yml
│   └── example_config.yml
├── docs/                   # Documentation
├── utilities/              # MATLAB utilities (loadData.m, plotData.m)
└── requirements.txt        # Python dependencies
```

## Installation

To set up the project in a virtual environment:

1. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   ```

2. **Activate the virtual environment:**
   - On Linux/Mac: `source .venv/bin/activate`
   - On Windows: `.venv\Scripts\activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

The `requirements.txt` file contains all necessary external dependencies including:
- `colorama` - For colored terminal output
- `pyvisa` - For VISA instrument communication
- `numpy` - For numerical operations and data arrays  
- `pyserial` - For serial communication with devices

---

## Automatic API Documentation

The project includes automatic API documentation generation for all device drivers and the main `data_logger` module using [pdoc3](https://pdoc3.github.io/pdoc/).

### Generating Documentation

To generate the API documentation:

1. **Ensure dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the documentation generator:**
   ```bash
   python scripts/generate_docs.py
   ```

3. **Open the documentation:**
   The documentation will be generated in `docs/api/` directory. Open `docs/api/index.html` in your web browser to view the complete API documentation.

### What's Documented

The automatic documentation includes:
- **data_logger.py** - Main data logging orchestrator with all methods
- **All device drivers in libs/** - Complete API for each instrument driver:
  - DMM6500 - Keithley DMM6500 Multimeter
  - Keysight34460A - Keysight 34460A Multimeter  
  - KeysightMSOX4154A - Keysight MSOX4154A Oscilloscope
  - StanfordPS310 - Stanford PS310 High Voltage Power Supply
  - RigolDP832, RigolDS7034 - Rigol instruments
  - And all other device drivers

The documentation is automatically generated from the Python docstrings in the source code and includes:
- Class and method signatures with type hints
- Comprehensive docstrings and usage examples
- **Supported measurement commands** for each instrument's `get()` method
- Full source code viewing
- Cross-references between modules

Each instrument driver documentation now prominently displays the supported measurement commands that can be used with the `get()` method, making it easy to see what measurements are available for each device.

For detailed device-specific documentation and usage guides, see the manual documentation in the `docs/` directory.

---

## Instructions for Using the `data_logger` Class

1. Create an instance of the `data_logger` class:
   ```python
   logger = data_logger()
   ```

2. Create a new output file using the `new_file()` method. Pass the desired filename as an argument:
   ```python
   logger.new_file("output.txt")
   ```

3. Connect the measurement device by calling the `connect()` method and passing the appropriate device handle as an argument. For example, if you are using the `Keysight34460A` device, use:
   ```python
   multimeter = logger.connect("Keysight34460A")
   ```
   
   Or for the Keithley DMM6500:
   ```python
   dmm = logger.connect("dmm6500")
   ```

4. Add measurement items to log using the `add()` method. Provide a meaningful label as the first argument, the device object as the second argument, and the specific measurement item as the third argument. Optionally, you can specify the channel number as the fourth argument (default is 1):
   ```python
   logger.add("Voltage", multimeter, "voltage")
   logger.add("Current", multimeter, "current")
   ```

5. Once you have added all the desired measurement items, call the `get_data()` method to retrieve the measurements as a dictionary:
   ```python
   measurements = logger.get_data()
   ```

6. Process and use the measurements as needed. For example, you can print the voltage measurement as follows:
   ```python
   voltage = measurements["Voltage"]
   print(f"Measured voltage: {voltage} V")
   ```

7. Finally, close the output file using the `close_file()` method:
   ```python
   logger.close_file()
   ```

**Note:**
- The `label` argument in the `add()` method is used as the column title in the output file, so you can set it to any meaningful title you want.
- The `item` argument in the `add()` method should be an exact value corresponding to the measurement item you want to retrieve from the device. The valid values depend on the specific device class. 
  - For the `Keysight34460A` device, the valid values are "statistics", "current", or "voltage".
  - For the `DMM6500` device, the valid values are "statistics", "current", "voltage", "resistance", "resistance_4w", "capacitance", "frequency", "period", or "temperature".

---

## Keithley DMM6500 Digital Multimeter

The DMM6500 library provides comprehensive support for the Keithley DMM6500 6.5-digit digital multimeter. This high-performance instrument offers precise measurements across multiple domains.

### Supported Measurements
- **DC/AC Voltage**: High-precision voltage measurements
- **DC/AC Current**: Current measurements with multiple ranges
- **Resistance**: Both 2-wire and 4-wire resistance measurements for maximum accuracy
- **Capacitance**: Capacitance measurements for component testing
- **Frequency & Period**: AC signal frequency and period measurements
- **Temperature**: Temperature measurements with appropriate sensors
- **Statistics**: Comprehensive statistical analysis of measurement data

### Example Usage
```python
from data_logger import data_logger

# Create logger and connect to DMM6500
logger = data_logger()
logger.new_file("dmm6500_measurements.txt")
dmm = logger.connect("dmm6500")

# Add various measurements
logger.add("DC_Voltage", dmm, "voltage")
logger.add("Resistance_2W", dmm, "resistance") 
logger.add("Resistance_4W", dmm, "resistance_4w")
logger.add("Capacitance", dmm, "capacitance")
logger.add("Frequency", dmm, "frequency")

# Take measurements
measurements = logger.get_data()
logger.close_file()
```

### Direct Usage (without data_logger)
```python
import sys
sys.path.append('./libs')
from DMM6500 import DMM6500

# Connect to DMM6500
dmm = DMM6500()  # Auto-connects if device is found

# Take individual measurements
voltage = dmm.measure_voltage()
current = dmm.measure_current()
resistance_2w = dmm.measure_resistance()
resistance_4w = dmm.measure_resistance_4w()

# Use generic get() method
capacitance = dmm.get("capacitance")
frequency = dmm.get("frequency")

# Advanced measurement with statistics
dmm.start_measurement(100)  # Take 100 readings
stats = dmm.get("statistics")  # [avg, std_dev, min, max]

dmm.disconnect()
```

### Buffer Download Script

The DMM6500 supports high-speed data acquisition with internal buffer storage (up to 7 million readings). A dedicated script is provided to download buffer data:

```bash
# Auto-detect and download buffer
python scripts/download_dmm6500_buffer.py

# Connect via IP address
python scripts/download_dmm6500_buffer.py --ip 169.254.233.96

# Add metadata message
python scripts/download_dmm6500_buffer.py -m "Voltage stability test at 10V"

# Specify buffer and output file
python scripts/download_dmm6500_buffer.py --buffer defbuffer1 --output my_data.csv

# Download and plot
python scripts/download_dmm6500_buffer.py --plot
```

**Options:**
- `--ip IP_ADDRESS` - Connect via IP address
- `--address VISA_ADDRESS` - Use specific VISA resource string
- `--buffer BUFFER_NAME` - Buffer to download (default: defbuffer1)
- `--output OUTPUT_FILE` - Output CSV filename (default: auto-generated)
- `-m, --message MESSAGE` - Add metadata message to file header
- `--chunk CHUNK_SIZE` - Points per fetch (default: 50000)
- `--plot` - Plot the data after download
- `--debug` - Enable verbose SCPI logging

The script automatically generates timestamped CSV files with metadata headers including sample statistics (mean, std dev, min, max).

---

## Keysight MSOX4154A Oscilloscope

The MSOX4154A library provides comprehensive measurement statistics capabilities for the Keysight MSOX4154A mixed-signal oscilloscope. This instrument offers precise waveform capture and built-in measurement functions for laboratory testing.

### Supported Measurements
- **Voltage Statistics**: VPP, VMAX, VMIN, VRMS, VAVerage, VTOP, VBASe, VAMPlitude
- **Timing Analysis**: Frequency, Period, Rise Time, Fall Time, Pulse Width, Duty Cycle
- **Waveform Statistics**: Comprehensive statistical analysis of captured waveform data
- **Multi-Channel**: Simultaneous measurements across all 4 analog channels

### Example Usage with data_logger
```python
from data_logger import data_logger

# Create logger and connect to oscilloscope
logger = data_logger()
logger.new_file("oscilloscope_measurements.txt")
osc = logger.connect("msox4154a")

# Add various measurements (channel parameter: 1-4)
logger.add("CH1_Statistics", osc, "statistics", channel=1)  # [avg, std_dev, min, max]
logger.add("CH1_Voltage", osc, "voltage", channel=1)        # Average voltage
logger.add("CH1_Voltage_RMS", osc, "voltage_rms", channel=1)
logger.add("CH1_Frequency", osc, "frequency", channel=1)
logger.add("CH2_Voltage_PP", osc, "voltage_pp", channel=2)  # Peak-to-peak

# Take measurements
measurements = logger.get_data()
logger.close_file()
```

### Direct Usage (without data_logger)
```python
import sys
sys.path.append('./libs')
from KeysightMSOX4154A import KeysightMSOX4154A

# Connect to oscilloscope (auto-detect or specific VISA address)
osc = KeysightMSOX4154A()  # Auto-connects if found
# OR: osc = KeysightMSOX4154A(auto_connect=False)
#     osc.connect("USB0::0x0957::0x17BC::MY59241237::INSTR")

# Get comprehensive voltage measurements
voltage_stats = osc.get_voltage_measurements("CHAN1")
print(f"Peak-to-Peak: {voltage_stats['VPP']:.4f} V")
print(f"RMS: {voltage_stats['VRMS']:.4f} V")

# Get timing measurements
timing_stats = osc.get_timing_measurements("CHAN1") 
print(f"Frequency: {timing_stats['FREQuency']:.2f} Hz")
print(f"Duty Cycle: {timing_stats['DCYCle']:.2f} %")

# Get waveform data with statistics
t, y, meta = osc.get_waveform(source="CHAN1", debug=True)
print(f"Captured {len(y)} samples at {meta['sample_rate_hz']:.0f} Hz")

# Use generic get() method (compatible with data_logger)
statistics = osc.get("statistics", channel=1)  # [avg, std_dev, min, max]
voltage = osc.get("voltage", channel=1)
frequency = osc.get("frequency", channel=1)

osc.disconnect()
```

### Available Measurements (get() method)
- `"statistics"` - Returns [average, std_deviation, minimum, maximum] 
- `"voltage"` - Average voltage
- `"voltage_rms"` - RMS voltage
- `"voltage_pp"` - Peak-to-peak voltage  
- `"frequency"` - Signal frequency
- `"period"` - Signal period
- `"all_measurements"` - Complete measurement dictionary

### Test Scripts
- `test_msox4154a_simple.py` - Basic test using data_logger framework
- `test_oscilloscope_direct.py` - Comprehensive direct driver test
- `test_msox4154a_statistics.py` - Advanced statistics collection with reporting

---

## Stanford PS310 High Voltage Power Supply

The Stanford PS310 library provides control capabilities for the Stanford Research Systems PS310 High Voltage Power Supply, supporting both programmatic control and interactive GUI operation.

### Interactive GUI Applications

**Desktop Application** (Recommended):
```bash
python apps/PS310/stanfordps310_gui_desktop.py
```
- Native desktop window with Chromium-based webview
- Single-command launch (server + GUI)
- Automatic shutdown when window closes
- See [docs/STANFORDPS310_DESKTOP_README.md](docs/STANFORDPS310_DESKTOP_README.md)

**Web-Based GUI**:
```bash
python apps/PS310/stanfordps310_gui.py
```
- Access via browser at `http://localhost:8082`
- Manual voltage control and adjustable voltage ramping
- Real-time monitoring with live voltage/current display
- See [docs/STANFORDPS310_GUI_README.md](docs/STANFORDPS310_GUI_README.md)

### GUI Features
- **Device Connection**: Auto-detection of GPIB devices with PyVISA
- **Manual Control**: Set voltage (-1250V to 0V) and current limit (0-21 mA)
- **Voltage Ramping**: Automated voltage sweeps with configurable step size and delay
- **Live Monitoring**: Real-time voltage, current, and output status display
- **Safety Features**: Voltage range validation, current limiting, emergency stop

### Programmatic Control

```python
from libs.StanfordPS310 import StanfordPS310

# Connect to PS310
ps310 = StanfordPS310(auto_connect=False)
ps310.connect("GPIB0::14::INSTR")

# Configure and set voltage
ps310.set_current_limit(0.010)  # 10 mA limit
ps310.set_voltage(-100)  # Set to -100V

# Enable output
ps310.set_output_state(True)

# Read measurements
voltage = ps310.measure_voltage()
current = ps310.measure_current()
print(f"Voltage: {voltage:.2f} V, Current: {current*1000:.3f} mA")

# Disable output and disconnect
ps310.set_output_state(False)
ps310.disconnect()
```

### REST API Control

The GUI provides a REST API for automation (see `apps/PS310/stanfordps310_gui_example.py`):

```python
import requests

BASE_URL = "http://localhost:8082"

# Connect to device
requests.post(f"{BASE_URL}/connect", json={"address": "GPIB0::14::INSTR"})

# Set voltage
requests.post(f"{BASE_URL}/set_voltage", json={"voltage": -100})

# Enable output
requests.post(f"{BASE_URL}/set_output", json={"state": True})

# Start voltage ramp
requests.post(f"{BASE_URL}/start_ramp", 
              json={"start": 0, "end": -500, "step": 10, "delay": 1})
```

### Safety Considerations

⚠️ **HIGH VOLTAGE DEVICE - EXTREME CAUTION REQUIRED**
- Maximum voltage: ±1250V
- Current limit: 0-21 mA
- Always disable output before disconnecting
- Use appropriate high voltage safety equipment
- Follow proper grounding procedures

---
