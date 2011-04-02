# -*- coding: cp1252 -*-

import init_config
from config import derpproxy as config

import packets
import loghandler
from util import Singleton

import sys
import time
import select
import socket
import random
import logging

log = logging.getLogger('derpproxy')

class BaseSocket(object):
    def __init__(self, socket=None):
        self.socket = socket
        self.buffer = ''

    def buffer_recv(self):
        newdata = self.socket.recv(16 * 1024)
        if newdata == '':
            self.on_close()
            return []
        self.buffer += newdata
        data, self.buffer = packets.parse_packets(self.buffer)
        return data

    def on_close(self):
        pass

    def fileno(self):
        return self.socket.fileno()

class ProxyServer(BaseSocket, Singleton):
    def __init__(self):
        BaseSocket.__init__(self)
        Singleton.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(config.proxy_bind)
        self.socket.listen(1)
        self.clientsocket = None
        self.clientaddr = ('', 0)
        self.serversocket = None

        loghandler.RootHandler()
        self.log = logging.getLogger('proxy')
        self.packlog = logging.getLogger('relay')
        self.packhandler = loghandler.PacketHandler(self.packlog)

        self.usablefds = [self]

        self.filters = {} # {modulename.functionname: function}
        self.enabledfilters = {}

        self.reload_modules()

    def loop(self):
        while True:
            readfds = select.select(self.usablefds, [], [])[0]
            for socket in readfds:
                socket.on_input()

    def on_input(self):
        sock, addr = self.socket.accept()
        self.log.info("Client connected %s:%s" % addr)
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.connect(config.server)

        [x.on_close() for x
            in [self.clientsocket, self.serversocket]
            if x is not None]

        self.clientsocket = RelaySocket('Client', sock, self, serversock)
        self.serversocket = RelaySocket('Server', serversock, self, sock)

    def filter(self, header, payload, target):
        self.stopped_filtering = False
        self.stopped_relaying = False
        for function in self.filters.values():
            function(header, payload, target)
            if self.stopped_filtering:
                break

        return self.stopped_relaying

    def stop_filter(self):
        self.stopped_filtering = True

    def stop_relay(self):
        self.stopped_relaying = True

    def reload_modules(self):
        self.filters = {}
        self.enabledfilters = {}
        for modulename in config.modules:
            fullname = 'proxymods.%s' % modulename
            if fullname in sys.modules:
                reload(sys.modules[fullname])
            else:
                __import__('proxymods.%s' % modulename)

        origset = set(self.filters.keys())
        filteredset = origset.copy()

        for pattern in config.disabled_filters:
            filteredset -= set(fnmatch.filter(filteredset, pattern))

        for key in filteredset:
            self.enabledfilters[key] = self.filters[key]


class RelaySocket(BaseSocket):
    def __init__(self, name, source, proxy, target):
        BaseSocket.__init__(self, source)
        self.target = target
        self.name = name

        self.proxy = proxy
        if self not in self.proxy.usablefds:
            self.proxy.usablefds.append(self)

    def on_close(self):
        self.socket.close()
        if self in self.proxy.usablefds:
            self.proxy.usablefds.remove(self)

    def on_input(self):
        data = self.buffer_recv()
        for header, payload in data:
            self.proxy.packlog.debug(self.name, header, payload)
            if not self.proxy.filter(header, payload, self.target):
                origdata = packets.make_packet(header, payload)
                self.target.send(origdata)
                

if __name__ == '__main__':
    ProxyServer().loop()
