#!/usr/bin/env python3
"""
Unit tests for the voltage glitch filter in StanfordPS310.

Tests the glitch filter that prevents discontinuous jumps to zero 
from voltages below -40V.
"""

import sys
from unittest.mock import Mock, MagicMock, patch

# Add libs directory to path
sys.path.insert(0, 'libs')

from StanfordPS310 import StanfordPS310


def test_glitch_filter_no_glitch_normal_operation():
    """Test that normal voltage readings pass through without filtering."""
    print("=" * 60)
    print("Test 1: Normal Operation (No Glitch)")
    print("=" * 60)
    
    with patch('pyvisa.ResourceManager'):
        ps310 = StanfordPS310(auto_connect=False)
        ps310.instrument = MagicMock()
        ps310.status = "Connected"
        
        # Test readings that should pass through unchanged
        # These are all decreasing (going more negative) or staying below -40V
        test_voltages = [
            (-100.0, -100.0, "Initial reading"),
            (-50.0, -50.0, "More negative, no glitch"),
            (-60.0, -60.0, "Even more negative, no glitch"),
            (-45.0, -45.0, "Less negative but still below -40V"),
        ]
        
        for input_v, expected_v, description in test_voltages:
            ps310.instrument.query = MagicMock(return_value=str(input_v))
            result = ps310.measure_voltage()
            assert result == expected_v, f"Expected {expected_v}, got {result}"
            print(f"   ✓ {description}: {input_v}V -> {result}V")
        
        print("\n✅ Test 1 passed: Normal voltages pass through correctly\n")


def test_glitch_filter_detects_glitch():
    """Test that glitch filter detects and holds previous value on first glitch."""
    print("=" * 60)
    print("Test 2: Glitch Detection")
    print("=" * 60)
    
    with patch('pyvisa.ResourceManager'):
        ps310 = StanfordPS310(auto_connect=False)
        ps310.instrument = MagicMock()
        ps310.status = "Connected"
        
        # Start with voltage below threshold (-50V)
        ps310.instrument.query = MagicMock(return_value="-50.0")
        result = ps310.measure_voltage()
        assert result == -50.0, f"Expected -50.0, got {result}"
        print(f"   ✓ Initial reading: {result}V")
        
        # Simulate a glitch: jump to 0V
        ps310.instrument.query = MagicMock(return_value="0.0")
        result = ps310.measure_voltage()
        
        # Should return previous value (-50V) instead of 0V
        assert result == -50.0, f"Expected -50.0 (held), got {result}"
        print(f"   ✓ Glitch detected: held previous value {result}V instead of 0V")
        
        print("\n✅ Test 2 passed: Glitch correctly detected and filtered\n")


def test_glitch_filter_recovery_after_consecutive_readings():
    """Test that filter recovers after consecutive readings above threshold."""
    print("=" * 60)
    print("Test 3: Recovery After Consecutive Readings")
    print("=" * 60)
    
    with patch('pyvisa.ResourceManager'):
        ps310 = StanfordPS310(auto_connect=False)
        ps310.instrument = MagicMock()
        ps310.status = "Connected"
        
        # Start with voltage below threshold (-60V)
        ps310.instrument.query = MagicMock(return_value="-60.0")
        result = ps310.measure_voltage()
        print(f"   ✓ Initial reading: {result}V")
        
        # First reading above threshold (glitch suspected, hold previous)
        ps310.instrument.query = MagicMock(return_value="-30.0")
        result = ps310.measure_voltage()
        assert result == -60.0, f"First reading above threshold: expected -60.0 (held), got {result}"
        print(f"   ✓ First above-threshold reading: held {result}V")
        
        # Second consecutive reading above threshold (real change, accept it)
        ps310.instrument.query = MagicMock(return_value="-25.0")
        result = ps310.measure_voltage()
        assert result == -25.0, f"Second reading: expected -25.0 (accepted), got {result}"
        print(f"   ✓ Second consecutive reading: accepted {result}V (filter reset)")
        
        print("\n✅ Test 3 passed: Filter correctly recovers after consecutive readings\n")


def test_glitch_filter_multiple_glitches():
    """Test handling of multiple glitch events."""
    print("=" * 60)
    print("Test 4: Multiple Glitch Events")
    print("=" * 60)
    
    with patch('pyvisa.ResourceManager'):
        ps310 = StanfordPS310(auto_connect=False)
        ps310.instrument = MagicMock()
        ps310.status = "Connected"
        
        # Reading 1: -100V
        ps310.instrument.query = MagicMock(return_value="-100.0")
        result = ps310.measure_voltage()
        assert result == -100.0
        print(f"   ✓ Reading 1: {result}V")
        
        # Reading 2: 0V (glitch, hold -100V)
        ps310.instrument.query = MagicMock(return_value="0.0")
        result = ps310.measure_voltage()
        assert result == -100.0, f"Expected -100.0 (held), got {result}"
        print(f"   ✓ Reading 2: glitch detected, held {result}V")
        
        # Reading 3: -5V (consecutive above threshold, accept)
        ps310.instrument.query = MagicMock(return_value="-5.0")
        result = ps310.measure_voltage()
        assert result == -5.0, f"Expected -5.0 (accepted), got {result}"
        print(f"   ✓ Reading 3: consecutive reading, accepted {result}V")
        
        # Reading 4: -80V (normal, below threshold)
        ps310.instrument.query = MagicMock(return_value="-80.0")
        result = ps310.measure_voltage()
        assert result == -80.0
        print(f"   ✓ Reading 4: {result}V")
        
        # Reading 5: -10V (another potential glitch, hold -80V)
        ps310.instrument.query = MagicMock(return_value="-10.0")
        result = ps310.measure_voltage()
        assert result == -80.0, f"Expected -80.0 (held), got {result}"
        print(f"   ✓ Reading 5: glitch detected, held {result}V")
        
        print("\n✅ Test 4 passed: Multiple glitches handled correctly\n")


