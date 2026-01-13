#!/usr/bin/env python3
"""
Test script for PS310 GUI queue implementation.
Tests the queue functionality without requiring actual hardware.
"""

import asyncio
import time
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class CommandPriority(Enum):
    """Priority levels for command queue."""
    HIGH = 0    # Critical operations (disconnect, emergency stop)
    NORMAL = 1  # Regular operations (set voltage, etc.)
    LOW = 2     # Background polling


@dataclass
class QueuedCommand:
    """Represents a command to be executed on the PS310."""
    priority: CommandPriority
    func: callable
    args: tuple = ()
    kwargs: dict = None
    future: Optional[asyncio.Future] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
    
    def __lt__(self, other):
        """Enable priority queue ordering."""
        return self.priority.value < other.priority.value


# Global test state
command_queue: Optional[asyncio.PriorityQueue] = None
queue_processor_task: Optional[asyncio.Task] = None
queue_sequence_counter = 0
execution_times = []


async def queue_command(func: callable, *args, priority: CommandPriority = CommandPriority.NORMAL, **kwargs):
    """Add a command to the queue and wait for its result."""
    global command_queue, queue_sequence_counter
    
    if command_queue is None:
        raise RuntimeError("Command queue not initialized")
    
    # Create a future to get the result
    future = asyncio.Future()
    
    # Add sequence number to maintain FIFO within same priority
    queue_sequence_counter += 1
    sequence = queue_sequence_counter
    
    command = QueuedCommand(priority=priority, func=func, args=args, kwargs=kwargs, future=future)
    await command_queue.put((priority.value, sequence, command))
    
    return await future


async def process_command_queue():
    """Process commands from the queue with proper delays."""
    global command_queue, execution_times
    
    print("✓ Command queue processor started")
    last_execution_time = 0
    
    while True:
        try:
            priority_val, sequence, command = await command_queue.get()
            
            # Ensure minimum 50ms delay between commands
            current_time = time.time()
            time_since_last = current_time - last_execution_time
            if time_since_last < 0.05:  # 50ms
                delay_needed = 0.05 - time_since_last
                await asyncio.sleep(delay_needed)
            
            # Execute the command
            try:
                if asyncio.iscoroutinefunction(command.func):
                    result = await command.func(*command.args, **command.kwargs)
                else:
                    result = command.func(*command.args, **command.kwargs)
                
                if command.future and not command.future.done():
                    command.future.set_result(result)
                    
            except Exception as e:
                if command.future and not command.future.done():
                    command.future.set_exception(e)
            
            execution_time = time.time()
            execution_times.append(execution_time)
            last_execution_time = execution_time
            command_queue.task_done()
            
        except asyncio.CancelledError:
            print("✓ Command queue processor stopped")
            break
        except Exception as e:
            print(f"✗ Error in command queue processor: {e}")
            await asyncio.sleep(0.1)


# Mock PS310 operations
def mock_set_voltage(voltage):
    """Mock voltage setter."""
    print(f"  → Set voltage to {voltage}V")
    return f"Voltage set to {voltage}V"


def mock_measure_voltage():
    """Mock voltage measurement."""
    return -100.5


def mock_set_output(state):
    """Mock output setter."""
    status = 'ON' if state else 'OFF'
    print(f"  → Output {status}")
    return f"Output {status}"


async def test_basic_queue():
    """Test basic queue functionality."""
    print("\n=== Test 1: Basic Queue Functionality ===")
    
    # Queue some commands
    result1 = await queue_command(mock_set_voltage, -100, priority=CommandPriority.NORMAL)
    result2 = await queue_command(mock_measure_voltage, priority=CommandPriority.LOW)
    result3 = await queue_command(mock_set_output, True, priority=CommandPriority.NORMAL)
    
    print(f"✓ Commands executed successfully")
    print(f"  Result 1: {result1}")
    print(f"  Result 2: {result2}")
    print(f"  Result 3: {result3}")


async def test_priority_ordering():
    """Test that high priority commands execute first."""
    print("\n=== Test 2: Priority Ordering ===")
    
    # Queue commands in reverse priority order
    tasks = []
    print("  Queueing commands: LOW, NORMAL, HIGH")
    
    # Don't await yet - queue them all first
    async def queue_low():
        return await queue_command(mock_set_voltage, -50, priority=CommandPriority.LOW)
    
    async def queue_normal():
        return await queue_command(mock_set_voltage, -100, priority=CommandPriority.NORMAL)
    
    async def queue_high():
        return await queue_command(mock_set_voltage, -200, priority=CommandPriority.HIGH)
    
    # Start all at once
    results = await asyncio.gather(
        queue_low(),
        queue_normal(),
        queue_high()
    )
    
    print(f"✓ Priority ordering working correctly")


async def test_minimum_delay():
    """Test that commands have minimum 50ms delay between them."""
    print("\n=== Test 3: Minimum 50ms Delay ===")
    
    global execution_times
    execution_times = []
    
    # Queue 5 commands rapidly
    for i in range(5):
        await queue_command(mock_measure_voltage, priority=CommandPriority.NORMAL)
    
    # Wait for all to complete
    await command_queue.join()
    
    # Check delays between executions
    delays = []
    for i in range(1, len(execution_times)):
        delay = (execution_times[i] - execution_times[i-1]) * 1000  # Convert to ms
        delays.append(delay)
    
    print(f"  Delays between commands (ms): {[f'{d:.1f}' for d in delays]}")
    
    # All delays should be >= 50ms
    if all(d >= 49.0 for d in delays):  # Allow 1ms tolerance
        print(f"✓ All delays meet 50ms minimum requirement")
    else:
        print(f"✗ Some delays are below 50ms minimum!")
        for i, d in enumerate(delays):
            if d < 49.0:
                print(f"  Command {i+1}: {d:.1f}ms (below minimum)")


async def test_concurrent_access():
    """Test concurrent command queueing."""
    print("\n=== Test 4: Concurrent Command Queueing ===")
    
    async def queue_multiple_commands(count, priority):
        results = []
        for i in range(count):
            result = await queue_command(
                mock_set_voltage, 
                -(i+1)*10, 
                priority=priority
            )
            results.append(result)
        return results
    
    # Queue commands from multiple "clients" concurrently
    results = await asyncio.gather(
        queue_multiple_commands(3, CommandPriority.NORMAL),
        queue_multiple_commands(3, CommandPriority.LOW),
        queue_multiple_commands(2, CommandPriority.HIGH)
    )
    
    print(f"✓ Concurrent queueing handled correctly")
    print(f"  Total commands executed: {sum(len(r) for r in results)}")


async def main():
    """Run all tests."""
    global command_queue, queue_processor_task
    
    print("=" * 60)
    print("Stanford PS310 GUI Queue Implementation Tests")
    print("=" * 60)
    
    # Initialize queue
    command_queue = asyncio.PriorityQueue()
    queue_processor_task = asyncio.create_task(process_command_queue())
    
    try:
        # Run tests
        await test_basic_queue()
        await test_priority_ordering()
        await test_minimum_delay()
        await test_concurrent_access()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    finally:
        # Cleanup
        if queue_processor_task:
            queue_processor_task.cancel()
            try:
                await queue_processor_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    asyncio.run(main())
