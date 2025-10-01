# Lab Data Logging - AI Assistant Instructions

This is a Python-based test equipment automation framework for laboratory measurements and data logging. The codebase follows a device-abstraction pattern for scientific instrument control.

## Architecture Overview

**Core Design Pattern**: The `data_logger` class acts as a centralized orchestrator that connects to various test instruments through standardized device wrapper classes in `libs/`.

- **Main Controller**: `data_logger.py` - Provides unified interface for device connection, measurement configuration, and data collection
- **Device Drivers**: `libs/*.py` - Individual instrument wrappers (DMM6500, Keysight34460A, KeysightMSOX4154A, RigolDP832, etc.) using PyVISA/serial communication
- **Data Flow**: Measurements → CSV files in `captures/` directory with timestamped filenames
- **Post-Processing**: MATLAB scripts (`loadData.m`, `plotData.m`) for statistical analysis and visualization

## Key Development Workflows

### Adding New Instruments
1. Create new device class in `libs/` following the established pattern (see `libs/DMM6500.py` or `libs/Keysight34460A.py`)
2. Implement standardized methods: `get()`, measurement functions (`measure_voltage()`, etc.), `connect()`/`disconnect()`
3. Add device mapping to `data_logger.connect()` method's devices dictionary
4. Update imports in `data_logger.py`

### Device Wrapper Conventions
- **Connection**: Auto-detect instruments using PyVISA resource manager or fixed addresses
- **Error Handling**: Use colorama-styled console output (`_ERROR_STYLE`, `_SUCCESS_STYLE`, `_WARNING_STYLE`)
- **Measurement Interface**: Provide both direct methods (`measure_voltage()`) and generic `get(item)` interface
- **Statistics Support**: For instruments like DMM6500, implement `get("statistics")` returning `[avg, std_dev, min, max]`

### Testing and Validation
- **Dependencies**: Run `verify_installation.py` to check PyVISA, colorama, numpy, pyserial installation
- **Instrument Testing**: Use `run_test.py` for DMM6500 buffer downloads and plotting
- **Oscilloscope Testing**: Use `test_oscilloscope_direct.py` or `test_msox4154a_simple.py` for MSOX4154A validation
- **Waveform Capture**: `test_waveforms.py` handles multi-instrument synchronization (oscilloscopes + DMM)

### Data Collection Patterns
```python
logger = data_logger()
logger.new_file("experiment.txt")
dmm = logger.connect("dmm6500")
osc = logger.connect("msox4154a") 
logger.add("Voltage", dmm, "voltage")  # Label, device, measurement_type
logger.add("CH1_Stats", osc, "statistics", channel=1)  # Oscilloscope channel stats
measurements = logger.get_data()
logger.close_file()
```

## Critical Implementation Details

- **File Management**: The logger prevents adding measurements to existing files (warns user to create new file)
- **Device Connection**: Each device class handles its own VISA/serial connection with auto-detection
- **Output Format**: Tab-delimited files with statistical data support (value + error columns)
- **Timestamping**: Consistent `YYYYMMDD_HHMMSS` format across all captured data files
- **Loading Indicators**: Use `loading.py` class for user feedback during long operations

## Integration Points

- **MATLAB Interface**: Data processing expects tab-delimited format with specific column naming conventions
- **Multi-Instrument Sync**: `test_waveforms.py` demonstrates coordinating oscilloscopes and DMMs for time-correlated measurements
- **Buffer Management**: DMM6500 supports high-speed digitizing via `defbuffer1` with `fetch_trace()` method

## Environment Setup
Always use virtual environment: `python3 -m venv .venv` → activate → `pip install -r requirements.txt`

When modifying device drivers, maintain backward compatibility with the `data_logger` interface and existing measurement scripts.