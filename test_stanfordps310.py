#!/usr/bin/env python3
"""
Test script for StanfordPS310 power supply library.

This script tests the negative voltage validation in the set_voltage method.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the loading module before importing StanfordPS310
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libs'))

from colorama import init, Fore, Style

# Create a minimal mock of the loading module
class loading:
    def delay_with_loading_indicator(self, delay):
        pass
    
    def input_with_flashing(self, prompt=''):
        return input(prompt)

# Make the mock available for import
sys.modules['loading'] = type(sys)('loading')
sys.modules['loading'].loading = loading

from libs.StanfordPS310 import StanfordPS310

init(autoreset=True)

def test_negative_voltage_check():
    """
    Test that the set_voltage method only accepts negative values.
    """
    print(Fore.CYAN + Style.BRIGHT + "\n=== Testing StanfordPS310 Negative Voltage Validation ===\n")
    
    # Create a mock StanfordPS310 instance (without auto-connect)
    print(Fore.YELLOW + "Creating StanfordPS310 instance (without auto-connect)...")
    try:
        # Mock the pyvisa ResourceManager
        class MockResourceManager:
            def list_resources(self):
                return []
        
        # Patch the ResourceManager before creating instance
        import libs.StanfordPS310 as ps_module
        original_rm = ps_module.pyvisa.ResourceManager
        ps_module.pyvisa.ResourceManager = MockResourceManager
        
        ps = StanfordPS310(auto_connect=False)
        
        # Restore original ResourceManager
        ps_module.pyvisa.ResourceManager = original_rm
        
        # Manually set status to Connected to bypass connection requirement for testing
        ps.status = "Connected"
        
        # Create a mock instrument object to prevent actual VISA calls
        class MockInstrument:
            def write(self, cmd):
                print(Fore.BLUE + f"  Mock write: {cmd}")
            
            def query(self, cmd):
                print(Fore.BLUE + f"  Mock query: {cmd}")
                return "0.0"
        
        ps.instrument = MockInstrument()
        
        print(Fore.GREEN + "✓ StanfordPS310 instance created successfully\n")
        
    except Exception as e:
        print(Fore.RED + f"✗ Failed to create instance: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 1: Valid negative voltage
    print(Fore.CYAN + "Test 1: Setting valid negative voltage (-5.0 V)")
    try:
        ps.set_voltage(-5.0)
        print(Fore.GREEN + "✓ Test 1 PASSED: Negative voltage accepted\n")
    except Exception as e:
        print(Fore.RED + f"✗ Test 1 FAILED: {e}\n")
        return False
    
    # Test 2: Valid negative voltage (more negative)
    print(Fore.CYAN + "Test 2: Setting valid negative voltage (-10.5 V)")
    try:
        ps.set_voltage(-10.5)
        print(Fore.GREEN + "✓ Test 2 PASSED: Negative voltage accepted\n")
    except Exception as e:
        print(Fore.RED + f"✗ Test 2 FAILED: {e}\n")
        return False
    
    # Test 3: Invalid positive voltage
    print(Fore.CYAN + "Test 3: Attempting to set positive voltage (5.0 V) - should fail")
    try:
        ps.set_voltage(5.0)
        print(Fore.RED + "✗ Test 3 FAILED: Positive voltage was accepted (should have been rejected)\n")
        return False
    except ValueError as e:
        if "must be negative" in str(e):
            print(Fore.GREEN + f"✓ Test 3 PASSED: Positive voltage correctly rejected with message:")
            print(Fore.YELLOW + f"  {e}\n")
        else:
            print(Fore.RED + f"✗ Test 3 FAILED: Wrong error message: {e}\n")
            return False
    
    # Test 4: Invalid zero voltage
    print(Fore.CYAN + "Test 4: Attempting to set zero voltage (0.0 V) - should fail")
    try:
        ps.set_voltage(0.0)
        print(Fore.RED + "✗ Test 4 FAILED: Zero voltage was accepted (should have been rejected)\n")
        return False
    except ValueError as e:
        if "must be negative" in str(e):
            print(Fore.GREEN + f"✓ Test 4 PASSED: Zero voltage correctly rejected with message:")
            print(Fore.YELLOW + f"  {e}\n")
        else:
            print(Fore.RED + f"✗ Test 4 FAILED: Wrong error message: {e}\n")
            return False
    
    # Test 5: Invalid non-numeric voltage
    print(Fore.CYAN + "Test 5: Attempting to set non-numeric voltage (string) - should fail")
    try:
        ps.set_voltage("invalid")
        print(Fore.RED + "✗ Test 5 FAILED: Non-numeric voltage was accepted (should have been rejected)\n")
        return False
    except ValueError as e:
        if "numeric value" in str(e):
            print(Fore.GREEN + f"✓ Test 5 PASSED: Non-numeric voltage correctly rejected\n")
        else:
            print(Fore.RED + f"✗ Test 5 FAILED: Wrong error message: {e}\n")
            return False
    
    return True

if __name__ == "__main__":
    print(Fore.CYAN + Style.BRIGHT + "\nStanfordPS310 Test Suite")
    print("=" * 60)
    
    success = test_negative_voltage_check()
    
    print("=" * 60)
    if success:
        print(Fore.GREEN + Style.BRIGHT + "\n✓ All tests PASSED!\n")
        sys.exit(0)
    else:
        print(Fore.RED + Style.BRIGHT + "\n✗ Some tests FAILED!\n")
        sys.exit(1)
