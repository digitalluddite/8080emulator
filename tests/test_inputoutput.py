from unittest import TestCase
import random
import logging

from machine import Machine8080
from cpu import Registers

class IoTest:
    def __init__(self):
        random.seed()
        self.ports = {}

    def read(self, port):
        return self.ports.setdefault(port, random.randint(0, 255))

    def write(self, port, val):
        self.ports[port] = val


class TestInputOutput(TestCase):
    def setUp(self):
        self.machine = Machine8080()
        self.machine.load('rom')
        self.machine._io = IoTest()
        logging.basicConfig(level=logging.DEBUG)

    def test_out(self):
        self.machine._registers[Registers.A] = 0x4f
        self.machine.out(0xd3, 0x2)
        self.machine._flags.clear_all() 
        self.assertEqual(self.machine._io.ports[2], 0x4f)
        for f in self.machine._flags:
            self.assertEqual(f, 0) 

    def test_in(self):
        self.machine._io.ports[1] = 0xab
        self.machine._flags.clear_all() 
        self.machine.input(0xdb, 1)
        self.assertEqual(self.machine._registers[Registers.A], 0xab)
        for f in self.machine._flags:
            self.assertEqual(f, 0)

