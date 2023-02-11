class Numeric(str):
    """
    >>> val = Numeric('item', 3)
    >>> val
    'item'
    >>> int(val)
    3
    """

    def __new__(cls, text, val):
        return super().__new__(cls, text)

    def __init__(self, text, val):
        assert isinstance(val, int)
        self.val = val

    def __int__(self):
        return self.val


ONLINE = 'Online'
OFFLINE = 'Offline'

OPEN = Numeric('Open', 1)
CLOSED = Numeric('Closed', 0)


class Lock:
    OPEN = Numeric('LockOpen', 0)
    CLOSED = Numeric('LockClosed', 1)


ON = Numeric('On', 1)
OFF = Numeric('Off', 0)
