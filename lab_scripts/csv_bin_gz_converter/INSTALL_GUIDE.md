# CSV to BIN.GZ Converter - Installation & Quick Start Guide

## Prerequisites

### Python (for CLI launcher)
- Python 3.8 or higher
- pip package manager

### Node.js and npm (Required for the Electron app)
- **Node.js 14+** with **npm 6+**
- Download from: https://nodejs.org/
- **This is required** — the app cannot run without Node.js installed

**After installing Node.js, verify the installation:**
```bash
node --version
npm --version
```

## Installation Methods

### Method 1: Install from Wheel Package (Recommended)

```bash
# Navigate to the package directory
cd lab_scripts/csv_bin_gz_converter

# Install the package
pip install csv_bin_gz_converter-1.0.0-py3-none-any.whl

# Verify installation
csv-bin-gz-converter --version

# Launch the application
csv-bin-gz-converter
```

### Method 2: Install from Source

```bash
# Navigate to the package directory
cd lab_scripts/csv_bin_gz_converter

# Install dependencies and package
pip install .

# Launch the application
csv-bin-gz-converter
```

### Method 3: Direct App Launch (No Python Installation Required)

```bash
# Install Electron dependencies only
cd apps/csv_bin_gz_electron
npm install

# Launch the app
npm start
```

## Quick Start

### 1. After Installation

If you installed via pip (Methods 1 or 2), simply run:
```bash
csv-bin-gz-converter
```

If you're launching directly (Method 3), run:
```bash
cd apps/csv_bin_gz_electron
npm start
```

### 2. Using the Application

1. The desktop application window opens showing the converter interface
2. **Select Files**: Click "Choose Files" or drag CSV files into the window
3. **Choose Converter**: Select the appropriate conversion type:
   - "Current Measurements" - Standard CSV to binary conversion
   - "Power Rails" - Power supply data with column reordering
4. **Configure (Optional)**:
   - If using Power Rails, select a column template if needed
   - Review the column mapping preview
5. **Convert**: Click the "Convert" button to process files
6. **Results**: Converted `.bin.gz` files are saved to the output directory

### 3. Output Files

For each converted CSV, you get:
- **File.bin.gz** - Compressed binary data
- **File_metadata.json** - Metadata including column names, types, and timestamps

### 4. Storing Converted Data

The binary output is ideal for database storage:

```python
# Example: Store in database
import sqlite3
from pathlib import Path

conn = sqlite3.connect('lab_records.db')
cursor = conn.cursor()

# Read and store binary data
with open('measurement_20260310_120000.bin.gz', 'rb') as f:
    binary_data = f.read()

cursor.execute("""
    INSERT INTO measurements (timestamp, filename, binary_data)
    VALUES (?, ?, ?)
""", ('2026-03-10 12:00:00', 'measurement_20260310_120000.bin.gz', binary_data))

conn.commit()
```

## Advanced Usage

### Using Python API

```python
from csv_bin_gz_converter import launch_app

# Launch the app programmatically
exit_code = launch_app(debug=True)
```

### Custom Column Templates

Create custom column mapping templates in `apps/csv_bin_gz_electron/column_templates/`:

```yaml
# templates/my_test.yml
columns:
  - name: "Time"
    mapping: "timestamp_column"
    units: "seconds"
  - name: "Voltage"
    mapping: "v_measurement"
    units: "volts"
  - name: "Current"
    mapping: "i_measurement"
    units: "amps"
```

Then select this template in the UI when converting Power Rails data.

### Configuration

Edit `apps/csv_bin_gz_electron/config.yml`:

```yaml
output:
  directory: "./captures"
  compressed: true
  metadata_included: true

templates:
  default: "standard"
  available:
    - "standard"
    - "power_rails"
    - "my_test"
```

## Troubleshooting

### Issue: "npm or Node.js not found" when launching

**Root Cause**: Node.js isn't installed or not in your system PATH.

**Solution**: Install Node.js from https://nodejs.org/
1. **Windows**: Download the installer and run it
   - Ensure "Add to PATH" is checked during installation
2. **macOS**: Use Homebrew
   ```bash
   brew install node
   ```
3. **Linux**: Use your package manager
   ```bash
   sudo apt-get install nodejs npm
   ```

**After installation**, restart your terminal and verify:
```bash
node --version
npm --version
csv-bin-gz-converter
```

### Issue: "Command not found: csv-bin-gz-converter"

**Solutions:**
- On Windows, use: `py -m csv_bin_gz_converter.cli`
- On macOS/Linux, ensure the venv is activated: `source .venv/bin/activate`
- Or reinstall the package with: `pip install --upgrade csv_bin_gz_converter-1.0.0-py3-none-any.whl`

### Issue: Application exits immediately after launching

**Solution**: The launcher automatically installs missing dependencies:
```bash
cd apps/csv_bin_gz_electron
npm install
csv-bin-gz-converter
```
npm install
npm start
```

### Issue: "Cannot find module" error

**Solution**: Ensure all dependencies are installed:
```bash
cd apps/csv_bin_gz_electron
rm -rf node_modules package-lock.json
npm install
npm start
```

### Issue: Port already in use

**Solution**: The app uses a port (default: 3000). If already in use:
1. Close other applications using that port
2. Or modify the port in `apps/csv_bin_gz_electron/config.yml`

## Updating the Package

To update to a new version:

```bash
# Uninstall current version
pip uninstall csv-bin-gz-converter -y

# Install new version
pip install csv_bin_gz_converter-1.0.0-py3-none-any.whl
```

## Uninstalling

```bash
pip uninstall csv-bin-gz-converter -y
```

The Electron app remains in `apps/csv_bin_gz_electron` and can still be launched via `npm start`.

## Support

For detailed usage information, see [README.md](README.md).

For issues with the Lab Data Logging project, refer to the main project documentation at `../../README.md`.
