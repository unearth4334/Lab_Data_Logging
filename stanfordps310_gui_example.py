#!/usr/bin/env python3
"""
Example script demonstrating automated control of the Stanford PS310
through the GUI's REST API.

This script shows how to programmatically control the power supply
for automated testing or integration with other lab equipment.
"""

import requests
import time
import sys

# GUI server configuration
BASE_URL = "http://localhost:8082"

def check_server():
    """Check if the GUI server is running."""
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def connect_ps310(address="GPIB0::14::INSTR"):
    """Connect to the PS310 power supply."""
    print(f"Connecting to PS310 at {address}...")
    response = requests.post(
        f"{BASE_URL}/connect",
        json={"address": address}
    )
    data = response.json()
    if data.get("success"):
        print("✓ Connected successfully")
        return True
    else:
        print(f"✗ Connection failed: {data.get('error')}")
        return False

def set_voltage(voltage):
    """Set the output voltage."""
    print(f"Setting voltage to {voltage}V...")
    response = requests.post(
        f"{BASE_URL}/set_voltage",
        json={"voltage": voltage}
    )
    data = response.json()
    if data.get("success"):
        print(f"✓ Voltage set to {voltage}V")
        return True
    else:
        print(f"✗ Failed to set voltage: {data.get('error')}")
        return False

def set_current_limit(current_mA):
    """Set the current limit in milliamps."""
    current_A = current_mA / 1000.0
    print(f"Setting current limit to {current_mA}mA...")
    response = requests.post(
        f"{BASE_URL}/set_current_limit",
        json={"current": current_A}
    )
    data = response.json()
    if data.get("success"):
        print(f"✓ Current limit set to {current_mA}mA")
        return True
    else:
        print(f"✗ Failed to set current limit: {data.get('error')}")
        return False

def set_output(state):
    """Enable or disable the high voltage output."""
    state_str = "ON" if state else "OFF"
    print(f"Turning output {state_str}...")
    response = requests.post(
        f"{BASE_URL}/set_output",
        json={"state": state}
    )
    data = response.json()
    if data.get("success"):
        print(f"✓ Output {state_str}")
        return True
    else:
        print(f"✗ Failed to set output: {data.get('error')}")
        return False

def get_status():
    """Get the current status and measurements."""
    response = requests.get(f"{BASE_URL}/status")
    return response.json()

def start_ramp(start, end, step, delay):
    """Start a voltage ramp."""
    print(f"\nStarting voltage ramp:")
    print(f"  From: {start}V")
    print(f"  To: {end}V")
    print(f"  Step: {step}V")
    print(f"  Delay: {delay}s")
    
    response = requests.post(
        f"{BASE_URL}/start_ramp",
        json={
            "start": start,
            "end": end,
            "step": step,
            "delay": delay
        }
    )
    data = response.json()
    if data.get("success"):
        print("✓ Ramp started")
        return True
    else:
        print(f"✗ Failed to start ramp: {data.get('error')}")
        return False

def monitor_ramp():
    """Monitor ramp progress until completion."""
    print("\nMonitoring ramp progress...")
    last_progress = -1
    
    while True:
        status = get_status()
        
        if not status.get("ramping"):
            print("✓ Ramp completed")
            break
        
        progress = status.get("ramp_progress", 0)
        if int(progress) != int(last_progress):
            voltage = status.get("set_voltage", 0)
            current = status.get("current", 0) * 1000  # Convert to mA
            print(f"  Progress: {progress:.0f}% | Voltage: {voltage:.1f}V | Current: {current:.3f}mA")
            last_progress = progress
        
        time.sleep(0.5)

def disconnect_ps310():
    """Disconnect from the PS310."""
    print("\nDisconnecting from PS310...")
    response = requests.post(f"{BASE_URL}/disconnect")
    data = response.json()
    if data.get("success"):
        print("✓ Disconnected")
        return True
    else:
        print(f"✗ Disconnect failed: {data.get('error')}")
        return False

def main():
    """Main example workflow."""
    print("=" * 60)
    print("Stanford PS310 GUI - API Control Example")
    print("=" * 60)
    
    # Check if server is running
    if not check_server():
        print("\n✗ Error: GUI server is not running")
        print("Please start the server with: python stanfordps310_gui.py")
        sys.exit(1)
    
    print("✓ GUI server is running\n")
    
    try:
        # Example 1: Manual voltage control
        print("\n" + "=" * 60)
        print("Example 1: Manual Voltage Control")
        print("=" * 60)
        
        # Connect to device
        if not connect_ps310():
            sys.exit(1)
        
        # Set current limit for safety
        set_current_limit(10)  # 10 mA
        
        # Set voltage and enable output
        set_voltage(-100)
        time.sleep(1)
        
        set_output(True)
        time.sleep(2)
        
        # Read and display status
        status = get_status()
        print(f"\nCurrent readings:")
        print(f"  Set Voltage: {status['set_voltage']:.1f}V")
        print(f"  Actual Voltage: {status['actual_voltage']:.1f}V")
        print(f"  Current: {status['current']*1000:.3f}mA")
        print(f"  Output: {'ON' if status['output_enabled'] else 'OFF'}")
        
        time.sleep(2)
        
        # Disable output
        set_output(False)
        
        # Example 2: Voltage ramping
        print("\n" + "=" * 60)
        print("Example 2: Voltage Ramping")
        print("=" * 60)
        
        # Set initial voltage
        set_voltage(0)
        time.sleep(1)
        
        # Enable output
        set_output(True)
        time.sleep(1)
        
        # Start voltage ramp
        if start_ramp(start=0, end=-300, step=20, delay=0.5):
            monitor_ramp()
        
        time.sleep(1)
        
        # Ramp back down
        if start_ramp(start=-300, end=0, step=20, delay=0.5):
            monitor_ramp()
        
        # Disable output
        set_output(False)
        
        # Disconnect
        disconnect_ps310()
        
        print("\n" + "=" * 60)
        print("✓ Example completed successfully")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        print("Disabling output and disconnecting...")
        set_output(False)
        disconnect_ps310()
        sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("Attempting to disable output and disconnect...")
        try:
            set_output(False)
            disconnect_ps310()
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
