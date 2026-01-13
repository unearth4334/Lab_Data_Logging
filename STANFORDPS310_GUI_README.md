# Stanford PS310 High Voltage Power Supply GUI

A web-based interactive GUI for controlling the Stanford Research Systems PS310 High Voltage Power Supply with adjustable voltage ramping capabilities.

## Features

### 🔌 Device Connection
- Auto-detection of GPIB devices using PyVISA
- Easy connection/disconnection interface
- Real-time connection status indicator

### 🎛️ Manual Control
- Set target voltage (-1250V to 0V for negative polarity model)
- Configure current limit (0 to 21 mA)
- Enable/disable high voltage output with safety checks
- Immediate voltage setpoint control

### 📊 Live Monitoring
- Real-time voltage readings (set point and actual output)
- Current monitoring in milliamps
- Output status display (ON/OFF)
- Connection status indicator
- Auto-updating display (1 second refresh rate)

### 🚀 Voltage Ramping
- **Adjustable Parameters:**
  - Start Voltage: Initial voltage setpoint
  - End Voltage: Target voltage setpoint
  - Step Size: Voltage increment per step
  - Delay: Time between steps (seconds)
- **Real-time Progress:**
  - Visual progress bar
  - Step count and estimated duration
  - Ability to stop ramp at any time
- **Safety Features:**
  - Validation of voltage ranges
  - Current limit protection
  - Emergency stop capability

### ⚠️ Safety Features
- High voltage safety warnings prominently displayed
- Maximum voltage limits enforced (-1250V to 0V)
- Current limiting (0 to 21 mA)
- Output disable before disconnect recommended
- Input validation for all parameters

## Installation

### Prerequisites

1. **Python 3.7+** with the following packages:
   ```bash
   pip install fastapi uvicorn pyvisa colorama
   ```

2. **VISA Backend**: Install one of the following:
   - **NI-VISA** (recommended for National Instruments GPIB adapters)
   - **pyvisa-py** (pure Python VISA implementation)
   ```bash
   pip install pyvisa-py
   ```

3. **GPIB Interface**: 
   - National Instruments GPIB-USB-HS adapter (or compatible)
   - Properly configured GPIB drivers for your operating system

### Running the GUI

1. Navigate to the Lab_Data_Logging directory:
   ```bash
   cd Lab_Data_Logging
   ```

2. Start the GUI server:
   ```bash
   python stanfordps310_gui.py
   ```

3. Open your web browser and navigate to:
   ```
   http://localhost:8082
   ```

4. The GUI is now ready to use!

## Usage Guide

### Connecting to the PS310

1. **Scan for Devices**: Click the "🔄 Refresh Devices" button to scan for available GPIB devices
2. **Select Address**: Choose your PS310's VISA address from the dropdown menu
3. **Connect**: Click the "🔌 Connect" button
4. Wait for the green "Connected" status indicator

### Setting Voltage Manually

1. Ensure the device is connected (green status indicator)
2. Enter desired voltage in the "Set Voltage (V)" field (must be negative, e.g., -100)
3. Optionally adjust the "Current Limit (mA)" (default: 10 mA)
4. Click "📝 Set Voltage" to apply the voltage setpoint
5. Click "⚡ Output ON" to enable the high voltage output
6. Monitor the actual output voltage and current in the Live Readings panel

### Using Voltage Ramping

The voltage ramping feature allows you to smoothly transition from one voltage to another over time, which is useful for:
- Gradual voltage application to sensitive devices
- Automated voltage sweeps for characterization
- Reducing stress on test equipment
- Preventing sudden voltage changes

**Example: Ramping from 0V to -500V**

1. Configure the ramp parameters:
   - **Start Voltage**: 0 V
   - **End Voltage**: -500 V
   - **Step Size**: 10 V (creates 50 steps)
   - **Delay**: 1 second (total duration ~50 seconds)

2. Review the "Ramp Info" which shows calculated steps and duration

3. **Important**: Enable the output first by clicking "⚡ Output ON"

4. Click "🚀 Start Ramp" to begin the voltage ramp

5. Monitor progress:
   - Progress bar shows completion percentage
   - Live readings display current voltage and current
   - Ramping status indicator turns yellow

6. To stop early: Click "🛑 Stop Ramp" at any time

**Ramp Direction**: The GUI automatically handles both increasing and decreasing voltage ramps based on your start and end values.

## Safety Considerations

⚠️ **HIGH VOLTAGE DEVICE - EXTREME CAUTION REQUIRED**

### Before Operating:
- Read and understand the PS310 user manual
- Verify all connections are secure before enabling output
- Use appropriate high voltage safety equipment (insulated tools, safety glasses)
- Ensure proper grounding of all equipment
- Work with a partner when dealing with high voltages

