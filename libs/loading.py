"""
Terminal Loading Indicators and Progress Display Utilities
===========================================================

This module provides utilities for displaying loading indicators and progress bars
in terminal/console applications during long-running operations.

Features
--------
- **Loading Bar**: ASCII-based progress bar display
- **Loading Indicator**: Animated spinner/dots for indefinite operations
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Flashing Input**: Input prompt with blinking cursor effect
- **Customizable**: Configurable bar length and display text

Basic Usage
-----------
```python
from libs.loading import loading
import time

loader = loading()

# Display progress bar
for i in range(101):
    loader.display_loading_bar(i/100.0, loading_text="Processing")
    time.sleep(0.05)
print()  # New line after completion

# Delay with loading indicator
loader.delay_with_loading_indicator(3.0)  # 3 second delay with animation
```

Loading Bar with Progress
--------------------------
```python
loader = loading(bar_length=20)

total_items = 100
for i in range(total_items):
    # Process item
    process_item(i)
    
    # Update progress
    progress = (i + 1) / total_items
    loader.display_loading_bar(progress, loading_text="Processing items")
```

Delayed Operations with Indicator
----------------------------------
```python
# Show loading animation during delay
print("Connecting to device...")
loader.delay_with_loading_indicator(5.0, message="Waiting")

print("Measuring...")
loader.delay_with_loading_indicator(2.5)
```

Interactive Input with Flash
-----------------------------
```python
# Get user input with flashing prompt (Windows only)
response = loader.input_with_flashing()
print(f"User entered: {response}")

# Use standard input as fallback on non-Windows
if not HAS_MSVCRT:
    response = input("Enter value: ")
```

Device Driver Integration
-------------------------
```python
class MyDevice:
    def __init__(self):
        self.loading = loading()
    
    def connect(self):
        print("Connecting to device...")
        self.loading.delay_with_loading_indicator(3.0)
        print("Connected!")
    
    def calibrate(self):
        steps = 10
        for i in range(steps):
            # Calibration step
            self.loading.display_loading_bar(
                (i+1)/steps, 
                loading_text="Calibrating"
            )
            time.sleep(0.5)
        print()  # New line after completion
```

Available Methods
-----------------
Progress Display:
- `display_loading_bar(percent, overwrite, loading_text)` - Show progress bar
- `delay_with_loading_indicator(seconds, message)` - Animated delay

User Input:
- `input_with_flashing()` - Get input with flashing cursor (Windows)

Constructor:
- `__init__(bar_length)` - Initialize with custom bar length

Platform Notes
--------------
**Windows**: Full feature support including flashing input cursor
**Linux/macOS**: Loading bars and delays work, flashing input falls back to standard input

The module automatically detects platform capabilities and provides appropriate
fallback behavior.

Usage in Device Drivers
------------------------
Most device drivers in the libs/ directory use this module for user feedback:

```python
# Common pattern in device drivers
try:
    from .loading import loading
except:
    from loading import loading

class DeviceDriver:
    def __init__(self):
        self.loading = loading()
    
    def long_operation(self):
        self.loading.delay_with_loading_indicator(5.0)
```

See Also
--------
- Device drivers: All libs/*.py files use this module
- data_logger: Uses loading indicators for file operations
"""

import time
import sys
import ctypes
import threading

# Windows-only imports with fallback
try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

class loading:
#   """
#   A class that provides methods for displaying a loading bar and delaying execution with a loading indicator.
#   """

    def __init__(self, bar_length=10):
#       """
#       Initialize the Loading object.
#
#       Args:
#           bar_length (int, optional): The length of the loading bar. Defaults to 10.
#       """
        self.bar_length = bar_length
        self._spinner_thread = None
        self._spinner_stop = False


    def display_loading_bar(self, percent, overwrite=True, loading_text="Loading"):
#       """
#       Display an ASCII loading bar based on the given completion percentage.
#
#       Args:
#           percent (float): The completion percentage, ranging from 0 to 1.
#           overwrite (bool, optional): If True, the loading bar overwrites the previous one. 
#               Defaults to True.
#           loading_text (str, optional): The text to display before the loading bar.
#               Defaults to "Loading".
#
#       Returns:
#           None
#
#       Example:
#           >>> from lab_data_logging.libs.loading import loading
#           >>> loader = loading()
#           >>> loader.display_loading_bar(0.0, overwrite=True)
#           Loading: [----------]  0%
#           >>> loader.display_loading_bar(0.0, overwrite=True, loading_text="Please wait")
#           Please wait: [----------]  0%
#       """
        bar_length = 10  # Length of the loading bar
        filled_length = int(percent * bar_length)
        empty_length = bar_length - filled_length
        
        bar = '[' + '#' * filled_length + '-' * empty_length + ']'
        percent_display = f"{int(percent * 100):2d}%"  # Format the percentage value
        
        loading_bar = f"{loading_text}: {bar} {percent_display}"
        
        if overwrite:
            print(loading_bar, end='\r')
        else:
            print(loading_bar)



    def delay_with_loading_bar(self, seconds, loading_text="Loading"):
