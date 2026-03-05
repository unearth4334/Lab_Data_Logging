# Lockout Hysteresis Test Package - Installation & Usage Guide

## Package Contents

Your installable Python package has been created in the `wheels/` directory:

- **Wheel file** (recommended): `lockout_hysteresis_test-1.0.0-py3-none-any.whl` (13.6 KB)
- **Source distribution**: `lockout_hysteresis_test-1.0.0.tar.gz` (12.1 KB)

## Installation

### Install from Wheel File (Recommended)

```bash
pip install lockout_hysteresis_test-1.0.0-py3-none-any.whl
```

### Install from Source

```bash
pip install lockout_hysteresis_test-1.0.0.tar.gz
```

### Verify Installation

```bash
pip show lockout-hysteresis-test
lockout-hysteresis-test --help
```

## Usage

### Command Line Interface

After installation, the `lockout-hysteresis-test` command is available globally:

```bash
# Interactive mode (press Enter at breakpoints)
lockout-hysteresis-test

# Automated with 1-second delays
lockout-hysteresis-test --auto

# Fully automated (no pauses)
lockout-hysteresis-test --no-debug

# Custom parameters
lockout-hysteresis-test --start 9.0 --end 15.0 --step 0.005 --settle 0.2

# Specify COM port
lockout-hysteresis-test --com COM15

# Set current limit
lockout-hysteresis-test --current 1.5
```

### Python API

```python
from lockout_hysteresis_test import run_lockout_test

# Run test with default settings
run_lockout_test()

# Run with custom parameters
run_lockout_test(
    v_start=10.0,
    v_end=14.0,
    v_step=0.005,
    settle_s=0.05,
    current_limit_a=2.0,
    mode='auto',  # 'debug', 'auto', or 'off'
    com_port='COM15',
    output_dir='./my_output'
)
```

## Database Storage

The wheel file is **~14 KB** - perfect for storing in a database:

1. **Store file**: Save the .whl file as a BLOB in your database
2. **Version tracking**: Use the version number (1.0.0) for tracking
3. **Metadata**: Store filename, size, upload date, description

Example database schema:
```sql
CREATE TABLE test_packages (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    version VARCHAR(50),
    filename VARCHAR(255),
    file_data BLOB,
    file_size INTEGER,
    upload_date TIMESTAMP,
    description TEXT
);
```

## Distribution Options

### Option 1: Direct File Share
Simply share the `.whl` file via email, network drive, or cloud storage.
Recipients install with: `pip install lockout_hysteresis_test-1.0.0-py3-none-any.whl`

### Option 2: Internal Package Index
Host an internal PyPI server and upload the package:
```bash
pip install twine
twine upload --repository-url http://your-pypi-server lockout_hysteresis_test-1.0.0-py3-none-any.whl
```

Then users install with:
```bash
pip install lockout-hysteresis-test --index-url http://your-pypi-server
```

### Option 3: Database Retrieval
Users can download the .whl from your database and install locally:
```bash
# Download from database to local file
download_from_db('lockout_hysteresis_test-1.0.0-py3-none-any.whl')

# Install
pip install lockout_hysteresis_test-1.0.0-py3-none-any.whl
```

## Updating the Package

To create a new version:

1. Update version in `lockout_hysteresis_test/pyproject.toml`
2. Rebuild: `py -m build`
3. Move new wheel from `dist/` to `wheels/`

## Uninstallation

```bash
pip uninstall lockout-hysteresis-test
```

## Dependencies

The package automatically installs these dependencies:
- pyvisa >= 1.13.0 (DMM6500 communication)
- pyserial >= 3.5 (DP711 communication)
- colorama >= 0.4.6 (colored terminal output)
- plotly >= 5.0.0 (interactive plotting)

## Hardware Requirements

- Rigol DP711 programmable DC power supply (RS-232/USB)
- Keithley DMM6500 digital multimeter (USB/Ethernet/GPIB)
- Device Under Test (DUT) with UV/OV protection circuit

## Troubleshooting

### Python Not Found
Use the `py` launcher on Windows:
```bash
py -m pip install lockout_hysteresis_test-1.0.0-py3-none-any.whl
```

### Import Errors
Ensure you're using Python 3.8 or later:
```bash
python --version
```

### COM Port Issues
The script will prompt for COM port selection if not specified.
Set environment variable for persistent selection:
```bash
# Windows
set DP711_COM_PORT=COM15

# Linux/Mac
export DP711_COM_PORT=/dev/ttyUSB0
```

## File Locations

- **Package source**: `lockout_hysteresis_test/`
- **Built packages**: `wheels/`
- **Test output**: `./output/lockout_hysteresis/` (in current working directory)

## Advantages Over EXE

✅ **Small size**: 14 KB vs 50+ MB for PyInstaller exe  
✅ **Python ecosystem**: Standard pip installation  
✅ **Cross-platform**: Works on Windows, Linux, macOS  
✅ **Debuggable**: Full Python traceback and debugging  
✅ **Database-friendly**: Tiny BLOB storage  
✅ **Version control**: Semantic versioning built-in  
✅ **Dependencies**: Automatically managed by pip  
✅ **Updatable**: Easy version upgrades  

## Support

For issues or questions, contact your lab automation team.
