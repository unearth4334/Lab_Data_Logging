#!/usr/bin/env python3
"""
Test script for PS310 GUI queue timeout implementation.
Tests the queue timeout functionality without requiring actual hardware.
"""

import asyncio
import time
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Timing constants (matching main implementation)
_MIN_COMMAND_DELAY = 0.25  # 250ms minimum delay between PS310 commands
_QUEUE_TIMEOUT = 5.0  # 5 seconds - commands older than this are canceled


class CommandPriority(Enum):
    """Priority levels for command queue."""
    HIGH = 0    # Critical operations (disconnect, emergency stop)
    NORMAL = 1  # Regular operations (set voltage, etc.)
    LOW = 2     # Background polling


@dataclass
class QueuedCommand:
    """Represents a command to be executed on the PS310."""
    priority: CommandPriority
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    future: Optional[asyncio.Future] = None
    enqueue_time: float = 0.0  # Timestamp when command was added to queue
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.enqueue_time == 0.0:
            self.enqueue_time = time.time()
    
    def __lt__(self, other):
        """Enable priority queue ordering."""
        return self.priority.value < other.priority.value
    
    def is_expired(self, timeout: float = _QUEUE_TIMEOUT) -> bool:
        """Check if command has been in queue longer than timeout."""
        return (time.time() - self.enqueue_time) > timeout


# Global test state
command_queue: Optional[asyncio.PriorityQueue] = None
queue_processor_task: Optional[asyncio.Task] = None
queue_sequence_counter = 0
queue_sequence_lock: Optional[asyncio.Lock] = None
execution_times = []
timeout_count = 0


async def queue_command(func: Callable, *args, priority: CommandPriority = CommandPriority.NORMAL, **kwargs):
    """Add a command to the queue and wait for its result."""
    global command_queue, queue_sequence_counter, queue_sequence_lock
    
    if command_queue is None:
        raise RuntimeError("Command queue not initialized")
    
    # Create a future to get the result
    future = asyncio.Future()
    
    # Add sequence number to maintain FIFO within same priority (with thread safety)
    async with queue_sequence_lock:
        queue_sequence_counter += 1
        sequence = queue_sequence_counter
    
    command = QueuedCommand(priority=priority, func=func, args=args, kwargs=kwargs, future=future)
    await command_queue.put((priority.value, sequence, command))
    
    return await future


async def process_command_queue():
    """Process commands from the queue with proper delays and timeout checking."""
    global command_queue, execution_times, timeout_count
    
    print("✓ Command queue processor started")
    last_execution_time = 0
    
    while True:
        try:
            priority_val, sequence, command = await command_queue.get()
            
            # Check if command has expired (been in queue too long)
            if command.is_expired(_QUEUE_TIMEOUT):
                queue_age = time.time() - command.enqueue_time
                error_msg = f"Command timeout: queued for {queue_age:.1f}s (max {_QUEUE_TIMEOUT}s)"
                print(f"  ⏱️  {error_msg}")
                timeout_count += 1
                
                # Set exception in future to notify caller
                if command.future and not command.future.done():
                    command.future.set_exception(TimeoutError(error_msg))
                
                command_queue.task_done()
                continue  # Skip execution, move to next command
            
            # Ensure minimum delay between commands
            current_time = time.time()
            time_since_last = current_time - last_execution_time
            if time_since_last < _MIN_COMMAND_DELAY:
                delay_needed = _MIN_COMMAND_DELAY - time_since_last
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
async def slow_command(delay: float):
    """Mock slow command that takes time to execute."""
    await asyncio.sleep(delay)
    return f"Command completed after {delay}s"


def fast_command():
    """Mock fast command."""
    return "Fast command completed"


