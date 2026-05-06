#!/usr/bin/env python

# -*- coding: UTF-8 -*-
# Calibration and/or adjustment app for Keithley 2400, v0.8, Jan.30.2024 (C) xDevs.com
# Tested with Raspberry Pi and Windows on Python 2.7.18 and Python 3.7.5
# DMM7510 stuff is untested yet
# https://xdevs.com/fix/kei2400
# https://xdevs.com/fix/kei2400pa
# https://xdevs.com/fix/hp3458a
#
# butchered by fenugrec just to keep fancy DMM stuff plus thin wrapper; based on 'cal2400_rev8.py'
import os
import sys
import time
import signal

# XXX not sure what this was, csv / logger thing
class b():
    write = print

'''
Currently this scripts only works with following DMMs:
 * 3458a   = HP/Agilent/Keysight 3458A 8.5-digit DMM with GPIB
 * 2002    = Keithley 2002 8.5-digit DMM with GPIB
 * 2001    = Keithley 2001 7.5-digit DMM with GPIB
 * 7510    = Keithley 7510 7.5-digit DMM with GPIB
 * 7510lan = Keithley 7510 7.5-digit DMM with LAN connection
'''

###################### Configuration settings for script #############################################################

dmm_temp = 23.0
dmm_type = "3458a"                                  # Reference DMM type. Supported types listed in legend above
hw_interface_type = "vxi"                           # Please select vxi or visa or linux-gpib
dmm_nplc = 10                                       # NPLC for DMM
run_acal = False                                    # If "True" then execute ACAL ALL on 3458A before calibration
gpib_addr_dmm = 1                                   # GPIB address of DUT K2400
gpib_vxi_ip = "192.168.1.10"                        # TCP/IP address of Agilent E5810A GPIB-LAN gateway
dmm_vxi_ip = "192.168.1.12"                         # TCP/IP address for LAN-equipped reference DMM (e.g. DMM7510)

#####################################################################################################################


if (hw_interface_type == "vxi"):
    import vxi11                           # Import library for Agilent E5810A/B GPIB to LAN bridge
elif (hw_interface_type == "visa"):
    import pyvisa                          # Import library for VISA interface
elif (hw_interface_type == "linux-gpib"):
    import Gpib                            # Import library for USB linux-gpib (works only on Linux)
else:
    print ('\033[31;1m -e- Incorrect interface define, use "vxi" or "visa" or "linux-gpib" for hw_interface_type parameter\033[39;0m')

class Timeout():
  """Timeout class using ALARM signal"""
  class Timeout(Exception): pass

  def __init__(self, sec):
    self.sec = sec

  def __enter__(self):
    if os.name == "nt":
        time.sleep(0.1)
    else:
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

  def __exit__(self, *args):
    if os.name == "nt":
        time.sleep(0.1)
    else:
        signal.alarm(0) # disable alarm

  def raise_timeout(self, *args):
    raise Timeout.Timeout()

# Class for the reference DMM instrument
class dmm_xdevs():
    global dmm_val
    data = ""
    temp = 26.5
    set_nplc = dmm_nplc # temporary internal value

    def __init__(self,gpib,name):
        self.gpib = gpib
        set_nplc = dmm_nplc
        if (hw_interface_type == "vxi"):
            try:
                self.inst = vxi11.Instrument(gpib_vxi_ip, "gpib0,%d" % gpib_addr_dmm)
                self.inst.timeout = 20
            except:
                print ('\033[31;1m -e- Cound not initialize GPIB-LAN bridge at %s for GPIB %d\033[39;0m' % (gpib_vxi_ip, gpib_addr_dmm))
        elif (hw_interface_type == "visa"):
            rm = pyvisa.ResourceManager()
            #rm.list_resources()   # Debug listing for all available interfaces
            self.inst = rm.open_resource('GPIB::%d"::INSTR' % gpib_addr_dmm)
        elif (hw_interface_type == "linux-gpib"):
            self.inst = Gpib.Gpib(0,gpib_addr_dmm,timeout = 20)
        self.name = name
        if (dmm_type == "3458a"):
            self.init_inst_3458()
        elif (dmm_type == "2002"):
            self.init_inst_2002()
        elif (dmm_type == "2001"):
            self.init_inst_2001()
        elif ((dmm_type == "7510") or (dmm_type == "7510lan")):
            self.init_inst_7510()

    def init_inst_3458(self):
        # Setup HP 3458A
        self.inst.write ("PRESET NORM")
#        self.inst.write ("OFORMAT ASCII")
        self.inst.write ("DCV 10")
#        self.inst.write ("TARM HOLD")
        self.inst.write ("TRIG AUTO")
        self.inst.write ("NPLC %.3f" % dmm_nplc)
        self.inst.write ("AZERO ON")
