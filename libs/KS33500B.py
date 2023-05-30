import pyvisa
try:
    from .loading import *
except:
    from loading import *

from colorama import init, Fore

_DELAY = 0.1
debug = 0      # disable/enable prints

resources = pyvisa.ResourceManager()

class KS33500B:
    def __init__(self):

        color = init(autoreset=True)

        try:
            self.resources = pyvisa.ResourceManager()
            self.instrument_list = self.resources.list_resources()
            self.loading = loading()
            self.address = [elem for elem in self.instrument_list if (elem.find('MY52') != -1)]

            if self.address.__len__() == 0:
                self.status = "Not Connected"
                print(Fore.RED + "Error! PyVISA failed to connect to KS33500B...")
            else:
                self.address = self.address[0]
                self.device = self.resources.open_resource(self.address)
                self.status = "Connected"
                print(Fore.GREEN + "Connected to " + self.address)

        except VisaIOError:
            self.status = "Not Connected"
            print(Fore.RED + "Error! PyVISA is not able to find any devices")

    def set_squ_dcyc(self,dcyc,source = 1):

        command = 'SOUR%d:FUNC:SQU:DCYC %f' % (source,dcyc)
        if debug:
            print(command)
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)


    def set_squ_freq(self,freq,source = 1):

        command = 'SOUR%d:FREQ %d Hz' % (source,freq)
        if debug:
            print(command)
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def set_squ_amp(self,amp,source = 1):

        command = 'SOUR%d:VOLT %f Vpp' % (source,amp)
        if debug:
            print(command)
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)

    def set_squ_offset(self,offset,source = 1):
            
        command = 'SOUR%d:VOLT:OFFS %f V' % (source,offset)
        if debug:
            print(command)
        self.device.write(command)
        self.loading.delay_with_loading_indicator(_DELAY)
