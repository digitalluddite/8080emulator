"""
implements a class that emulates the IO bus.  I guess (though I'm not positive)
that this will also then include "connections" to the graphics.
"""


class IOBus:
    def __init__(self):
        self.ports = {}

    def read(self, port):
        return self.ports.setdefault(port, 0)

    def write(self, port, val):
        self.ports[port] = val

