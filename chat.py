import re
import chat
import logging

log = logging.getLogger('chat')

chat_regexps = {
    'public': re.compile("^<(.+)> (.*)$"),
    'private': re.compile(r"^\xc3\x82\xc2\xa77(.+) whispers (.*)$"),
    'irc_public': re.compile(r"\[IRC\] <\xc2\xa7a(.*)\xc2\xa7f> (.*) $"),
    'irc_private': re.compile(r"\[IRC privmsg\] <\xc2\xa7a(.*)\xc2\xa7f> (.*) $"),
}

def on_chat(self, name, header, payload):
    log.info('Chat: %s', payload.message)
    for type, regex in chat_regexps.iteritems():
        match = regex.match(payload.message)
        if match:
            nick, message = match.groups()
            getattr(chat, "on_chat_%s" % type)(self, nick, message)
            break

def on_chat_public(self, nick, message):
    if message.startswith("!"):
        reply = lambda x: self.chat("%s: %s" % (nick, x))
        on_command_line(self, nick, message[1:], reply)

on_chat_irc_public = on_chat_public

def on_chat_private(self, nick, message):
    reply = lambda x: self.chat("/tell %s %s" % (nick, x))
    on_command_line(self, nick, message.lstrip("!"), reply)

def on_chat_irc_private(self, nick, message):
    reply = lambda x: self.chat("/ircw %s %s" % (nick, x))
    on_command_line(self, nick, message.lstrip("!"), reply)

def on_command_line(self, nick, cmdline, reply):
    log.info('Command: %s', cmdline)
    cmdname = cmdline.split()[0]
    args = ' '.join(cmdline.split()[1:])
    noop = lambda self, nick, args, reply: None
    getattr(chat, "cmd_%s" % cmdname, noop)(self, nick, args, reply)


### Commands

def cmd_say(self, nick, args, reply):
    reply(args)

def cmd_chat(self, nick, args, reply):
    if nick != 'dx':
        return
    self.chat(args)
    
def cmd_eval(self, nick, args, reply):
    if nick != 'dx':
        return

    try:
        try:
            reply(repr(eval(args)))
        except SyntaxError:
            exec args
    except:
        log.exception("!eval exception")
        reply("nope.avi")

def cmd_set(self, nick, args, reply):
    what, value = args.split()
    value = eval(value)
    if what in ['x', 'y', 'z', 'yaw', 'pitch']:
        setattr(self, what, value)

def cmd_respawn(self, nick, args, reply):
    self.conn.send_packet("respawn")

def cmd_whereis(self, nick, args, reply):
    p = find_player(self, args)
    if p:
        reply("found (eid=%s) at %.2f / %.2f / %.2f" % (p.eid, p.x, p.y, p.z))

def cmd_near(self, nick, args, reply):
    reply(', '.join([x.name for x in self.players.values()]))

def find_player(self, name):
    for p in self.players.values():
        if p.name == name:
            return p

def cmd_tp(self, nick, args, reply):
    p = find_player(self, args)
    if p:
        self.x = p.x + 1
        self.y = p.y
        self.z = p.z

def cmd_help(self, nick, args, reply):
    reply(', '.join([x[4:] for x in dir(chat) if x.startswith("cmd_")]))

def cmd_give(self, nick, args, reply):
    if nick == 'dx':
        self.chat("/give " + args)


def cmd_derp(self, nick, args, reply):
    args = args.split()
    x = int(args[0])
    y = int(args[1])
    z = int(args[2])
    text = ' '.join(args[3:]).split("\\n")
    text1 = text2 = text3 = text4 = ''
    try:
        text1 = text.pop(0)
        text2 = text.pop(0)
        text3 = text.pop(0)
        text4 = text.pop(0)
    except IndexError:
        pass
    #x = -1, y = 65, z = 13)
    self.conn.send_packet("sign",
        x=x, y=y, z=z,
        line1=text1, line2=text2,
        line3=text3, line4=text4,
    )

