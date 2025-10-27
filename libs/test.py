

from KeysightMSOX4154A import KeysightMSOX4154A

# Take output dir as input argument
import sys
import os
output_dir = sys.argv[1] if len(sys.argv) > 1 else "."
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
os.chdir(output_dir)
print(f"Output directory: {os.getcwd()}")


# Create an instance of the KeysightMSOX4154A class
oscilloscope = KeysightMSOX4154A()
# Get a screenshot from the oscilloscope
screenshot_data = oscilloscope.get_screenshot()
# Save the screenshot to a file
# Create filename like screenshot_YYYYMMDD_HHMMSS.png
import datetime
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"screenshot_{timestamp}.png"
print(f"Saving screenshot to {filename}")

with open(filename, "wb") as f:
    f.write(screenshot_data)

# Disconnect from the oscilloscope
oscilloscope.disconnect()