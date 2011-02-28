# -*- coding: cp1252 -*-
from construct import Container

from timer import Timer, TimerManager
from storage import Storage
from util import Singleton
import packets
import loghandler

import sys
import time
import select
import socket
import random
import logging

log = logging.getLogger('derpbot')


SERVER, PORT = 'localhost', 25565
USERNAME = 'derpbot' #spasysheep

class Connection(object):
    def __init__(self, derpbot, host, port, username):
        self.host = host
        self.port = port
        self.username = username
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.log = logging.getLogger('connection')
        self.packlog = logging.getLogger('packets')
        self.packhandler = loghandler.PacketHandler(self.packlog)

        self.buffer = ''
        self.last_sent_packet = time.time()

        self.timers = TimerManager.get()

    def connect(self):
        self.log.info('Connecting...')
        self.socket.connect((self.host, self.port))
        self.log.debug('Established')

        self.send_packet("handshake", username=self.username)
        self.log.debug('Handshake sent')

    def send(self, data):
        self.last_sent_packet = time.time()
        self.socket.send(data)

    def send_packet(self, name, **kwargs):
        header = packets.packets_by_name[name]
        self.packlog.debug('send', header, kwargs)
        self.send(packets.make_packet(name, **kwargs))

    def loop_iter(self):
        if self.last_sent_packet < (time.time() - 60):
            self.send_packet('ping')
        self.timers.run_timers()

        if not select.select([self.socket], [], [], 0.1)[0]:
            return

        newdata = self.socket.recv(16 * 1024)
        self.buffer += newdata
        data, self.buffer = packets.parse_packets(self.buffer)
        if not data and len(self.buffer) > 5:
            if len(self.buffer) > 20 * 1024:
                print repr(self.buffer)
                exit()

        for header, payload in data:
            self.packlog.debug('recv', header, payload)
            name = packets.packets[header].name
            yield (name, header, payload)

#entity-(position|location|orientation)' | egrep -v '(create:|velocity:|chunk:|ping:|time:

class Derpbot(Singleton):
    def __init__(self):
        Singleton.__init__(self)

        loghandler.RootHandler(self)
        self.conn = Connection(self, SERVER, PORT, USERNAME)
        self.packhandler = self.conn.packhandler

        self.timers = TimerManager.get()
        self.storage = Storage.load()

        self.x = self.y = self.z = 0
        self.stance = 0
        self.yaw = 180
        self.pitch = 180
        self.flying = 1

        self.health = 0

        self.players = {} # by eid

        self.path = None

    def start(self):
        self.conn.connect()
        noop = lambda self, name, header, payload: None
        noop = noop.__get__(self)
        while True:
            for name, header, payload in self.conn.loop_iter():
                method = "on_%s" % name.replace("-", "_")
                fn = getattr(self, method, noop)
                fn(name, header, payload)

                try:
                    handlers = reload(__import__('handlers'))
                    fn2 = getattr(handlers, method, noop)(name, header, payload)
                except:
                    log.exception("Handler exception")

    def on_handshake(self, name, header, payload):
        self.conn.send_packet("login", protocol=9, username=USERNAME,
            unused='Password', seed=0, dimension=0)

    def on_ping(self, name, header, payload):
        self.conn.send_packet("ping")

    def chat(self, message):
        self.conn.send_packet("chat", message=message[:90])

if __name__ == '__main__':
    Derpbot().start()
