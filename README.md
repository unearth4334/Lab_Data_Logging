# Lab Data Logging
Python project for interfacing with test equipment for automated testing and data-logging.

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

---
