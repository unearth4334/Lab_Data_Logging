#!/usr/bin/env python3
"""
Integration test for the DMM6500 resistance plotter.
Tests the complete workflow without GUI.
"""

import sys
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

# Add the current directory to the path
sys.path.append('.')

try:
    from dmm6500_resistance_plotter import DMM6500ResistancePlotter, MockDMM6500
    print("✓ Successfully imported DMM6500ResistancePlotter")
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

def test_full_integration():
    """Test the complete integration without GUI."""
    print("\nRunning Full Integration Test...")
    print("=" * 40)
    
    # Create plotter with test parameters
    plotter = DMM6500ResistancePlotter(
        measurement_interval=0.1,
        slope_threshold=0.05,
        max_points=50
    )
    
    # Connect to mock DMM
    success = plotter.connect_dmm()
    if not success:
        print("✗ Failed to connect to DMM")
        return False
    
    print(f"✓ Connected to DMM: {type(plotter.dmm).__name__}")
    
    # Setup non-interactive plotting
    plotter.fig = plt.figure(figsize=(10, 6))
    plotter.ax = plotter.fig.add_subplot(111)
    plotter.line, = plotter.ax.plot([], [], 'b-', linewidth=2, label='Resistance')
    plotter.ax.set_xlabel('Time (seconds)')
    plotter.ax.set_ylabel('Resistance (Ohms)')
    plotter.ax.set_title('DMM6500 Integration Test')
    plotter.ax.grid(True, alpha=0.3)
    plotter.ax.legend()
    
    # Simulate measurements
    print("\nTaking measurements...")
    measurements_taken = 0
    stable_detected = False
    changing_detected = False
    
    for i in range(20):  # Take 20 measurements
        # Simulate the update_plot functionality
        resistance = plotter.measure_resistance()
        if resistance is not None:
            plotter.add_measurement(resistance)
            measurements_taken += 1
            
            # Update the plot data
            if len(plotter.timestamps) > 0:
                plotter.line.set_data(plotter.timestamps, plotter.resistance_values)
                plotter.ax.relim()
                plotter.ax.autoscale_view()
                
                # Test slope calculation after 10 measurements
                if len(plotter.resistance_values) >= 10:
                    slope, r_squared = plotter.calculate_slope()
                    
                    if slope is not None:
                        # Check color logic
                        if abs(slope) < plotter.slope_threshold:
                            status = "STABLE"
                            stable_detected = True
                        else:
                            status = "CHANGING"
                            changing_detected = True
                        
                        print(f"Measurement {measurements_taken:2d}: "
                              f"R = {resistance:7.2f} Ω, "
                              f"Slope = {slope:+.6f} Ω/s, "
                              f"Status = {status}")
        
        time.sleep(0.05)  # Short delay
    
    # Save a test plot
    plotter.fig.savefig('integration_test_plot.png', dpi=100, bbox_inches='tight')
    print(f"\n✓ Test plot saved as: integration_test_plot.png")
    
    # Disconnect
    plotter.disconnect_dmm()
    print("✓ Disconnected from DMM")
    
    # Verify results
    print(f"\nTest Results:")
    print(f"- Measurements taken: {measurements_taken}")
    print(f"- Data points stored: {len(plotter.resistance_values)}")
    print(f"- Stable status detected: {stable_detected}")
    print(f"- Changing status detected: {changing_detected}")
    
    # Check that we got good data
    if measurements_taken >= 15:
        print("✓ Sufficient measurements taken")
    else:
        print("✗ Insufficient measurements taken")
        return False
    
    if len(plotter.resistance_values) == measurements_taken:
        print("✓ All measurements stored correctly")
    else:
        print("✗ Measurement storage error")
        return False
    
    # Check that we have reasonable resistance values (using mock DMM)
    if len(plotter.resistance_values) > 0:
        avg_resistance = np.mean(plotter.resistance_values)
        if 990 < avg_resistance < 1010:  # Mock DMM should be around 1000Ω
            print(f"✓ Resistance values reasonable (avg: {avg_resistance:.1f} Ω)")
        else:
            print(f"✗ Resistance values unreasonable (avg: {avg_resistance:.1f} Ω)")
            return False
    
    print("\n✓ Integration test passed!")
    return True

def test_command_line_interface():
    """Test that the command line interface works."""
    print("\nTesting Command Line Interface...")
    print("=" * 40)
    
    import subprocess
    import os
    
    # Test help command
    try:
        result = subprocess.run([
            sys.executable, 'dmm6500_resistance_plotter.py', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and 'usage:' in result.stdout:
            print("✓ Help command works")
        else:
            print("✗ Help command failed")
            return False
            
    except Exception as e:
        print(f"✗ Error testing help command: {e}")
        return False
    
    print("✓ Command line interface test passed!")
    return True

def main():
    """Run all integration tests."""
    print("DMM6500 Resistance Plotter - Integration Tests")
    print("=" * 50)
    
    all_tests_passed = True
    
    try:
        # Run integration test
        if not test_full_integration():
            all_tests_passed = False
        
        # Test command line interface  
        if not test_command_line_interface():
            all_tests_passed = False
        
        print("\n" + "=" * 50)
        if all_tests_passed:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("\nThe DMM6500 resistance plotter is ready to use!")
            print("\nQuick start:")
            print("  python dmm6500_resistance_plotter.py")
        else:
            print("❌ Some integration tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())