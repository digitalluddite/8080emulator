from unittest import TestCase

from machine import Machine8080
from machine import OutOfMemoryException

ROM_PATH = ""

class TestMachine8080(TestCase):
    def setUp(self):
        self.machine = Machine8080()
        self.machine.load()

    def test_read_memory(self):
        bytes = self.machine.read_memory(0, 10)
        self.assertTrue(len(bytes) == 10)
        with self.assertRaises(OutOfMemoryException):
            self.machine.read_memory(0xfff0, 100)
        bytes = self.machine.read_memory(0, 4)
        self.assertTrue(bytes == [0x00, 0x00, 0x00, 0xc3])
