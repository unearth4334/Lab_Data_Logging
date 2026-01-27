#!/bin/bash
# Stanford PS310 Desktop Application Launcher for Linux/macOS
# This script launches the desktop application with the Chromium-based webview

echo "======================================================================"
echo "Stanford PS310 High Voltage Power Supply - Desktop Application"
echo "======================================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.7+ and try again"
    exit 1
fi

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "WARNING: Not running in a virtual environment"
    echo "It's recommended to use a virtual environment"
    echo ""
    echo "To create and activate a virtual environment:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Starting Stanford PS310 Desktop Application..."
echo ""
echo "Close the application window to exit."
echo ""

# Launch the desktop application
cd "$(dirname "$0")/.." && python3 apps/PS310/stanfordps310_gui_desktop.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Application failed to start"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Install dependencies: pip install -r requirements.txt"
    echo "  2. Check that pywebview is installed: pip install pywebview"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  3. On Linux, install GTK components:"
        echo "     Ubuntu/Debian: sudo apt install python3-gi python3-gi-cairo gir1.2-webkit2-4.0"
        echo "     Fedora: sudo dnf install python3-gobject gtk3 webkit2gtk3"
        echo "     Arch: sudo pacman -S python-gobject gtk3 webkit2gtk"
    fi
    
    echo ""
    exit 1
fi

echo ""
echo "Application closed successfully"
