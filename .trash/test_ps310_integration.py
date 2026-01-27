#!/usr/bin/env python3
"""
Integration test for PS310 GUI connection with HVON? timeout fallback.
Simulates the actual GUI connection scenario without requiring hardware.
"""

import sys
import asyncio
from unittest.mock import Mock, MagicMock, patch
import pyvisa.errors
import pyvisa.constants

# Add libs directory to path
sys.path.insert(0, 'libs')

from StanfordPS310 import StanfordPS310


class MockInstrument:
    """Mock VISA instrument that simulates PS310 with voltage-based state detection."""
    
    def __init__(self):
        self.timeout = 5000
        self.read_termination = '\n'
        self.write_termination = '\n'
        self._commands_sent = []
        self._queries_sent = []
        self._output_on = False  # Track output state internally for simulation
        
    def write(self, command):
        """Simulate write command."""
        self._commands_sent.append(command)
        # Track output state changes
        if command == "HVON":
            self._output_on = True
        elif command == "HVOF":
            self._output_on = False
        
    def query(self, command):
        """Simulate query with voltage-based output state."""
        self._queries_sent.append(command)
        
        # Return mock values for queries
        if command == "*IDN?":
            return "StanfordResearchSystems,PS310,2067,1.40"
        elif command == "VSET?":
            return "-100.0"
        elif command == "VOUT?":
            # Return non-zero voltage when output is on, zero when off
            if self._output_on:
                return "-99.5"
            else:
                return "0.0"
        elif command == "IOUT?":
            return "0.001" if self._output_on else "0.0"
        else:
            return "0"
    
    def close(self):
        """Simulate close."""
        pass


async def test_gui_connection_scenario():
    """Test the GUI connection scenario with voltage-based output state."""
    print("=" * 60)
    print("Integration Test: GUI Connection with Voltage-Based State")
    print("=" * 60)
    
    # Step 1: Create PS310 instance without auto-connect
    print("\n1. Creating PS310 instance...")
    with patch('pyvisa.ResourceManager') as mock_rm_class:
        # Setup mock ResourceManager
        mock_rm = MagicMock()
        mock_rm_class.return_value = mock_rm
        mock_rm.list_resources.return_value = ["GPIB0::14::INSTR"]
        
        # Create mock instrument
        mock_instrument = MockInstrument()
        mock_rm.open_resource.return_value = mock_instrument
        
        ps310 = StanfordPS310(auto_connect=False)
        print("   ✓ PS310 instance created")
        
        # Step 2: Connect to device (simulating GUI connect endpoint)
        print("\n2. Connecting to device at GPIB0::14::INSTR...")
        ps310.connect(address="GPIB0::14::INSTR")
        print("   ✓ Connected successfully")
        print(f"   - IDN: StanfordResearchSystems,PS310,2067,1.40")
        
        # Step 3: Query initial values (simulating GUI initial reads)
        print("\n3. Reading initial values...")
        
        # These should work fine
        set_voltage = ps310.get_voltage()
        print(f"   ✓ Set voltage: {set_voltage} V")
        
        actual_voltage = ps310.measure_voltage()
        print(f"   ✓ Actual voltage: {actual_voltage} V")
        
        current = ps310.measure_current()
        print(f"   ✓ Current: {current} A")
        
        # This should use voltage measurement and not raise exception
        try:
            output_state = ps310.get_output_state()
            print(f"   ✓ Output state: {output_state} (determined from voltage measurement)")
            print("   ✓ No exception raised - voltage-based detection working!")
        except Exception as e:
            print(f"   ✗ FAILED: get_output_state raised exception: {e}")
            return False
        
        # Step 4: Test that state tracking works after setting output
        print("\n4. Testing state tracking after set_output_state...")
        ps310.set_output_state(True)
        state_after_on = ps310.get_output_state()
        if state_after_on != True:
            print(f"   ✗ FAILED: Expected True, got {state_after_on}")
            return False
        print("   ✓ State correctly detected as True after HVON (voltage is non-zero)")
        
        ps310.set_output_state(False)
        state_after_off = ps310.get_output_state()
        if state_after_off != False:
            print(f"   ✗ FAILED: Expected False, got {state_after_off}")
            return False
        print("   ✓ State correctly detected as False after HVOF (voltage is zero)")
        
        # Step 5: Verify commands sent to device
        print("\n5. Verifying command sequence...")
        print(f"   - Total commands sent: {len(mock_instrument._commands_sent)}")
        print(f"   - Total queries sent: {len(mock_instrument._queries_sent)}")
        
        # Check that VOUT? was used for state detection (multiple times during get_output_state calls)
        vout_query_count = mock_instrument._queries_sent.count("VOUT?")
        print(f"   - VOUT? query attempts: {vout_query_count}")
        
        if vout_query_count == 0:
            print("   ✗ FAILED: VOUT? was never queried")
            return False
        print("   ✓ VOUT? was used for output state detection")
        
        # Check that HVON? was NOT attempted (since it's write-only)
        hvon_query_count = mock_instrument._queries_sent.count("HVON?")
        if hvon_query_count > 0:
            print(f"   ✗ FAILED: HVON? should not be queried (it's write-only), but was queried {hvon_query_count} times")
            return False
        print("   ✓ HVON? was not queried (correct, as it's write-only)")
        
        # Step 6: Test disconnect
        print("\n6. Testing disconnect...")
        ps310.disconnect()
        if ps310._output_state != False:
            print(f"   ✗ FAILED: State should be reset to False after disconnect, got {ps310._output_state}")
            return False
        print("   ✓ Disconnect successful, state reset")
        
        print("\n" + "=" * 60)
        print("✓ Integration test passed!")
        print("=" * 60)
        print("\nSummary:")
        print("  - Device connection works with voltage-based state detection")
        print("  - Initial value reads complete without errors")
        print("  - Output state detection via voltage measurement works correctly")
        print("  - State tracking accurately reflects actual output voltage")
        print("  - HVON? is not queried (correct behavior for write-only command)")
        return True


