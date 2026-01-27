#!/usr/bin/env python3
"""
Quick Start Guide for Stanford PS310 Desktop Application

This script demonstrates the various ways to launch and use the desktop application.
"""

import os
import sys

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")

def main():
    print_header("Stanford PS310 Desktop Application - Quick Start Guide")
    
    print("This guide shows you how to launch the Stanford PS310 desktop application.\n")
    
    # Basic usage
    print_header("1. Basic Usage (Recommended)")
    print("Simply run the desktop launcher script:")
    print("\n  $ python stanfordps310_gui_desktop.py\n")
    print("This will:")
    print("  • Start the FastAPI server automatically")
    print("  • Open a native window with the PS310 control interface")
    print("  • Shut down the server when you close the window")
    
    # Custom port
    print_header("2. Using a Custom Port")
    print("If port 8082 is already in use, specify a different port:")
    print("\n  $ export PS310_GUI_PORT=8083")
    print("  $ python stanfordps310_gui_desktop.py\n")
    print("Or on Windows:")
    print("\n  > set PS310_GUI_PORT=8083")
    print("  > python stanfordps310_gui_desktop.py\n")
    
    # Executable (Unix)
    if os.name != 'nt':
        print_header("3. Making the Script Executable (Linux/macOS)")
        print("Make the script executable and run directly:")
        print("\n  $ chmod +x stanfordps310_gui_desktop.py")
        print("  $ ./stanfordps310_gui_desktop.py\n")
    
    # Troubleshooting
    print_header("Troubleshooting")
    print("If you encounter issues:\n")
    
    print("• Missing pywebview:")
    print("    $ pip install pywebview\n")
    
    print("• Missing dependencies:")
    print("    $ pip install -r requirements.txt\n")
    
    if os.name != 'nt':
        print("• Linux: Missing GTK components:")
        print("    Ubuntu/Debian:")
        print("      $ sudo apt install python3-gi python3-gi-cairo gir1.2-webkit2-4.0\n")
        print("    Fedora:")
        print("      $ sudo dnf install python3-gobject gtk3 webkit2gtk3\n")
        print("    Arch:")
        print("      $ sudo pacman -S python-gobject gtk3 webkit2gtk\n")
    else:
        print("• Windows: Missing WebView2:")
        print("    Download and install Microsoft Edge WebView2 Runtime")
        print("    from https://developer.microsoft.com/microsoft-edge/webview2/\n")
    
    # Testing
    print_header("Testing the Installation")
    print("Run the component tests to verify everything is working:")
    print("\n  $ python test_ps310_desktop.py\n")
    print("This tests server startup and shutdown without opening a GUI window.")
    
    # Features
    print_header("Main Features")
    print("Once the application is running, you can:")
    print("  • Connect to your PS310 via GPIB")
    print("  • Set voltage and current limits")
    print("  • Enable/disable high voltage output")
    print("  • Create automated voltage ramps")
    print("  • Monitor voltage and current in real-time")
    print("  • View live progress during voltage ramping")
    
    # Safety
    print_header("⚠️  SAFETY REMINDER")
    print("HIGH VOLTAGE DEVICE - EXTREME CAUTION REQUIRED\n")
    print("  • Maximum voltage: ±1250V")
    print("  • Always use appropriate safety equipment")
    print("  • Disable output before disconnecting")
    print("  • Follow proper high voltage procedures")
    
    # More info
    print_header("More Information")
    print("For detailed documentation, see:")
    print("  • STANFORDPS310_DESKTOP_README.md - Desktop app guide")
    print("  • STANFORDPS310_GUI_README.md - Web interface details")
    print("  • README.md - General Lab_Data_Logging info")
    
    print("\n" + "=" * 70)
    print("Ready to start? Run: python stanfordps310_gui_desktop.py")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