def test_glitch_filter_boundary_conditions():
    """Test glitch filter at boundary voltage (-40V)."""
    print("=" * 60)
    print("Test 5: Boundary Conditions at -40V")
    print("=" * 60)
    
    with patch('pyvisa.ResourceManager'):
        ps310 = StanfordPS310(auto_connect=False)
        ps310.instrument = MagicMock()
        ps310.status = "Connected"
        
        # Reading 1: Exactly at threshold (-40V)
        ps310.instrument.query = MagicMock(return_value="-40.0")
        result = ps310.measure_voltage()
        assert result == -40.0
        print(f"   ✓ Reading 1: {result}V (at threshold)")
        
        # Reading 2: Just below threshold (-40.1V)
        ps310.instrument.query = MagicMock(return_value="-40.1")
        result = ps310.measure_voltage()
        assert result == -40.1
        print(f"   ✓ Reading 2: {result}V (just below threshold)")
        
        # Reading 3: Jump to just above threshold (-39.9V) - should trigger filter
        ps310.instrument.query = MagicMock(return_value="-39.9")
        result = ps310.measure_voltage()
        assert result == -40.1, f"Expected -40.1 (held), got {result}"
        print(f"   ✓ Reading 3: jump detected, held {result}V")
        
        # Reading 4: Another reading above threshold - should accept
        ps310.instrument.query = MagicMock(return_value="-35.0")
        result = ps310.measure_voltage()
        assert result == -35.0, f"Expected -35.0 (accepted), got {result}"
        print(f"   ✓ Reading 4: consecutive reading, accepted {result}V")
        
        print("\n✅ Test 5 passed: Boundary conditions handled correctly\n")


def test_glitch_filter_reset_on_disconnect():
    """Test that glitch filter state is reset on disconnect."""
    print("=" * 60)
    print("Test 6: Filter Reset on Disconnect")
    print("=" * 60)
    
    with patch('pyvisa.ResourceManager'):
        ps310 = StanfordPS310(auto_connect=False)
        ps310.instrument = MagicMock()
        ps310.status = "Connected"
        
        # Set up some state
        ps310.instrument.query = MagicMock(return_value="-50.0")
        result = ps310.measure_voltage()
        print(f"   ✓ Reading before disconnect: {result}V")
        
        # Verify internal state exists
        assert ps310._prev_voltage == -50.0
        print(f"   ✓ Previous voltage stored: {ps310._prev_voltage}V")
        
        # Disconnect
        ps310.disconnect()
        print(f"   ✓ Disconnected")
        
        # Verify state was reset
        assert ps310._prev_voltage == 0.0, "Previous voltage should be reset to 0"
        assert ps310._consecutive_above_threshold == 0, "Counter should be reset to 0"
        print(f"   ✓ Filter state reset (prev_voltage={ps310._prev_voltage}, counter={ps310._consecutive_above_threshold})")
        
        print("\n✅ Test 6 passed: Filter state correctly reset on disconnect\n")


def test_glitch_filter_bypass():
    """Test that glitch filter can be bypassed with apply_filter=False."""
    print("=" * 60)
    print("Test 7: Filter Bypass Option")
    print("=" * 60)
    
    with patch('pyvisa.ResourceManager'):
        ps310 = StanfordPS310(auto_connect=False)
        ps310.instrument = MagicMock()
        ps310.status = "Connected"
        
        # Set up voltage below threshold
        ps310.instrument.query = MagicMock(return_value="-50.0")
        result = ps310.measure_voltage()
        print(f"   ✓ Initial reading: {result}V")
        
        # Now jump to 0V - with filter, should hold previous value
        ps310.instrument.query = MagicMock(return_value="0.0")
        filtered_result = ps310.measure_voltage(apply_filter=True)
        assert filtered_result == -50.0, f"With filter: expected -50.0, got {filtered_result}"
        print(f"   ✓ With filter (apply_filter=True): held {filtered_result}V")
        
        # Without filter, should return raw 0V
        unfiltered_result = ps310.measure_voltage(apply_filter=False)
        assert unfiltered_result == 0.0, f"Without filter: expected 0.0, got {unfiltered_result}"
        print(f"   ✓ Without filter (apply_filter=False): returned {unfiltered_result}V")
        
        print("\n✅ Test 7 passed: Filter can be bypassed correctly\n")


def run_all_tests():
    """Run all glitch filter tests."""
    print("\n")
    print("🧪 Stanford PS310 Glitch Filter Unit Tests")
    print()
    
    try:
        test_glitch_filter_no_glitch_normal_operation()
        test_glitch_filter_detects_glitch()
        test_glitch_filter_recovery_after_consecutive_readings()
        test_glitch_filter_multiple_glitches()
        test_glitch_filter_boundary_conditions()
        test_glitch_filter_reset_on_disconnect()
        test_glitch_filter_bypass()
        
        print("=" * 60)
        print("✅ All glitch filter tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
