class Singleton(object):
    '''Not really singleton but close'''
    instance = None

    def __init__(self):
        if type(self).instance is not None:
            raise TypeError("Already instantiated, use .get()")
        type(self).instance = self

    @classmethod
    def get(cls):
        return cls.instance or cls()

import __main__
def bind_to_derpbot(f):
    return f.__get__(__main__.Derpbot.get())

def bind_as_filter(f):
    derpproxy = __main__.ProxyServer.get()
    newfunc = f.__get__(derpproxy)

    modname = newfunc.__module__
    if modname.startswith("proxymods."):
        modname = modname.split(".", 1)[1]
    fullname = '%s.%s' % (modname, newfunc.__name__)

    derpproxy.filters[fullname] = newfunc
    return newfunc

class dict2(dict):
    __getattr__ = lambda *args: dict.__getitem__(*args)
    __setattr__ = lambda *args: dict.__setitem__(*args)
