#!/usr/bin/env python3
"""
Test script for the parameterized output path generation
"""

import sys
sys.path.append('.')

from measurement_gui import generate_output_path, load_defaults
from datetime import datetime

def test_path_generation():
    """Test the output path generation function."""
    print("=== Testing Output Path Generation ===")
    
    # Test cases
    test_cases = [
        ("./captures", "1", "Test"),
        ("./captures", "123", "VDD_2V0_Test"),
        ("/data/measurements", "99999", "Board_Characterization"),
        ("C:/Lab_Data", "42", "Noise_Analysis"),
    ]
    
    for destination, board_num, label in test_cases:
        path = generate_output_path(destination, board_num, label)
        print(f"Input: dest='{destination}', board='{board_num}', label='{label}'")
        print(f"Output: {path}")
        print()

def test_defaults_loading():
    """Test the defaults loading function."""
    print("=== Testing Defaults Loading ===")
    
    defaults = load_defaults()
    print("Loaded defaults:")
    for key, value in defaults.items():
        print(f"  {key}: {value}")
    
if __name__ == "__main__":
    test_path_generation()
    test_defaults_loading()