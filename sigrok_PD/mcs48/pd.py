##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 fenugrec <fenugrec@users.sourceforge.net>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

## TODO
## - giving channel #s instead of names to self.wait() is completely retarded.
## - annotate on span between ALE an PSEN edges


import sigrokdecode as srd

class ChannelError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'mcs48'
    name = 'Intel MCS-48'
    longname = 'Intel MCS-48 ext memory'
    desc = 'Intel MCS-48 external memory access'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['mcs48']
    channels = tuple({
            'id': 'd%d' % i,
            'name': 'D%d' % i,
            'desc': 'CPU data line %d' % i
            } for i in range(8)
    ) + tuple({
            'id': 'a%d' % i,
            'name': 'A%d' % i,
            'desc': 'CPU addr line %d' % i
            } for i in range(8,13)
    ) + (
        {'id': 'ale', 'name': 'ALE', 'desc': 'Address Latch Enable'},
        {'id': 'psen', 'name': '/PSEN', 'desc': 'Program Store Enable'},
    )

    annotations = (
        ('addr', 'Address'),
        ('data', 'Data'),
    )

    annotation_rows = (
        ('addr', 'Address', (0,)),
        ('data', 'Data', (1,)),
    )

    def __init__(self):
        self.addr = 0
        self.addr_s = 0
        self.data = 0
        self.data_s = 0

        #flag to make sure we get an ALE pulse first
        self.started = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)


    def newaddr(self, pins):
        # falling edge on ALE : reconstruct address
        self.started = 1
        tempaddr = 0

        for i in range(13):
            tempaddr |= pins[i] << i

        self.addr = tempaddr
        self.addr_s = self.samplenum

    def ale_rise(self):
        if self.started:
            self.put(self.addr_s, self.samplenum, self.out_ann, [0, ['A 0x%04X' % self.addr]])

    def newdata(self, pins):
        # falling edge on PSEN : get data
        tempdata = 0

        for i in range(8):
            tempdata |= pins[i] << i
        self.data = tempdata
        self.data_s = self.samplenum

    def psen_rise(self):
        if self.started:
            self.put(self.data_s, self.samplenum, self.out_ann, [1, ['D 0x%02X' % self.data]])

    def decode(self):
        # Sample address on the falling ALE edge;
        # Save data on falling edge of PSEN.

        while True:
            pins = self.wait([{13: 'f'}, {13: 'r'}, {14: 'f'}, {14: 'r'}])

            # Handle those conditions (one or more) that matched this time.
            if self.matched[0]:
                self.newaddr(pins[0:])
            if self.matched[1]:
                self.ale_rise()
            if self.matched[2]:
                self.newdata(pins[0:])
            if self.matched[3]:
                self.psen_rise()