### During Operation:
- Always disable output before disconnecting or adjusting connections
- Monitor current readings to detect short circuits or overload conditions
- Keep current limit set to appropriate level for your application (default: 10 mA)
- Use the gradual voltage ramping feature when possible
- Be aware of maximum voltage rating (±1250V)

### Emergency Procedures:
- Click "🔴 Output OFF" immediately if issues occur
- Use the "🛑 Stop Ramp" button to halt voltage ramping
- Disconnect the device using the "🔌 Disconnect" button
- In case of emergency, use the PS310's front panel emergency stop if available

## Technical Details

### Architecture
- **Backend**: FastAPI web framework for RESTful API
- **Frontend**: Pure HTML/CSS/JavaScript (no external dependencies)
- **Communication**: GPIB via PyVISA
- **Update Rate**: 1 Hz for status and measurements

### API Endpoints

The GUI provides the following REST API endpoints:

- `GET /` - Main GUI interface
- `GET /list_visa_resources` - List available VISA devices
- `POST /connect` - Connect to PS310 at specified address
- `POST /disconnect` - Disconnect from PS310
- `POST /set_voltage` - Set output voltage
- `POST /set_current_limit` - Set current limit
- `POST /set_output` - Enable/disable output
- `POST /start_ramp` - Start voltage ramping
- `POST /stop_ramp` - Stop voltage ramping
- `GET /status` - Get current device status and measurements

### Logging

The GUI creates a log file `stanfordps310_gui.log` with detailed information about:
- Connection events
- Voltage and current settings
- Ramp operations and progress
- Errors and warnings

## Troubleshooting

### "PyVISA is not installed"
```bash
pip install pyvisa pyvisa-py
```

### "Could not locate a VISA implementation"
Install NI-VISA from National Instruments website or install pyvisa-py:
```bash
pip install pyvisa-py
```

### No devices found
1. Check GPIB cable connections
2. Verify PS310 is powered on
3. Check GPIB address on PS310 front panel (default is typically 14)
4. Ensure GPIB-USB adapter drivers are installed
5. Try refreshing devices using the "🔄 Refresh Devices" button

### Connection fails
1. Verify the VISA address is correct (e.g., GPIB0::14::INSTR)
2. Check that no other software is using the GPIB device
3. Restart the PS310 power supply
4. Try restarting the GUI server

### Ramp doesn't start
1. Ensure the device is connected (green status indicator)
2. Verify ramp parameters are valid (voltages within -1250V to 0V)
3. Check that output is enabled before starting ramp
4. Ensure step size is positive and non-zero

## Integration with Lab_Data_Logging

This GUI is designed to work seamlessly with the Lab_Data_Logging framework:

- Uses the same `StanfordPS310` driver from `libs/StanfordPS310.py`
- Follows the same coding style and patterns as `measurement_gui.py`
- Logs to consistent format for integration with other lab tools
- Can be extended to include data logging and capture features

## Advanced Usage

### Custom Port and Host

The GUI binds to localhost (`127.0.0.1`) by default for security. You can customize this using environment variables:

```bash
# Change port (default: 8082)
export PS310_GUI_PORT=8083
python stanfordps310_gui.py

# Enable network access (use with caution!)
export PS310_GUI_HOST=0.0.0.0
python stanfordps310_gui.py
```

### Remote Access

For secure remote access, use SSH tunneling instead of exposing the server to the network:

```bash
# On the remote machine, create an SSH tunnel
ssh -L 8082:localhost:8082 user@lab-computer

# Then access the GUI locally at
http://localhost:8082
```

**Security Note**: The GUI has no authentication. Exposing it to the network allows anyone to control the high voltage power supply. Only use network binding (`PS310_GUI_HOST=0.0.0.0`) on trusted, isolated networks with proper firewall rules.

### Automation
The REST API can be used for automated control:

```python
import requests

# Connect
requests.post('http://localhost:8082/connect', 
              json={'address': 'GPIB0::14::INSTR'})

# Set voltage
requests.post('http://localhost:8082/set_voltage', 
              json={'voltage': -100})

# Enable output
requests.post('http://localhost:8082/set_output', 
              json={'state': True})

# Start ramp
requests.post('http://localhost:8082/start_ramp',
              json={'start': -100, 'end': -500, 'step': 10, 'delay': 1})
```

## Contributing

When extending this GUI, please:
1. Follow the existing code style and patterns
2. Add appropriate error handling and validation
3. Update this README with new features
4. Test thoroughly with actual hardware when possible
5. Add logging for important operations

## License

This software is licensed under the Apache License 2.0, consistent with the Lab_Data_Logging project.

## Credits

- **PS310 Driver**: Based on the StanfordPS310 driver in `libs/StanfordPS310.py`
- **GUI Framework**: Inspired by the measurement_gui.py pattern
- **Laboratory**: Developed for precision high voltage power supply control in laboratory environments

---

**Last Updated**: January 2026  
**Version**: 1.0.0  
**Author**: Lab_Data_Logging Project Contributors
