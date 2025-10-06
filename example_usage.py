#!/usr/bin/env python3
"""
Example usage script for DMM6500 Resistance Plotter

This script demonstrates how to use the DMM6500 resistance plotter
with different configurations.
"""

import sys
import os

# Add the current directory to the path
sys.path.append('.')

from dmm6500_resistance_plotter import DMM6500ResistancePlotter

def example_basic_usage():
    """Basic usage example with default settings."""
    print("Example 1: Basic usage with default settings")
    print("- Measurement interval: 1.0 seconds")
    print("- Slope threshold: 0.01 Ω/s")
    print("- Max points: 100")
    
    plotter = DMM6500ResistancePlotter()
    print("Run: python dmm6500_resistance_plotter.py")
    print()

def example_fast_measurement():
    """Example with faster measurements."""
    print("Example 2: Fast measurements")
    print("- Measurement interval: 0.5 seconds")
    print("- Slope threshold: 0.05 Ω/s")
    print("- Max points: 200")
    
    print("Run: python dmm6500_resistance_plotter.py --interval 0.5 --threshold 0.05 --max-points 200")
    print()

def example_sensitive_monitoring():
    """Example for sensitive slope monitoring."""
    print("Example 3: Sensitive slope monitoring")
    print("- Measurement interval: 2.0 seconds")
    print("- Slope threshold: 0.001 Ω/s (very sensitive)")
    print("- Max points: 50")
    
    print("Run: python dmm6500_resistance_plotter.py --interval 2.0 --threshold 0.001 --max-points 50")
    print()

def example_verbose_mode():
    """Example with verbose logging."""
    print("Example 4: Verbose mode for debugging")
    print("- Default settings with verbose logging enabled")
    
    print("Run: python dmm6500_resistance_plotter.py --verbose")
    print()

def main():
    """Display usage examples."""
    print("DMM6500 Resistance Plotter - Usage Examples")
    print("=" * 50)
    print()
    
    example_basic_usage()
    example_fast_measurement()
    example_sensitive_monitoring()
    example_verbose_mode()
    
    print("Key Features:")
    print("- Real-time resistance measurements from DMM6500")
    print("- Autoscaling plot that updates in real-time")
    print("- Slope calculation for latest 10 measurements")
    print("- Visual box indicator around latest 10 points")
    print("- Box color changes based on slope threshold:")
    print("  * RED: |slope| >= threshold (resistance changing)")
    print("  * GREEN: |slope| < threshold (resistance stable)")
    print()
    
    print("To test without hardware:")
    print("python test_dmm6500_plotter.py")
    print()
    
    print("Notes:")
    print("- Press Ctrl+C to stop measurements")
    print("- If no DMM6500 is connected, a mock device will be used for testing")
    print("- The script requires matplotlib for plotting")

if __name__ == "__main__":
    main()