async def test_multiple_parallel_requests():
    """Test that multiple parallel requests don't cause issues."""
    print("\n" + "=" * 60)
    print("Integration Test: Parallel State Queries")
    print("=" * 60)
    
    with patch('pyvisa.ResourceManager') as mock_rm_class:
        # Setup mock
        mock_rm = MagicMock()
        mock_rm_class.return_value = mock_rm
        mock_rm.list_resources.return_value = ["GPIB0::14::INSTR"]
        mock_instrument = MockInstrument()
        mock_rm.open_resource.return_value = mock_instrument
        
        ps310 = StanfordPS310(auto_connect=False)
        ps310.connect(address="GPIB0::14::INSTR")
        
        # Set state to True
        ps310.set_output_state(True)
        
        print("\n1. Making 10 parallel calls to get_output_state...")
        # Make multiple parallel calls
        tasks = [asyncio.create_task(asyncio.to_thread(ps310.get_output_state)) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should return True (voltage-based detection)
        if all(r == True for r in results):
            print("   ✓ All 10 calls returned True (voltage-based state detection)")
        else:
            print(f"   ✗ FAILED: Got inconsistent results: {results}")
            return False
        
        # Change state and test again
        ps310.set_output_state(False)
        print("\n2. Making 10 parallel calls after setting state to False...")
        tasks = [asyncio.create_task(asyncio.to_thread(ps310.get_output_state)) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        if all(r == False for r in results):
            print("   ✓ All 10 calls returned False (voltage-based state detection)")
        else:
            print(f"   ✗ FAILED: Got inconsistent results: {results}")
            return False
        
        print("\n" + "=" * 60)
        print("✓ Parallel requests test passed!")
        print("=" * 60)
        return True


async def main():
    """Run all integration tests."""
    print("\n")
    print("🧪 Stanford PS310 GUI Connection Integration Tests")
    print()
    
    try:
        success = True
        
        # Test 1: GUI connection scenario
        success = await test_gui_connection_scenario() and success
        
        # Test 2: Parallel requests
        success = await test_multiple_parallel_requests() and success
        
        if success:
            print("\n✅ All integration tests passed!")
            print("\nConclusion:")
            print("  The HVON? timeout issue has been successfully fixed.")
            print("  The PS310 GUI desktop app should now connect without errors.")
            return 0
        else:
            print("\n❌ Some integration tests failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
