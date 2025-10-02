# Lab Data Logging CLI API - Backdoor Testing Interface

This CLI API provides command-line access to all the functionality available in the web GUI, designed specifically for testing and automation purposes.

## Overview

The `lab_cli.py` script serves as a backdoor interface that bypasses the web UI and allows direct interaction with the measurement system. This is particularly useful for:

- Automated testing and continuous integration
- Batch processing multiple configurations
- Scripting and workflow automation
- Quick testing without web browser dependency
- Remote execution and headless operation

## Installation

No additional installation is required beyond the main project dependencies. The CLI uses the same virtual environment and dependencies as the web GUI.

## Quick Start

```bash
# Show all available commands
python lab_cli.py --help

# Run a basic test with default settings
python lab_cli.py run-test

# Run a test with specific configuration
python lab_cli.py run-test --config example_config.yml

# List all available test results
python lab_cli.py list-results

# Generate HTML report from existing data
python lab_cli.py generate-report ./captures/00001_Test_20251002.143000
```

## Commands

### `run-test` - Execute Measurement Capture

Runs a complete measurement capture session with the specified configuration.

#### Basic Usage
```bash
python lab_cli.py run-test [OPTIONS]
```

#### Options
- `--config FILE` - Load configuration from YAML file
- `--visa-address ADDRESS` - VISA address of oscilloscope
- `--destination DIR` - Base destination directory for results
- `--board-number NUMBER` - Board number for naming (default: from config)
- `--label LABEL` - Test label for naming (default: from config)
- `--channels CH1 CH2 ...` - Channels to capture (space-separated)
- `--capture-types TYPE1 TYPE2 ...` - Types of data to capture
- `--no-timestamp` - Disable automatic timestamping
- `--timestamp-format FORMAT` - Timestamp format (YYYYMMDD.HHMMSS or YYYYMMDD_HHMMSS)
- `--save-config FILE` - Save final configuration to file

#### Examples
```bash
# Run with default configuration
python lab_cli.py run-test

# Run with specific channels and capture types
python lab_cli.py run-test --channels CH1 CH2 M1 --capture-types measurements waveforms screenshot html_report

# Run from configuration file with overrides
python lab_cli.py run-test --config my_config.yml --board-number TEST123

# Run and save the final configuration
python lab_cli.py run-test --save-config last_run_config.yml
```

### `list-results` - List Available Test Results

Lists all available test results in the specified directory.

#### Usage
```bash
python lab_cli.py list-results [--results-dir DIR]
```

#### Options
- `--results-dir DIR` - Directory to search for results (default: captures)

### `generate-report` - Generate HTML Report

Generates an HTML report from existing test data.

#### Usage
```bash
python lab_cli.py generate-report INPUT_DIR [--output OUTPUT_FILE]
```

#### Arguments
- `INPUT_DIR` - Directory containing test data
- `--output OUTPUT_FILE` - Output HTML file path (optional)

#### Examples
```bash
# Generate report with automatic naming
python lab_cli.py generate-report ./captures/00001_Test_20251002.143000

# Generate report with specific output file
python lab_cli.py generate-report ./captures/00001_Test_20251002.143000 --output custom_report.html
```

### `validate-config` - Validate Configuration File

Validates a configuration file and reports any issues.

#### Usage
```bash
python lab_cli.py validate-config CONFIG_FILE
```

#### Examples
```bash
python lab_cli.py validate-config example_config.yml
python lab_cli.py validate-config my_test_setup.yml
```

## Configuration Files

Configuration files use YAML format and support all the same options as the web GUI.

### Example Configuration

```yaml
# Oscilloscope connection
visa_address: "USB0::0x0957::0x17BC::MY56310625::INSTR"

# Output configuration
destination: "./captures"
board_number: "00001"
label: "CLI_Test"

# Channels to capture
channels:
  CH1: true
  CH2: false
  CH3: false
  CH4: false
  M1: true

# Types of data to capture
capture_types:
  measurements: true
  waveforms: true
  screenshot: true
  config: true
  html_report: true

# Timestamping
auto_timestamp: true
timestamp_format: "YYYYMMDD.HHMMSS"
```

