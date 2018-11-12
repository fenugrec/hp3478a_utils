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

## Note
##
##
## TODO
## - giving channel #s instead of names to self.wait() is completely retarded.
## - make A12 optional; it's here because of an instrument (HP3478A) that
## drives a generic IO pin to access 8kB of ROM; the MCS48 only has
## a 4kB address space.


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
        ('romdata', 'Address:Data'),
    )

    binary = (
        ('romdata', 'AAAA:DD'),
    )

    def __init__(self):
        self.addr_latch = 0 #lower 8 bits
        self.addr_s = 0 #ALE edge position
        self.data = 0

        #flag to make sure we get an ALE pulse first
        self.started = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_bin = self.register(srd.OUTPUT_BINARY)


    def newaddr(self, pins):
        # falling edge on ALE : reconstruct address
        self.started = 1
        tempaddr = 0

        for i in range(8):
            tempaddr |= pins[i] << i

        self.addr_latch = tempaddr
        self.addr_s = self.samplenum

    def newdata(self, pins):
        # edge on PSEN : get data
        tempdata = 0
        addr = self.addr_latch

        for i in range(8):
            tempdata |= pins[i] << i
        for i in range(8,13):
            #high order bits were not latched !
            addr |= pins[i] << i

        self.data = tempdata
        if self.started:
            self.put(self.addr_s, self.samplenum, self.out_ann, [0, ['%04X:' % addr + '%02X' % self.data]])
            self.put(self.addr_s, self.samplenum, self.out_bin, [0, bytes([(addr >> 8) & 0xFF, addr & 0xFF, self.data])])


    def decode(self):
        # Sample address on the falling ALE edge;
        # Save data on falling edge of PSEN.

        while True:
            pins = self.wait([{13: 'f'},{14: 'r'}])

            # Handle those conditions (one or more) that matched this time.
            if self.matched[0]:
                self.newaddr(pins[0:])
            if self.matched[1]:
                self.newdata(pins[0:])
