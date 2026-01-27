# PS310 Debug Logging Feature

## Overview

Added debug logging for all PS310 VISA interactions to aid in troubleshooting connection and communication issues.

## Usage

### Desktop Application

Enable debug logging by using the `--debug` flag when launching the desktop app:

```bash
python stanfordps310_gui_desktop.py --debug
```

### Output

When debug mode is enabled:
- All VISA commands sent to the PS310 are logged
- All responses received from the PS310 are logged
- Any errors during communication are logged
- Logs include timestamp, operation description, command, and response

### Example Log Output

```
2026-01-13 15:30:45,123 - libs.StanfordPS310 - DEBUG - PS310 Interaction - Opening VISA resource | Command: open_resource(GPIB0::14::INSTR)
2026-01-13 15:30:45,234 - libs.StanfordPS310 - DEBUG - PS310 Interaction - Querying device identification | Command: *IDN?
2026-01-13 15:30:45,345 - libs.StanfordPS310 - DEBUG - PS310 Interaction - Received identification | Response: StanfordResearchSystems,PS310,2067,1.40
2026-01-13 15:30:45,456 - libs.StanfordPS310 - DEBUG - PS310 Interaction - Setting voltage | Command: VSET -100.000
2026-01-13 15:30:45,567 - libs.StanfordPS310 - DEBUG - PS310 Interaction - Voltage set successfully | Response: -100.000 V
2026-01-13 15:30:45,678 - libs.StanfordPS310 - DEBUG - PS310 Interaction - Enabling HV output | Command: HVON
2026-01-13 15:30:45,789 - libs.StanfordPS310 - DEBUG - PS310 Interaction - HV output enabled | Response: ON
2026-01-13 15:30:45,890 - libs.StanfordPS310 - DEBUG - PS310 Interaction - Measuring output voltage | Command: VOUT?
2026-01-13 15:30:46,001 - libs.StanfordPS310 - DEBUG - PS310 Interaction - Measured voltage | Response: -99.8 V
2026-01-13 15:30:46,112 - libs.StanfordPS310 - DEBUG - PS310 Interaction - Querying output state | Command: HVON?
2026-01-13 15:30:47,223 - libs.StanfordPS310 - DEBUG - PS310 Interaction - HVON? query timeout - using cached state | Response: ON (cached)
```

## Implementation Details

### Environment Variable

The debug mode is controlled by the `PS310_DEBUG` environment variable:
- Set to `'1'` to enable debug logging
- Any other value (or unset) disables debug logging

### Logged Operations

The following operations are logged when debug mode is enabled:

1. **Connection Operations**
   - Opening VISA resources
   - Querying device identification (*IDN?)
   - Clearing status registers (*CLS)
   - Connection establishment

2. **Voltage Operations**
   - Setting voltage (VSET)
   - Querying voltage setpoint (VSET?)
   - Measuring output voltage (VOUT?)

3. **Current Operations**
   - Setting current limit (ILIM)
   - Querying current limit (ILIM?)
   - Measuring output current (IOUT?)

4. **Output Control**
   - Enabling output (HVON)
   - Disabling output (HVOF)
   - Querying output state (HVON?) including timeout fallback

5. **Error Conditions**
   - VISA communication errors
   - Timeout errors
   - Command failures

### Log Format

Each log entry includes:
- **Timestamp**: Date and time of the operation
- **Logger name**: `libs.StanfordPS310`
- **Level**: `DEBUG`
- **Operation**: Description of what's being done
- **Command**: VISA command sent (if applicable)
- **Response**: Response received (if applicable)
- **Error**: Error message (if applicable)

## Benefits

- **Troubleshooting**: Easily identify communication issues
- **Protocol Analysis**: Understand the command sequence
- **Performance Monitoring**: See timing of operations
- **Error Diagnosis**: Detailed error information for failed operations
- **Development**: Helpful when implementing new features or fixing bugs

## Performance Impact

When debug mode is **disabled** (default):
- Zero performance impact - all logging checks return immediately
- No log messages generated

When debug mode is **enabled**:
- Minimal performance impact
- Only debug-level log messages generated
- Log messages written to file and console as configured

## Configuration

### Log Files

Desktop application logs are written to:
- `stanfordps310_desktop.log` - General application logs
- Console output - Real-time feedback

### Changing Log Level

To see debug logs, ensure logging is configured at DEBUG level:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see PS310 interactions
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Use Cases

1. **Connection Debugging**: Identify why device won't connect
2. **Timeout Investigation**: See exactly which command times out
3. **Protocol Verification**: Confirm correct SCPI commands are sent
4. **Firmware Compatibility**: Understand device behavior differences
5. **Performance Tuning**: Identify slow operations

## Notes

- Debug logging is automatically enabled when using `--debug` flag
- Logs include sensitive data (voltage/current values) - handle appropriately
- No credentials or secrets are logged
- HVON? timeout fallback is always logged to aid troubleshooting
