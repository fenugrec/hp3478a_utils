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
        # higher voltage ranges need 2x OPER to confirm; just always send 2
        self.write('OPER;*CLS;OPER')
        return
    def disable(self):
        self.write('STBY')
        return
    def set_dcv(self, x):
        self.write(f'EXTSENSE OFF')
        self.write(f'OUT {x} V')
        return
    def set_dci(self, x):
        self.write(f'EXTSENSE OFF')
        self.write(f'OUT {x} A')
        return
    def set_acv(self, x, freq):
        self.write(f'EXTSENSE OFF')
        self.write(f'OUT {x} V, {freq} Hz')
        return
    def set_aci(self, x, freq):
        self.write(f'EXTSENSE OFF')
        self.write(f'OUT {x} A, {freq} Hz')
        return
    def set_r(self, x):
        self.write(f'EXTSENSE OFF')
        self.write(f'OUT {x} OHM')
    def set_r4(self, x):
        self.write(f'EXTSENSE ON')
        self.write(f'OUT {x} OHM')
        return

