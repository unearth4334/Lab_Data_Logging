import pyvisa

# Create a ResourceManager instance
rm = pyvisa.ResourceManager()

# List all available resources
print("Available VISA resources:")
print(rm.list_resources())   
