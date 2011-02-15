import cPickle
from cStringIO import StringIO

from util import Singleton
from timer import Timer

STORAGE = 'storage.dat'

class Storage(Singleton, dict):
    _dirty = False
        
    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        if value and not self._dirty:
            Timer('storage', 15, target=self.save).start()
        self._dirty = True
    
    def wrap(l, names):
        for name in names:
            def f(self, *args):
                self.touch()
                return getattr(dict, name)(self, *args)
            l[name] = f
    wrap(locals(), ['__delitem__', '__setitem__', 'pop', 'popitem', 'setdefault'])
    del wrap

    def touch(self):
        '''You pervert'''
        self.dirty = True
    
    def __repr__(self):
        d = self.dirty and "dirty" or "clean"
        return "<Storage (%s): %s>" % (d, dict.__repr__(self))

    def save(self):
        if not self.dirty:
            return False

        self.dirty = False
        
        tmp = StringIO()
        try:
            cPickle.dump(self, tmp, protocol=2)
        except:
            raise
        else:
            open(STORAGE, "wb").write(tmp.getvalue())
    
    @classmethod
    def load(cls):
        if cls.instance is not None:
            return cls.instance
        try:
            return cls(cPickle.load(open(STORAGE, "rb")))
        except IOError:
            return cls()

def get():
    return Storage.get()

def init(bot):
    bot.storage = Storage.load()
