import serial
import time
import statistics
import numpy

from colorama import init, Fore

_delay = 0.01  # in seconds
debug = 0      # disable/enable prints


temperatures = [150, 140, 130, 120, 110, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0, -10, -20, -30, -40, -50, -55]
voltages = [302.785, 358.164, 412.739, 466.76, 520.551, 574.117, 627.49, 680.654, 733.608, 786.36, 838.882, 891.178, 943.227, 995.05, 1046.647, 1097.987, 1149.07, 1199.884, 1250.398, 1300.593, 1350.441, 1375.219]

class EPS:
    def __init__(self,com_port='COM16',baud_rate=9600):

        color = init(autoreset=True)


        try:
            self.ser = serial.Serial(com_port,baud_rate,timeout=1)
            self.status = "Connected"
            self.ser.write(str('READ(IDN)\r').encode('ascii'))
            time.sleep(_delay)
            self.identity = self.ser.readline()
            self.identity = self.ser.readline()
            self.identity = self.identity[0:(len(self.identity))-2]
            self.identity = 'Hercules MCU, Device ID: %s' % (self.identity)
            print(Fore.GREEN + 'Connected to %s' % (self.identity))

        except:
            self.status = "Not Connected"
            print(Fore.RED + "Error! Serial Failed to Connect to EPS...")

    def get(self,item,channel=1):

        items = { "READ_TIME"    :self.read_time,
                  "READ_TEMP1":self.read_temp1,
                  "READ_HEATER1":self.read_heater1}

        result = items[item]()

        return result


    def read_time(self):
        if debug:
            print("READ(TIME)")
        command = 'READ(TIME)\r'

        self.ser.write(str(command).encode('ascii'))
        time.sleep(_delay)
        val = self.ser.readline()
        val = self.ser.readline()
        return (float(val[0:(len(val))-2])/1000,0)

    def read_temp1(self):
        if debug:
            print("READ(TEMP1)")
        command = 'READ(TEMP1)\r'

        self.ser.write(str(command).encode('ascii'))
        time.sleep(_delay)
        val = self.ser.readline()
        val = self.ser.readline()
        print(val)
        #return (numpy.interp(1600*float(val[0:(len(val))-2])/0xFFF,voltages,temperatures),0)
        return(1,0)
    
    def read_heater1(self):
        if debug:
            print("READ(HEATER1)")
        command = 'READ(HEATER1)\r'

        self.ser.write(str(command).encode('ascii'))
        time.sleep(_delay)
        val = self.ser.readline()
        val = self.ser.readline()
        return (float(val[0:(len(val))-2]),0)
    
    def heater_on(self):
        if debug:
            print('WRITE(HEATER1,ON)')
        command = 'WRITE(HEATER1,ON)\r'
        self.ser.write(str(command).encode('ascii'))
        time.sleep(_delay)
        val = self.ser.readline()
        val = self.ser.readline()

    def heater_off(self):
        if debug:
            print('WRITE(HEATER1,OFF)')
        command = 'WRITE(HEATER1,OFF)\r'
        self.ser.write(str(command).encode('ascii'))
        time.sleep(_delay)
        val = self.ser.readline()
        val = self.ser.readline()


    def disconnect(self):
        if self.ser.isOpen():
            self.ser.close()
            print("Disconnected from Hercules!")
