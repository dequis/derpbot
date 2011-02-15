import time
import logging
import packets
import traceback

from storage import Storage

class PacketHandler(logging.StreamHandler):
    def __init__(self, packlog):
        logging.StreamHandler.__init__(self)
        packlog.handlers = [self]
        packlog.propagate = 0

        self.filtered = Storage.get().setdefault('filtered', [])
        for name in ['chunk', 'entity-location', 'entity-orientation','entity-position','create','velocity','location','ping','time','animate','destroy','mob']:
            self.add_filter_by_name(name)

    def add_filter_by_name(self, name):
        header = packets.packets_by_name[name]
        if header not in self.filtered:
            self.filtered.append(header)

    def remove_filter_by_name(self, name):
        header = packets.packets_by_name[name]
        if header in self.filtered:
            self.filtered.remove(header)

    def filter(self, record):
        return (record.args[0] not in self.filtered)

    def format(self, record):
        header, payload = record.args
        payload = repr(payload).replace("\n", "")
        name = packets.packets[header].name

        return "%s %s (%02x/%03d) %s %s" % (time.strftime('%H:%M'),
            record.msg.capitalize(), header, header, name, payload)

class Formatter(logging.Formatter):
    def __init__(self):
        logging.Formatter.__init__(self)
        self.fmt = '%(asctime)s %(message)s'
        self.datefmt = '%H:%M'

class RootHandler(logging.StreamHandler):
    def __init__(self, derpbot):
        logging.StreamHandler.__init__(self)
        self.derpbot = derpbot
        self.last_exc = ''

        self.formatter = Formatter()

        logging.root.handlers = [self]
        logging.root.setLevel(0)
        self.setLevel(0)

    def emit(self, record):
        if record.exc_info:
            lastline = traceback.format_exception(*record.exc_info)[-1].strip()
            if self.last_exc != lastline:
                self.derpbot.chat(lastline)
                self.last_exc = lastline

        logging.StreamHandler.emit(self, record)
