# DMM6500 Resistance Measurement Plotter

A Python script for real-time resistance measurement collection and visualization from the Keithley DMM6500 Digital Multimeter.

## Features

- **Real-time measurements**: Configurable measurement intervals from the DMM6500
- **Live plotting**: Auto-scaling plots with each new data point (GUI mode)
- **Statistical analysis**: Automatic calculation of statistics for the latest 10 measurements
- **Dual modes**: GUI mode with matplotlib plotting or text-only mode for headless environments
- **Demo mode**: Test functionality without hardware connection
- **Data management**: Configurable maximum data points for memory efficiency
- **Cross-platform**: Works on Windows, Linux, and macOS

## Requirements

- Python 3.7+
- Dependencies from `requirements.txt`:
  - `matplotlib>=3.5.0` (for plotting functionality)
  - `numpy>=1.21.0` (for statistical calculations)
  - `pyvisa>=1.11.0` (for DMM6500 communication)
  - `colorama>=0.4.6` (for colored terminal output)

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure the DMM6500 device library is available:
   ```bash
   # The script automatically imports from ./libs/DMM6500.py
   ```

## Usage

### Basic Usage

```bash
# Real hardware - GUI mode with plotting
python3 resistance_plotter.py --interval 2.0

# Real hardware - text-only mode
python3 resistance_plotter.py --interval 1.0 --no-gui

# Demo mode for testing (no hardware required)
python3 resistance_plotter.py --demo --interval 0.5 --max-points 50
```

### Command Line Options

```
Options:
  -h, --help            Show help message and exit
  --interval INTERVAL   Measurement interval in seconds (default: 1.0)
  --max-points MAX      Maximum number of points to display (default: 100)
  --demo               Run in demo mode without hardware connection
  --no-gui             Run without GUI (text-only mode)
```

### Examples

1. **Fast measurements with statistics tracking**:
   ```bash
   python3 resistance_plotter.py --demo --interval 0.5 --max-points 20
   ```

2. **Long-term monitoring**:
   ```bash
   python3 resistance_plotter.py --interval 5.0 --max-points 200
   ```

3. **Headless operation**:
   ```bash
   python3 resistance_plotter.py --no-gui --interval 2.0
   ```

## Features in Detail

### Real-time Measurements

The script connects to the DMM6500 and takes resistance measurements at user-defined intervals. Each measurement is timestamped and stored for analysis.

### Autoscaling Plots

In GUI mode, the script provides:
- **Main plot**: Time-series plot of resistance vs. time with automatic scaling
- **Statistics plot**: Bar chart of the latest 10 measurements with statistical overlays
- **Real-time updates**: Plot refreshes automatically with new data

### Statistical Analysis

After collecting at least 10 measurements, the script calculates and displays:
- **Mean**: Average resistance of the latest 10 measurements
- **Standard deviation**: Measure of measurement variability
- **Min/Max**: Range of the latest 10 measurements

Example output:
```
--- Latest 10 Measurements Statistics ---
Mean: 1023.45 Ω
Std Dev: 2.34 Ω
Min: 1019.87 Ω
Max: 1027.12 Ω
----------------------------------------
```

### Demo Mode

For testing and development without hardware:
- Generates realistic resistance data with noise and drift
- Simulates DMM6500 behavior
- Allows full functionality testing

## Integration with Existing Systems

The resistance plotter can be used alongside the existing `data_logger` infrastructure:

```python
# Example: Using both systems
from data_logger import data_logger
from resistance_plotter import ResistancePlotter

# Setup structured logging
logger = data_logger()
logger.new_file("resistance_log.txt")
dmm = logger.connect("dmm6500")
logger.add("Resistance", dmm, "resistance")

# Setup real-time visualization
plotter = ResistancePlotter(interval=2.0, demo_mode=False)
# Use both systems in parallel for comprehensive data acquisition
```

## Architecture

The script is designed with modularity in mind:

- **`ResistancePlotter` class**: Main coordination and data management
- **Measurement loop**: Separate thread for continuous data collection
- **Plotting updates**: Separate thread for GUI updates (when applicable)
- **Statistics engine**: Automatic calculation of measurement statistics
- **Cross-platform compatibility**: Handles different operating systems gracefully

## Error Handling

The script includes robust error handling for:
- Hardware connection failures
- Missing dependencies
- Invalid command-line arguments
- Measurement errors
- GUI/display issues

## Output Formats

### Text Mode Output
```
Measurement 15: 1025.67 Ω (t=14.2s)
Measurement 16: 1023.45 Ω (t=15.2s)

--- Latest 10 Measurements Statistics ---
Mean: 1024.56 Ω
Std Dev: 3.21 Ω
Min: 1019.87 Ω
Max: 1029.34 Ω
----------------------------------------
```

### GUI Mode Features
- Real-time line plot with automatic scaling
- Statistical overlay on measurements
- Bar chart of latest 10 measurements
- Information panel with current statistics

## Testing

Run the included test suite:
```bash
python3 test_resistance_plotter.py
```

The test suite includes:
- Unit tests for all core functionality
- Functional tests with simulated data
- Demo mode validation
- Error condition testing

## Troubleshooting

### Common Issues

1. **"DMM6500 not found"**
   - Ensure the DMM6500 is connected and powered on
   - Check VISA drivers are installed
   - Try demo mode to verify script functionality

2. **"matplotlib not available"**
   - Install matplotlib: `pip install matplotlib>=3.5.0`
   - Use `--no-gui` flag for text-only operation

3. **"VISA implementation not found"**
   - Install VISA drivers (NI-VISA or pyvisa-py)
   - Use demo mode for testing: `--demo`

### Performance Tips

- For long-term monitoring, use larger `--max-points` values
- For real-time analysis, use shorter `--interval` values
- Use `--no-gui` mode for lower resource usage
- Consider data logging integration for permanent storage

## License

This project is licensed under the Apache License 2.0. See the license headers in the source files for details.

## Contributing

This script is part of the Lab Data Logging project. Contributions should follow the project's coding standards and include appropriate tests.