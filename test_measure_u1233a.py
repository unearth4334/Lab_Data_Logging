#!/usr/bin/env python3
"""
Test script for measure_u1233a.py
Tests the U1233A measurement script with simulated data.
"""

import sys
import os
import csv
import time
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

# Add libs directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

from measure_u1233a import U1233ADataLogger


def test_initialization():
    """Test that U1233ADataLogger initializes correctly."""
    logger = U1233ADataLogger(max_points=50, interval=0.5)
    
    assert logger.max_points == 50
    assert logger.interval == 0.5
    assert logger.multimeter is None
    assert logger.csv_file is None
    assert logger.measurement_count == 0
    assert len(logger.timestamps) == 0
    assert len(logger.measurements) == 0
    
    print("✓ Initialization test passed")


def test_csv_file_creation():
    """Test CSV file creation with correct filename format."""
    logger = U1233ADataLogger()
    
    # Test CSV file opening
    filename = logger.open_csv_file()
    
    # Check filename format (yyyy-mm-dd_u1233a_measurements.csv)
    date_str = datetime.now().strftime('%Y-%m-%d')
    expected_filename = f"{date_str}_u1233a_measurements.csv"
    
    assert filename == expected_filename
    assert logger.csv_file is not None
    assert logger.csv_writer is not None
    
    # Close and cleanup
    logger.close_csv_file()
    
    # Verify file was created and has header
    assert os.path.exists(filename)
    
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ['Timestamp', 'Elapsed_Time_s', 'Measurement', 'Error']
    
    # Cleanup
    os.remove(filename)
    
    print(f"✓ CSV file creation test passed (filename: {expected_filename})")


def test_simulated_measurements():
    """Test measurement collection with simulated multimeter."""
    logger = U1233ADataLogger(max_points=10, interval=0.1)
    
    # Mock the multimeter
    mock_multimeter = Mock()
    mock_multimeter.measure = Mock(return_value=(3.14159, 0.00001))
    mock_multimeter.identity = "Mock U1233A Multimeter"
    
    logger.multimeter = mock_multimeter
    
    # Open CSV file
    filename = logger.open_csv_file()
    
    # Simulate a few measurements
    logger.start_time = time.time()
    
    for i in range(5):
        measurement, error = logger.get_measurement()
        
        assert measurement == 3.14159
        assert error == 0.00001
        
        elapsed = time.time() - logger.start_time
        logger.timestamps.append(elapsed)
        logger.measurements.append(measurement)
        logger.measurement_count += 1
        
        # Write to CSV
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        logger.csv_writer.writerow([timestamp_str, f"{elapsed:.3f}", 
                                    f"{measurement:.6f}", f"{error:.6f}"])
        
        time.sleep(0.01)  # Small delay
    
    # Close CSV
    logger.close_csv_file()
    
    # Verify data was collected
    assert logger.measurement_count == 5
    assert len(logger.timestamps) == 5
    assert len(logger.measurements) == 5
    
    # Verify CSV file contains data
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 6  # Header + 5 data rows
        
        # Check first data row
        assert len(rows[1]) == 4
        assert rows[1][2] == "3.141590"  # Measurement value
        assert rows[1][3] == "0.000010"  # Error value
    
    # Cleanup
    os.remove(filename)
    
    print(f"✓ Simulated measurements test passed ({logger.measurement_count} measurements)")


def test_plot_configuration():
    """Test that plot is configured correctly."""
    logger = U1233ADataLogger()
    
    # Check plot exists
    assert logger.fig is not None
    assert logger.ax is not None
    assert logger.line is not None
    
    # Check plot labels
    assert logger.ax.get_xlabel() == 'Time (seconds)'
    assert logger.ax.get_ylabel() == 'Measurement Value'
    assert 'U1233A Real-Time Measurements' in logger.ax.get_title()
    
    print("✓ Plot configuration test passed")


def test_data_deque_behavior():
    """Test that data deque respects max_points limit."""
    logger = U1233ADataLogger(max_points=5)
    
    # Add more than max_points
    for i in range(10):
        logger.timestamps.append(float(i))
        logger.measurements.append(float(i) * 2)
    
    # Should only keep last 5 points
    assert len(logger.timestamps) == 5
    assert len(logger.measurements) == 5
    assert list(logger.timestamps) == [5.0, 6.0, 7.0, 8.0, 9.0]
    assert list(logger.measurements) == [10.0, 12.0, 14.0, 16.0, 18.0]
    
    print("✓ Data deque behavior test passed")


def test_connection_error_handling():
    """Test connection error handling."""
    logger = U1233ADataLogger()
    
    # Mock U1233A to raise an error
    with patch('measure_u1233a.U1233A', side_effect=Exception("Connection failed")):
        result = logger.connect()
        assert result is False
    
    print("✓ Connection error handling test passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Testing U1233A Measurement Script")
    print("=" * 60)
    print()
    
    tests = [
        test_initialization,
        test_csv_file_creation,
        test_simulated_measurements,
        test_plot_configuration,
        test_data_deque_behavior,
        test_connection_error_handling
    ]
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            return False
        except Exception as e:
            print(f"✗ {test.__name__} raised exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print()
    print("=" * 60)
    print("✅ All tests passed successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
