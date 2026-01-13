# Stanford PS310 Desktop Application - Screenshot Documentation

## Application Overview

The Stanford PS310 Desktop Application provides a native window experience for controlling the high voltage power supply.

### Main Window Features

**Window Title**: "Stanford PS310 High Voltage Power Supply Control"
**Default Size**: 1400x900 pixels (resizable, minimum 800x600)

### Interface Layout

The application displays the full web-based GUI in a native window with:

1. **Header Section**
   - Purple gradient background with title "⚡ Stanford PS310 High Voltage Power Supply"
   - Professional and modern appearance

2. **Left Panel - Connection & Control**
   - Device connection controls with VISA address selection
   - Manual voltage and current limit settings
   - Output enable/disable buttons
   - Status indicators (green when connected, red when disconnected)

3. **Right Panel - Monitoring & Ramping**
   - Large display showing actual voltage in real-time
   - Smaller displays for set voltage and current
   - Voltage ramping controls with visual preview
   - Progress bar for ramp operations

### Window Controls

- **Native window decorations**: Standard minimize, maximize, and close buttons
- **Resizable**: User can adjust window size as needed
- **Minimum size enforced**: Prevents window from becoming too small to use
- **Clean shutdown**: Closing the window properly terminates the server

### Platform-Specific Appearance

**Windows**:
- Uses Microsoft Edge WebView2 (Chromium-based)
- Native Windows 11 window styling
- Smooth rendering and animations

**macOS**:
- Uses native WebKit engine
- Native macOS window styling with traffic lights
- Follows macOS design guidelines

**Linux**:
- Uses WebKit2GTK
- Native GTK+ window styling
- Follows desktop environment theme

### Example Use Case

1. **Launch Application**
   ```bash
   python stanfordps310_gui_desktop.py
   ```

2. **Window Opens Automatically**
   - No need to manually open a browser
   - No need to remember the URL
   - Server starts in background automatically

3. **Control Device**
   - All standard web GUI features available
   - Real-time updates and live monitoring
   - Voltage ramping with visual feedback

4. **Close Application**
   - Simply close the window
   - Server shuts down automatically
   - Clean resource cleanup

### Advantages Over Web Version

- ✅ **Single-command launch**: No separate server startup needed
- ✅ **Native integration**: Appears as a regular desktop application
- ✅ **Automatic cleanup**: Server stops when window closes
- ✅ **No browser clutter**: Dedicated window for device control
- ✅ **Taskbar presence**: Easy to find and switch to application

### Screenshot Notes

When running in a graphical environment, the application window displays:

- Full-color interface with purple/gradient theme
- Responsive layout that adapts to window size
- Real-time updating displays (voltage, current)
- Interactive controls and buttons
- Visual feedback for all operations
- Progress indicators for voltage ramping

The appearance is identical to the web version, but wrapped in a native desktop window for better integration with the operating system.

### Technical Details

**Backend**: FastAPI server running on localhost:8082
**Frontend**: Chromium-based webview (platform-dependent)
**Communication**: HTTP REST API between window and server
**Threading**: Server runs in background daemon thread
**Shutdown**: Graceful cleanup with proper resource management

---

For the actual GUI appearance, see the web version screenshots in STANFORDPS310_GUI_README.md. The desktop application displays the exact same interface, just in a native window instead of a browser tab.
