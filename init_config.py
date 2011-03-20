import sys
try:
    import config
except ImportError:
    import default_config
    sys.modules['config'] = default_config
