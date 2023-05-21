import serial
import time
import statistics
import numpy

from colorama import init, Fore

_delay = 0.01  # in seconds
debug = 0      # disable/enable prints

class U1233A:
    def __init__(self,com_port='COM23',baud_rate=9600):

        color = init(autoreset=True)

        try:
            self.ser = serial.Serial(com_port,baud_rate,timeout=1)
            self.status = "Connected"
            self.ser.write(str('*IDN?\n').encode('ascii'))
            time.sleep(_delay)
            self.identity = self.ser.readline()
            self.identity = '%s' % (self.identity)
            self.identity = self.identity[2:(len(self.identity)-5)]
            print(Fore.GREEN + 'Connected to %s' % (self.identity))

        except:
            self.status = "Not Connected"
            print(Fore.RED + "Error! Serial Failed to Connect to U1233A...")

    def get(self,item,channel=1):

        items = { "MEAS"    :self.measure,
                  "MEAS_AVG":self.measure_avg}

        result = items[item]()

        return result


    def measure(self):
        if debug:
            print("READ?")
        command = 'READ?\n'

        self.ser.write(str(command).encode('ascii'))
        time.sleep(_delay)
        val = self.ser.readline()
        return (float(val),0)

    def measure_avg(self,n=50):

        val = numpy.zeros(n)
        for x in range(n):
            time.sleep(_delay)
            temp = self.measure()
            val[x]=temp[0]

        return (statistics.fmean(val),statistics.stdev(val))

    def disconnect(self):
        if self.ser.isOpen():
            self.ser.close()
            print("Disconnected from Fluke45")
