#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Zhang Cheng <cheng.zhang@cloudacc-inc.com>
# 
# Author:     Zhang Cheng <cheng.zhang@cloudacc-inc.com>
# Maintainer: Zhang Cheng <cheng.zhang@cloudacc-inc.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import curses

class Interface:
    def __init__(self, timestamp, rx_bytes, rx_packets, tx_bytes, tx_packets):
        self.rx = [rx_bytes, rx_packets] 
        self.tx = [tx_bytes, tx_packets]
        self.timestamp = timestamp

    def report(self, timestamp, rx_bytes, rx_packets, tx_bytes, tx_packets):
        timestamp_delta = timestamp - self.timestamp
        [rx_bps, rx_pps] = map(lambda old, new: (new - old) / timestamp_delta,
                self.rx, [rx_bytes, rx_packets])
        [tx_bps, tx_pps] = map(lambda old, new: (new - old) / timestamp_delta,
                self.tx, [tx_bytes, tx_packets])
        self.rx = [rx_bytes, rx_packets] 
        self.tx = [tx_bytes, tx_packets]
        self.timestamp = timestamp 
        return [rx_bps, rx_pps, tx_bps, tx_pps]

class Screen:
    def __init__(self, nr_iface):
        self.stdscr = curses.initscr()
        curses.noecho() 
        curses.cbreak() 
        curses.curs_set(0)
        self.stdscr.keypad(1)
        self.stdscr.nodelay(True)

        self.stdscr.refresh()

        self.colwidth = 16
        self.pad = curses.newpad(nr_iface + 3, self.colwidth*3+2)
        self.pad.border()

    def __del__(self):
        import curses
        curses.nocbreak() 
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def print_ifaces(self, ifaces, to_readable):
        padline = 1
        self.pad.addstr(padline, 1+self.colwidth,   "RX")
        self.pad.addstr(padline, 1+self.colwidth*2, "TX")

        for iface in ifaces:
            padline += 1
            name = iface[0]
            timestamp = float(iface[1])
            rx_bytes, rx_packets, tx_bytes, tx_packets = \
                    map(lambda x: int(x), iface[2:]) 
            speed = interfaces[name].report(timestamp, 
                    rx_bytes, rx_packets, tx_bytes, rx_packets)
            rx_speed = to_readable(speed[0]) + " " * self.colwidth
            tx_speed = to_readable(speed[2]) + " " * self.colwidth
            self.pad.addnstr(padline, 1, name, self.colwidth)
            self.pad.addnstr(padline, 1+self.colwidth, rx_speed, self.colwidth)
            self.pad.addnstr(padline, 1+self.colwidth*2, tx_speed, self.colwidth)

        self.pad.refresh(0,0, 0,0, nr_iface + 2, self.colwidth*3+1)

    def getch(self):
        return self.stdscr.getch()


def extract_netdev_once():
    timestamp = time.time()
    with open("/proc/net/dev") as f:
        lines = f.readlines()[2:]

    for line in lines:
        values = line.replace(':', ' ').split()
        name = values[0]
        [rx_bytes, rx_packets] = values[1:3]
        [tx_bytes, tx_packets] = values[9:11]
        yield [name, timestamp, rx_bytes, rx_packets, tx_bytes, tx_packets]

    return

def extract_netdev():
    while True:
        results = []
        for result in extract_netdev_once():
            results.append(result)
        yield results
        time.sleep(1)

def to_readable_bytes(size):
    for x in ['B/s', 'KB/s', 'MB/s']:
        if size < 1024.0:
            return "%3.1f %s" %(size, x)
        size /= 1024.0
    return "%3.1f GB/s" %(size)

def to_readable_bits(size):
    size *= 8.0
    for x in ['b/s', 'Kb/s', 'Mb/s']:
        if size < 1024.0:
            return "%3.1f %s" %(size, x)
        size /= 1024.0
    return "%3.1f Gb/s" %(size)

def print_speed(name, speed, to_readable):
    rx_speed = to_readable(speed[0])
    tx_speed = to_readable(speed[2])
    print(name, rx_speed, tx_speed)


# now we get to work

# initialize, find all interfaces
interfaces = dict()
nr_iface = 0
for iface in extract_netdev_once():
    nr_iface += 1
    name = iface[0]
    timestamp = float(iface[1])
    rx_bytes, rx_packets, tx_bytes, tx_packets = \
            map(lambda x: int(x), iface[2:]) 
    interfaces[name] = \
            Interface(timestamp, rx_bytes, rx_packets, tx_bytes, tx_packets)

screen = Screen(nr_iface)

try:
    to_readable = to_readable_bytes
    for ifaces in extract_netdev():
        ch = screen.getch()
        if ch == ord('q'):
            exit(0)
        elif ch == ord('b'):
            to_readable = to_readable_bits
        elif ch == ord('B'):
            to_readable = to_readable_bytes
        screen.print_ifaces(ifaces, to_readable)
except:
    exit(0)
    

# vim:ai:et:sts=4:tw=80:sw=4:
