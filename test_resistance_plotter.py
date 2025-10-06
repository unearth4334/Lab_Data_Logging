#!/usr/bin/env python3
"""
Test script for the resistance_plotter.py functionality.

This script tests the core components of the resistance plotter
without requiring hardware or GUI components.
"""

import sys
import time
import unittest
from unittest.mock import Mock, patch
from collections import deque
import numpy as np

# Add the current directory to the path
sys.path.insert(0, '.')

# Import the resistance plotter
from resistance_plotter import ResistancePlotter

class TestResistancePlotter(unittest.TestCase):
    """Test cases for the ResistancePlotter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.plotter = ResistancePlotter(
            interval=0.1, 
            max_points=20, 
            demo_mode=True, 
            no_gui=True
        )
    
    def test_initialization(self):
        """Test proper initialization of the plotter."""
        self.assertEqual(self.plotter.interval, 0.1)
        self.assertEqual(self.plotter.max_points, 20)
        self.assertTrue(self.plotter.demo_mode)
        self.assertTrue(self.plotter.no_gui)
        self.assertEqual(self.plotter.measurement_count, 0)
        self.assertEqual(len(self.plotter.resistances), 0)
        self.assertEqual(len(self.plotter.timestamps), 0)
    
    def test_demo_measurement(self):
        """Test that demo measurements generate reasonable values."""
        resistance = self.plotter.measure_resistance()
        self.assertIsInstance(resistance, float)
        self.assertGreater(resistance, 0)
        # Should be around 1000Ω ± some variation
        self.assertGreater(resistance, 800)
        self.assertLess(resistance, 1200)
    
    def test_data_storage(self):
        """Test that data is properly stored."""
        # Add some test data
        for i in range(5):
            self.plotter.timestamps.append(i * 0.1)
            self.plotter.resistances.append(1000 + i)
            self.plotter.measurement_count += 1
        
        self.assertEqual(len(self.plotter.timestamps), 5)
        self.assertEqual(len(self.plotter.resistances), 5)
        self.assertEqual(self.plotter.measurement_count, 5)
        self.assertEqual(list(self.plotter.resistances), [1000, 1001, 1002, 1003, 1004])
    
    def test_max_points_limit(self):
        """Test that data storage respects max_points limit."""
        # Add more data than max_points
        for i in range(25):  # More than max_points (20)
            self.plotter.timestamps.append(i * 0.1)
            self.plotter.resistances.append(1000 + i)
        
        # Should be limited to max_points
        self.assertEqual(len(self.plotter.timestamps), 20)
        self.assertEqual(len(self.plotter.resistances), 20)
        # Should contain the latest 20 values
        expected = list(range(1005, 1025))  # 1005 to 1024
        self.assertEqual(list(self.plotter.resistances), expected)
    
    def test_statistics_calculation_insufficient_data(self):
        """Test statistics calculation with insufficient data."""
        # Add only 5 measurements
        for i in range(5):
            self.plotter.resistances.append(1000 + i)
        
        stats_available = self.plotter.calculate_latest_10_stats()
        self.assertFalse(stats_available)
    
    def test_statistics_calculation_sufficient_data(self):
        """Test statistics calculation with sufficient data."""
        # Add exactly 10 measurements
        test_values = [1000, 1005, 1010, 995, 1015, 1020, 990, 1025, 1030, 985]
        for value in test_values:
            self.plotter.resistances.append(value)
        
        stats_available = self.plotter.calculate_latest_10_stats()
        self.assertTrue(stats_available)
        
        # Check calculated statistics
        expected_mean = np.mean(test_values)
        expected_std = np.std(test_values)
        expected_min = np.min(test_values)
        expected_max = np.max(test_values)
        
        self.assertAlmostEqual(self.plotter.latest_10_stats['mean'], expected_mean, places=2)
        self.assertAlmostEqual(self.plotter.latest_10_stats['std'], expected_std, places=2)
        self.assertEqual(self.plotter.latest_10_stats['min'], expected_min)
        self.assertEqual(self.plotter.latest_10_stats['max'], expected_max)
    
    def test_statistics_calculation_more_than_10(self):
        """Test statistics calculation with more than 10 measurements."""
        # Add 15 measurements
        test_values = list(range(1000, 1015))
        for value in test_values:
            self.plotter.resistances.append(value)
        
        stats_available = self.plotter.calculate_latest_10_stats()
        self.assertTrue(stats_available)
        
        # Should use only the latest 10
        latest_10 = test_values[-10:]  # 1005 to 1014
        expected_mean = np.mean(latest_10)
        
        self.assertAlmostEqual(self.plotter.latest_10_stats['mean'], expected_mean, places=2)
        self.assertEqual(self.plotter.latest_10_stats['min'], min(latest_10))
        self.assertEqual(self.plotter.latest_10_stats['max'], max(latest_10))
    
    def test_dmm_connection_demo_mode(self):
        """Test DMM connection in demo mode."""
        result = self.plotter.connect_dmm()
        self.assertTrue(result)
        self.assertIsNone(self.plotter.dmm)  # Should be None in demo mode
    
    @patch('resistance_plotter.DMM6500')
    def test_dmm_connection_real_mode(self, mock_dmm_class):
        """Test DMM connection in real mode."""
        # Create a non-demo plotter
        plotter = ResistancePlotter(demo_mode=False, no_gui=True)
        
        # Mock successful connection
        mock_dmm = Mock()
        mock_dmm.status = "Connected"
        mock_dmm_class.return_value = mock_dmm
        
        result = plotter.connect_dmm()
        self.assertTrue(result)
        self.assertEqual(plotter.dmm, mock_dmm)
    
    @patch('resistance_plotter.DMM6500')
    def test_dmm_connection_failure(self, mock_dmm_class):
        """Test DMM connection failure."""
        # Create a non-demo plotter
        plotter = ResistancePlotter(demo_mode=False, no_gui=True)
        
        # Mock failed connection
        mock_dmm = Mock()
        mock_dmm.status = "Not Connected"
        mock_dmm_class.return_value = mock_dmm
        
        result = plotter.connect_dmm()
        self.assertFalse(result)
    
    def test_measure_resistance_real_mode(self):
        """Test resistance measurement in real mode with mocked DMM."""
        plotter = ResistancePlotter(demo_mode=False, no_gui=True)
        
        # Mock DMM
        mock_dmm = Mock()
        mock_dmm.measure_resistance.return_value = 1234.56
        plotter.dmm = mock_dmm
        
        resistance = plotter.measure_resistance()
        self.assertEqual(resistance, 1234.56)
        mock_dmm.measure_resistance.assert_called_once()


def run_functional_test():
    """Run a functional test of the resistance plotter."""
    print("Running functional test of resistance plotter...")
    print("=" * 50)
    
    # Create a plotter instance
    plotter = ResistancePlotter(
        interval=0.2, 
        max_points=15, 
        demo_mode=True, 
        no_gui=True
    )
    
    print(f"Created plotter with interval={plotter.interval}s, max_points={plotter.max_points}")
    
    # Simulate taking measurements
    print("\nSimulating 12 measurements...")
    start_time = time.time()
    
    for i in range(12):
        # Simulate measurement
        resistance = plotter.measure_resistance()
        current_time = time.time() - start_time
        
        # Store data
        plotter.timestamps.append(current_time)
        plotter.resistances.append(resistance)
        plotter.measurement_count += 1
        
        print(f"Measurement {plotter.measurement_count}: {resistance:.2f} Ω (t={current_time:.1f}s)")
        
        # Check if we can calculate stats
        if plotter.measurement_count >= 10:
            stats_available = plotter.calculate_latest_10_stats()
            if stats_available:
                stats = plotter.latest_10_stats
                print(f"  Latest 10 - Mean: {stats['mean']:.2f}Ω, "
                      f"Std: {stats['std']:.2f}Ω, "
                      f"Range: {stats['min']:.2f}-{stats['max']:.2f}Ω")
        
        time.sleep(0.1)  # Short delay between measurements
    
    print(f"\nFunctional test completed successfully!")
    print(f"Total measurements: {plotter.measurement_count}")
    print(f"Data points stored: {len(plotter.resistances)}")


def main():
    """Main test function."""
    print("DMM6500 Resistance Plotter Test Suite")
    print("=" * 40)
    
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "=" * 40)
    
    # Run functional test
    run_functional_test()


if __name__ == '__main__':
    main()