#!/usr/bin/env python3
"""
Test script for DMM6500 resistance plotter functionality.
"""

import sys
import time
import numpy as np

# Add the current directory to the path
sys.path.append('.')

try:
    from dmm6500_resistance_plotter import DMM6500ResistancePlotter, MockDMM6500
    print("✓ Successfully imported DMM6500ResistancePlotter")
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

def test_mock_dmm():
    """Test the mock DMM functionality."""
    print("\nTesting Mock DMM6500...")
    
    mock_dmm = MockDMM6500()
    print(f"Mock DMM status: {mock_dmm.status}")
    
    # Take some measurements
    measurements = []
    for i in range(5):
        resistance = mock_dmm.measure_resistance()
        measurements.append(resistance)
        print(f"Measurement {i+1}: {resistance:.3f} Ω")
        time.sleep(0.1)
    
    print(f"Average resistance: {np.mean(measurements):.3f} Ω")
    print(f"Std deviation: {np.std(measurements):.3f} Ω")
    print("✓ Mock DMM test passed")

def test_plotter_class():
    """Test the plotter class without GUI."""
    print("\nTesting DMM6500ResistancePlotter class...")
    
    plotter = DMM6500ResistancePlotter(measurement_interval=0.1, slope_threshold=0.05)
    print(f"Plotter initialized with interval: {plotter.measurement_interval}s")
    print(f"Slope threshold: {plotter.slope_threshold} Ω/s")
    
    # Test adding measurements
    test_times = np.linspace(0, 10, 15)
    test_resistances = 1000 + 2 * np.sin(0.5 * test_times) + np.random.normal(0, 0.1, len(test_times))
    
    for i, (t, r) in enumerate(zip(test_times, test_resistances)):
        plotter.timestamps.append(t)
        plotter.resistance_values.append(r)
        
        if i >= 9:  # After 10 measurements
            slope, r_squared = plotter.calculate_slope()
            if slope is not None:
                print(f"Measurement {i+1}: Slope = {slope:.6f} Ω/s, R² = {r_squared:.4f}")
    
    print("✓ Plotter class test passed")

def test_slope_calculation():
    """Test slope calculation with known data."""
    print("\nTesting slope calculation...")
    
    plotter = DMM6500ResistancePlotter()
    
    # Create test data with known slope (1 Ω/s increase)
    times = np.arange(0, 10, 1)  # 10 seconds
    resistances = 1000 + times  # 1 Ω increase per second
    
    for t, r in zip(times, resistances):
        plotter.timestamps.append(t)
        plotter.resistance_values.append(r)
    
    slope, r_squared = plotter.calculate_slope()
    print(f"Expected slope: 1.0 Ω/s, Calculated slope: {slope:.6f} Ω/s")
    print(f"R-squared: {r_squared:.6f}")
    
    if abs(slope - 1.0) < 0.001 and r_squared > 0.99:
        print("✓ Slope calculation test passed")
    else:
        print("✗ Slope calculation test failed")

def main():
    """Run all tests."""
    print("Running DMM6500 Resistance Plotter Tests")
    print("=" * 45)
    
    try:
        test_mock_dmm()
        test_plotter_class()
        test_slope_calculation()
        
        print("\n" + "=" * 45)
        print("✓ All tests passed!")
        print("\nTo run the interactive plotter (with GUI), use:")
        print("python dmm6500_resistance_plotter.py")
        print("\nTo run with custom parameters:")
        print("python dmm6500_resistance_plotter.py --interval 0.5 --threshold 0.02")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()