import time

from util import Singleton

class TimerManager(Singleton):
    instance = None

    def __init__(self):
        Singleton.__init__(self)
        self.list = []
        self.by_name = {}

    def add(self, timer):
        self.list.append(timer)
        self.by_name[timer.name] = timer

    def remove(self, timer):
        if timer in self.list:
            self.list.remove(timer)
        if timer.name in self.by_name:
            del self.by_name[timer.name]

    def reorder(self):
        self.list.sort(key=lambda x: x.next_timeout)

    def get_next_timeout(self):
        if self.list:
            return self.list[0].next_timeout

    def run_timers(self):
        for timer in self.list[:]:
            timer.trigger()

    @classmethod
    def get_timer(cls, name):
        return cls.get().by_name[name]

class Timer(object):
    def __init__(self, name, interval, *args, **kwargs):
        self.manager = TimerManager.get()
        self.next_timeout = -1

        self.name = name
        self.interval = interval
        self.args = args
        self.kwargs = kwargs

        self.target = kwargs.pop("target", lambda *args, **kwargs: None)
        self.repeat = kwargs.pop("repeat", True)

    def start(self):
        self.update_timeout()
        self.manager.add(self)

    def update_timeout(self):
        self.next_timeout = time.time() + self.interval
        self.manager.reorder()

    def trigger(self):
        if self.next_timeout > time.time():
            return

        self.run()

        if self.repeat:
            self.update_timeout()
        else:
            self.manager.remove(self)
    
    def run(self):
        self.target(*self.args, **self.kwargs)