#       """
#       Delay the execution for the specified number of seconds while displaying a loading bar.
#
#       Args:
#           seconds (float): The number of seconds to delay.
#           loading_text (str, optional): The text to display before the loading bar.
#               Defaults to "Loading".
#
#       Returns:
#           None
#
#       Example:
#           >>> from lab_data_logging.libs.loading import loading
#           >>> loader = loading()
#           >>> loader.delay_with_loading_bar(3, loading_text="Waiting")
#           Waiting: [###-------]  30%
#           Waiting: [#######---]  70%
#           Waiting: [##########] 100%
#       """
        start_time = time.time()  # Get the starting time
        
        while True:
            elapsed_time = time.time() - start_time  # Calculate the elapsed time
            
            if elapsed_time >= seconds:
                break  # Exit the loop if the desired time delay has passed
            
            percent = elapsed_time / seconds
            self.display_loading_bar(percent, overwrite=True, loading_text=loading_text)
            
            time.sleep(0.1)  # Wait for a short period before updating the loading bar

        self.display_loading_bar(1.0, overwrite=True, loading_text=loading_text)  # Display the loading bar at 100%



    def delay_with_loading_indicator(self, seconds):
#       """
#       Delay the execution for the specified number of seconds while displaying a loading indicator.
#
#       Args:
#           seconds (float): The number of seconds to delay.
#
#       Returns:
#           None
#
#       Example:
#           >>> from lab_data_logging.libs.loading import loading
#           >>> loader = loading()
#           >>> loader.delay_with_loading_indicator(5)
#       """
        symbols = ['|', '/', '-', '\\']  # List of loading symbols
        start_time = time.time()  # Get the starting time
        
        while True:
            elapsed_time = time.time() - start_time  # Calculate the elapsed time
            
            if elapsed_time >= seconds:
                break  # Exit the loop if the desired time delay has passed
            
            # Display the loading symbol
            symbol_index = int(time.time()*10) % 4
            sys.stdout.write('\b' + symbols[symbol_index])
            sys.stdout.flush()
            
            time.sleep(0.1)  # Wait for a short period before displaying the next symbol

        sys.stdout.write('\b ')  # Clear the loading symbol
        sys.stdout.flush()

    def input_with_flashing(self, input_prompt=""):

        print(input_prompt)

        if HAS_MSVCRT:
            # Windows-specific flashing behavior
            while True:
                if msvcrt.kbhit():
                    break
                try:
                    ctypes.windll.user32.FlashWindow(ctypes.windll.kernel32.GetConsoleWindow(), True)
                except:
                    pass  # Gracefully handle if windll is not available
                time.sleep(0.5)  # Adjust the delay as needed
            return input()
        else:
            # Non-Windows: simple input without flashing
            return input()

    def _spinner_worker(self, message):
        """Worker thread for the spinner animation."""
        # Braille block patterns for smooth spinner animation
        braille_patterns = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        idx = 0
        while not self._spinner_stop:
            sys.stdout.write(f'\r{message} {braille_patterns[idx % len(braille_patterns)]} ')
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)
        # Clear the spinner line
        sys.stdout.write('\r' + ' ' * (len(message) + 3) + '\r')
        sys.stdout.flush()

    def start_spinner(self, message="Processing"):
        """
        Start an animated spinner in a background thread.
        
        Args:
            message (str): The message to display alongside the spinner.
        
        Example:
            >>> loader = loading()
            >>> loader.start_spinner("Searching for device")
            >>> # Do some work...
            >>> loader.stop_spinner()
        """
        if self._spinner_thread and self._spinner_thread.is_alive():
            return  # Already running
        
        self._spinner_stop = False
        self._spinner_thread = threading.Thread(target=self._spinner_worker, args=(message,), daemon=True)
        self._spinner_thread.start()

    def stop_spinner(self):
        """
        Stop the animated spinner.
        
        Example:
            >>> loader = loading()
            >>> loader.start_spinner("Processing")
            >>> time.sleep(2)
            >>> loader.stop_spinner()
            >>> print("Done!")
        """
        if self._spinner_thread and self._spinner_thread.is_alive():
            self._spinner_stop = True
            self._spinner_thread.join(timeout=0.5)
            self._spinner_thread = None

    def example_usage(self):
#       """
#       An example usage of the Loading class.
#       """
        total_increments = 100
        
        for i in range(total_increments + 1):
            percent = i / total_increments
            self.display_loading_bar(percent, overwrite=True)
            time.sleep(0.1)
        print("\nLoading complete!")

        self.delay_with_loading_indicator(5)
        print("Time delay complete!")