async def test_queue_timeout():
    """Test that commands expire after 5 seconds in queue."""
    print("\n=== Test 1: Queue Timeout After 5 Seconds ===")
    
    global timeout_count
    timeout_count = 0
    
    # Queue multiple slow commands that will block the queue for a long time
    print("  Queueing 3 slow blocking commands (3 seconds each)...")
    
    # Queue all tasks but wrap them to handle exceptions
    async def safe_queue_command(*args, **kwargs):
        try:
            return await queue_command(*args, **kwargs)
        except TimeoutError:
            # Silently handle timeout - we'll check timeout_count later
            return None
    
    task1 = asyncio.create_task(safe_queue_command(slow_command, 3, priority=CommandPriority.NORMAL))
    
    # Give it a moment to start
    await asyncio.sleep(0.1)
    
    task2 = asyncio.create_task(safe_queue_command(slow_command, 3, priority=CommandPriority.NORMAL))
    task3 = asyncio.create_task(safe_queue_command(slow_command, 3, priority=CommandPriority.NORMAL))
    
    # Queue several LOW priority commands that will wait in queue for 9+ seconds
    print("  Queueing 3 LOW priority commands that will wait in queue...")
    task4 = asyncio.create_task(safe_queue_command(fast_command, priority=CommandPriority.LOW))
    task5 = asyncio.create_task(safe_queue_command(fast_command, priority=CommandPriority.LOW))
    task6 = asyncio.create_task(safe_queue_command(fast_command, priority=CommandPriority.LOW))
    
    # Wait for all slow commands to finish (takes ~9 seconds + delays)
    print("  Waiting for slow commands to complete...")
    await task1
    print("  ✓ Slow command 1 completed")
    result2 = await task2
    if result2:
        print("  ✓ Slow command 2 completed")
    else:
        print("  ⏱️  Slow command 2 timed out")
    result3 = await task3
    if result3:
        print("  ✓ Slow command 3 completed")
    else:
        print("  ⏱️  Slow command 3 timed out")
    
    # Try to get results from LOW priority commands - should have timed out
    timed_out = 0
    for i, task in enumerate([task4, task5, task6], 4):
        result = await task
        if result is None:
            print(f"  ✓ Command {i} timed out as expected")
            timed_out += 1
        else:
            print(f"  Command {i} completed: {result}")
    
    print(f"  Total commands timed out: {timeout_count}")
    if timeout_count > 0:
        print("✓ Queue timeout working correctly")
    else:
        print("✗ No commands timed out - timeout mechanism not working")


async def test_fresh_commands_not_timeout():
    """Test that fresh commands (< 5 seconds in queue) do not timeout."""
    print("\n=== Test 2: Fresh Commands Do Not Timeout ===")
    
    global timeout_count
    timeout_count = 0
    
    # Queue several fast commands
    print("  Queueing 5 fast commands...")
    tasks = [
        asyncio.create_task(queue_command(fast_command, priority=CommandPriority.NORMAL))
        for _ in range(5)
    ]
    
    # All should complete without timeout
    for i, task in enumerate(tasks, 1):
        try:
            result = await task
            print(f"  ✓ Command {i} completed: {result}")
        except TimeoutError as e:
            print(f"  ✗ Command {i} unexpectedly timed out: {e}")
    
    if timeout_count == 0:
        print("✓ No fresh commands timed out (correct)")
    else:
        print(f"✗ {timeout_count} commands incorrectly timed out")


async def test_high_priority_bypass():
    """Test that HIGH priority commands can bypass queue."""
    print("\n=== Test 3: HIGH Priority Commands Bypass Queue ===")
    
    global timeout_count
    timeout_count = 0
    
    # Queue a slow blocking command
    print("  Queueing slow blocking command (2 seconds)...")
    task1 = asyncio.create_task(queue_command(slow_command, 2, priority=CommandPriority.NORMAL))
    
    # Give it a moment to start
    await asyncio.sleep(0.1)
    
    # Queue low priority commands
    print("  Queueing 3 LOW priority commands...")
    low_tasks = [
        asyncio.create_task(queue_command(fast_command, priority=CommandPriority.LOW))
        for _ in range(3)
    ]
    
    # Queue a HIGH priority command - should execute next after current command
    print("  Queueing 1 HIGH priority command...")
    high_task = asyncio.create_task(queue_command(fast_command, priority=CommandPriority.HIGH))
    
    # Wait for slow command to finish
    await task1
    
    # High priority should complete before low priority
    try:
        result = await high_task
        print(f"  ✓ HIGH priority command completed: {result}")
    except TimeoutError as e:
        print(f"  ✗ HIGH priority command timed out: {e}")
    
    # Wait a bit for low priority commands
    await asyncio.sleep(1)
    
    print("✓ Priority bypass test completed")


async def main():
    """Run all tests."""
    global command_queue, queue_processor_task, queue_sequence_lock
    
    print("=" * 70)
    print("Stanford PS310 GUI Queue Timeout Tests")
    print("=" * 70)
    
    # Initialize queue and lock
    command_queue = asyncio.PriorityQueue()
    queue_sequence_lock = asyncio.Lock()
    queue_processor_task = asyncio.create_task(process_command_queue())
    
    try:
        # Run tests
        await test_queue_timeout()
        await test_fresh_commands_not_timeout()
        await test_high_priority_bypass()
        
        print("\n" + "=" * 70)
        print("✓ All tests completed!")
        print("=" * 70)
        
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
