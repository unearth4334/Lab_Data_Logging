import pyvisa
import statistics
import numpy
try:
    from .loading import *
except:
    from loading import *

from colorama import init, Fore, Back

_DELAY = 0.05

resources = pyvisa.ResourceManager()

class DL3021:
    def __init__(self):

        color = init(autoreset=True)
        self.loading = loading()

        try:
            self.resources = pyvisa.ResourceManager()
            self.instrument_list = self.resources.list_resources()
            
            self.address = [elem for elem in self.instrument_list if (elem.find('DL3') != -1)]

            if self.address.__len__() == 0:
                self.status = "Not Connected"
                print(Fore.RED + "Error! PyVISA failed to connect to DL3021...")
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
                  "CURR"    :self.measure_current,
                  "VOLT_AVG":self.measure_volt_avg,
                  "CURR_AVG":self.measure_current_avg }

        result = items[item]()

        isAvg = item.find('_AVG')

        if isAvg > 0:
            return result

        else:
            return (result,0)
        

    def measure_voltage(self):
        # define a MEASURE VOLTAGE function
        command = ':MEAS:VOLT?'
        volt = self.device.query(command)
        volt = float(volt)
        self.loading.delay_with_loading_indicator(_DELAY)
        return volt

    def measure_current(self):
        # define a MEASURE CURRENT function
        command = ':MEAS:CURR?'
        curr = self.device.query(command)
        curr = float(curr)
        self.loading.delay_with_loading_indicator(_DELAY)
        return curr

    def measure_power(self):
        # define a MEASURE POWER function
        command = ':MEAS:POW?'
        power = self.device.query(command)
        power = float(power)
        self.loading.delay_with_loading_indicator(_DELAY)
        return power

    def measure_resistance(self):
        # define a MEASURE RESISTANCE function
        command = ':MEAS:RES?'
        res = self.device.query(command)
        res = float(res)
        self.loading.delay_with_loading_indicator(_DELAY)
        return res

    def set_slew_rate(self, val):
        # define a SET SLEW RATE function
        command = ':SOURCE:CURRENT:SLEW %s' % val
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def is_enabled(self):
        # define a IS ENABLED function
        command = ':SOURCE:INPUT:STAT?'
        enabled = self.device.query(command)
        self.loading.delay_with_loading_indicator(_DELAY)
        return enabled

    def enable(self):
        # define a ENABLE function
        mode = self.query_mode()
        if mode == 'CC':
            modeString = ' %s MODE | %.2f A   '%(mode,self.get_cc_current())
        elif mode == 'CR':
            modeString = ' %s MODE | %.2f OHM '%(mode,self.set_cr_resistance())
        elif mode == 'CV':
            modeString = ' %s MODE | %.2f V   '%(mode,self.set_cv_voltage())
        elif mode == 'CP':
            modeString = ' %s MODE | %.2f W   '%(mode,self.set_cp_power())
        print(Back.WHITE + Fore.BLACK +'\rProgrammable Load (DL3021):\t'\
             + Back.GREEN + ' ON ' + Back.BLUE + Fore.WHITE + "%s"%modeString)
        command = ':SOURCE:INPUT:STAT ON'
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def disable(self):
        # define a DISABLE function
        print(Back.WHITE + Fore.BLACK +'\rProgrammable Load (DL3021):\t' + Back.RED + ' OFF ')
        command = ':SOURCE:INPUT:STAT OFF'
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def input_status(self):
        # define a DISABLE function
        command = ':SOURCE:INPUT:STAT?'
        result = self.device.query(command)
        self.loading.delay_with_loading_indicator(_DELAY)
        mode = self.query_mode()

        print(Back.WHITE + Fore.BLACK +'\rProgrammable Load (DL3021):\t', end = '')
        if result == 0:
            print(Back.RED + ' OFF ', end = '')
        else:
            print(Back.GREEN + ' ON ', end = '')
        if mode == 'CC':
            modeString = ' %s MODE | %.2f A   '%(mode,self.get_cc_current())
        elif mode == 'CR':
            modeString = ' %s MODE | %.2f OHM '%(mode,self.set_cr_resistance())
        elif mode == 'CV':
            modeString = ' %s MODE | %.2f V   '%(mode,self.set_cv_voltage())
        elif mode == 'CP':
            modeString = ' %s MODE | %.2f W   '%(mode,self.set_cp_power())
        print(Back.BLUE + Fore.WHITE + "%s"%modeString)
        
        return result[0:(len(result)-1)]

    def select_mode(self, mode):
        # define a SELECT MODE function (CURR, RES, VOLT, POW)
        command = ':SOURCE:FUNCTION %s' % mode
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def query_mode(self):
        # define a QUERY MODE function
        command = ':SOURCE:FUNCTION?'
        mode = self.device.query(command)
        self.loading.delay_with_loading_indicator(_DELAY)
        return mode[0:(len(mode)-1)]

    def set_cc_current(self, val):
        # define a SET CC CURRENT function
        command = ':SOURCE:CURRENT:LEV:IMM %s' % val
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def set_cr_resistance(self, val):
        # define a SET CR RESISTANCE function
        command = ':SOURCE:RES:LEV:IMM %s' % val
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)        

    def set_cp_power(self, val):
        # define a SET CP POWER function
        command = ':SOURCE:POWER:LEV:IMM %s' % val
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def set_cv_voltage(self, val):
        # define a SET CV VOLTAGE function
        command = ':SOURCE:VOLT:LEV:IMM %s' % val
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def set_cp_ilim(self, val):
        # define a SET CP CURRENT LIMIT function
        command = ':SOURCE:POWER:ILIM %s' % val
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def get_cc_current(self):
        # define a SET CC CURRENT function
        command = ':SOURCE:CURRENT:LEV:IMM?'
        value = self.device.query(command)
        self.loading.delay_with_loading_indicator(_DELAY)
        return float(value)
    
    def get_cr_resistance(self):
        # define a SET CR RESISTANCE function
        command = ':SOURCE:RES:LEV:IMM?'
        value = self.device.query(command)
        self.loading.delay_with_loading_indicator(_DELAY)
        return float(value)

    def get_cp_power(self):
        # define a SET CP POWER function
        command = ':SOURCE:POWER:LEV:IMM?'
        value = self.device.query(command)
        self.loading.delay_with_loading_indicator(_DELAY)
        return float(value)

    def get_cv_voltage(self):
        # define a SET CV VOLTAGE function
        command = ':SOURCE:VOLT:LEV:IMM?'
        value = self.device.query(command)
        self.loading.delay_with_loading_indicator(_DELAY)
        return float(value)

    def measure_current_avg(self,n=50):

        val = numpy.zeros(n)
        for x in range(n):
            self.loading.display_loading_bar(x/n,loading_text="Averaging measurements from DL3021 Load")
            self.loading.delay_with_loading_indicator(_DELAY)
            val[x]=self.measure_current()

        return (statistics.fmean(val),statistics.stdev(val))

    def measure_volt_avg(self,n=10):

        val = numpy.zeros(n)
        for x in range(n):
            self.loading.display_loading_bar(x/n,loading_text="Averaging measurements from DL3021 Load")
            self.loading.delay_with_loading_indicator(_DELAY)
            val[x]=self.measure_voltage()

        return (statistics.fmean(val),statistics.stdev(val))
    
    def configure_output_sense(self, val = True):
        # define a CHANNEL SELECT function
        if val == True:
            command = ':OUTP:SENS ON'
        elif val == False:
            command = ':OUTP:SENS OFF'
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def reset(self):
        return self.device.write("*RST")
