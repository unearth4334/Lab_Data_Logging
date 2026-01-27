#!/usr/bin/env python3
"""
Unit test for StanfordPS310 output state handling.
Tests the voltage-based output state determination.
"""

import sys
from unittest.mock import Mock, MagicMock, patch
import pyvisa.errors
import pyvisa.constants

# Add libs directory to path
sys.path.insert(0, 'libs')

from StanfordPS310 import StanfordPS310


def test_output_state_voltage_based():
    """Test that output state is determined by voltage measurement."""
    print("=" * 60)
    print("Test: Voltage-Based Output State Determination")
    print("=" * 60)
    
    # Create a mock PS310 instance without connecting
    with patch('pyvisa.ResourceManager'):
        ps310 = StanfordPS310(auto_connect=False)
        
        # Test 1: Initial state should be False
        print("\n1. Testing initial state...")
        assert ps310._output_state == False, "Initial output state should be False"
        print("   ✓ Initial state is False")
        
        # Test 2: Manually set instrument and status to simulate connection
        print("\n2. Simulating connection...")
        ps310.instrument = MagicMock()
        ps310.status = "Connected"
        ps310.instrument.timeout = 5000
        print("   ✓ Connection simulated")
        
        # Test 3: Test set_output_state updates cached state
        print("\n3. Testing set_output_state caches state...")
        ps310.instrument.write = MagicMock()
        ps310.set_output_state(True)
        assert ps310._output_state == True, "State should be True after setting to True"
        print("   ✓ State cached as True after set_output_state(True)")
        
        ps310.set_output_state(False)
        assert ps310._output_state == False, "State should be False after setting to False"
        print("   ✓ State cached as False after set_output_state(False)")
        
        # Test 4: Test get_output_state with non-zero voltage returns True
        print("\n4. Testing get_output_state with non-zero voltage...")
        
        # Mock measure_voltage to return non-zero voltage (-500V)
        ps310.instrument.query = MagicMock(return_value="-500.0")
        
        result = ps310.get_output_state()
        assert result == True, "Should return True when voltage is non-zero"
        assert ps310._output_state == True, "Should update cached state to True"
        print("   ✓ Returned True when voltage is -500V")
        
        # Test 5: Test get_output_state with zero voltage returns False
        print("\n5. Testing get_output_state with zero voltage...")
        
        # Mock measure_voltage to return zero voltage
        ps310.instrument.query = MagicMock(return_value="0.0")
        
        result = ps310.get_output_state()
        assert result == False, "Should return False when voltage is zero"
        assert ps310._output_state == False, "Should update cached state to False"
        print("   ✓ Returned False when voltage is 0V")
        
        # Test 6: Test get_output_state with small voltage (< 0.1V threshold) returns False
        print("\n6. Testing get_output_state with small voltage...")
        
        # Mock measure_voltage to return small voltage (0.05V)
        ps310.instrument.query = MagicMock(return_value="0.05")
        
        result = ps310.get_output_state()
        assert result == False, "Should return False when voltage is below threshold"
        assert ps310._output_state == False, "Should update cached state to False"
        print("   ✓ Returned False when voltage is 0.05V (below 0.1V threshold)")
        
        # Test 7: Test get_output_state with voltage at threshold returns True
        print("\n7. Testing get_output_state with voltage at threshold...")
        
        # Mock measure_voltage to return voltage above threshold (0.2V)
        ps310.instrument.query = MagicMock(return_value="0.2")
        
        result = ps310.get_output_state()
        assert result == True, "Should return True when voltage is above threshold"
        assert ps310._output_state == True, "Should update cached state to True"
        print("   ✓ Returned True when voltage is 0.2V (above 0.1V threshold)")
        
        # Test 8: Test get_output_state fallback on error
        print("\n8. Testing get_output_state fallback on error...")
        
        # Set cached state to True
        ps310._output_state = True
        
        # Mock query to raise error
        def mock_query_error(cmd):
            raise Exception("Test error")
        
        ps310.instrument.query = mock_query_error
        
        # Should return cached state without raising exception
        result = ps310.get_output_state()
        assert result == True, "Should return cached state (True) on error"
        print("   ✓ Returned cached state (True) on error")
        
        # Test 9: Test disconnect resets cached state
        print("\n9. Testing disconnect resets cached state...")
        ps310._output_state = True
        ps310.disconnect()
        assert ps310._output_state == False, "Disconnect should reset cached state to False"
        print("   ✓ Cached state reset to False on disconnect")
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return True


if __name__ == "__main__":
    print("\n")
    print("🧪 Stanford PS310 Output State Tests")
    print()
    
    try:
        # Run tests
        success = test_output_state_voltage_based()
        
        if success:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
