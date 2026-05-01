#!/usr/bin/env python

# fenugrec 2026, gplv3
# probably fluke5700 mfc

import logging

class cal_mfc():
    def __init__(self, pyvisa_res):
        self.logf = logging.getLogger()
        self.dmm = pyvisa_res
        return
    def write(self, s):
        #just wrap with logging
        self.logf.debug(f'cal write "{s}"')
        self.dmm.write(s)
        return
    def enable(self):
        self.write('OPER')
        return
    def disable(self):
        self.write('STBY')
        return
    def set_dcv(self, x):
        self.write(f'OUT {x} V')
        return
    def set_dci(self, x):
        self.write(f'OUT {x} A')
        return
    def set_acv(self, x, freq):
        self.write(f'OUT {x} V, {freq} Hz')
        return
    def set_aci(self, x, freq):
        self.write(f'OUT {x} A, {freq} Hz')
        return
    def set_r(self):
        self.write(f'OUT {x} OHM')
        return

