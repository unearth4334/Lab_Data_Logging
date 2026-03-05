# UV/OV Lockout Hysteresis Test

Automated test script for measuring under-voltage (UV) and over-voltage (OV) lockout hysteresis on power supply protection circuits.

## Installation

```bash
pip install lockout-hysteresis-test-1.0.0-py3-none-any.whl
```

## Hardware Requirements

- **Rigol DP711** programmable DC power supply (RS-232/USB)
- **Keithley DMM6500** digital multimeter (USB/Ethernet/GPIB)
- Device Under Test (DUT) with UV/OV protection circuit

## Usage

### Command Line

```bash
# Interactive mode (press Enter at breakpoints)
lockout-hysteresis-test

# Automated with 1-second delays
lockout-hysteresis-test --auto

# Fully automated (no pauses)
lockout-hysteresis-test --no-debug

# Custom sweep parameters
lockout-hysteresis-test --start 9.0 --end 15.0 --step 0.005 --settle 0.2

# Specify COM port
lockout-hysteresis-test --com COM15

# Set current limit
lockout-hysteresis-test --current 1.5
```

### Python API

```python
from lockout_hysteresis_test import run_lockout_test

# Run test programmatically
run_lockout_test(
    v_start=10.0,
    v_end=14.0,
    v_step=0.005,
    settle_s=0.05,
    current_limit_a=2.0,
    mode='debug'  # 'debug', 'auto', or 'off'
)
```

## Test Procedure

1. DP711 sweeps voltage from low → high (rising edge)
2. DP711 sweeps voltage from high → low (falling edge)
3. DMM6500 records voltage at each setpoint
4. Data saved to CSV in `output/lockout_hysteresis/`
5. Interactive Plotly chart shows hysteresis band

## Output Files

- **CSV**: `lockout_hysteresis_YYYYMMDD_HHMMSS.csv` - Raw measurement data
- **HTML**: `lockout_hysteresis_YYYYMMDD_HHMMSS.html` - Interactive plot

## License

Apache License 2.0
