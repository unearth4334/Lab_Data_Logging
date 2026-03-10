# Lab Scripts Packaging Guide

This directory contains Python packages for laboratory automation scripts. Follow these guidelines when creating new packaged lab scripts.

## Directory Structure Convention

Each package should follow this standard structure:

```
lab_scripts/
  └── <package_name>/
      ├── dist/                           # Built distributions (wheel + tar.gz)
      │   ├── <package_name>-1.0.0-py3-none-any.whl
      │   └── <package_name>-1.0.0.tar.gz
      ├── <package_name>/                  # Source code package
      │   ├── drivers/                     # Device/driver modules
      │   │   ├── __init__.py
      │   │   └── <device>.py
      │   ├── __init__.py                  # Package entry point
      │   ├── cli.py                       # Command-line interface
      │   ├── main.py or core.py           # Main functionality
      │   └── utils.py (optional)          # Utility functions
      ├── pyproject.toml                   # Package metadata & build config
      ├── README.md                        # User documentation
      ├── INSTALL_GUIDE.md                 # Installation & usage guide
      ├── MANIFEST.in                      # File inclusion rules
      └── .gitignore (optional)
```

## Naming Conventions

- **Folder name**: Use lowercase with underscores: `dmm6500_buffer_download`, `lockout_hysteresis_test`
- **Python package name**: Match folder name using underscores
- **CLI command name**: Use hyphens: `dmm6500-buffer-download`, `lockout-hysteresis-test`
- **Distribution folder**: Use `dist/` for built distributions

## Creating a New Packaged Lab Script

### Step 1: Create the Folder Structure

```bash
cd lab_scripts/
mkdir my_lab_script
cd my_lab_script
mkdir my_lab_script/drivers
touch pyproject.toml README.md INSTALL_GUIDE.md MANIFEST.in
touch my_lab_script/__init__.py
touch my_lab_script/cli.py
touch my_lab_script/main.py
```

### Step 2: Create `pyproject.toml`

Use this template:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-lab-script"
version = "1.0.0"
description = "Brief description of what the script does"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "Apache-2.0"}
authors = [
    {name = "Redlen Technologies"}
]

dependencies = [
    "pyvisa>=1.13.0",  # For instrument communication
    "pyserial>=3.5",   # For serial devices
    "colorama>=0.4.6", # For colored output
]

[project.optional-dependencies]
plot = ["matplotlib>=3.5.0"]

[project.scripts]
my-lab-script = "my_lab_script.cli:main"

[project.urls]
Homepage = "https://github.com/redlentech/lab-data-logging"
```

### Step 3: Create `__init__.py`

```python
"""
My Lab Script - Brief Description
==================================
"""

__version__ = "1.0.0"

from .main import run_experiment  # Add your main functions

__all__ = ["run_experiment"]
```

### Step 4: Create `cli.py`

```python
import argparse
import sys
from .main import run_experiment

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Description of your lab script'
    )
    
    parser.add_argument('--param', type=str, help='Parameter description')
    args = parser.parse_args()
    
    try:
        run_experiment(param=args.param)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Step 5: Create Documentation

See existing packages (`lockout_hysteresis_test`, `dmm6500_buffer_download`) for examples of README.md and INSTALL_GUIDE.md.

### Step 6: Build the Package

See the "Building Packages" section below for using the automated build script.

## Building Packages

### Using the Automated Build Script

The `build_package.py` script provides a convenient way to build lab_scripts packages with automatic validation, cleaning, and artifact management.

#### Basic Usage

```bash
# From lab_scripts directory
python build_package.py <package_folder>

# Examples:
python build_package.py dmm6500_buffer_download
python build_package.py lockout_hysteresis_test
python build_package.py GEN4_BRUP_dmm6500_buffer_download
```

The script accepts flexible path inputs:
- Package name only: `dmm6500_buffer_download`
- Relative path: `lab_scripts/dmm6500_buffer_download`
- Absolute path: `C:\...\Lab_Data_Logging\lab_scripts\dmm6500_buffer_download`

#### Options

```bash
# Clean old artifacts before building
python build_package.py dmm6500_buffer_download --clean

# Build and install the package
python build_package.py dmm6500_buffer_download --clean --install

# Enable verbose output for debugging
python build_package.py dmm6500_buffer_download --verbose
```

**Available flags:**
- `--clean`: Remove old build artifacts (dist/, build/, *.egg-info/) before building
- `--install`: Automatically install the built wheel file after building
- `--verbose`: Show detailed build output

#### What the Script Does

1. **Validates** the package structure (checks for pyproject.toml)
2. **Cleans** old build artifacts if `--clean` is specified
3. **Builds** both wheel (.whl) and source (.tar.gz) distributions
4. **Lists** the generated artifacts with file sizes
5. **Installs** the package if `--install` is specified

