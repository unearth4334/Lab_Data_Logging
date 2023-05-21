from libs.devices.DL3021 import *
from libs.devices.DP832 import *
from libs.devices.DS7034 import *
from libs.devices.FLUKE45 import *
from libs.devices.KA3010P import *
from libs.devices.KS33500B import *
from libs.devices.Keysight34460A import *
from libs.devices.U1233A import *
from libs.devices.DAC import *
from libs.devices.EPS import *

from colorama import init, Fore



#import matlab.engine
import time
import os

class logData2:

    def __init__(self):

        color = init(autoreset=True)

        self.labels   = []
        self.devices  = []
        self.items    = []
        self.channels = []

    def build_filename(self, name, num=0):
        root, ext = os.path.splitext(name)
        return '%s%d%s' % (root, num, ext) if num else name

    def find_next_filename(self, name, max_tries=100):
        if not os.path.exists(name): return name
        else:
            for i in range(max_tries):
                test_name = self.build_filename(name, i+1)
                if not os.path.exists(test_name): return test_name
            return None

    def connect(self,device):

        devices = { "DL3021"  :DL3021,
                    "DP832"   :DP832,
                    "DS7034"  :DS7034,
                    "FLUKE45" :FLUKE45,
                    "KA3010P" :KA3010P,
                    "KS33500B":KS33500B,
                    "Keysight34460A":Keysight34460A,
                    "U1233A"  :U1233A,
                    "DAC"     :DAC,
                    "EPS"     :EPS }

        try:
            device_Object = devices[device]()
            return device_Object
        except:
            print(Fore.RED + 'Error! Invalid input \"' + device + '\"...')
            return 0

    def add(self, label, device_object, item, channel=1):

        if device_object.status != 'Connected':
            print(Fore.RED + 'Error! Device not connected...')
        else:
            self.labels.append(label)
            self.devices.append(device_object)
            self.items.append(item)
            self.channels.append(channel)

    def newFile(self, filename = 'data.txt'):

        try:
            if self.f.writable():
                print('Saving \"'+self.filename+'\"...')
                self.f.close()
                print(Fore.GREEN + 'File \"'+self.filename+'\" saved...')
        except:
            pass

        self.filename = self.find_next_filename(filename)

        try:
            self.f = open(self.filename,'w')
            print('\r' + 'Opened file \"'+self.filename+'\"')
        except:
            print('\r' + Fore.RED + 'Error! Failed to open file \"'+self.filename+'\"...')

    def get(self):

        try:
            if self.f.writable():
                if self.f.tell()==0:
                    self.f.write('')
                    for i in range(len(self.labels)):
                        self.f.write('%s\t%s'%(self.labels[i],self.labels[i]+'_e'))
                        if i != len(self.labels)-1:
                            self.f.write('\t')
                    self.f.write('\n')
            else:
                print('\r' + Fore.YELLOW + 'Warning! No file is open...')
        except:
            print('\r' + Fore.YELLOW + 'Warning! No file is open...')

        for i in range(len(self.devices)):
            value = self.devices[i].get(self.items[i],self.channels[i])
            try:
                self.f.write('%.10f\t%.10f'%(value[0],value[1]))
                if i != len(self.devices)-1:
                    self.f.write('\t')
                print('\r' + Back.WHITE + Fore.BLACK + '%s\t'%self.labels[i]\
                       + Back.BLUE + Fore.WHITE + ' %.4f +/- %.4f '%(value[0],value[1]) )
            except:
                pass
        try:
            self.f.write('\n')
        except:
            pass

    def save(self):
        try:
            if self.f.writable():
                print('Saving \"'+self.filename+'\"...')
                self.f.close()
                print(Fore.GREEN + 'File \"'+self.filename+'\" saved...')
            else:
                print(Fore.RED + 'Error! No filestream available to save...')
        except:
            print(Fore.RED + 'Error! No filestream available to save...')