#        self.inst.write ("NRDGS 1,AUTO")
        self.inst.write ("MATH OFF")
        self.inst.write ("END ALWAYS")
        self.inst.write ("NDIG 9")
        self.inst.write ("DELAY 0")

    def init_inst_2001(self):
        # Setup Keithley 2001 DVM
        if (dmm_nplc > 10):
            set_nplc = 10
        else:
            set_nplc = dmm_nplc
        self.inst.write("*RST\n")
        self.inst.write(":SYST:PRES")
        self.inst.write(":INIT:CONT OFF\n")
        self.inst.write(":SYST:AZER:TYPE SYNC\n")
        self.inst.write(":SYST:AZER:STAT ON\n")
        self.inst.write(":ABOR\n")
        self.inst.write(":SYST:LSYN:STAT ON;\n")
        self.inst.write(":INP:PRE:STAT OFF")
        self.inst.write(":SENS:VOLT:DC:AVER:COUN 10")
        self.inst.write(":SENS:VOLT:DC:DIG 8")
        self.inst.write(":SENS:VOLT:DC:AVER:ADV OFF; TCON MOV")
        self.inst.write(":SENS:VOLT:DC:NPLC %.3f" % set_nplc)
        self.inst.write(":SENS:CURR:DC:AVER:COUN 10")
        self.inst.write(":SENS:CURR:DC:AVER:ADV OFF; TCON MOV")
        self.inst.write(":SENS:CURR:DC:NPLC %.3f" % set_nplc)
        self.inst.write(":SENS:CURR:DC:DIG 8")
        self.inst.write(":FORM:ELEM READ")

    def init_inst_2002(self):
        # Setup Keithley 2002 DVM
        if (dmm_nplc > 50):
            set_nplc = 50
        else:
            set_nplc = dmm_nplc
        self.inst.write("*RST\n")
        self.inst.write(":SYST:PRES")
        self.inst.write(":INIT:CONT OFF\n")
        self.inst.write(":SYST:AZER:TYPE SYNC\n")
        self.inst.write(":SYST:AZER:STAT ON\n")
        self.inst.write(":ABOR\n")
        self.inst.write(":SYST:LSYN:STAT ON;\n")
        self.inst.write(":INP:PRE:STAT OFF")
        self.inst.write(":SENS:VOLT:DC:AVER:COUN 10")
        self.inst.write(":SENS:VOLT:DC:DIG 8")
        self.inst.write(":SENS:VOLT:DC:AVER:ADV OFF; TCON MOV")
        self.inst.write(":SENS:VOLT:DC:NPLC %.3f" % set_nplc)
        self.inst.write(":SENS:CURR:DC:AVER:COUN 10")
        self.inst.write(":SENS:CURR:DC:AVER:ADV OFF; TCON MOV")
        self.inst.write(":SENS:CURR:DC:NPLC %.3f" % set_nplc)
        self.inst.write(":SENS:CURR:DC:DIG 8")
        self.inst.write(":FORM:ELEM READ")

    def init_inst_7510(self):
        # Setup Keithley DMM7510
        if (dmm_nplc > 15):
            set_nplc = 15
        else:
            set_nplc = dmm_nplc
        self.inst.write("*RST\n")
        self.inst.write(":SYST:PRES")
        self.inst.write(":INIT:CONT OFF\n")
        self.inst.write(":SYST:AZER:TYPE SYNC\n")
        self.inst.write(":SYST:AZER:STAT ON\n")
        self.inst.write(":ABOR\n")
        self.inst.write(":SYST:LSYN:STAT ON;\n")
        self.inst.write(":INP:PRE:STAT OFF")
        self.inst.write(":SENS:VOLT:DC:AVER:COUN 10")
        self.inst.write(":SENS:VOLT:DC:DIG 7")
        self.inst.write(":SENS:VOLT:DC:AVER:ADV OFF; TCON MOV")
        self.inst.write(":SENS:VOLT:DC:NPLC %.3f" % set_nplc)
        self.inst.write(":SENS:CURR:DC:AVER:COUN 10")
        self.inst.write(":SENS:CURR:DC:AVER:ADV OFF; TCON MOV")
        self.inst.write(":SENS:CURR:DC:NPLC %.3f" % set_nplc)
        self.inst.write(":SENS:CURR:DC:DIG 7")
        self.inst.write(":FORM:ELEM READ")

    def set_dcv_range(self, cmd):
        if (dmm_type == "3458a"):
            self.inst.write ("NPLC %.3f" % dmm_nplc)
            self.inst.write ("DCV %.6e" % cmd)
        else:
            self.inst.write(":SENS:FUNC 'VOLT:DC'")
            self.inst.write(":SENS:VOLT:DC:DIG 8")
            self.inst.write(":SENS:VOLT:DC:RANG %.6e" % cmd)

    def set_dci_range(self, cmd):
        if (dmm_type == "3458a"):
            self.inst.write ("NPLC %.3f" % dmm_nplc)
            self.inst.write ("DCI %.6e" % cmd)
        else:
            self.inst.write(":SENS:FUNC 'CURR:DC'")
            self.inst.write(":SENS:CURR:DC:DIG 8")
            self.inst.write(":SENS:CURR:DC:RANG %.6e" % cmd)

    def switch_dci(self):
        if (dmm_type == "3458a"):
            self.inst.write ("PRESET NORM")
            self.inst.write ("AZERO ON")
            self.inst.write ("NRDGS 1,AUTO")
            self.inst.write ("OFORMAT ASCII")
            self.inst.write ("FUNC DCI,AUTO")
            self.inst.write ("NDIG 9")
        else:
            self.inst.write(":ABOR\n")
            self.inst.write(":SENS:FUNC 'CURR:DC'")
            self.inst.write(":SENS:CURR:DC:DIG 8")

    def write(self,cmd):
        self.inst.write(cmd)

    def read(self):
        return self.inst.read()

    def read_data(self,cmd):
        data_float = 0.0
        data_str = ""
        self.inst.write(cmd)

        try:
            with Timeout(10):
                data_str = self.inst.read()
        except Timeout.Timeout:
            print ("Timeout exception from dmm %s on read_data() inst.read()\n" % self.name)
            return (0,float(0))
        #print ("Reading from dmm %s = %s" % (self.name,data_str))
        try:
            data_float = float(data_str)
        except ValueError:
            print("Exception thrown by dmm %s on read_data() - ValueError = %s\n" % (self.name,data_str))
            return (0,float(0)) # Exception on float conversion, 0 = error
        return (1,data_float) # Good read, 1 = converted to float w/o exception

    def get_temp(self):
        global dmm_temp
        print("\r\nReading DMM temp\r\n")
        if (dmm_type == "3458a"):
            self.inst.write("TARM AUTO,1")
            self.temp_status_flag,temp = self.read_data("TEMP?")
        else:
            print ("\r\nThis DMM does not support internal temperature readout\r\n")
            return 0

        if (self.temp_status_flag):
            self.temp = temp
        dmm_temp = self.temp
        return self.temp

    def get_temp_status(self):
        return self.temp_status_flag

    def get_data(self):
        global dmm_val
        if (dmm_type == "3458a"):
            self.status_flag,data = self.read_data("TRIG SGL")
        else:
            self.status_flag,data = self.read_data("READ?")
        if (self.status_flag):
            self.data = data
            dmm_val = float(data)
        return self.data

    def exec_acal(self):
        if (dmm_type == "3458a"):
            sys.stdout.write ("\r\n\033[1;35m -i- ACAL ALL procedure start, please wait 15 minutes to complete.\r\n")
            self.inst.write("ACAL ALL")
            for cnt in range(0 ,290):        # wait 870 seconds, print dot every 3s
                sys.stdout.write ("\033[0;40m*")
                time.sleep(3)
                sys.stdout.flush()
            print("ACAL procedure done...\033[1;39m")
        else:
            print("This instrument does not support ACAL\033[1;39m")

    def exec_idn(self):
        if (dmm_type == "3458a"):
            self.inst.write ("END ALWAYS")
            self.inst.write ("ID?")
        else:
            self.inst.write ("*IDN?")
        dat = self.inst.read()
        tstr = dat.split()
        if (tstr[0] == "HP3458A"):
            sys.stdout.write ("\r\033[1;32m%s detected...\r\n\033[1;39m" % tstr[0])
            b.write("\r%s detected... \r" % tstr)
        elif ((tstr[0] == "KEITHLEY") and (tstr[3][:4] == "2002")):
            sys.stdout.write ("\r\033[1;32mKeithley 2002 detected... %s \r\n\033[1;39m" % tstr)
            b.write("\rKeithley 2002 detected... %s \r" % tstr)
        elif ((tstr[0] == "KEITHLEY") and (tstr[3][:4] == "2001")):
            sys.stdout.write ("\r\033[1;32mKeithley 2001 detected... %s \r\n\033[1;39m" % tstr)
            b.write("\rKeithley 2001 detected... %s \r" % tstr)
        elif ((tstr[0] == "KEITHLEY") and (tstr[2][:7] == "DMM7510")):
            sys.stdout.write ("\r\033[1;32mKeithley DMM7510 detected... %s \r\n\033[1;39m" % tstr)
            b.write("\rKeithley DMM7510 detected... %s \r" % tstr)
        else:
            sys.stdout.write ("\r\033[1;31mNo reference DMM present, exiting!\033[1;39m")
            quit()

    def get_data_status(self):
        return self.status_flag

# super thin wrapper to match func names
class dmm_wrapper(dmm_xdevs):
    def __init__(self):
        #        self.pyvis_res = pyvisa_res
        #super().__init__(pyvisa_res, 'xdev_3458')
        super().__init__(None, 'xdevs_3478')
        ids = super().exec_idn()
        super().init_inst_3458()
        return

# set whatever necessary to measure volts
    def config_v(self):
        super().set_dcv_range(40)
        return

# set whatever necessary to measure up to 1A
    def config_i(self):
        super().set_dci_range(3)
        return

# manual range
    def range_v(self, expect):
        super().set_dcv_range(expect)
        return

    def range_i(self, expect):
        super().set_dci_range(expect)
        return

#get single reading
    def read_v(self):
        return super().get_data()

    def read_i(self):
        return super().get_data()

