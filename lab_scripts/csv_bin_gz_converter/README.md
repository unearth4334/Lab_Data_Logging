# CSV to BIN.GZ Converter

A desktop application for converting CSV measurement files to binary `.bin.gz` format with JSON metadata support.

## Features

- **CSV to Binary Conversion**: Convert measurement CSV files to compressed binary format
- **Metadata Support**: Automatic JSON metadata generation
- **Column Mapping**: Reorder and map columns via YAML templates
- **Power Rails Support**: Specialized handling for power supply measurement data
- **User-Friendly UI**: Desktop application with drag-and-drop support
- **No Installation Required**: Portable Electron app

## Installation

### Option 1: Install from Wheel Package

```bash
pip install csv_bin_gz_converter-1.0.0-py3-none-any.whl
csv-bin-gz-converter
```

### Option 2: Install from Source

```bash
pip install .
csv-bin-gz-converter
```

### Option 3: Clone and Run Directly

```bash
cd ../../apps/csv_bin_gz_electron
npm install
npm start
```

## Usage

### Launching the Application

#### Via Python CLI
```bash
csv-bin-gz-converter
```

#### Via Direct Launch
```bash
cd apps/csv_bin_gz_electron
npm start
```

### Using the Application UI

1. **Start the app** using any of the methods above
2. **Select CSV files** - Click "Select Files" or drag files into the interface
3. **Choose conversion type** - Select from available converters:
   - Current Measurement CSV
   - Power Rails CSV (with column reordering)
4. **Configure columns** (optional) - Use YAML templates to map column names
5. **Convert** - Click "Convert" to generate `.bin.gz` files with metadata

## Application Structure

```
apps/csv_bin_gz_electron/
├── app/handlers/
│   └── csv-handlers.js          # CSV processing logic
├── app/renderer/
│   ├── index.html               # UI layout
│   ├── renderer.js              # UI interactivity
│   └── styles.css               # Styling
├── column_templates/            # YAML column mapping templates
├── config.yml                   # Application configuration
├── main.js                      # Electron main process
└── package.json                 # Node.js dependencies
```

## Configuration

Edit `apps/csv_bin_gz_electron/config.yml` to customize:
- Default column templates
- Output directory preferences
- Data format options
- Supported CSV types

## Column Templates

Place YAML files in `column_templates/` to define custom column mappings:

```yaml
# Example: power_rails_template.yml
columns:
  - name: "Time (s)"
    mapping: "timestamps"
  - name: "Voltage (V)"
    mapping: "voltage_measurements"
  - name: "Current (A)"
    mapping: "current_measurements"
```

## Output Format

The converter produces:
- **Binary File** (`.bin.gz`): Compressed binary data
- **Metadata** (`_metadata.json`): Column names, types, units, timestamps

## Troubleshooting

### Application Won't Launch
- Ensure Node.js is installed: `node --version`
- Install dependencies: `npm install` in the app directory
- Check for port conflicts (default: 3000)

### Cannot Find Files
- Verify CSV files exist and are readable
- Check file permissions
- Ensure file format is valid CSV (comma-separated values)

### Conversion Error
- Validate CSV column headers
- Check column template YAML syntax
- Review application logs for detailed errors

## Dependencies

### Python
- `pyyaml` - Configuration file parsing
- `colorama` - Colored terminal output

### Node.js / Electron
- `electron` - Desktop application framework
- `csv-parse` - CSV parsing library

## Development

To contribute or modify the application:

1. Navigate to `apps/csv_bin_gz_electron`
2. Install dependencies: `npm install`
3. Modify source files
4. Launch with: `npm start`

## License

Apache License 2.0

## Support

For issues or feature requests, refer to the main Lab Data Logging project documentation.
