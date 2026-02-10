# CSV to BIN.GZ Converter (Electron App)

A desktop application for converting CSV files to binary .bin.gz format with JSON metadata, built using the Electron App Framework.

## Features

- Convert current measurement CSV files to .bin.gz format
- Convert power rails CSV files with optional column reordering
- Column name mapping and reordering via templates
- Portable - no admin rights or installation required
- Supports custom Python executable paths

## Project Structure

```
csv_bin_gz_electron/
├── electron-app-framework/      # Framework submodule (../../electron-app-framework)
├── app/                          # Application-specific code
│   ├── handlers/
│   │   └── csv-handlers.js      # CSV processing IPC handlers
│   ├── preload.js               # Custom preload (extends framework)
│   └── renderer/                # UI files
│       ├── index.html
│       ├── renderer.js
│       └── styles.css
├── column_templates/            # YAML templates for column mapping
├── config.yml                   # App configuration
├── main-new.js                  # Application entry point (uses framework)
├── package-new.json             # Dependencies
└── launch-new.sh                # Launcher script

Legacy files (to be removed after migration):
├── main.js (old)
├── preload.js (old)
├── renderer/ (old)
├── package.json (old)
└── launch.sh (old)
```

## Usage

### Running the App

```bash
# Make executable
chmod +x launch-new.sh

# Run
./launch-new.sh
```

The launcher will:
1. Auto-detect or use bundled Node.js
2. Install framework dependencies if needed
3. Install app dependencies if needed
4. Launch the Electron application

### Workflow

1. **Select Current CSV**: Choose your current measurement CSV file
2. **Select Power Rails CSV**: Choose your power rails CSV file
3. **(Optional) Reorder Columns**: Configure column ordering and renaming for power rails
4. **Select Output Folder**: Choose where to save the converted files
5. **Configure Settings**: Set sample rate and optionally specify Python executable
6. **Execute**: Run the conversion pipeline

### Column Templates

Column templates are stored in `column_templates/` as YAML files:

```yaml
# column_templates/example.yml
name: "Standard Layout"
columns:
  - "Timestamp"
  - "AVDD_I"
  - "DVDD_I"
  - "HVMON"
```

These serve as reference layouts when reordering columns.

## Configuration

Edit `config.yml` to set defaults:

```yaml
default_python_executable: "/path/to/python"
```

## Dependencies

### Framework Dependencies (auto-installed)
- electron: ^31.0.0

### App Dependencies (auto-installed)
- csv-parse: ^5.5.6
- js-yaml: ^4.1.0

### Python Scripts (must exist in project)
- `scripts/csv_to_bin_gz(current).py`
- `scripts/csv_to_bin_gz(power_rails).py` 
- `scripts/reorder_csv_columns.py`

## Development

### Adding Custom Features

1. **Add IPC Handler**: Edit `app/handlers/csv-handlers.js`
2. **Expose to Renderer**: Update `app/preload.js`
3. **Use in UI**: Call from `app/renderer/renderer.js`

### Framework Documentation

See `../../electron-app-framework/README.md` for framework documentation and `../../electron-app-framework/EXAMPLES.md` for usage examples.

## Migration from Old Structure

To switch to the framework-based version:

1. Test the new version: `./launch-new.sh`
2. Verify all functionality works
3. Backup old files
4. Replace:
   - `main.js` → `main-new.js`
   - `package.json` → `package-new.json`
   - `launch.sh` → `launch-new.sh`
   - `preload.js` → `app/preload.js`
   - `renderer/` → `app/renderer/`
5. Remove old files

## Troubleshooting

### "Node.js not found"
- Install Node.js system-wide, or
- Download portable Node.js and extract to `../../electron-app-framework/nodejs/`

### "Module not found"
```bash
# Reinstall dependencies
cd ../../electron-app-framework && npm install
cd apps/csv_bin_gz_electron && npm install
```

### Python script errors
- Check that scripts exist in `../../scripts/`
- Verify Python is installed or specify custom path in config.yml
- Check log output for detailed error messages

## License

Part of the Lab Data Logging project - UNLICENSED (proprietary)
