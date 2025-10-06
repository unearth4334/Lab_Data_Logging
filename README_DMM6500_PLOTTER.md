# DMM6500 Resistance Plotter

A Python script for real-time resistance measurement and plotting from a Keithley DMM6500 Digital Multimeter.

## Features

- **Real-time plotting**: Measurements are taken at configurable intervals and plotted in real-time
- **Autoscaling**: The plot automatically scales to fit all data points
- **Slope analysis**: Calculates the slope of the latest 10 measurements
- **Visual indicators**: A colored box around the latest 10 data points:
  - **RED**: Slope magnitude >= threshold (resistance is changing)
  - **GREEN**: Slope magnitude < threshold (resistance is stable)
- **Configurable parameters**: Measurement interval, slope threshold, and maximum points
- **Mock mode**: Includes a mock DMM for testing without hardware

## Installation

Ensure you have the required dependencies installed:

```bash
pip install matplotlib numpy pyvisa pyvisa-py
```

## Usage

### Basic Usage

```bash
python dmm6500_resistance_plotter.py
```

This starts measurements with default settings:
- Measurement interval: 1.0 seconds
- Slope threshold: 0.01 Ω/s
- Maximum points: 100

### Command Line Options

```bash
python dmm6500_resistance_plotter.py [options]

Options:
  -h, --help                 Show help message
  -i, --interval SECONDS     Measurement interval in seconds (default: 1.0)
  -t, --threshold OHMS_PER_SEC  Slope threshold for color change (default: 0.01)
  -m, --max-points N         Maximum number of points to display (default: 100)
  -v, --verbose              Enable verbose logging
```

### Examples

**Fast measurements with sensitive slope detection:**
```bash
python dmm6500_resistance_plotter.py --interval 0.5 --threshold 0.005
```

**Slow measurements for long-term monitoring:**
```bash
python dmm6500_resistance_plotter.py --interval 5.0 --max-points 200
```

**Debug mode:**
```bash
python dmm6500_resistance_plotter.py --verbose
```

## Testing

Run the test script to verify functionality without hardware:

```bash
python test_dmm6500_plotter.py
```

View usage examples:

```bash
python example_usage.py
```

## How It Works

1. **Connection**: The script automatically connects to a DMM6500 multimeter
2. **Measurement**: Resistance measurements are taken at the specified interval
3. **Data Storage**: Measurements are stored with timestamps
4. **Plotting**: The plot updates in real-time with autoscaling
5. **Slope Calculation**: After 10+ measurements, the slope of the latest 10 points is calculated using linear regression
6. **Visual Feedback**: A colored box is drawn around the latest 10 points:
   - Box color indicates whether the resistance is stable (green) or changing (red)
   - Slope value and R² are displayed in a text box

## Algorithm Details

### Slope Calculation

The slope is calculated using linear regression on the latest 10 data points:

```
slope = (n×Σ(xy) - Σ(x)×Σ(y)) / (n×Σ(x²) - (Σ(x))²)
```

Where:
- n = 10 (number of points)
- x = time values
- y = resistance values

### Color Threshold Logic

```python
if abs(slope) < threshold:
    box_color = 'green'  # Stable
else:
    box_color = 'red'    # Changing
```

## Mock Mode

If no DMM6500 is connected, the script automatically uses a mock device that simulates:
- Base resistance of 1000Ω
- Slow sinusoidal drift (±2Ω)
- Random noise (±0.5Ω)

This allows testing and demonstration without hardware.

## Error Handling

- **Connection errors**: Gracefully falls back to mock mode
- **Measurement errors**: Logged and skipped (plot continues)
- **User interruption**: Clean disconnection on Ctrl+C

## Requirements

- Python 3.6+
- matplotlib
- numpy
- pyvisa
- pyvisa-py (for VISA backend)
- Keithley DMM6500 (optional - mock mode available)

## File Structure

```
dmm6500_resistance_plotter.py  # Main script
test_dmm6500_plotter.py       # Test suite
example_usage.py              # Usage examples
README_DMM6500_PLOTTER.md     # This documentation
```

## License

Apache License 2.0 - See LICENSE file for details.