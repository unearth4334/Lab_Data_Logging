#!/usr/bin/env python3
"""
Desktop application launcher for Stanford PS310 Power Supply GUI.
Uses a Chromium-based webview to display the FastAPI web interface.

This script:
1. Starts the FastAPI server in a background thread
2. Opens a desktop window with the web interface
3. Automatically shuts down the server when the window is closed
"""

import sys
import os
import threading
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stanfordps310_desktop.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import pywebview
try:
    import webview
except ImportError:
    logger.error("pywebview is not installed. Install it with: pip install pywebview")
    print("\n❌ Error: pywebview is not installed")
    print("Please install it with: pip install pywebview")
    sys.exit(1)

# Import uvicorn and FastAPI app
try:
    import uvicorn
    from stanfordps310_gui import app
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    print(f"\n❌ Error: Failed to import required modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


class ServerThread(threading.Thread):
    """Background thread for running the FastAPI server."""
    
    def __init__(self, host="127.0.0.1", port=8082):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.server = None
        self.should_exit = threading.Event()
        
    def run(self):
        """Run the uvicorn server."""
        logger.info(f"Starting FastAPI server on {self.host}:{self.port}")
        
        # Configure uvicorn with proper shutdown handling
        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=False  # Reduce log verbosity
        )
        self.server = uvicorn.Server(config)
        
        try:
            self.server.run()
        except Exception as e:
            logger.error(f"Server error: {e}")
            
    def stop(self):
        """Stop the server gracefully."""
        logger.info("Stopping FastAPI server...")
        if self.server:
            self.should_exit.set()
            self.server.should_exit = True
            # Give server a moment to shut down gracefully
            time.sleep(0.5)


def wait_for_server(host, port, timeout=10):
    """Wait for the server to start responding."""
    import socket
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                logger.info("Server is ready")
                return True
        except Exception:
            pass
        time.sleep(0.2)
    
    return False


def is_headless_environment():
    """
    Detect if running in a headless environment (no GUI available).
    
    Returns:
        True if headless, False otherwise
    """
    # Allow override via environment variable
    if os.environ.get('PYWEBVIEW_GUI') == '1':
        return False  # User explicitly wants to try GUI
    
    # Check for explicit headless flag
    if os.environ.get('HEADLESS') == 'true':
        return True
    
    # Check DISPLAY environment variable (Linux/Unix)
    # This is the primary indicator for X11-based systems
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        display = os.environ.get('DISPLAY')
        # DISPLAY must be set to a non-empty value
        # None = unset (definitely headless)
        # '' = empty string (also headless - invalid display)
        if display is None or not display.strip():
            return True
    
    return False


def on_closing():
    """Called when the webview window is closing."""
    logger.info("Window closing - shutting down application")
    return True  # Allow window to close


def main():
    """Main entry point for the desktop application."""
    print("=" * 70)
    print("🚀 Stanford PS310 Power Supply - Desktop Application")
    print("=" * 70)
    print()
    
    # Check for headless environment before proceeding
    if is_headless_environment():
        print("❌ Error: Cannot run desktop application in headless environment")
        print()
        print("This application requires a graphical display to show the window.")
        print()
        print("Alternative solutions:")
        print("  1. Use the web interface instead:")
        print("     python stanfordps310_gui.py")
        print("     Then open http://127.0.0.1:8082 in a browser")
        print()
        print("  2. If on a remote server, use SSH X11 forwarding:")
        print("     ssh -X user@server")
        print()
        print("  3. Use a virtual display (Linux):")
        print("     xvfb-run python stanfordps310_gui_desktop.py")
        print()
        logger.error("Cannot start desktop application in headless environment")
        return 1
    
    # Configuration
    host = os.environ.get("PS310_GUI_HOST", "127.0.0.1")
    port = int(os.environ.get("PS310_GUI_PORT", "8082"))
    url = f"http://{host}:{port}"
    
    # Start the FastAPI server in a background thread
    print(f"📡 Starting web server at {url}...")
    server_thread = ServerThread(host=host, port=port)
    server_thread.start()
    
    # Wait for server to be ready
    print("⏳ Waiting for server to start...")
    if not wait_for_server(host, port, timeout=10):
        print("❌ Error: Server failed to start within timeout period")
        logger.error("Server failed to start within timeout")
        sys.exit(1)
    
    print("✅ Server is running")
    print()
    print("🌐 Opening application window...")
    print()
    print("⚠️  HIGH VOLTAGE DEVICE - Use appropriate safety precautions!")
    print("💡 Close the window to exit the application")
    print("=" * 70)
    print()
    
    try:
        # Create and start the webview window
        window = webview.create_window(
            title="Stanford PS310 High Voltage Power Supply Control",
            url=url,
            width=1400,
            height=900,
            resizable=True,
            fullscreen=False,
            min_size=(800, 600)
        )
        
        # Set the closing event handler
        window.events.closing += on_closing
        
        # Start the webview (this blocks until window is closed)
        webview.start(debug=False)
        
    except Exception as e:
        logger.error(f"Error creating webview: {e}", exc_info=True)
        print(f"\n❌ Error: Failed to create application window: {e}")
        print("\nTroubleshooting:")
        print("  - On Linux: Install PyGObject and webkit2gtk")
        print("    Ubuntu/Debian: sudo apt install python3-gi python3-gi-cairo gir1.2-webkit2-4.0")
        print("  - On macOS: pywebview uses native WebKit (usually works out of box)")
        print("  - On Windows: pywebview uses Edge WebView2 (install from Microsoft if needed)")
        return 1
    
    finally:
        # Clean shutdown
        print("\n🛑 Shutting down...")
        logger.info("Application closing - stopping server")
        server_thread.stop()
        
        # Give background tasks time to clean up
        time.sleep(1)
        
        print("✅ Application closed successfully")
        logger.info("Application shutdown complete")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
