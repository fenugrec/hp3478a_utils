#!/usr/bin/env python

# fenugrec 2026, gplv3
#
# customize this for DMM to be used with cal / pv
#
# example code for hp3478a

class dmm_3478():
    def __init__(self, pyvisa_res):
        self.dmm = pyvisa_res
        ids = '3478'
#    ids = self.dmm.query('*idn?')
        if not ids:
            print("no DMM ?")
            quit()
        else:
            print(f"connected to DMM:\n{ids}")
        return

# set whatever necessary to measure volts
    def config_v(self):
        # DCV, autorange, 5.5dig, internal trig, autozero
        self.dmm.write('F1RAN5T1Z1')
        return

# set whatever necessary to measure up to 1A
    def config_i(self):
        # DCA, autorange, 5.5dig, internal trig, autozero
        self.dmm.write('F5RAN5T1Z1')
        return

# manual range
    def range_v(self, expect):
        return

    def range_i(self, expect):
        return

#get single reading
    def read_v(self):
        return self.dmm.read_ascii_values()[0]

    def read_i(self):
        return self.dmm.read_ascii_values()[0]

