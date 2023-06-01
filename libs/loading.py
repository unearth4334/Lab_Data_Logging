import time
import sys
import ctypes
import msvcrt

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

    def input_with_flashing(self, input_prompt):

        print(input_prompt)

        while True:

            if msvcrt.kbhit():
                break
            ctypes.windll.user32.FlashWindow(ctypes.windll.kernel32.GetConsoleWindow(), True )
            time.sleep(0.5)  # Adjust the delay as needed

        return input()

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