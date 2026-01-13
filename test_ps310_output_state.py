#!/usr/bin/env python3
"""
Unit test for StanfordPS310 output state handling.
Tests the fallback mechanism for HVON? query timeouts.
"""

import sys
from unittest.mock import Mock, MagicMock, patch
import pyvisa.errors

# Add libs directory to path
sys.path.insert(0, 'libs')

from StanfordPS310 import StanfordPS310


def test_output_state_caching():
    """Test that output state is cached and used as fallback."""
    print("=" * 60)
    print("Test: Output State Caching Mechanism")
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
        
        # Test 4: Test get_output_state with timeout falls back to cached state
        print("\n4. Testing get_output_state timeout fallback...")
        
        # Set cached state to True
        ps310._output_state = True
        
        # Mock query to raise timeout error
        def mock_query_timeout(cmd):
            raise pyvisa.errors.VisaIOError(-1073807339)  # VI_ERROR_TMO
        
        ps310.instrument.query = mock_query_timeout
        
        # Should return cached state without raising exception
        result = ps310.get_output_state()
        assert result == True, "Should return cached state (True) on timeout"
        print("   ✓ Returned cached state (True) on HVON? timeout")
        
        # Change cached state and test again
        ps310._output_state = False
        result = ps310.get_output_state()
        assert result == False, "Should return cached state (False) on timeout"
        print("   ✓ Returned cached state (False) on HVON? timeout")
        
        # Test 5: Test get_output_state updates cache when query succeeds
        print("\n5. Testing get_output_state updates cache on success...")
        
        # Mock successful query returning "1" (on)
        ps310.instrument.query = MagicMock(return_value="1")
        result = ps310.get_output_state()
        assert result == True, "Should return True when query returns '1'"
        assert ps310._output_state == True, "Should update cached state to True"
        print("   ✓ Returned True and updated cache when query returned '1'")
        
        # Mock successful query returning "0" (off)
        ps310.instrument.query = MagicMock(return_value="0")
        result = ps310.get_output_state()
        assert result == False, "Should return False when query returns '0'"
        assert ps310._output_state == False, "Should update cached state to False"
        print("   ✓ Returned False and updated cache when query returned '0'")
        
        # Test 6: Test disconnect resets cached state
        print("\n6. Testing disconnect resets cached state...")
        ps310._output_state = True
        ps310.disconnect()
        assert ps310._output_state == False, "Disconnect should reset cached state to False"
        print("   ✓ Cached state reset to False on disconnect")
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return True


def test_timeout_restoration():
    """Test that timeout is properly restored after get_output_state."""
    print("\n" + "=" * 60)
    print("Test: Timeout Restoration")
    print("=" * 60)
    
    with patch('pyvisa.ResourceManager'):
        ps310 = StanfordPS310(auto_connect=False)
        
        # Simulate connection
        ps310.instrument = MagicMock()
        ps310.status = "Connected"
        original_timeout = 5000
        ps310.instrument.timeout = original_timeout
        
        # Mock query to raise timeout
        def mock_query_timeout(cmd):
            raise pyvisa.errors.VisaIOError(-1073807339)
        
        ps310.instrument.query = mock_query_timeout
        ps310._output_state = False
        
        # Call get_output_state (will timeout and use cached value)
        result = ps310.get_output_state()
        
        # Check that timeout was restored
        assert ps310.instrument.timeout == original_timeout, \
            f"Timeout should be restored to {original_timeout}, got {ps310.instrument.timeout}"
        print("   ✓ Timeout properly restored after exception")
        
        print("\n" + "=" * 60)
        print("✓ Timeout restoration test passed!")
        print("=" * 60)
        return True


if __name__ == "__main__":
    print("\n")
    print("🧪 Stanford PS310 Output State Fallback Tests")
    print()
    
    try:
        # Run tests
        success = True
        success = test_output_state_caching() and success
        success = test_timeout_restoration() and success
        
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
