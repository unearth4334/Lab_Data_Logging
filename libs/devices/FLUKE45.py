import serial
import time
import statistics
import numpy

from colorama import init, Fore

_delay = 0.01  # in seconds
debug = 0      # disable/enable prints

class FLUKE45:
    def __init__(self,com_port='COM7',baud_rate=9600):

        color = init(autoreset=True)

        try:
            self.ser = serial.Serial(com_port,baud_rate)
            self.status = "Connected"
            self.ser.write(str('*IDN?\n').encode('ascii'))
            time.sleep(_delay)
            self.ser.readline()
            self.identity = self.ser.readline()
            self.identity = '%s' % (self.identity)
            self.identity = self.identity[2:(len(self.identity)-3)]
            print(Fore.GREEN + 'Connected to %s' % (self.identity))

        except:
            self.status = "Not Connected"
            print(Fore.RED + "Error! Serial Failed to Connect to FLUKE45...")



    def meas(self):
        if debug:
            print("MEAS?")
        command = 'MEAS?\n'

        self.ser.write(str(command).encode('ascii'))
        time.sleep(_delay)
        self.ser.readline()
        self.ser.readline()
        val = self.ser.readline()
        val = '%s' % (val)
        val = val[2:(len(val)-3)]
        return float(val)

    def measure_avg(self,n):

        val = numpy.zeros(n)
        for x in range(n):
            time.sleep(_delay)
            val[x]=self.measure()

        return (statistics.fmean(val),statistics.stdev(val))

    def disconnect(self):
        if self.ser.isOpen():
            self.ser.close()
            print("Disconnected from Fluke45")
