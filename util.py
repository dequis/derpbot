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