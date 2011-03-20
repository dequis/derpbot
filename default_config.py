from util import dict2 as _dict2

logging = _dict2()
logging.filters = []

derpbot = _dict2()
derpbot.server = ('localhost', 25565)
derpbot.username = 'derpbot'

derpproxy = _dict2()
derpproxy.server = ('localhost', 25565)
derpproxy.proxy_bind = ('127.0.0.1', 25566)
