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
- The `item` argument in the `add()` method should be an exact value corresponding to the measurement item you want to retrieve from the device. The valid values depend on the specific device class. For the `Keysight34460A` device, the valid values are "statistics", "current", or "voltage".

---
