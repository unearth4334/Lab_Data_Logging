import pyvisa
import time
import statistics
import numpy
from colorama import init, Fore
from loading import *

_delay = 0.1  # in seconds

class DS7034:
    def __init__(self):

        self.loader = loading()

        color = init(autoreset=True)

        try:
            self.resources = pyvisa.ResourceManager()
            self.instrument_list = self.resources.list_resources()
            
            self.address = [elem for elem in self.instrument_list if (elem.find('DS7') != -1)]

            if self.address.__len__() == 0:
                self.status = "Not Connected"
                print(Fore.RED + "Error! PyVISA failed to connect to DS7034...")
            else:
                self.address = self.address[0]
                self.device = self.resources.open_resource(self.address)
                self.status = "Connected"
                print(Fore.GREEN + "Connected to " + self.address)

        except VisaIOError:
            self.status = "Not Connected"
            print(Fore.RED + "Error! PyVISA is not able to find any devices...")

    def get(self,item,channel=1):

        items = { "VAVG"    :self.measure_item,
                  "VMAX"    :self.measure_item,
                  "VMIN"    :self.measure_item,
                  "VAVG_STAT":self.measure_stat,
                  "VMAX_STAT":self.measure_stat,
                  "VPP_STAT":self.measure_stat,
                  "PDUT_STAT":self.measure_stat,
                  "FREQ_STAT":self.measure_stat,
                  "RFD_STAT":self.measure_stat,
                  "RRD_STAT":self.measure_stat,
                  "VMIN_STAT":self.measure_stat,
                  "PSL_STAT":self.measure_stat,
                  "NSL_STAT":self.measure_stat,
                  "VTOP_STAT":self.measure_stat,
                  "VBAS_STAT":self.measure_stat }

        isStat = item.find('_STAT')

        if isStat > 0:

            item_x = item[0:isStat]

        else:
            item_x = item

        result = items[item](item_x,'CHAN%d'%(channel))

        return result


    def measure_item(self, item, source):
        # measure waveform parameter of the specified source
        # item: {VMAX|VMIN|VPP|VTOP|VBASe|VAMP|VAVG|VRMS|OVERshoot|
        #   PREShoot|MARea|MPARea|PERiod|FREQuency|RTIMe|FTIMe|PWIDth|
        #   NWIDth|PDUTy|NDUTy|TVMax|TVMin|PSLewrate|NSLewrate|VUPPer|
        #   VMID|VLOWer|VARiance|PVRMs|PPULses|NPULses|PEDGes|NEDGes|
        #   RRDelay|RFDelay|FRDelay|FFDelay|RRPHase|RFPHase|FRPHase|FFPHase } 
        # source: {D0|D1|D2|D3|D4|D5|D6|D7|D8|D9|D10|D11|D12|D13|D14|D15|
        #   CHANnel1|CHANnel2|CHANnel3|CHANnel4|MATH1|MATH2|MATH3|MATH4}
        command = ':MEAS:ITEM? %s, %s' % (item, source)
        value = self.device.query(command)
        value = float(value)
        self.loader.delay_with_loading_indicator(_delay)
        return (value,0)

    def measure_avg(self, item, source, n):

        val = numpy.zeros(n)
        for x in range(n):
            val[x]=self.measure_item(item, source)

        return (statistics.fmean(val),statistics.stdev(val))

    def measure_stat_reset(self):
        # Clear the statistics and make statistics again
        command = ':MEAS:STAT:RES'
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)

    def enable_statistics(self, value = 1):
        # Enable statistics
        command = ':MEAS:STAT:DISP %d'%value
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)

    def measure_stat(self, item, source):
        # measure waveform parameter of the specified source
        # item: {VMAX|VMIN|VPP|VTOP|VBASe|VAMP|VAVG|VRMS|OVERshoot|
        #   PREShoot|MARea|MPARea|PERiod|FREQuency|RTIMe|FTIMe|PWIDth|
        #   NWIDth|PDUTy|NDUTy|TVMax|TVMin|PSLewrate|NSLewrate|VUPPer|
        #   VMID|VLOWer|VARiance|PVRMs|PPULses|NPULses|PEDGes|NEDGes|
        #   RRDelay|RFDelay|FRDelay|FFDelay|RRPHase|RFPHase|FRPHase|FFPHase }
        # type: {MAXimum|MINimum|CURRent|AVERages|DEViation}
        # source: {D0|D1|D2|D3|D4|D5|D6|D7|D8|D9|D10|D11|D12|D13|D14|D15|
        #   CHANnel1|CHANnel2|CHANnel3|CHANnel4|MATH1|MATH2|MATH3|MATH4}
        if isinstance(source,int) and source in range(1,5):
            command1 = ':MEAS:STAT:ITEM? AVER,%s,CHAN%d' % (item, source)
            command2 = ':MEAS:STAT:ITEM? DEV,%s,CHAN%d' % (item, source)
        else:
            command1 = ':MEAS:STAT:ITEM? AVER,%s,%s' % (item, source)
            command2 = ':MEAS:STAT:ITEM? DEV,%s,%s' % (item, source)
        value = self.device.query(command1)
        value = float(value)
        self.loader.delay_with_loading_indicator(_delay)
        value_e = self.device.query(command2)
        value_e = float(value_e)
        self.loader.delay_with_loading_indicator(_delay)
        return (value,value_e)
        
    def measure_stat_item(self, item, stattype, source):
        # measure waveform parameter of the specified source
        # item: {VMAX|VMIN|VPP|VTOP|VBASe|VAMP|VAVG|VRMS|OVERshoot|
        #   PREShoot|MARea|MPARea|PERiod|FREQuency|RTIMe|FTIMe|PWIDth|
        #   NWIDth|PDUTy|NDUTy|TVMax|TVMin|PSLewrate|NSLewrate|VUPPer|
        #   VMID|VLOWer|VARiance|PVRMs|PPULses|NPULses|PEDGes|NEDGes|
        #   RRDelay|RFDelay|FRDelay|FFDelay|RRPHase|RFPHase|FRPHase|FFPHase }
        # type: {MAXimum|MINimum|CURRent|AVERages|DEViation}
        # source: {D0|D1|D2|D3|D4|D5|D6|D7|D8|D9|D10|D11|D12|D13|D14|D15|
        #   CHANnel1|CHANnel2|CHANnel3|CHANnel4|MATH1|MATH2|MATH3|MATH4}
        command = ':MEAS:STAT:ITEM? %s,%s,%s' % (stattype, item, source)
        value = self.device.query(command)
        value = float(value)
        self.loader.delay_with_loading_indicator(_delay)
        return value
    
    def measure_clear(self,value):
        # value : {ITEM1|ITEM2|ITEM3|ITEM4|ITEM5|ITEM6|ITEM7|ITEM8|ITEM9|ITEM10|ALL}
        command = ':MEAS:CLE %s' % (value)
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)
    
    def set_time_scale(self,val):
        command = ':TIM:MAIN:SCAL %f' % (val)
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)

    def set_vertical_offset(self,val,channel):

        command = ':CHAN%d:OFFS %f' % (channel,round(val,3))
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)

    def set_vertical_scale(self,val,channel):

        command = ':CHAN%d:SCAL %f' % (channel,round(val,3))
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)

    def configure_probe_impedance(self,val,channel):

        # channel = {1|2|3|4}
        # val = {OMEG:FIFT}

        command = ':CHAN%d:IMP %s' % (channel,val)
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)

    def configure_probe_gain(self,val,channel):

        # channel = {1|2|3|4}
        # val = {0.01|0.02|0.05|0.1|0.2|0.5|1|2|5|10|20|50|100|200|500|1000}

        command = ':CHAN%d:PROB %d' % (channel,val)
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)

    def configure_probe_bwlimit(self,val,channel):

        # channel = {1|2|3|4}
        # val = {20M|250M|OFF}

        command = ':CHAN%d:BWL %s' % (channel,val)
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)

    def configure_trigger_edge(self,val,channel):

        # source: {1|2|3|4}
        # val = (-5 × VerticalScale - OFFSet) to (5 × VerticalScale - OFFSet) 

        command = ':TRIG:EDGE:SOUR CHAN%d' % (channel)
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)
        command = ':TRIG:EDGE:LEV %f' % (round(val,3))
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)

    def get_probe_gain(self, channel):
        command = ':CHAN%d:PROB?' % (channel)
        value = self.device.query(command)
        value = float(value)
        self.loader.delay_with_loading_indicator(_delay)
        return value
    
    def get_probe_bwlimit(self, channel):
        command = ':CHAN%d:BWL?' % (channel)
        value = self.device.query(command)
        self.loader.delay_with_loading_indicator(_delay)
        return value[0:(len(value)-1)]
    
    def get_probe_impedance(self, channel):
        command = ':CHAN%d:IMP?' % (channel)
        value = self.device.query(command)
        self.loader.delay_with_loading_indicator(_delay)
        return value[0:(len(value)-1)]

    def quick_img(self):

        command = ':Q:OPER SIM'
        self.device.write(command)
        time.sleep(2)

    def configure_probe(self,channel, impedance = 'OMEG',gain = 10, bwlimit = 'OFF'):

        self.configure_probe_impedance(impedance,channel)
        self.configure_probe_gain(gain,channel)
        self.configure_probe_bwlimit(bwlimit,channel)
    
        if self.get_probe_impedance(channel) != impedance or\
        self.get_probe_gain(channel) != gain or\
        self.get_probe_bwlimit(channel) != bwlimit:
            return False
        
        if channel == 1:
            print('\r\033[93m' +'Probe 1'+'\033[39m' + ': IMP:%s, GAIN:%d, BWL:%s'%(impedance,gain,bwlimit))
        if channel == 2:
            print('\r\033[96m' +'Probe 2'+'\033[39m' + ': IMP:%s, GAIN:%d, BWL:%s'%(impedance,gain,bwlimit))
        if channel == 3:
            print('\r\033[95m' +'Probe 3'+'\033[39m' + ': IMP:%s, GAIN:%d, BWL:%s'%(impedance,gain,bwlimit))
        if channel == 4:
            print('\r\033[94m' +'Probe 4'+'\033[39m' + ': IMP:%s, GAIN:%d, BWL:%s'%(impedance,gain,bwlimit))

        
            
    
        return True

    def press_key(self,key):

        #key: {CH1|CH2|CH3|CH4|MATH|REF|LA|DECode|MOFF|F1|F2|F3|F4|F5|F6|F7|
        #    NPRevious|NNEXt|NSTop|VOFFset1|VOFFset2|VOFFset3|VOFFset4|
        #    VSCale1|VSCale2|VSCale3|VSCale4|HSCale|HPOSition|KFUNction|
        #    TLEVel|TMENu|TMODe|DEFault|CLEar|AUTO|RSTop|SINGle|QUICk|
        #    MEASure|ACQuire|STORage|CURSor|DISPlay|UTILity|FORCe|
        #    GENerator1|GENerator2|BACK|TOUCh|ZOOM|SEARch|WSCale|WPOSition}

        command = ':SYST:KEY:PRES %s' % (key)
        self.device.write(command)
        self.loader.delay_with_loading_indicator(_delay)