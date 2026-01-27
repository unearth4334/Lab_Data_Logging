# Stanford PS310 Desktop Application

A native desktop application for controlling the Stanford Research Systems PS310 High Voltage Power Supply. This application embeds the web-based GUI in a Chromium-based window for a more integrated experience.

## Features

### 🖥️ Native Desktop Experience
- **Standalone Application**: No need to manually start the server and open a browser
- **Chromium-Based**: Uses modern web technologies with a native window wrapper
- **Auto-Shutdown**: Server automatically stops when you close the window
- **Single Launch**: Just run one script to start everything

### 🔒 Improved Security
- Server binds to localhost by default (not accessible from network)
- No browser tabs left running in the background
- Clean shutdown process ensures all resources are properly released

### 💻 Cross-Platform Support
- **Windows**: Uses Edge WebView2 (built into Windows 11, installable on Windows 10)
- **macOS**: Uses native WebKit framework (works out of the box)
- **Linux**: Uses WebKit2GTK (requires installation - see below)

## Installation

### Prerequisites

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Platform-Specific Requirements**:

   **Linux (Ubuntu/Debian)**:
   ```bash
   sudo apt update
   sudo apt install python3-gi python3-gi-cairo gir1.2-webkit2-4.0
   ```

   **macOS**:
   No additional installation needed - uses native WebKit.

   **Windows**:
   - Windows 11: WebView2 is pre-installed
   - Windows 10: Download and install [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)

## Usage

### Starting the Application

Simply run the desktop launcher script:

```bash
python stanfordps310_gui_desktop.py
```

Or if made executable:

```bash
./stanfordps310_gui_desktop.py
```

### What Happens

1. **Server Starts**: The FastAPI server starts automatically in the background on `localhost:8082`
2. **Window Opens**: A desktop window opens showing the PS310 control interface
3. **Use Normally**: Control your PS310 just like the web version
4. **Close to Exit**: Close the window to shut down both the GUI and server

### Application Window

The application opens a resizable window (default 1400x900 pixels) with:
- Full web GUI interface
- Native window controls (minimize, maximize, close)
- Minimum size constraint (800x600) to ensure usability
- Clean integration with your desktop environment

## Configuration

You can customize the server settings using environment variables:

```bash
# Change the server port (default: 8082)
export PS310_GUI_PORT=8083
python stanfordps310_gui_desktop.py

# Change the server host (advanced - usually not needed)
export PS310_GUI_HOST=127.0.0.1
python stanfordps310_gui_desktop.py
```

## Comparison: Desktop App vs Web Server

### Desktop Application (`stanfordps310_gui_desktop.py`)
**Advantages**:
- ✅ Single command to launch everything
- ✅ Automatic server startup and shutdown
- ✅ Native window appearance
- ✅ No browser tabs to manage
- ✅ Better security (server not exposed)

**Disadvantages**:
- ❌ Requires platform-specific webview dependencies
- ❌ Cannot access remotely (by design)
- ❌ Single window only

### Web Server (`stanfordps310_gui.py`)
**Advantages**:
- ✅ Works in any browser
- ✅ Can be accessed remotely (with SSH tunneling)
- ✅ Multiple users can connect (not recommended for safety)
- ✅ Fewer platform-specific dependencies

**Disadvantages**:
- ❌ Must manually start server and open browser
- ❌ Server keeps running if browser is closed
- ❌ Need to remember the URL and port

## Troubleshooting

### "pywebview is not installed"
```bash
pip install pywebview
```

### Linux: "No module named 'gi'"
Install the GObject introspection bindings:
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-webkit2-4.0
```

For other Linux distributions, install equivalent packages:
- **Fedora/RHEL**: `sudo dnf install python3-gobject gtk3 webkit2gtk3`
- **Arch**: `sudo pacman -S python-gobject gtk3 webkit2gtk`

### Windows: "WebView2 Runtime not found"
Download and install the [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).

### macOS: Application window doesn't open
Ensure you're using Python 3.7+ and that you have the latest version of macOS. The native WebKit should work out of the box.

### Server fails to start
1. Check if port 8082 is already in use:
   ```bash
   # Linux/macOS
   lsof -i :8082
   
   # Windows
   netstat -ano | findstr :8082
   ```

2. Change the port using environment variable:
   ```bash
   export PS310_GUI_PORT=8083
   python stanfordps310_gui_desktop.py
   ```

### Window opens but shows error
1. Check the log file `stanfordps310_desktop.log` for details
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Ensure the StanfordPS310 driver is available in `libs/`

## Logging

The application creates two log files:
- `stanfordps310_desktop.log` - Desktop application events (window, server)
- `stanfordps310_gui.log` - Web server and PS310 communication events

Both files are useful for troubleshooting issues.

## Safety

⚠️ **HIGH VOLTAGE DEVICE - EXTREME CAUTION REQUIRED**

The desktop application provides the same safety features as the web version:
- Voltage range limits enforced
- Current limiting
- Emergency stop capability
- Output disable before disconnect

**Always follow proper high voltage safety procedures!**

## Technical Details

### Architecture

```
┌─────────────────────────────────────┐
│   Desktop Window (pywebview)        │
│   ┌─────────────────────────────┐   │
│   │                             │   │
│   │   Web UI (HTML/CSS/JS)      │   │
│   │                             │   │
│   └─────────────────────────────┘   │
│              │                       │
│              │ HTTP (localhost)      │
│              ▼                       │
│   ┌─────────────────────────────┐   │
│   │  FastAPI Server (thread)    │   │
│   │  ┌────────────────────────┐ │   │
│   │  │ stanfordps310_gui.py   │ │   │
│   │  └────────────────────────┘ │   │
│   └─────────────────────────────┘   │
│              │                       │
│              │ PyVISA/GPIB           │
│              ▼                       │
│   ┌─────────────────────────────┐   │
│   │  Stanford PS310 Device      │   │
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Components

1. **pywebview**: Provides the desktop window wrapper
   - Windows: Uses Edge WebView2 (Chromium-based)
   - macOS: Uses WebKit
   - Linux: Uses WebKit2GTK

2. **FastAPI Server**: Runs in a background daemon thread
   - Handles all PS310 communication
   - Provides REST API endpoints
   - Manages command queue and background tasks

3. **Shutdown Process**: When window closes:
   - Window close event is captured
   - Server receives shutdown signal
   - FastAPI cleanup handlers run
   - Background tasks are cancelled
   - PS310 connection is safely closed

## Development

When extending the desktop application:

1. **Server Changes**: Modify `stanfordps310_gui.py` (automatically used by desktop app)
2. **Desktop Features**: Modify `stanfordps310_gui_desktop.py`
3. **Testing**: Test both web and desktop versions to ensure compatibility

### Adding New Features

The desktop application automatically inherits all features from the web version. To add desktop-specific features:

```python
# In stanfordps310_gui_desktop.py

# Example: Add window title updates based on connection status
def update_window_title(window, status):
    if status['connected']:
        window.set_title(f"PS310 Control - Connected: {status['address']}")
    else:
        window.set_title("PS310 Control - Disconnected")
```

## Related Files

- `stanfordps310_gui.py` - FastAPI web server and GUI (used by this app)
- `stanfordps310_gui_example.py` - API usage examples
- `libs/StanfordPS310.py` - PS310 device driver
- `STANFORDPS310_GUI_README.md` - Web version documentation

## License

This software is licensed under the Apache License 2.0, consistent with the Lab_Data_Logging project.

---

**Last Updated**: January 2026  
**Version**: 1.0.0  
**Author**: Lab_Data_Logging Project Contributors
