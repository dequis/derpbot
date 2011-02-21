import chat
reload(chat)
import handlers
from timer import Timer
from util import bind_to_derpbot

from construct import Container
import packets


import re
import random
import logging
log = logging.getLogger('handlers')

on_chat = chat.on_chat

@bind_to_derpbot
def on_spawn(self, name, header, payload):
    self.x = payload.x
    self.y = payload.y
    self.z = payload.z
    #self.stance = self.y + 1.62

@bind_to_derpbot
def on_location(self, name, header, payload):
    self.x = payload.position.x
    self.y = payload.position.y
    self.z = payload.position.z
    self.stance = payload.position.stance
    send_position(self, False)

@bind_to_derpbot
def send_position(self, change=True):
    if change and self.path:
        self.path.step()

    if not (0.1 < (self.stance - self.y) < 1.65):
        # avoid kicks
        self.stance = self.y + 1.62

    position = Container(x=self.x, y=self.stance, stance=self.y, z=self.z)
    look = Container(rotation=self.yaw, pitch=self.pitch)
    flying = Container(flying=self.flying)
   
    self.conn.send_packet("location",
        position=position,
        look=look,
        flying=flying)


@bind_to_derpbot
def on_handshake(self, name, header, payload):
    def reloader(self):
        import handlers
        reload(handlers)
        return handlers.send_position(self)
    Timer('position', 0.5, self, target=reloader).start()

class Player(object):
    def __init__(self, name, eid, x, y, z):
        self.name = name
        self.eid = eid
        self.x = x
        self.y = y
        self.z = z
        

@bind_to_derpbot
def on_player(self, name, header, payload):
    self.players[payload.eid] = Player(payload.username, payload.eid,
        payload.x / 32.0, payload.y / 32.0, payload.z / 32.0)

@bind_to_derpbot
def on_entity_position(self, name, header, payload):
    if payload.eid in self.players:
        player = self.players[payload.eid]
        player.x += payload.x / 32.0
        player.y += payload.y / 32.0
        player.z += payload.z / 32.0

@bind_to_derpbot
def on_entity_location(self, name, header, payload):
    if payload.eid in self.players:
        player = self.players[payload.eid]
        player.x += payload.x / 32.0
        player.y += payload.y / 32.0
        player.z += payload.z / 32.0

@bind_to_derpbot
def on_destroy(self, name, header, payload):
    if payload.eid in self.players:
        del self.players[payload.eid]

@bind_to_derpbot
def on_health(self, name, header, payload):
    newhealth = payload.hp / 2.0
    if newhealth < self.health:
        self.chat("ow! (health=%.1f)" % (newhealth))
    self.health = newhealth
