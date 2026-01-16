#!/usr/bin/env python3
"""
Test script for measure_dmm6500.py
Tests the DMM6500 measurement script with simulated data.
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

from measure_dmm6500 import DMM6500DataLogger


def test_initialization():
    """Test that DMM6500DataLogger initializes correctly."""
    # Test with plot disabled (default)
    logger = DMM6500DataLogger(max_points=50, interval=0.5, measurement_type='voltage', enable_plot=False)
    
    assert logger.max_points == 50
    assert logger.interval == 0.5
    assert logger.measurement_type == 'voltage'
    assert logger.enable_plot == False
    assert logger.multimeter is None
    assert logger.csv_file is None
    assert logger.measurement_count == 0
    assert len(logger.timestamps) == 0
    assert len(logger.measurements) == 0
    assert logger.fig is None
    assert logger.ax is None
    
    # Test with plot enabled
    logger_plot = DMM6500DataLogger(max_points=50, interval=0.5, measurement_type='voltage', enable_plot=True)
    assert logger_plot.enable_plot == True
    assert logger_plot.fig is not None
    assert logger_plot.ax is not None
    
    print("✓ Initialization test passed")


def test_csv_file_creation():
    """Test CSV file creation with correct filename format."""
    for meas_type in ['voltage', 'current', 'resistance', 'temperature']:
        logger = DMM6500DataLogger(measurement_type=meas_type, enable_plot=False)
        
        # Test CSV file opening
        filename = logger.open_csv_file()
        
        # Check filename format (yyyy-mm-dd_dmm6500_<type>_measurements.csv)
        date_str = datetime.now().strftime('%Y-%m-%d')
        expected_filename = f"{date_str}_dmm6500_{meas_type}_measurements.csv"
        
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
            assert header == ['Timestamp', 'Elapsed_Time_s', 'Measurement']
        
        # Cleanup
        os.remove(filename)
    
    print(f"✓ CSV file creation test passed for all measurement types")


def test_simulated_measurements():
    """Test measurement collection with simulated multimeter."""
    for meas_type in ['voltage', 'current', 'resistance', 'temperature']:
        logger = DMM6500DataLogger(max_points=10, interval=0.1, measurement_type=meas_type, enable_plot=False)
        
        # Mock the multimeter
        mock_multimeter = Mock()
        mock_multimeter.measure_voltage = Mock(return_value=5.0)
        mock_multimeter.measure_current = Mock(return_value=0.5)
        mock_multimeter.measure_resistance = Mock(return_value=1000.0)
        mock_multimeter.measure_temperature = Mock(return_value=25.0)
        
        logger.multimeter = mock_multimeter
        
        # Open CSV file
        filename = logger.open_csv_file()
        
        # Simulate a few measurements
        logger.start_time = time.time()
        
        for i in range(5):
            measurement = logger.get_measurement()
            
            assert measurement is not None
            if meas_type == 'voltage':
                assert measurement == 5.0
            elif meas_type == 'current':
                assert measurement == 0.5
            elif meas_type == 'resistance':
                assert measurement == 1000.0
            elif meas_type == 'temperature':
                assert measurement == 25.0
            
            elapsed = time.time() - logger.start_time
            logger.timestamps.append(elapsed)
            logger.measurements.append(measurement)
            logger.measurement_count += 1
            
            # Write to CSV
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            logger.csv_writer.writerow([timestamp_str, f"{elapsed:.3f}", 
                                        f"{measurement:.6f}"])
            
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
            
            # Check first data row format
            assert len(rows[1]) == 3
        
        # Cleanup
        os.remove(filename)
    
    print(f"✓ Simulated measurements test passed for all measurement types ({logger.measurement_count} measurements each)")


def test_plot_configuration():
    """Test that plot is configured correctly."""
    for meas_type in ['voltage', 'current', 'resistance', 'temperature']:
        logger = DMM6500DataLogger(measurement_type=meas_type, enable_plot=True)
        
        # Check plot exists
        assert logger.fig is not None
        assert logger.ax is not None
        assert logger.line is not None
        
        # Check plot labels
        assert logger.ax.get_xlabel() == 'Time (seconds)'
        
        # Check Y-axis label is appropriate for measurement type
        ylabel = logger.ax.get_ylabel()
        if meas_type == 'voltage':
            assert 'Voltage' in ylabel
        elif meas_type == 'current':
            assert 'Current' in ylabel
        elif meas_type == 'resistance':
            assert 'Resistance' in ylabel or 'Ω' in ylabel
        elif meas_type == 'temperature':
            assert 'Temperature' in ylabel or '°C' in ylabel
        
        # Check title
        title = logger.ax.get_title()
        assert 'DMM6500' in title
        assert meas_type.capitalize() in title
    
    print("✓ Plot configuration test passed for all measurement types")


def test_data_deque_behavior():
    """Test that data deque respects max_points limit."""
    logger = DMM6500DataLogger(max_points=5, enable_plot=False)
    
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
    logger = DMM6500DataLogger(enable_plot=False)
    
    # Mock DMM6500 to raise an error
    with patch('measure_dmm6500.DMM6500', side_effect=Exception("Connection failed")):
        result = logger.connect()
        assert result is False
    
    print("✓ Connection error handling test passed")


def test_measurement_types():
    """Test that all measurement types are supported."""
    valid_types = ['voltage', 'current', 'resistance', 'temperature']
    
    for meas_type in valid_types:
        logger = DMM6500DataLogger(measurement_type=meas_type, enable_plot=False)
        assert logger.measurement_type == meas_type
    
    print("✓ Measurement types test passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Testing DMM6500 Measurement Script")
    print("=" * 60)
    print()
    
    tests = [
        test_initialization,
        test_csv_file_creation,
        test_simulated_measurements,
        test_plot_configuration,
        test_data_deque_behavior,
        test_connection_error_handling,
        test_measurement_types
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
