import serial
import time

from colorama import init, Fore

_delay = 1  # in seconds

class DAC:
    def __init__(self):

        color = init(autoreset=True)

        try:
            self.ser = serial.Serial(port='COM10',baudrate=115200,timeout=.1)
            time.sleep(3)
            self.status = "Connected"
            
            print(Fore.GREEN + 'Connected to DAC and INA226 through Arduino on COM10')

        except:
            self.status = "Not Connected"
            print(Fore.RED + "Error! Failed to connect to DAC and INA226 through Arduino on COM10")

    def set_value(self, item, val):
        # define a SET VOLTAGE function
        command = 'SET:%s=%d\n' % (item,val)
        self.ser.write(bytes(command,'utf-8'))
        time.sleep(_delay)
        

    def get(self,item,channel=1):

        items = { "DACA"    :self.meas,
                  "DACB"    :self.meas,
                  "DACC"    :self.meas,
                  "DACD"    :self.meas,
                  "VOLT"    :self.meas,
                  "CURR"    :self.meas }

        item_x = item

        result = items[item](item_x)

        return result

    def meas(self,item):

        command = 'MEAS:%s?\n' % (item)

        self.ser.write(bytes(command,'utf-8'))
        time.sleep(_delay)
        val = self.ser.readline()
        val = val[0:(len(val)-2)]
        val = float(val)
        return (val,0)