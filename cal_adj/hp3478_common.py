#!/usr/bin/env python

# fenugrec 2026, gplv3

# - common funcs for performance verif and cal
# - eventually could wrap around pyvisa resource to better handle logging some/all commands passthru

import logging
from statistics import median, stdev

## dummy pyvisa resources for offline debugging
class pyvisa_dummy():
    def __init__(self, name):
        self.logf = logging.getLogger()
        self.name = name
        self.val = 0    # dummy val for readings etc; increment on every query
    def write(self, ws):
        self.logf.debug(f"{self.name}.write('{ws}')")
    def query(self, qs):
        self.logf.debug(f"{self.name}.query('{qs}') => {self.val}")
        self.val = self.val + 1
        return f'{self.val}'
    def read_ascii_values(self):
        self.logf.debug(f"{self.name}.read_ascii_values() => {self.val}")
        self.val = self.val + 1
        return [self.val]
    def query_ascii_values(self, qs):
        if 'errorqueue.count' in qs:
            self.logf.debug(f"{self.name} QAV errorq_count, ret 0")
            return [0] #ugly : force 0 so testmode works
        self.logf.debug(f"{self.name}.query_ascii_values('{qs}') => {self.val}")
        self.val = self.val + 1
        return [self.val]

# given an arbitrary func that returns one val, take readings and compute stats
class read_multi():
    def __init__(self, readfunc, discard, keep, logfunc, prefix=''):
        raw = []
        for i in range(0, discard + keep):
            raw.append(readfunc())
        filtered = raw[-keep:]
        self.median=median(filtered)
        self.stdev=stdev(filtered)
        self.raw_rdg = raw
        self.filtered = filtered
        logfunc(f'[{prefix}] discarded {discard}, kept {keep} readings; median={self.median:.7g} stdev={self.stdev:.7g} raw={raw}')

