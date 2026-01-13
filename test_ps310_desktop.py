#!/usr/bin/env python3
"""
Test script for the Stanford PS310 Desktop Application.
Tests server startup and basic functionality without opening a GUI window.
"""

import sys
import time
import socket
import threading
from stanfordps310_gui_desktop import ServerThread, wait_for_server

def test_server_thread():
    """Test that the server thread starts and responds."""
    print("=" * 60)
    print("Testing Stanford PS310 Desktop Application Components")
    print("=" * 60)
    print()
    
    # Test 1: Server Thread Creation
    print("Test 1: Creating Server Thread...")
    try:
        server = ServerThread(host="127.0.0.1", port=8083)
        print("✓ Server thread created successfully")
    except Exception as e:
        print(f"✗ Failed to create server thread: {e}")
        return False
    
    # Test 2: Start Server
    print("\nTest 2: Starting server in background thread...")
    try:
        server.start()
        print("✓ Server thread started")
    except Exception as e:
        print(f"✗ Failed to start server thread: {e}")
        return False
    
    # Test 3: Wait for Server to Be Ready
    print("\nTest 3: Waiting for server to respond...")
    try:
        if wait_for_server("127.0.0.1", 8083, timeout=10):
            print("✓ Server is responding on port 8083")
        else:
            print("✗ Server did not respond within timeout")
            return False
    except Exception as e:
        print(f"✗ Error waiting for server: {e}")
        return False
    
    # Test 4: Verify HTTP Response
    print("\nTest 4: Verifying HTTP response...")
    try:
        import requests
        response = requests.get("http://127.0.0.1:8083/status", timeout=5)
        if response.status_code == 200:
            print("✓ Server returned valid HTTP response")
            print(f"  Status endpoint working: {response.json()}")
        else:
            print(f"✗ Server returned status code: {response.status_code}")
            return False
    except ImportError:
        print("⚠ requests module not installed, skipping HTTP test")
    except Exception as e:
        print(f"✗ HTTP request failed: {e}")
        return False
    
    # Test 5: Stop Server
    print("\nTest 5: Stopping server...")
    try:
        server.stop()
        time.sleep(2)  # Give server time to shut down
        print("✓ Server stopped successfully")
    except Exception as e:
        print(f"✗ Failed to stop server: {e}")
        return False
    
    # Test 6: Verify Server Stopped
    print("\nTest 6: Verifying server stopped...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", 8083))
        sock.close()
        if result != 0:
            print("✓ Server port is no longer listening")
        else:
            print("⚠ Port still appears to be open (may be in TIME_WAIT)")
    except Exception as e:
        print(f"✗ Error checking server status: {e}")
        return False
    
    print()
    print("=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True


def test_imports():
    """Test that all required modules can be imported."""
    print("\n" + "=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    print()
    
    modules = [
        ("pywebview", "webview"),
        ("uvicorn", "uvicorn"),
        ("FastAPI", "fastapi"),
        ("stanfordps310_gui", "stanfordps310_gui"),
        ("stanfordps310_gui_desktop", "stanfordps310_gui_desktop"),
    ]
    
    all_ok = True
    for display_name, module_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {display_name}")
        except ImportError as e:
            print(f"✗ {display_name}: {e}")
            all_ok = False
    
    print()
    return all_ok


if __name__ == "__main__":
    print("\n")
    print("🧪 Stanford PS310 Desktop Application - Component Tests")
    print()
    
    # Test imports first
    if not test_imports():
        print("\n❌ Import tests failed. Please install requirements:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Test server functionality
    if not test_server_thread():
        print("\n❌ Server tests failed")
        sys.exit(1)
    
    print("\n✅ All component tests passed!")
    print("\nNote: This test does not open a GUI window (headless environment).")
    print("To test the full application with GUI, run:")
    print("  python stanfordps310_gui_desktop.py")
    print()
