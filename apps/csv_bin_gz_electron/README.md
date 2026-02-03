# CSV to BIN.GZ Electron App

This app wraps the CSV conversion helpers and provides a simple left-to-right flow UI for:
- Current CSV → current_capture.bin.gz + JSON
- Power rails CSV → power_rails.bin.gz + JSON
- Optional power rails column reorder (uses reorder_csv_columns.py)

## Setup

From this folder:

1. Install dependencies
   - npm install

2. Start the app
   - npm start

## Notes
- The app invokes the Python scripts in the repository scripts folder.
- You can optionally set a Python executable path in the UI.
- Reorder output is written to the output folder with a .reordered.csv suffix.
