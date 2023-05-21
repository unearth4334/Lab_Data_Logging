import serial
import time

from colorama import init, Fore

_delay = 0.2  # in seconds

class KA3010P:
    def __init__(self,com_port='COM19',baud_rate=9600):

        color = init(autoreset=True)

        try:
            self.ser = serial.Serial(com_port,baud_rate)
            self.status = "Connected"
            self.ser.write(str('*IDN?\n').encode('ascii'))
            time.sleep(_delay)
            self.identity = self.ser.readline()
            self.identity = '%s' % (self.identity)
            self.identity = self.identity[2:(len(self.identity)-3)]
            print(Fore.GREEN + 'Connected to %s' % (self.identity))

        except:
            self.status = "Not Connected"
            print(Fore.RED + "Error! Serial failed to connect to KA3010P...")

    def get(self,item,channel=1):

        items = { "CURR"    :self.measure_current,
                  "VOLT"    :self.measure_voltage }

        result = items[item]()

        return result

    def set_voltage(self, val):
        # define a SET VOLTAGE function
        time.sleep(_delay)
        command = 'VSET1:%s' % val
        self.ser.write(str(command).encode('ascii'))

    def set_current(self, val):
        # define a SET CURRENT function
        time.sleep(_delay)
        command = 'ISET1:%s' % val
        self.ser.write(str(command).encode('ascii'))

    def get_voltage(self):
        # define a GET VOLTAGE function
        command = 'VSET1?'
        self.ser.write(str(command).encode('ascii'))
        time.sleep(_delay)
        val = self.ser.read(self.ser.in_waiting)
        val = '%s' % (val)
        val = val[2:(len(val)-1)]
        val = float(val)
        return val

    def get_current(self):
        # define a GET CURRENT function
        command = 'ISET1?'
        self.ser.write(str(command).encode('ascii'))
        time.sleep(_delay)
        val = self.ser.read(self.ser.in_waiting)
        val = '%s' % (val)
        val = val[2:(len(val)-1)]
        val = float(val)
        return val
    
    def measure_voltage(self):
        # define a MEASURE VOLTAGE function
        command = 'VOUT1?'
        self.ser.write(str(command).encode('ascii'))
        time.sleep(_delay)
        val = self.ser.read(self.ser.in_waiting)
        val = '%s' % (val)
        val = val[2:(len(val)-1)]
        val = float(val)
        return (val,0)

    def measure_current(self):
        # define a MEASURE CURRENT function
        command = 'IOUT1?'
        self.ser.write(str(command).encode('ascii'))
        time.sleep(_delay)
        val = self.ser.read(self.ser.in_waiting)
        val = '%s' % (val)
        val = val[2:(len(val)-1)]
        val = float(val)
        return (val,0)

    def turn_on(self):
        # define a TURN ON function
        time.sleep(_delay)
        command = 'OUT1'
        self.ser.write(str(command).encode('ascii'))

    def turn_off(self):
        # define a TURN OFF function
        time.sleep(_delay)
        command = 'OUT0'
        self.ser.write(str(command).encode('ascii'))
        