#### Output Example

```
============================================================
  Lab Scripts Package Builder
============================================================

📁 Package: dmm6500_buffer_download
   Path: C:\...\lab_scripts\dmm6500_buffer_download

🧹 Cleaning build artifacts in dmm6500_buffer_download...
  Cleaned 3 artifact(s)

🔨 Building package: dmm6500_buffer_download
  Running: python -m build C:\...\dmm6500_buffer_download
  ✓ Build completed successfully

📦 Build artifacts:
  dmm6500-buffer-download-1.0.0-py3-none-any.whl (0.01 MB)
  dmm6500-buffer-download-1.0.0.tar.gz (0.01 MB)

============================================================
  ✓ Build process completed successfully!
============================================================
```

### Manual Build Method

For manual builds without the script:

```bash
cd lab_scripts/my_lab_script
py -m build --wheel --sdist
```

## Package Size Guidelines

Aim for small packages suitable for database storage:

- **Wheel files**: < 20 KB (without heavy dependencies)
- **Source distributions**: < 15 KB
- Use only necessary dependencies

## Best Practices

### 1. **Standalone Drivers**
- Copy device drivers into your package's `drivers/` folder
- Don't import from parent lab_data_logging project
- Example: `dmm6500_buffer_download/dmm6500_buffer_download/drivers/dmm6500.py`

### 2. **Consistent Styling**
- Use colorama for colored console output
- Follow the patterns in existing packages
- Include progress bars for long operations

### 3. **Documentation**
- README.md: Feature overview, hardware requirements, examples
- INSTALL_GUIDE.md: Installation, usage, troubleshooting, database storage
- Docstrings: Function and class documentation
- Comments: Complex logic explanation

### 4. **Error Handling**
- Graceful error messages with colorama
- Try-finally blocks for cleanup (disconnect devices)
- Meaningful exit codes (0 for success, 1 for error)

### 5. **CLI Design**
- `--help` with clear descriptions
- Optional parameters with sensible defaults
- Support multiple connection modes (auto-detect, explicit address)
- `--debug` flag for verbose logging

### 6. **Testing**
- Include docstring examples
- Test with `pip install .` before packaging
- Verify wheel installation works: `pip install <name>.whl`

## Distribution

Wheels are ideal for storing in test records databases:

```sql
CREATE TABLE lab_tool_packages (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    version VARCHAR(50),
    description TEXT,
    filename VARCHAR(255),
    file_data BLOB,
    file_size INTEGER,
    upload_date TIMESTAMP
);
```

## Updating a Package

### Using the Build Script (Recommended)

```bash
# Clean and rebuild the package
python build_package.py <package_name> --clean
```

### Manual Method

1. Make changes to source files in `<package_name>/`
2. Clean old builds: `rm -r build/ *.egg-info/ dist/*`
3. Rebuild: `py -m build`
4. Verify: `pip install dist/<package>.whl`

## Example Packages

- **lockout_hysteresis_test**: UV/OV threshold testing
  - Location: `lab_scripts/lockout_hysteresis_test/dist/`
  - Size: ~12 KB wheel
  - Dependencies: pyvisa, pyserial, colorama, plotly
  - Type: Python CLI

- **dmm6500_buffer_download**: DMM6500 buffer download tool
  - Location: `lab_scripts/dmm6500_buffer_download/dist/`
  - Size: ~11 KB wheel
  - Dependencies: pyvisa, colorama (optional: matplotlib)
  - Type: Python CLI

- **csv_bin_gz_converter**: CSV to binary converter (Electron desktop app)
  - Location: `lab_scripts/csv_bin_gz_converter/dist/`
  - Size: ~8 KB wheel (Python launcher)
  - Dependencies: pyyaml, colorama
  - Type: Python CLI + Electron app launcher
  - CLI Command: `csv-bin-gz-converter`

## Troubleshooting

**Build fails with "no pyproject.toml"**
- Ensure you're in the correct directory (lab_scripts/my_lab_script/)
- Check file exists: `ls pyproject.toml`

**Import errors in CLI**
- Verify `__init__.py` exists and imports are correct
- Test import: `python -c "import my_lab_script"`

**Package won't install**
- Check Python version: `python --version` (need 3.8+)
- Verify dependencies installable: `pip list`

**csv-bin-gz-converter app won't launch**
- **Required**: Node.js 14+ must be installed for Electron apps
- Install Node.js from https://nodejs.org/
- Verify: `node --version && npm --version`
- The launcher will provide setup instructions if Node.js is missing

**Need to rebuild**
- Always clean first: `rm build/ *.egg-info/ dist/*`
- Check for .pyc files in source directory

## References

- [Python Packaging Guide](https://packaging.python.org/)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [PEP 517 - Build System Interface](https://www.python.org/dev/peps/pep-0517/)