### Provided Configuration Files

- `example_config.yml` - Full example with all options documented
- `quick_test_config.yml` - Minimal configuration for fast testing
- `comprehensive_test_config.yml` - Captures everything for thorough testing

## Batch Processing Examples

### Test Multiple Configurations
```bash
#!/bin/bash
for config in configs/*.yml; do
    echo "Running test with config: $config"
    python lab_cli.py run-test --config "$config"
done
```

### Generate Reports for All Results
```bash
#!/bin/bash
for result_dir in captures/*/; do
    if [ -d "$result_dir" ]; then
        echo "Generating report for: $result_dir"
        python lab_cli.py generate-report "$result_dir"
    fi
done
```

### Automated Testing Pipeline
```bash
#!/bin/bash
# Validate configuration
python lab_cli.py validate-config test_config.yml || exit 1

# Run the test
python lab_cli.py run-test --config test_config.yml || exit 1

# List results to verify
python lab_cli.py list-results

echo "Automated test completed successfully"
```

## Integration with CI/CD

The CLI returns appropriate exit codes for integration with continuous integration systems:

- `0` - Success
- `1` - Error or failure

Example GitHub Actions workflow:
```yaml
- name: Run Lab Data Logging Test
  run: |
    python lab_cli.py validate-config ci_test_config.yml
    python lab_cli.py run-test --config ci_test_config.yml
    
- name: Archive Test Results
  uses: actions/upload-artifact@v2
  with:
    name: test-results
    path: captures/
```

## Advanced Usage

### Environment Variables

The CLI respects the same environment variables as the main application:

- Virtual environment detection is automatic
- VISA libraries are detected from the system

### Logging

The CLI provides detailed logging output to help with debugging:

```bash
# Run with verbose output (logging is enabled by default)
python lab_cli.py run-test --config debug_config.yml
```

### Error Handling

The CLI provides comprehensive error handling and reporting:

- Configuration validation before execution
- Detailed error messages with suggestions
- Proper exit codes for scripting
- Exception tracebacks for debugging

## Example Scripts

Use the provided example scripts to get started:

- `cli_examples.sh` - Interactive examples for Linux/macOS
- `cli_examples.bat` - Interactive examples for Windows

```bash
# Run interactive examples (Linux/macOS)
chmod +x cli_examples.sh
./cli_examples.sh

# Run interactive examples (Windows)
cli_examples.bat
```

## Troubleshooting

### Common Issues

1. **VISA Address Not Found**
   - Check that the oscilloscope is connected and powered on
   - Verify the VISA address using Keysight Connection Expert
   - Try using auto-detection by omitting the `--visa-address` parameter

2. **Permission Errors**
   - Ensure the destination directory is writable
   - Check that the virtual environment is properly activated

3. **Import Errors**
   - Verify that all dependencies are installed in the virtual environment
   - Check that the current working directory is correct

4. **Configuration Validation Errors**
   - Use `validate-config` command to check configuration files
   - Refer to the example configurations for proper format

### Debug Mode

For detailed debugging information, you can modify the logging level in the script or redirect output:

```bash
# Capture all output for debugging
python lab_cli.py run-test --config test.yml > debug.log 2>&1
```

## API Reference

The CLI provides the same functionality as the web GUI but through a command-line interface. Key functions include:

- `load_defaults()` - Load default configuration
- `run_measurement_capture()` - Execute measurement capture
- `list_results()` - List available results
- `validate_config()` - Validate configuration
- `build_output_dir()` - Generate output directory paths

All functions return appropriate status codes and detailed error information for integration into larger systems.

## Security Considerations

This CLI API is designed as a "backdoor" for testing purposes. In production environments:

- Restrict access to the CLI script
- Validate all input parameters
- Use secure configuration file storage
- Monitor CLI usage and access logs
- Consider network security when used remotely

## Support

For issues specific to the CLI API, check:

1. The configuration file format and validation
2. VISA address connectivity
3. Virtual environment activation
4. File permissions and directory access
5. Dependencies and imports

The CLI API uses the same underlying libraries as the web GUI, so most troubleshooting steps are identical.