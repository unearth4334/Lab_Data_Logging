# Lab Data Logging - Instrument Measurement Commands Reference

This document provides a comprehensive overview of all supported measurement commands for each instrument in the `libs/` directory. Use this as a quick reference to see what measurements are available for each device.

## Quick Reference Table

| Instrument | Type | Supported Commands | Details |
|------------|------|-------------------|---------|
| [DMM6500](#dmm6500) | Multimeter | 4 commands | voltage, current, resistance, statistics |
| [Keysight34460A](#keysight34460a) | Multimeter | 3 commands | voltage, current, statistics |
| [KeysightMSOX4154A](#keysightmsox4154a) | Oscilloscope | 9 commands | statistics, voltage variants, frequency, period |
| [StanfordPS310](#stanfordps310) | High Voltage PSU | 3 commands | voltage, current, set_voltage |
| [RigolDP832](#rigoldp832) | Power Supply | 6 commands | voltage, current, power + averages |
| [RigolDS7034](#rigolds7034) | Oscilloscope | 16 commands | voltage/frequency measurements + statistics |
| [DL3021](#dl3021) | Electronic Load | 4 commands | VOLT, CURR + averages |
| [FLUKE45](#fluke45) | Multimeter | 1 command | voltage |
| [KA3010P](#ka3010p) | Power Supply | 2 commands | VOLT, CURR |
| [U1233A](#u1233a) | Handheld Multimeter | 2 commands | MEAS, MEAS_AVG |
| [DAC](#dac) | DAC/INA226 | 6 commands | DAC channels + VOLT, CURR |
| [EPS](#eps) | Environmental Control | 3 commands | READ_TIME, READ_TEMP1, READ_HEATER1 |
| [DP832](#dp832) | Power Supply | 2 commands | VOLT, CURR |

---

## Detailed Command Reference

### DMM6500
**Keithley DMM6500 6.5-Digit Multimeter**

**Supported Commands:**
- `"voltage"` - DC voltage measurement in volts
- `"current"` - DC current measurement in amperes
- `"resistance"` - 2-wire resistance measurement in ohms
- `"statistics"` - Returns [mean, std_dev, min, max] for current function

**Usage Example:**
```python
dmm = logger.connect("dmm6500")
voltage = dmm.get("voltage")
current = dmm.get("current")
resistance = dmm.get("resistance")
stats = dmm.get("statistics")  # [mean, std_dev, min, max]
```

**Documentation:** [DMM6500.html](libs/DMM6500.html)

---

### Keysight34460A
**Keysight 34460A 6.5-Digit Multimeter**

**Supported Commands:**
- `"voltage"` - DC voltage measurement in volts
- `"current"` - DC current measurement in amperes
- `"statistics"` - Returns [mean, std_dev, min, max] for multiple readings

**Usage Example:**
```python
dmm = logger.connect("keysight34460a")
voltage = dmm.get("voltage")
current = dmm.get("current")
stats = dmm.get("statistics")
```

**Documentation:** [Keysight34460A.html](libs/Keysight34460A.html)

---

### KeysightMSOX4154A
**Keysight MSOX4154A Mixed Signal Oscilloscope**

**Supported Commands:**
- `"statistics"` - Returns [mean, std_dev, min, max, vpp] for specified channel
- `"voltage"` - Mean voltage measurement in volts
- `"voltage_rms"` - RMS voltage measurement
- `"voltage_pp"` - Peak-to-peak voltage (Vpp)
- `"frequency"` - Signal frequency in Hz
- `"period"` - Signal period in seconds
- `"xat_max"` or `"x_at_max"` - Time position of maximum voltage
- `"full_screen_average"` or `"vaverage"` - Full screen voltage average
- `"all_measurements"` - Returns complete statistics dictionary

**Usage Example:**
```python
scope = logger.connect("msox4154a")
stats = scope.get("statistics", channel=1)  # [mean, std_dev, min, max, vpp]
voltage = scope.get("voltage", channel=2)
frequency = scope.get("frequency", channel=1)
vpp = scope.get("voltage_pp", channel=3)
```

**Documentation:** [KeysightMSOX4154A.html](libs/KeysightMSOX4154A.html)

---

### StanfordPS310
**Stanford Research Systems PS310 High Voltage Power Supply**

**Supported Commands:**
- `"voltage"` - Measure actual output voltage in volts
- `"current"` - Measure actual output current in amperes
- `"set_voltage"` - Read voltage setpoint (target voltage)

**Usage Example:**
```python
hvps = logger.connect("stanfordps310")
voltage = hvps.get("voltage")      # Measured output voltage
current = hvps.get("current")      # Measured output current
setpoint = hvps.get("set_voltage") # Target voltage setting
```

**Documentation:** [StanfordPS310.html](libs/StanfordPS310.html)

---

### RigolDP832
**Rigol DP832 Triple-Output Power Supply**

**Supported Commands:**
- `"voltage"` - Measure actual output voltage in volts
- `"current"` - Measure actual output current in amperes
- `"power"` - Calculate power (voltage × current) in watts
- `"average_voltage"` - Average voltage over multiple measurements
- `"average_current"` - Average current over multiple measurements
- `"average_power"` - Average power over multiple measurements

**Usage Example:**
```python
psu = logger.connect("rigoldp832")
voltage = psu.get("voltage", channel=1)
current = psu.get("current", channel=1)
power = psu.get("power", channel=1)
avg_v = psu.get("average_voltage", channel=2)
```

**Documentation:** [RigolDP832.html](libs/RigolDP832.html)

---

### RigolDS7034
**Rigol DS7034 Digital Oscilloscope**

**Supported Commands:**
- `"VAVG"` - Average voltage measurement
- `"VMAX"` - Maximum voltage measurement
- `"VMIN"` - Minimum voltage measurement
- `"VAVG_STAT"` - Average voltage with statistics
- `"VMAX_STAT"` - Maximum voltage with statistics
- `"VPP_STAT"` - Peak-to-peak voltage with statistics
- `"PDUT_STAT"` - Positive duty cycle with statistics
- `"FREQ_STAT"` - Frequency measurement with statistics
- `"RFD_STAT"` - Rise-to-fall delay with statistics
- `"RRD_STAT"` - Rise-to-rise delay with statistics
- `"VMIN_STAT"` - Minimum voltage with statistics
- `"PSL_STAT"` - Positive slew rate with statistics
- `"NSL_STAT"` - Negative slew rate with statistics
- `"VTOP_STAT"` - Top voltage with statistics
- `"VBAS_STAT"` - Base voltage with statistics
- `"SCREENSHOT"` - Capture oscilloscope screen

**Usage Example:**
```python
scope = logger.connect("rigolds7034")
vavg = scope.get("VAVG", channel=1)
vpp_stats = scope.get("VPP_STAT", channel=2)
freq_stats = scope.get("FREQ_STAT", channel=1)
screenshot = scope.get("SCREENSHOT")  # No channel needed
```

**Documentation:** [RigolDS7034.html](libs/RigolDS7034.html)

---

### DL3021
**DL3021 Programmable DC Electronic Load**

**Supported Commands:**
- `"VOLT"` - Measure input voltage in volts
- `"CURR"` - Measure load current in amperes
- `"VOLT_AVG"` - Average voltage measurement (returns mean and stdev)
- `"CURR_AVG"` - Average current measurement (returns mean and stdev)

**Usage Example:**
```python
load = logger.connect("dl3021")
voltage = load.get("VOLT")
current = load.get("CURR")
mean_v, stdev_v = load.get("VOLT_AVG")  # Returns tuple
```

**Documentation:** [DL3021.html](libs/DL3021.html)

---

### FLUKE45
**Fluke 45 Digital Multimeter**

**Supported Commands:**
- `"voltage"` - DC voltage measurement in volts

**Usage Example:**
```python
dmm = logger.connect("fluke45")
voltage = dmm.get("voltage")
```

**Documentation:** [FLUKE45.html](libs/FLUKE45.html)

---

### KA3010P
**Korad KA3010P Programmable DC Power Supply**

**Supported Commands:**
- `"VOLT"` - Measure actual output voltage in volts
- `"CURR"` - Measure actual output current in amperes

**Usage Example:**
```python
psu = logger.connect("ka3010p")
voltage = psu.get("VOLT")
current = psu.get("CURR")
```

**Documentation:** [KA3010P.html](libs/KA3010P.html)

---

### U1233A
**Agilent U1233A Handheld Digital Multimeter**

**Supported Commands:**
- `"MEAS"` - Single measurement reading (voltage, current, or resistance depending on mode)
- `"MEAS_AVG"` - Average of multiple measurements (returns mean and stdev)

**Usage Example:**
```python
dmm = logger.connect("u1233a")
value, error = dmm.get("MEAS")           # Single reading
mean, stdev = dmm.get("MEAS_AVG")        # Averaged reading
```

**Documentation:** [U1233A.html](libs/U1233A.html)

---

### DAC
**DAC and INA226 Arduino Interface Driver**

**Supported Commands:**
- `"DACA"` - DAC channel A output value
- `"DACB"` - DAC channel B output value
- `"DACC"` - DAC channel C output value
- `"DACD"` - DAC channel D output value
- `"VOLT"` - INA226 bus voltage measurement
- `"CURR"` - INA226 current measurement

*Note: All measurements return a tuple (value, error_estimate).*

**Usage Example:**
```python
dac = logger.connect("dac")
voltage, error = dac.get("VOLT")
current, error = dac.get("CURR")
daca_val, error = dac.get("DACA")
```

**Documentation:** [DAC.html](libs/DAC.html)

---

### EPS
**Hercules MCU Environmental Control System**

**Supported Commands:**
- `"READ_TIME"` - Read timestamp from system
- `"READ_TEMP1"` - Read temperature from sensor 1
- `"READ_HEATER1"` - Read heater 1 control value

*Note: All measurements return a tuple (value, error_estimate).*

**Usage Example:**
```python
eps = logger.connect("eps")
time_val, error = eps.get("READ_TIME")
temp_val, error = eps.get("READ_TEMP1")
heater_val, error = eps.get("READ_HEATER1")
```

**Documentation:** [EPS.html](libs/EPS.html)

---

### DP832
**Rigol DP832 Triple-Output Power Supply (Alternative Driver)**

**Supported Commands:**
- `"VOLT"` - Measure actual output voltage in volts
- `"CURR"` - Measure actual output current in amperes

**Usage Example:**
```python
psu = logger.connect("dp832")
voltage = psu.get("VOLT", channel=1)
current = psu.get("CURR", channel=2)
```

**Documentation:** [DP832.html](libs/DP832.html)

---

## Usage Notes

### General Usage Pattern

All instruments follow the same pattern for accessing measurements through the `data_logger` framework:

```python
from data_logger import data_logger

# Initialize logger
logger = data_logger()
logger.new_file("measurements.txt")

# Connect to instrument
instrument = logger.connect("instrument_name")

# Get measurements using supported commands
value = instrument.get("command_name", channel=1)  # channel optional

# Log measurements
logger.add(instrument, "command_name", channel=1, label="My_Label")
logger.get_data()

# Clean up
logger.close_file()
instrument.disconnect()
```

### Channel Parameters

Some instruments support multi-channel measurements:
- **Oscilloscopes** (KeysightMSOX4154A, RigolDS7034): Use `channel` parameter (1-4)
- **Power Supplies** (RigolDP832, DP832): Use `channel` parameter for multiple outputs
- **Single-channel devices**: Channel parameter ignored or not needed

### Return Types

- **Single values**: Most commands return a single float
- **Statistics**: Return lists/tuples: `[mean, std_dev, min, max]` or `[mean, std_dev, min, max, vpp]`
- **Error tuples**: Some devices return `(value, error_estimate)`
- **Averaged measurements**: Return `(mean, stdev)` tuples

---

## Additional Resources

- **Main Documentation**: [data_logger.html](data_logger.html)
- **Device Driver Standards**: See `docs/DEVICE_DRIVER_STANDARD.md` in repository
- **Quick Reference**: See `docs/DEVICE_DRIVER_QUICK_REFERENCE.md` in repository

---

## Summary Statistics

- **Total Instruments with Measurement Commands**: 13
- **Total Measurement Commands**: 61
- **Instrument Categories**:
  - Multimeters: 4 (DMM6500, Keysight34460A, FLUKE45, U1233A)
  - Oscilloscopes: 2 (KeysightMSOX4154A, RigolDS7034)
  - Power Supplies: 4 (StanfordPS310, RigolDP832, KA3010P, DP832)
  - Electronic Loads: 1 (DL3021)
  - Special Purpose: 2 (DAC, EPS)

---

*Generated for Lab Data Logging API Documentation*  
*For detailed information on each instrument, click the documentation links or select from the main index.*
