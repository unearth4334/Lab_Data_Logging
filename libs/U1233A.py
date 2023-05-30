import serial
import statistics
import numpy
import serial.tools.list_ports
import os
try:
    from .loading import *
except:
    from loading import *

from colorama import init, Fore, Back, Style

# Constants and global variables
_MAX_FILENAMES = 100
_VALUE_PADDING = 40
_ERROR_STYLE = Fore.RED + Style.BRIGHT + "\rError! "
_SUCCESS_STYLE = Fore.GREEN + Style.BRIGHT + "\r"
_WARNING_STYLE = Fore.YELLOW + Style.BRIGHT + "\rWarning! "
_DELAY = 0.1
_CONNECTION_TIMEOUT = 1

class U1233A:
    def __init__(self,auto_connect=True, baud_rate=9600,com_port=None):

        init(autoreset=True)
        self.status = "Not Connected"
        self.ser = None
        self.identity = None
        self.loading = loading()

        if auto_connect:
            self.connect(baud_rate,baud_rate)

        if self.status == "Not Connected":
            self.com_port = self.select_com_port()
            if self.com_port is None:
                self.status = "Not Connected"
                error_message = "No COM port selected."
                raise ConnectionError(_ERROR_STYLE + error_message)
                return None
            

            try:
                self.ser = self.__select_com_port(baud_rate,com_port)
                self.status = "Connected"

            except:
                self.status = "Not Connected"
                error_message = "Failed to connect to U1233A on COM port %s." % (self.com_port)
                raise ConnectionError(_ERROR_STYLE + error_message)
                return None
        
    def connect(self,baud_rate=9600,com_port=None):

        try:
            if com_port is None:
                com_port = int(os.environ['U1233A_COM_PORT_ENV_VAR'])
            self.ser = serial.Serial(com_port,baud_rate,timeout=_CONNECTION_TIMEOUT)
            self.status = "Connected"
        except:
            ports = serial.tools.list_ports.comports()
            if not ports:
                error_message = "No COM ports found."
                raise ConnectionError(_ERROR_STYLE + error_message)

            print("Available COM ports:")
            for i, port in enumerate(ports, start=1):
                print(f"{i}. {port.device} - {port.description}")

            while True:
                try:
                    selection = int(input("Select a COM port (1, 2, ...): "))
                    if 1 <= selection <= len(ports):
                        com_port = ports[selection - 1].device
                        os.environ['U1233A_COM_PORT_ENV_VAR']= str(com_port)
                        break
                    else:
                        print(_ERROR_STYLE + "Error! Invalid selection.")
                except ValueError:
                    error_message = "Invalid input. Please enter a number."
                    print(_ERROR_STYLE + error_message)

            try:
                self.ser = serial.Serial(com_port,baud_rate,timeout=_CONNECTION_TIMEOUT)
                self.status = "Connected"
            except:
                error_message = f"Failed to connect to U1233A on COM port {com_port}."
                raise ConnectionError(_ERROR_STYLE + error_message)
            
        self.ser.write(str('*IDN?\n').encode('ascii'))
        self.loading.delay_with_loading_indicator(_DELAY)
        self.identity = self.ser.readline().decode('ascii').strip()
        if len(self.identity) < 5:
            error_message = f"Failed to connect to U1233A on COM port {com_port}. Check that the device is connected and powered on."
            raise ConnectionError(_ERROR_STYLE + error_message)
        print(_SUCCESS_STYLE + f"Connected to {self.identity} on COM port {com_port}.")
        return self.ser

    def get(self,item,channel=1):

        items = { "MEAS"    :self.measure,
                  "MEAS_AVG":self.measure_avg}

        result = items[item]()

        return result


    def measure(self):

        command = 'READ?\n'

        self.ser.write(str(command).encode('ascii'))
        self.loading.delay_with_loading_indicator(_DELAY)
        val = self.ser.readline()
        return (float(val),0)

    def measure_avg(self,n=50):

        val = numpy.zeros(n)
        for x in range(n):
            self.loading.delay_with_loading_indicator(_DELAY)
            temp = self.measure()
            val[x]=temp[0]

        return (statistics.fmean(val),statistics.stdev(val))

    def disconnect(self):
        if self.ser.isOpen():
            self.ser.close()
            print("Disconnected from {self.identity} on COM port {self.com_port}.")

# Test code
if __name__ == "__main__":
    multimeter = U1233A()
    print(f"Measurement: {multimeter.get('MEAS')}")
    print(f"Average measurement: {multimeter.get('MEAS_AVG')}")
    multimeter.disconnect()
