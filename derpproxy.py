# -*- coding: cp1252 -*-
from construct import Container

import packets
import loghandler

import sys
import time
import select
import socket
import random
import logging

log = logging.getLogger('derpproxy')

# enter target server here
SERVER, PORT = 'localhost', 25565
# proxy always listens on 127.0.0.1:25566

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

class ProxyServer(BaseSocket):
    def __init__(self, derpproxy, bind, port):
        BaseSocket.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((bind, port))
        self.socket.listen(1)
        self.clientsocket = None
        self.clientaddr = ('', 0)
        self.serversocket = None

        self.log = logging.getLogger('proxy')
        self.packlog = logging.getLogger('relay')
        self.packhandler = loghandler.PacketHandler(self.packlog)

        self.usablefds = [self]

    def loop(self):
        while True:
            readfds = select.select(self.usablefds, [], [])[0]
            for socket in readfds:
                socket.on_input()

    def on_input(self):
        sock, addr = self.socket.accept()
        self.log.info("Client connected %s:%s" % addr)
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.connect((SERVER, PORT))

        [x.on_close() for x
            in [self.clientsocket, self.serversocket]
            if x is not None]

        self.clientsocket = RelaySocket('Client', sock, self, serversock)
        self.serversocket = RelaySocket('Server', serversock, self, sock)

    def filter(self, header, payload):
        # if this returns false, no filtering is done
        return False

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
            if not self.proxy.filter(header, payload):
                origdata = packets.make_packet(header, payload)
                self.target.send(origdata)
                

class DerpProxy(object):
    def __init__(self):
        loghandler.RootHandler(self)
        self.proxy = ProxyServer(self, '127.0.0.1', 25566)

    def start(self):
        self.proxy.loop()

if __name__ == '__main__':
    DerpProxy().start()
