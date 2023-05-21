import pyvisa
import time

from colorama import init, Fore, Back

_delay = 0.01  # in seconds

class DP832:
    def __init__(self):

        color = init(autoreset=True)

        try:
            self.resources = pyvisa.ResourceManager()
            self.instrument_list = self.resources.list_resources()
            
            self.address = [elem for elem in self.instrument_list if (elem.find('DP8') != -1)]

            if self.address.__len__() == 0:
                self.status = "Not Connected"
                print(Fore.RED + "Error! PyVISA failed to connect to DP832...")
            else:
                self.address = self.address[0]
                self.device = self.resources.open_resource(self.address)
                self.status = "Connected"
                print(Fore.GREEN + "Connected to " + self.address)

        except VisaIOError:
            self.status = "Not Connected"
            print(Fore.RED + "Error! PyVISA is not able to find any devices")

    def get(self,item,channel=1):

        items = { "VOLT"    :self.measure_voltage,
                  "CURR"    :self.measure_current }

        result = items[item]()

        return (result,0)

    def select_output(self, chan):
        # define a CHANNEL SELECT function

        
        command = ':INST:NSEL %s' % chan
        self.device.write(command)
        time.sleep(_delay)

    def toggle_output(self, chan, state):
        # define a TOGGLE OUTPUT function
        if state == 1 or state == 'ON':
            print('\r' + Back.WHITE + Fore.BLACK +'Power Supply (DP832) Channel %d:\t'%(chan)\
                  + Back.GREEN + ' ON ' + Back.BLUE + Fore.WHITE + "  %.2f V | %.2f A   "\
                    %(self.get_voltage(chan),self.get_current(chan)))
            command = ':OUTP CH%s,%d' % (chan, 1)
        else:
            print('\r' + Back.WHITE + Fore.BLACK +'Power Supply (DP832) Channel %d:\t'%(chan)\
                  + Back.RED + ' OFF ')
            command = ':OUTP CH%s,%d' % (chan, 0)
        self.device.write(command)
        time.sleep(_delay)

    def set_voltage(self, chan, val):
        # define a SET VOLTAGE function
        command = ':INST:NSEL %s' % chan
        self.device.write(command)
        time.sleep(_delay)
        command = ':VOLT %s' % val
        self.device.write(command)
        time.sleep(_delay)

    def set_current(self, chan, val):
        # define a SET CURRENT function
        command = ':INST:NSEL %s' % chan
        self.device.write(command)
        time.sleep(_delay)
        command = ':CURR %s' % val
        self.device.write(command)
        time.sleep(_delay)

    def get_voltage(self, chan):
        command = ':INST:NSEL %s' % chan
        self.device.write(command)
        command = ':VOLT?'
        value = self.device.query(command)
        time.sleep(_delay)
        return float(value)

    def get_current(self, chan):
        command = ':INST:NSEL %s' % chan
        self.device.write(command)
        command = ':CURR?'
        value = self.device.query(command)
        time.sleep(_delay)
        return float(value)

    def set_ovp(self, chan, val):
        # define a SET VOLT PROTECTION function
        command = ':INST:NSEL %s' % chan
        self.device.write(command)
        time.sleep(_delay)
        command = ':VOLT:PROT %s' % val
        self.device.write(command)
        time.sleep(_delay)

    def toggle_ovp(self, state):
        # define a TOGGLE VOLTAGE PROTECTION function
        command = ':VOLT:PROT:STAT %s' % state
        self.device.write(command)
        time.sleep(_delay)

    def set_ocp(self, chan, val):
        # define a SET CURRENT PROTECTION function
        command = ':INST:NSEL %s' % chan
        self.device.write(command)
        time.sleep(_delay)
        command = ':CURR:PROT %s' % val
        self.device.write(command)
        time.sleep(_delay)

    def toggle_ocp(self, state):
        # define a TOGGLE CURRENT PROTECTION function
        command = ':CURR:PROT:STAT %s' % state
        self.device.write(command)
        time.sleep(_delay)

    def measure_voltage(self, chan = 1):
        # define a MEASURE VOLTAGE function
        command = ':MEAS:VOLT? CH%s' % chan
        volt = self.device.query(command)
        volt = float(volt)
        time.sleep(_delay)
        return volt

    def measure_current(self, chan = 1):
        # define a MEASURE CURRENT function
        command = ':MEAS:CURR? CH%s' % chan
        curr = self.device.query(command)
        curr = float(curr)
        time.sleep(_delay)
        return curr

    def measure_power(self, chan = 1):
        # define a MEASURE POWER function
        command = ':MEAS:POWE? CH%s' % chan
        power = self.device.query(command)
        power = float(power)
        time.sleep(_delay)
        return power


    def reset(self):
        return self.device.write("*RST")
