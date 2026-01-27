# Repository Reorganization Summary

## Date
January 27, 2026

## Overview
The Lab_Data_Logging repository has been reorganized to improve maintainability and clarity by establishing a clean directory structure that separates core infrastructure, utility scripts, GUI applications, configuration files, documentation, and deprecated/test code.

## New Directory Structure

```
Lab_Data_Logging/
├── data_logger.py          # Core data logging orchestrator
├── libs/                   # Device driver libraries
│   ├── DMM6500.py         # Keithley DMM6500 driver
│   ├── KeysightMSOX4154A.py  # Oscilloscope driver
│   ├── StanfordPS310.py   # High voltage power supply driver
│   └── ...                # Other instrument drivers
├── gui/                    # GUI applications
│   ├── measurement_gui.py
│   ├── stanfordps310_gui.py
│   ├── stanfordps310_gui_desktop.py
│   ├── stanfordps310_gui_example.py
│   └── quickstart_ps310_desktop.py
├── scripts/                # Utility scripts
│   ├── verify_installation.py
│   ├── lab_cli.py
│   ├── generate_report.py
│   ├── generate_static_report.py
│   ├── make_avdd_report.py
│   ├── plot_hvmon.py
│   ├── cli_examples.sh
│   ├── cli_examples.bat
│   ├── launch_ps310_desktop.sh
│   └── launch_ps310_desktop.bat
├── config/                 # Configuration files
│   ├── defaults.yml
│   ├── defaults.yml.example
│   ├── example_config.yml
│   ├── demo_config.yml
│   ├── quick_test_config.yml
│   └── comprehensive_test_config.yml
├── docs/                   # Documentation
│   ├── CEF_IMPLEMENTATION_SUMMARY.md
│   ├── CLI_IMPLEMENTATION_SUMMARY.md
│   ├── CLI_README.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── STANFORDPS310_DESKTOP_README.md
│   ├── STANFORDPS310_GUI_README.md
│   ├── PS310_DEBUG_LOGGING.md
│   ├── STANFORDPS310_FIX_SUMMARY.md
│   ├── STANFORDPS310_DESKTOP_SCREENSHOTS.md
│   ├── BEFORE_AFTER_COMPARISON.md
│   └── REPOSITORY_REORGANIZATION.md (this file)
├── utilities/              # MATLAB utilities
│   ├── loadData.m
│   └── plotData.m
├── .trash/                 # Deprecated and test files
│   ├── test_ps310_*.py (6 files)
│   ├── test_glitch_filter.py
│   ├── test_measurement_results.py
│   ├── custom_label_test_report.html
│   ├── measurement_report.html
│   └── .temp/
├── requirements.txt        # Python dependencies
├── README.md              # Main project documentation
├── LICENSE
└── .gitignore
```

## Changes Made

### Files Moved to `scripts/`
Utility scripts that assist with installation verification, CLI operations, report generation, and launching applications:
- `verify_installation.py`
- `lab_cli.py`
- `plot_hvmon.py`
- `generate_report.py`
- `generate_static_report.py`
- `make_avdd_report.py`
- `cli_examples.sh`
- `cli_examples.bat`
- `launch_ps310_desktop.sh`
- `launch_ps310_desktop.bat`

### Files Moved to `gui/`
GUI applications for measurements and instrument control:
- `measurement_gui.py` - Main measurement GUI application
- `stanfordps310_gui.py` - Web-based PS310 control interface
- `stanfordps310_gui_desktop.py` - Desktop PS310 control application
- `stanfordps310_gui_example.py` - Example usage of PS310 GUI API
- `quickstart_ps310_desktop.py` - Quick start guide for PS310 desktop app

### Files Moved to `config/`
Configuration files for various test and measurement scenarios:
- `defaults.yml`
- `defaults.yml.example`
- `example_config.yml`
- `demo_config.yml`
- `quick_test_config.yml`
- `comprehensive_test_config.yml`

### Files Moved to `docs/`
Documentation files describing implementations, fixes, and features:
- All `*_SUMMARY.md` files
- All `*_README.md` files (except main README.md)
- Screenshot documentation
- Debug/fix documentation

### Files Moved to `.trash/`
Test files and temporary code that are no longer actively used:
- All `test_*.py` files (8 files)
- HTML test reports
- `.temp/` folder

### Path Updates
Updated references in the following files to reflect new structure:
- `scripts/launch_ps310_desktop.sh` - Updated to reference `gui/stanfordps310_gui_desktop.py`
- `scripts/launch_ps310_desktop.bat` - Updated to reference `gui\stanfordps310_gui_desktop.py`
- `scripts/cli_examples.sh` - Updated to reference `scripts/` and `config/` folders
- `scripts/cli_examples.bat` - Updated to reference `scripts\` and `config\` folders
- `scripts/lab_cli.py` - Updated to load defaults from `config/defaults.yml`
- `gui/measurement_gui.py` - Updated to load defaults from `config/defaults.yml`
- `README.md` - Updated with new repository structure and path references

## Running Applications After Reorganization

### GUI Applications
From the project root directory:
```bash
# Measurement GUI
python gui/measurement_gui.py

# Stanford PS310 Desktop Application
python gui/stanfordps310_gui_desktop.py

# Or use the launcher scripts
./scripts/launch_ps310_desktop.sh      # Linux/macOS
scripts\launch_ps310_desktop.bat       # Windows
```

### CLI Scripts
From the project root directory:
```bash
# Verify installation
python scripts/verify_installation.py

# Run CLI commands
python scripts/lab_cli.py run-test --config config/example_config.yml
python scripts/lab_cli.py list-results
python scripts/lab_cli.py generate-report ./captures/results_dir/

# View CLI examples
./scripts/cli_examples.sh              # Linux/macOS
scripts\cli_examples.bat               # Windows
```

### Using Configuration Files
Configuration files are now in the `config/` folder:
```bash
python scripts/lab_cli.py run-test --config config/quick_test_config.yml
```

## Benefits of This Organization

1. **Clearer Purpose**: Each directory has a specific, well-defined purpose
2. **Easier Navigation**: Files are grouped by function rather than all in the root
3. **Core vs. Utilities**: Clear separation between core infrastructure and helper scripts
4. **Test Code Isolated**: Old test code is moved to `.trash/` to avoid confusion
5. **Better Documentation**: All documentation is centralized in the `docs/` folder
6. **Configuration Management**: All YAML config files are in one place
7. **Maintainability**: Future developers can quickly understand the structure

## Core vs. Non-Core

**Core Infrastructure** (remains in root and `libs/`):
- `data_logger.py` - Main orchestrator
- `libs/` - Device drivers
- `utilities/` - MATLAB utilities

**Everything Else** (organized into subdirectories):
- GUI applications → `gui/`
- Utility scripts → `scripts/`
- Configuration → `config/`
- Documentation → `docs/`
- Deprecated code → `.trash/`

## Notes for Developers

- When creating new scripts, place them in `scripts/`
- When creating new GUI applications, place them in `gui/`
- Configuration files should go in `config/`
- Documentation should go in `docs/`
- The `libs/` folder is for instrument drivers only
- Test files should be placed in a proper test directory or removed when no longer needed
